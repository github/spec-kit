"""Tests for GenericIntegration."""

import os
import shutil
import zipfile
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations.base import MarkdownIntegration
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.integration_state import write_integration_json
from specify_cli.extensions import ExtensionCatalog, ExtensionError, ExtensionManager
from specify_cli import save_init_options


@pytest.fixture
def generic_extension(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "extension.yml").write_text(yaml.safe_dump({
        "schema_version": "1.0",
        "extension": {
            "id": "sample", "name": "Sample", "version": "1.0.0",
            "description": "Sample commands", "author": "Test",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {"commands": [{
            "name": "speckit.sample.run",
            "file": "commands/run.md",
            "description": "Run sample",
        }]},
    }), encoding="utf-8")
    (source / "commands").mkdir()
    (source / "scripts").mkdir()
    (source / "scripts" / "run.sh").write_text("echo sample\n", encoding="utf-8")
    (source / "commands" / "run.md").write_text(
        "---\ndescription: Run sample\nscripts:\n  sh: scripts/run.sh\n---\n"
        "Execute {SCRIPT} with {ARGS}; see scripts/run.sh. "
        "Then __SPECKIT_COMMAND_TASKS__.\n",
        encoding="utf-8",
    )
    return source


def generic_project(tmp_path, *, skills=False, commands_dir=".custom/commands"):
    project = tmp_path / "project"
    project.mkdir()
    opts = {"commands_dir": commands_dir, "skills": skills}
    integration = get_integration("generic")
    manifest = IntegrationManifest("generic", project)
    integration.setup(project, manifest, parsed_options=opts)
    manifest.save()
    write_integration_json(
        project, version="1.0.0", integration_key="generic",
        settings={"generic": {"parsed_options": opts}},
    )
    save_init_options(project, {"ai": "generic", "ai_skills": skills, "script": "sh"})
    return project


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_lifecycle(tmp_path, generic_extension, skills):
    project = generic_project(
        tmp_path, skills=skills,
        commands_dir=".custom/skills" if skills else ".custom/commands",
    )
    output_dir = project / ".custom" / ("skills" if skills else "commands")
    core = output_dir / ("speckit-taskstoissues/SKILL.md" if skills else "speckit.taskstoissues.md")
    core_content = core.read_bytes()
    unrelated = output_dir / ("user-skill/SKILL.md" if skills else "user.md")
    unrelated.parent.mkdir(parents=True, exist_ok=True)
    unrelated.write_text("user-owned", encoding="utf-8")
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    artifact = output_dir / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    assert artifact.is_file()
    content = artifact.read_text(encoding="utf-8")
    assert ".specify/extensions/sample/scripts/run.sh" in content
    assert "{SCRIPT}" not in content
    assert "$ARGUMENTS" in content
    assert ("/speckit-tasks" if skills else "/speckit.tasks") in content
    manager.register_enabled_extensions_for_agent("generic")
    assert artifact.read_text(encoding="utf-8") == content
    if skills:
        sibling = artifact.parent / "user-notes.md"
        sibling.write_text("keep this", encoding="utf-8")
    assert manager.remove("sample")
    assert not artifact.exists()
    if skills:
        assert sibling.read_text(encoding="utf-8") == "keep this"
    assert core.read_bytes() == core_content
    assert unrelated.read_text(encoding="utf-8") == "user-owned"


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_preserves_modified_artifact(tmp_path, generic_extension, skills):
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    artifact.write_text(artifact.read_text(encoding="utf-8") + "\nuser edit\n", encoding="utf-8")
    assert manager.remove("sample")
    assert artifact.read_text(encoding="utf-8").endswith("user edit\n")


@pytest.mark.parametrize("operation", ["resync", "remove", "force"])
def test_generic_skill_symlinked_directory_is_not_owned(
    tmp_path, generic_extension, operation,
):
    project = generic_project(tmp_path, skills=True)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    skill_dir = project / ".custom/commands/speckit-sample-run"
    other_dir = project / "moved-skill"
    skill_dir.rename(other_dir)
    try:
        skill_dir.symlink_to(other_dir, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")
    other_skill = other_dir / "SKILL.md"
    original = other_skill.read_bytes()

    if operation == "resync":
        source = manager.extensions_dir / "sample/commands/run.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nnew source\n", encoding="utf-8")
        manager.register_enabled_extensions_for_agent("generic", force=True)
        assert manager._generic_owned_names(
            manager.registry.get("sample"), ["speckit-sample-run"], skills=True,
        ) == []
    elif operation == "force":
        with pytest.raises(ExtensionError, match="cannot be replaced safely"):
            manager.install_from_directory(generic_extension, "1.0.0", force=True)
        assert manager.registry.is_installed("sample")

    if operation != "force":
        assert manager.remove("sample")
    assert skill_dir.is_symlink()
    assert other_skill.read_bytes() == original


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_rejects_modified_artifact_on_disable(
    tmp_path, generic_extension, skills,
):
    from typer.testing import CliRunner
    from specify_cli import app

    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    artifact.write_text("user edit", encoding="utf-8")
    manager.register_enabled_extensions_for_agent("generic")
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        result = CliRunner().invoke(app, ["extension", "disable", "sample"])
    finally:
        os.chdir(old_cwd)
    assert result.exit_code == 1
    assert "modified or is not owned" in result.output
    assert artifact.read_text(encoding="utf-8") == "user edit"
    assert manager.registry.get("sample")["enabled"] is True


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_reports_missing_registration_options(
    tmp_path, generic_extension, skills,
):
    project = generic_project(tmp_path, skills=skills)
    (project / ".specify/integration.json").unlink()
    with pytest.raises(ExtensionError, match="generic"):
        ExtensionManager(project).install_from_directory(generic_extension, "1.0.0")
    assert not ExtensionManager(project).registry.is_installed("sample")


@pytest.mark.parametrize("invalid_settings", ["missing", "malformed"])
def test_generic_skills_remove_with_invalid_settings(
    tmp_path, generic_extension, invalid_settings,
):
    project = generic_project(tmp_path, skills=True)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    skill = project / ".custom/commands/speckit-sample-run/SKILL.md"
    other_root = project / ".github/skills/speckit-sample-run/SKILL.md"
    other_root.parent.mkdir(parents=True)
    other_root.write_bytes(skill.read_bytes())
    state_file = project / ".specify/integration.json"
    if invalid_settings == "missing":
        state_file.unlink()
    else:
        state_file.write_text("{", encoding="utf-8")

    assert manager.remove("sample")
    assert not skill.exists()
    assert not other_root.exists()
    assert not manager.registry.is_installed("sample")


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_after_cli_init(tmp_path, generic_extension, skills):
    from typer.testing import CliRunner
    from specify_cli import app

    project = tmp_path / "initialized"
    project.mkdir()
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        result = CliRunner().invoke(app, [
            "init", "--here", "--integration", "generic",
            "--integration-options=--commands-dir .myagent/commands" + (
                " --skills" if skills else ""
            ),
            "--script", "sh",
        ], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)
    assert result.exit_code == 0, result.output
    runner = CliRunner()
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        installed = runner.invoke(
            app, ["extension", "add", str(generic_extension), "--dev"]
        )
        assert installed.exit_code == 0, installed.output
    finally:
        os.chdir(old_cwd)
    output = project / ".myagent/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    assert output.is_file()
    try:
        os.chdir(project)
        removed = runner.invoke(app, ["extension", "remove", "sample", "--force"])
        assert removed.exit_code == 0, removed.output
    finally:
        os.chdir(old_cwd)
    assert not output.exists()


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_remove_after_directory_upgrade(
    tmp_path, generic_extension, skills,
):
    from typer.testing import CliRunner
    from specify_cli import app

    project = tmp_path / "upgrade"
    project.mkdir()
    runner = CliRunner()
    suffix = " --skills" if skills else ""
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        init = runner.invoke(app, [
            "init", "--here", "--integration", "generic",
            f"--integration-options=--commands-dir .old/output{suffix}",
            "--script", "sh",
        ], catch_exceptions=False)
        assert init.exit_code == 0, init.output
        manager = ExtensionManager(project)
        manager.install_from_directory(generic_extension, "1.0.0")
        name = "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
        old_output = project / ".old/output" / name
        assert old_output.is_file()
        upgrade = runner.invoke(app, [
            "integration", "upgrade", "generic", "--force",
            f"--integration-options=--commands-dir .new/output{suffix}",
        ], catch_exceptions=False)
        assert upgrade.exit_code == 0, upgrade.output
        new_output = project / ".new/output" / name
        assert new_output.is_file()
        manager = ExtensionManager(project)
        assert f".new/output/{name}" in manager.registry.get("sample")["generic_artifact_hashes"]
        assert manager.remove("sample")
        assert not old_output.exists()
        assert not new_output.exists()
    finally:
        os.chdir(old_cwd)


@pytest.mark.parametrize("replacement_content", [
    "replacement with different bytes",
    "---\nmetadata:\n  source: extension:sample\n---\nedited generated skill",
])
def test_generic_skills_upgrade_preserves_replaced_or_modified_skill(
    tmp_path, generic_extension, replacement_content,
):
    from typer.testing import CliRunner
    from specify_cli import app

    project = tmp_path / "upgrade-preserves-edited-skill"
    project.mkdir()
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        runner = CliRunner()
        initialized = runner.invoke(app, [
            "init", "--here", "--integration", "generic",
            "--integration-options=--commands-dir .custom/skills --skills",
            "--script", "sh",
        ], catch_exceptions=False)
        assert initialized.exit_code == 0, initialized.output

        manager = ExtensionManager(project)
        manager.install_from_directory(generic_extension, "1.0.0")
        skill = project / ".custom/skills/speckit-sample-run/SKILL.md"
        assert skill.is_file()
        skill.write_text(replacement_content, encoding="utf-8")

        upgraded = runner.invoke(app, [
            "integration", "upgrade", "generic", "--force",
            "--integration-options=--commands-dir .custom/skills --skills",
        ], catch_exceptions=False)
        assert upgraded.exit_code == 0, upgraded.output
        assert skill.read_text(encoding="utf-8") == replacement_content
    finally:
        os.chdir(old_cwd)


def test_generic_skills_upgrade_refreshes_artifact_digest(
    tmp_path, generic_extension,
):
    from typer.testing import CliRunner
    from specify_cli import app

    project = generic_project(tmp_path, skills=True)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    skill = project / ".custom/commands/speckit-sample-run/SKILL.md"
    relative = skill.relative_to(project).as_posix()
    original_digest = manager.registry.get("sample")["generic_artifact_hashes"][relative]
    source = manager.extensions_dir / "sample/commands/run.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nupdated source\n", encoding="utf-8")

    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        upgraded = CliRunner().invoke(app, [
            "integration", "upgrade", "generic", "--force",
            "--integration-options=--commands-dir .custom/commands --skills",
        ], catch_exceptions=False)
        assert upgraded.exit_code == 0, upgraded.output
    finally:
        os.chdir(old_cwd)

    assert "updated source" in skill.read_text(encoding="utf-8")
    manager = ExtensionManager(project)
    current_digest = manager.registry.get("sample")["generic_artifact_hashes"][relative]
    assert current_digest != original_digest
    assert current_digest == sha256(skill.read_bytes()).hexdigest()
    assert manager.remove("sample")
    assert not skill.exists()


def test_generic_command_refreshes_owned_artifact_and_missing_alias(
    tmp_path, generic_extension,
):
    manifest_path = generic_extension / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["commands"][0]["aliases"] = ["speckit.sample.alias"]
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    project = generic_project(tmp_path)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    output = project / ".custom/commands"
    primary = output / "speckit.sample.run.md"
    alias = output / "speckit.sample.alias.md"
    assert primary.is_file() and alias.is_file()
    alias.unlink()
    source = manager.extensions_dir / "sample/commands/run.md"
    source.write_text(source.read_text(encoding="utf-8") + "\nnew content\n", encoding="utf-8")

    manager.register_enabled_extensions_for_agent("generic")

    assert "new content" in primary.read_text(encoding="utf-8")
    assert "new content" in alias.read_text(encoding="utf-8")
    hashes = manager.registry.get("sample")["generic_artifact_hashes"]
    assert hashes[primary.relative_to(project).as_posix()] == sha256(primary.read_bytes()).hexdigest()
    assert hashes[alias.relative_to(project).as_posix()] == sha256(alias.read_bytes()).hexdigest()
    assert manager.remove("sample")
    assert not primary.exists() and not alias.exists()


@pytest.mark.parametrize("skills", [False, True])
@pytest.mark.parametrize("ignored_source", [False, True])
def test_generic_partial_registration_rolls_back_all_artifacts(
    tmp_path, generic_extension, skills, ignored_source,
):
    manifest_path = generic_extension / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["commands"].append({
        "name": "speckit.sample.missing",
        "file": "commands/missing.md",
        "description": "Missing source",
    })
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    if ignored_source:
        (generic_extension / "commands/missing.md").write_text(
            "---\ndescription: Missing source\n---\ncontent\n", encoding="utf-8",
        )
        (generic_extension / ".extensionignore").write_text(
            "commands/missing.md\n", encoding="utf-8",
        )
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)

    with pytest.raises(ExtensionError, match="missing"):
        manager.install_from_directory(generic_extension, "1.0.0")

    output = project / ".custom/commands"
    assert not (output / ("speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md")).exists()
    assert not (manager.extensions_dir / "sample").exists()
    assert not manager.registry.is_installed("sample")
    (generic_extension / "commands/missing.md").write_text(
        "---\ndescription: Resolved source\n---\ncontent\n", encoding="utf-8",
    )
    (generic_extension / ".extensionignore").unlink(missing_ok=True)
    manager.install_from_directory(generic_extension, "1.0.0")
    assert manager.registry.is_installed("sample")
    assert manager.remove("sample")


@pytest.mark.parametrize("skills", [False, True])
def test_generic_registration_write_error_rolls_back_partial_install(
    tmp_path, generic_extension, skills, monkeypatch,
):
    manifest_path = generic_extension / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["commands"].append({
        "name": "speckit.sample.other",
        "file": "commands/other.md",
        "description": "Another command",
    })
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (generic_extension / "commands/other.md").write_text(
        "---\ndescription: Another command\n---\ncontent\n", encoding="utf-8",
    )
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    output_dir = project / ".custom/commands"
    first = output_dir / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    second = output_dir / (
        "speckit-sample-other/SKILL.md" if skills else "speckit.sample.other.md"
    )
    original_write = Path.write_text

    def fail_second_write(path, *args, **kwargs):
        if path == second:
            raise OSError("simulated artifact write error")
        return original_write(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_second_write)
    with pytest.raises(OSError, match="simulated artifact write error"):
        manager.install_from_directory(generic_extension, "1.0.0")
    monkeypatch.undo()

    assert not first.exists()
    assert not second.exists()
    assert not (manager.extensions_dir / "sample").exists()
    assert not manager.registry.is_installed("sample")
    manager.install_from_directory(generic_extension, "1.0.0")
    assert first.is_file() and second.is_file()
    assert manager.remove("sample")


def test_generic_failed_registration_preserves_reinstall_config(
    tmp_path, generic_extension,
):
    (generic_extension / "sample-config.yml").write_text(
        "default: true\n", encoding="utf-8",
    )
    project = generic_project(tmp_path)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0", register_commands=False)
    assert manager.remove("sample", keep_config=True)
    config = manager.extensions_dir / "sample/sample-config.yml"
    config.write_text("user: preserved\n", encoding="utf-8")

    manifest_path = generic_extension / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["commands"].append({
        "name": "speckit.sample.other",
        "file": "commands/other.md",
        "description": "Another command",
    })
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (generic_extension / "commands/other.md").write_text(
        "---\ndescription: Another command\n---\ncontent\n", encoding="utf-8",
    )
    (generic_extension / ".extensionignore").write_text(
        "commands/other.md\n", encoding="utf-8",
    )
    with pytest.raises(ExtensionError, match="missing invocation artifacts"):
        manager.install_from_directory(generic_extension, "1.0.0")

    assert config.read_text(encoding="utf-8") == "user: preserved\n"
    assert (config.parent / ".keep-config").exists()
    assert not (config.parent / "extension.yml").exists()
    assert not (project / ".custom/commands/speckit.sample.run.md").exists()
    (generic_extension / ".extensionignore").unlink()
    manager.install_from_directory(generic_extension, "1.0.0")
    assert config.read_text(encoding="utf-8") == "user: preserved\n"
    assert manager.remove("sample")


def test_generic_extension_skills_accepts_project_alias(tmp_path, generic_extension):
    project = generic_project(tmp_path, skills=True)
    alias = tmp_path / "project-alias"
    try:
        alias.symlink_to(project, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")

    manager = ExtensionManager(alias)
    manager.install_from_directory(generic_extension, "1.0.0")
    skill = alias / ".custom/commands/speckit-sample-run/SKILL.md"
    assert skill.is_file()
    assert manager.remove("sample")
    assert not skill.exists()


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_does_not_overwrite_existing_command_or_skill(
    tmp_path, generic_extension, skills,
):
    project = generic_project(tmp_path, skills=skills)
    output = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("<!-- Extension: sample -->\nmy own command", encoding="utf-8")
    with pytest.raises(ExtensionError, match="cannot be replaced safely"):
        ExtensionManager(project).install_from_directory(generic_extension, "1.0.0")
    assert output.read_text(encoding="utf-8") == "<!-- Extension: sample -->\nmy own command"
    manager = ExtensionManager(project)
    assert not manager.registry.is_installed("sample")
    assert not (manager.extensions_dir / "sample").exists()
    output.unlink()
    if skills:
        output.parent.rmdir()
    manager.install_from_directory(generic_extension, "1.0.0")
    assert manager.registry.is_installed("sample")
    assert manager.remove("sample")


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_force_reinstall_only_replaces_owned_artifacts(
    tmp_path, generic_extension, skills,
):
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    manager.install_from_directory(generic_extension, "1.0.0", force=True)
    assert artifact.is_file()
    assert manager.remove("sample")
    assert not artifact.exists()


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_force_reinstall_preserves_edited_artifacts(
    tmp_path, generic_extension, skills,
):
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    artifact.write_text("edited output", encoding="utf-8")
    with pytest.raises(ExtensionError, match="cannot be replaced safely"):
        manager.install_from_directory(generic_extension, "1.0.0", force=True)
    assert artifact.read_text(encoding="utf-8") == "edited output"
    assert manager.registry.is_installed("sample")
    assert (manager.extensions_dir / "sample/extension.yml").is_file()


@pytest.mark.parametrize("skills", [False, True])
@pytest.mark.parametrize("fail_install", [False, True])
@pytest.mark.parametrize("disabled", [False, True])
def test_generic_extension_update_uses_project_registrar(
    tmp_path, generic_extension, skills, fail_install, disabled,
):
    from typer.testing import CliRunner
    from specify_cli import app

    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    original = artifact.read_bytes()
    if disabled:
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, ["extension", "disable", "sample"])
            assert result.exit_code == 0, result.output
        finally:
            os.chdir(old_cwd)
        assert not artifact.exists()
    updated_source = tmp_path / "updated-source"
    shutil.copytree(generic_extension, updated_source)
    manifest_path = updated_source / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["extension"]["version"] = "2.0.0"
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    command_file = updated_source / "commands/run.md"
    command_file.write_text(
        command_file.read_text(encoding="utf-8") + "\nupdated command\n",
        encoding="utf-8",
    )
    archive = tmp_path / "sample-update.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        for file in updated_source.rglob("*"):
            if file.is_file():
                zip_file.write(file, file.relative_to(updated_source))

    def install_update(self, _zip_path, speckit_version, *, catalog_name=None):
        if fail_install:
            raise RuntimeError("simulated update failure")
        return self.install_from_directory(
            updated_source, speckit_version, catalog_name=catalog_name
        )

    with (
        patch.object(Path, "cwd", return_value=project),
        patch.object(ExtensionCatalog, "get_extension_info", return_value={
            "id": "sample",
            "name": "Sample",
            "version": "2.0.0",
            "_install_allowed": True,
        }),
        patch.object(ExtensionCatalog, "download_extension", return_value=archive),
        patch.object(ExtensionManager, "install_from_zip", install_update),
    ):
        result = CliRunner().invoke(
            app, ["extension", "update", "sample"], input="y\n",
        )

    manager = ExtensionManager(project)
    if fail_install:
        assert result.exit_code == 1
        assert "simulated update failure" in result.output
        assert manager.registry.get("sample")["version"] == "1.0.0"
        if disabled:
            assert not artifact.exists()
        else:
            assert artifact.read_bytes() == original
    else:
        assert result.exit_code == 0, result.output
        assert manager.registry.get("sample")["version"] == "2.0.0"
        if disabled:
            assert not artifact.exists()
            old_cwd = os.getcwd()
            try:
                os.chdir(project)
                enabled = CliRunner().invoke(app, ["extension", "enable", "sample"])
                assert enabled.exit_code == 0, enabled.output
            finally:
                os.chdir(old_cwd)
            assert "updated command" in artifact.read_text(encoding="utf-8")
        else:
            assert artifact.read_bytes() != original
            assert "updated command" in artifact.read_text(encoding="utf-8")
    assert ExtensionManager(project).registry.get("sample")["enabled"] is (
        not (disabled and fail_install)
    )
    manager = ExtensionManager(project)
    assert manager.remove("sample")
    assert not artifact.exists()


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_rejects_escaping_directory(
    tmp_path, generic_extension, skills,
):
    project = generic_project(tmp_path, skills=skills)
    write_integration_json(
        project, version="1.0.0", integration_key="generic",
        settings={"generic": {"parsed_options": {"commands_dir": "../outside"}}},
    )
    with pytest.raises(ExtensionError, match="escapes project root"):
        ExtensionManager(project).install_from_directory(generic_extension, "1.0.0")
    assert not (tmp_path / "outside").exists()
    assert not ExtensionManager(project).registry.is_installed("sample")


@pytest.mark.parametrize("skills", [False, True])
def test_generic_dev_extension_removes_links(tmp_path, generic_extension, skills):
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0", link_commands=True)
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    assert artifact.is_file()
    assert manager.remove("sample")
    assert not artifact.exists()
    assert not artifact.is_symlink()


@pytest.mark.parametrize("skills", [False, True])
def test_generic_dev_extension_preserves_edited_link(tmp_path, generic_extension, skills):
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0", link_commands=True)
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    if not artifact.is_symlink():
        pytest.skip("symlink creation is unavailable")
    artifact.write_text("user edit", encoding="utf-8")
    assert manager.remove("sample")
    assert not artifact.is_symlink()
    assert artifact.read_text(encoding="utf-8") == "user edit"


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_disable_and_enable(tmp_path, generic_extension, skills):
    from typer.testing import CliRunner
    from specify_cli import app

    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    output = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        runner = CliRunner()
        disabled = runner.invoke(app, ["extension", "disable", "sample"])
        assert disabled.exit_code == 0, disabled.output
        assert not output.exists()
        assert (project / ".specify/extensions/sample/extension.yml").exists()
        enabled = runner.invoke(app, ["extension", "enable", "sample"])
        assert enabled.exit_code == 0, enabled.output
        assert output.is_file()
    finally:
        os.chdir(old_cwd)


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_enable_reports_colliding_user_file(
    tmp_path, generic_extension, skills,
):
    from typer.testing import CliRunner
    from specify_cli import app

    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    artifact = project / ".custom/commands" / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        runner = CliRunner()
        disabled = runner.invoke(app, ["extension", "disable", "sample"])
        assert disabled.exit_code == 0, disabled.output
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("user-owned", encoding="utf-8")
        enabled = runner.invoke(app, ["extension", "enable", "sample"])
    finally:
        os.chdir(old_cwd)
    assert enabled.exit_code == 1
    assert "Could not register generic invocations" in enabled.output
    assert artifact.read_text(encoding="utf-8") == "user-owned"
    assert ExtensionManager(project).registry.get("sample")["enabled"] is False


@pytest.mark.parametrize("skills", [False, True])
def test_generic_extension_enable_rejects_partial_registration(
    tmp_path, generic_extension, skills,
):
    from typer.testing import CliRunner
    from specify_cli import app

    manifest_path = generic_extension / "extension.yml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["provides"]["commands"].append({
        "name": "speckit.sample.other",
        "file": "commands/other.md",
        "description": "Another command",
    })
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (generic_extension / "commands/other.md").write_text(
        "---\ndescription: Another command\n---\ncontent\n", encoding="utf-8",
    )
    project = generic_project(tmp_path, skills=skills)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    output = project / ".custom/commands"
    collision = output / (
        "speckit-sample-run/SKILL.md" if skills else "speckit.sample.run.md"
    )
    other = output / (
        "speckit-sample-other/SKILL.md" if skills else "speckit.sample.other.md"
    )
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        runner = CliRunner()
        assert runner.invoke(app, ["extension", "disable", "sample"]).exit_code == 0
        collision.parent.mkdir(parents=True, exist_ok=True)
        collision.write_text("edited replacement", encoding="utf-8")
        enabled = runner.invoke(app, ["extension", "enable", "sample"])
        assert enabled.exit_code == 1
        assert "Could not register generic invocations" in enabled.output
        assert collision.read_text(encoding="utf-8") == "edited replacement"
        assert not other.exists()
        assert ExtensionManager(project).registry.get("sample")["enabled"] is False
        collision.unlink()
        if skills:
            collision.parent.rmdir()
        enabled = runner.invoke(app, ["extension", "enable", "sample"])
        assert enabled.exit_code == 0, enabled.output
    finally:
        os.chdir(old_cwd)
    assert collision.is_file() and other.is_file()


@pytest.mark.parametrize("invalid_settings", ["missing", "malformed"])
def test_generic_extension_enable_failure_restores_disabled_state(
    tmp_path, generic_extension, invalid_settings,
):
    from typer.testing import CliRunner
    from specify_cli import app

    project = generic_project(tmp_path)
    manager = ExtensionManager(project)
    manager.install_from_directory(generic_extension, "1.0.0")
    output = project / ".custom/commands/speckit.sample.run.md"
    state_file = project / ".specify/integration.json"
    original_state = state_file.read_bytes()
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        runner = CliRunner()
        assert runner.invoke(app, ["extension", "disable", "sample"]).exit_code == 0
        if invalid_settings == "missing":
            state_file.unlink()
        else:
            state_file.write_text("{", encoding="utf-8")
        result = runner.invoke(app, ["extension", "enable", "sample"])
        assert result.exit_code == 1
        assert "Could not register generic invocations" in result.output
        assert not output.exists()
        assert ExtensionManager(project).registry.get("sample")["enabled"] is False
        state_file.write_bytes(original_state)
        assert runner.invoke(app, ["extension", "enable", "sample"]).exit_code == 0
        assert output.is_file()
    finally:
        os.chdir(old_cwd)


class TestGenericIntegration:
    """Tests for GenericIntegration — requires --commands-dir option."""

    # -- Registration -----------------------------------------------------

    def test_registered(self):
        from specify_cli.integrations import INTEGRATION_REGISTRY
        assert "generic" in INTEGRATION_REGISTRY

    def test_is_markdown_integration(self):
        assert isinstance(get_integration("generic"), MarkdownIntegration)

    # -- Config -----------------------------------------------------------

    def test_config_folder_is_none(self):
        i = get_integration("generic")
        assert i.config["folder"] is None

    def test_config_requires_cli_false(self):
        i = get_integration("generic")
        assert i.config["requires_cli"] is False

    # -- Options ----------------------------------------------------------

    def test_options_include_commands_dir(self):
        i = get_integration("generic")
        opts = i.options()
        assert len(opts) == 2
        assert opts[0].name == "--commands-dir"
        assert opts[0].required is True
        assert opts[0].is_flag is False

    def test_options_include_skills_flag(self):
        i = get_integration("generic")
        opts = i.options()
        skills_opt = next(o for o in opts if o.name == "--skills")
        assert skills_opt.is_flag is True
        assert skills_opt.required is False
        assert skills_opt.default is False

    # -- Setup / teardown -------------------------------------------------

    def test_setup_requires_commands_dir(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        with pytest.raises(ValueError, match="--commands-dir is required"):
            i.setup(tmp_path, m, parsed_options={})

    def test_setup_requires_nonempty_commands_dir(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        with pytest.raises(ValueError, match="--commands-dir is required"):
            i.setup(tmp_path, m, parsed_options={"commands_dir": ""})

    @pytest.mark.parametrize("blank", ["  ", "\t"])
    def test_resolve_commands_dir_rejects_blank_parsed_value(self, blank):
        """A whitespace-only value must raise too: it resolves to a directory
        literally named " ", scattering command files just like the empty case."""
        from specify_cli.integrations.generic import GenericIntegration

        with pytest.raises(ValueError, match="--commands-dir is required"):
            GenericIntegration._resolve_commands_dir({"commands_dir": blank}, {})

    @pytest.mark.parametrize(
        "raw", ["--commands-dir ' '", "--commands-dir='  '", "--commands-dir '\t'"]
    )
    def test_resolve_commands_dir_rejects_blank_raw_value(self, raw):
        """Same rule on the raw_options branch, so the two cannot drift apart."""
        from specify_cli.integrations.generic import GenericIntegration

        with pytest.raises(ValueError, match="--commands-dir is required"):
            GenericIntegration._resolve_commands_dir({}, {"raw_options": raw})

    @pytest.mark.parametrize("padded", ["  .myagent/cmds  ", "\t.myagent/cmds"])
    def test_resolve_commands_dir_returns_padded_value_verbatim(self, padded):
        """A padded but non-blank value is accepted and returned UNCHANGED: the
        blankness test uses strip(), but rewriting the value would silently
        retarget a directory the user asked for by name."""
        from specify_cli.integrations.generic import GenericIntegration

        assert GenericIntegration._resolve_commands_dir(
            {"commands_dir": padded}, {}
        ) == padded
        # Quoted in raw_options, since shlex.split() would otherwise consume the
        # surrounding whitespace before this code ever sees it.
        assert GenericIntegration._resolve_commands_dir(
            {}, {"raw_options": f"--commands-dir='{padded}'"}
        ) == padded

    @pytest.mark.parametrize("raw", ["--commands-dir=", "--commands-dir ''", '--commands-dir ""'])
    def test_resolve_commands_dir_rejects_empty_raw_value(self, raw):
        """An empty --commands-dir in raw_options must raise the same "required"
        error as the parsed-options path — not return "" (which resolves to the
        project root and writes command files there). Mirrors the parsed branch."""
        from specify_cli.integrations.generic import GenericIntegration

        with pytest.raises(ValueError, match="--commands-dir is required"):
            GenericIntegration._resolve_commands_dir({}, {"raw_options": raw})

    def test_resolve_commands_dir_accepts_nonempty_raw_value(self):
        """A non-empty raw --commands-dir still resolves unchanged."""
        from specify_cli.integrations.generic import GenericIntegration

        assert GenericIntegration._resolve_commands_dir(
            {}, {"raw_options": "--commands-dir .myagent/commands"}
        ) == ".myagent/commands"
        assert GenericIntegration._resolve_commands_dir(
            {}, {"raw_options": "--commands-dir=.myagent/commands"}
        ) == ".myagent/commands"

    def test_setup_writes_to_correct_directory(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/commands"},
        )
        expected_dir = tmp_path / ".myagent" / "commands"
        assert expected_dir.exists(), f"Expected directory {expected_dir} was not created"
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) > 0, "No command files were created"
        for f in cmd_files:
            assert f.resolve().parent == expected_dir.resolve(), (
                f"{f} is not under {expected_dir}"
            )

    def test_setup_creates_md_files(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) > 0
        for f in cmd_files:
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".md")

    def test_templates_are_processed(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, f"{f.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{f.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{f.name} has unprocessed {{ARGS}}"
            assert "__SPECKIT_COMMAND_" not in content, f"{f.name} has unprocessed __SPECKIT_COMMAND_*__"

    def test_all_files_tracked_in_manifest(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.install(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = i.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []

    def test_modified_file_survives_uninstall(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.install(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        m.save()
        modified = created[0]
        modified.write_text("user modified this", encoding="utf-8")
        removed, skipped = i.uninstall(tmp_path, m)
        assert modified.exists()
        assert modified in skipped

    def test_different_commands_dirs(self, tmp_path):
        """Generic should work with various user-specified paths."""
        for path in [".agent/commands", "tools/ai-cmds", ".custom/prompts"]:
            project = tmp_path / path.replace("/", "-")
            project.mkdir()
            i = get_integration("generic")
            m = IntegrationManifest("generic", project)
            created = i.setup(
                project, m,
                parsed_options={"commands_dir": path},
            )
            expected = project / path
            assert expected.is_dir(), f"Dir {expected} not created for {path}"
            cmd_files = [f for f in created if "scripts" not in f.parts]
            assert len(cmd_files) > 0

    # -- Skills mode --------------------------------------------------------

    def test_setup_writes_skill_md_when_skills_flag_set(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/skills", "skills": True},
        )
        skill_files = [f for f in created if "scripts" not in f.parts]
        assert len(skill_files) > 0
        for f in skill_files:
            assert f.name == "SKILL.md"
            assert f.parent.name.startswith("speckit-")
            assert f.parent.parent == tmp_path / ".myagent" / "skills"

    def test_skill_content_has_expected_frontmatter(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/skills", "skills": True},
        )
        plan_skill = tmp_path / ".myagent" / "skills" / "speckit-plan" / "SKILL.md"
        assert plan_skill.exists()
        content = plan_skill.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert 'name: "speckit-plan"' in content
        assert "description:" in content
        assert "compatibility:" in content
        assert "{SCRIPT}" not in content
        assert "__AGENT__" not in content
        assert "__SPECKIT_COMMAND_" not in content

    def test_skill_content_has_hook_command_note(self, tmp_path):
        """SKILL.md bodies get the shared dot-to-hyphen hook invocation
        note, matching what SkillsIntegration.setup() produces for other
        skills-format agents (e.g. Claude)."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/skills", "skills": True},
        )
        constitution_skill = (
            tmp_path / ".myagent" / "skills" / "speckit-constitution" / "SKILL.md"
        )
        assert constitution_skill.exists()
        content = constitution_skill.read_text(encoding="utf-8")
        assert (
            "replace dots (`.`) with hyphens (`-`)" in content
        ), "generic --skills output is missing the hook-invocation note"
        assert "`speckit.git.commit` → `/speckit-git-commit`" in content

    def test_skills_flag_false_keeps_flat_markdown(self, tmp_path):
        """Without --skills, behavior is unchanged: flat speckit.<name>.md files."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/commands", "skills": False},
        )
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) > 0
        for f in cmd_files:
            assert f.name.endswith(".md")
            assert f.name.startswith("speckit.")
            assert f.parent == tmp_path / ".myagent" / "commands"

    def test_skill_files_tracked_in_manifest(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/skills", "skills": True},
        )
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_skills_install_uninstall_roundtrip(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.install(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/skills", "skills": True},
        )
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = i.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []

    # -- Context section ---------------------------------------------------

    def test_setup_does_not_write_context_section(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        for path in tmp_path.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert "<!-- SPECKIT START -->" not in text

    def test_plan_command_has_no_context_placeholder(self, tmp_path):
        """The core plan command must not carry a context-file placeholder —
        agent context files are owned by the opt-in agent-context extension."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        plan_file = tmp_path / ".custom" / "cmds" / "speckit.plan.md"
        assert plan_file.exists()
        content = plan_file.read_text(encoding="utf-8")
        assert "__CONTEXT_FILE__" not in content

    def test_plan_defines_quickstart_as_validation_guide(self, tmp_path):
        """The generated plan command should keep quickstart.md out of implementation scope."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        plan_file = tmp_path / ".custom" / "cmds" / "speckit.plan.md"
        assert plan_file.exists()
        content = plan_file.read_text(encoding="utf-8")

        assert "Create quickstart validation guide" in content
        assert "runnable validation scenarios" in content
        assert "Do not include full implementation code" in content
        assert "implementation details belong in `tasks.md` and the implementation phase" in content

    def test_implement_loads_constitution_context(self, tmp_path):
        """The generated implement command should load constitution governance context."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        implement_file = tmp_path / ".custom" / "cmds" / "speckit.implement.md"
        assert implement_file.exists()
        content = implement_file.read_text(encoding="utf-8")
        assert ".specify/memory/constitution.md" in content

    @pytest.mark.parametrize(
        "command_stem",
        [
            "analyze",
            "clarify",
            "converge",
            "implement",
            "plan",
            "checklist",
            "specify",
            "tasks",
            "taskstoissues",
        ],
    )
    def test_command_loads_constitution_context(self, tmp_path, command_stem):
        """Every command except constitution must reference constitution.md."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        cmd_file = tmp_path / ".custom" / "cmds" / f"speckit.{command_stem}.md"
        assert cmd_file.exists(), f"Command file missing: {cmd_file.name}"
        content = cmd_file.read_text(encoding="utf-8")
        assert "constitution.md" in content, (
            f"speckit.{command_stem}.md must reference constitution.md"
        )

    def test_constitution_command_exists(self, tmp_path):
        """The constitution command itself must exist but is not required to load itself."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        cmd_file = tmp_path / ".custom" / "cmds" / "speckit.constitution.md"
        assert cmd_file.exists()

    # -- CLI --------------------------------------------------------------

    def test_cli_generic_without_commands_dir_fails(self, tmp_path):
        """--integration generic without --integration-options should fail."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(tmp_path / "test-generic"), "--integration", "generic",
        ])
        # Generic requires --commands-dir via --integration-options
        assert result.exit_code != 0


    def test_complete_file_inventory_sh(self, tmp_path):
        """Every file produced by specify init --integration generic --integration-options=--commands-dir ... --script sh."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-generic-sh"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--integration-options=--commands-dir .myagent/commands",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file() and ".git" not in p.parts
        )
        expected = sorted([
            ".myagent/commands/speckit.analyze.md",
            ".myagent/commands/speckit.checklist.md",
            ".myagent/commands/speckit.clarify.md",
            ".myagent/commands/speckit.constitution.md",
            ".myagent/commands/speckit.converge.md",
            ".myagent/commands/speckit.implement.md",
            ".myagent/commands/speckit.plan.md",
            ".myagent/commands/speckit.specify.md",
            ".myagent/commands/speckit.tasks.md",
            ".myagent/commands/speckit.taskstoissues.md",
            ".specify/init-options.json",
            ".specify/integration.json",
            ".specify/integrations/generic.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/.gitignore",
            ".specify/memory/.constitution-template.json",
            ".specify/memory/constitution.md",
            ".specify/scripts/bash/check-prerequisites.sh",
            ".specify/scripts/bash/common.sh",
            ".specify/scripts/bash/create-new-feature.sh",
            ".specify/scripts/bash/resolve-template.sh",
            ".specify/scripts/bash/setup-plan.sh",
            ".specify/scripts/bash/setup-tasks.sh",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
            ".specify/workflows/speckit/workflow.yml",
            ".specify/workflows/workflow-registry.json",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )

    # -- Skills-mode alignment (separator, next-steps, add-on registration) --

    def test_effective_invoke_separator_tracks_skills_flag(self, tmp_path):
        """The separator used to render shared templates and next-step
        guidance must match the layout ``setup()`` actually writes."""
        i = get_integration("generic")
        assert i.effective_invoke_separator({"skills": True}, tmp_path) == "-"
        assert i.effective_invoke_separator({"skills": False}, tmp_path) == "."
        assert i.effective_invoke_separator(None, tmp_path) == "."

    def test_shared_template_and_next_steps_use_hyphen_in_skills_mode(self, tmp_path):
        """End-to-end: with --skills, shared templates and the printed next
        steps must reference /speckit-plan (the layout actually generated),
        not the nonexistent flat /speckit.plan."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "generic-skills-e2e"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--integration-options=--commands-dir .myagent/skills --skills",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"

        plan_template = project / ".specify" / "templates" / "plan-template.md"
        content = plan_template.read_text(encoding="utf-8")
        assert "__SPECKIT_COMMAND_PLAN__" not in content
        assert "/speckit-plan" in content
        assert "/speckit.plan" not in content

        assert "/speckit-plan" in result.output
        assert "/speckit.plan" not in result.output

    def test_shared_template_and_next_steps_use_dot_without_skills_flag(
        self, tmp_path
    ):
        """Regression guard: default flat-mode generic is unchanged — shared
        templates and next steps still reference the flat /speckit.plan."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "generic-flat-e2e"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--integration-options=--commands-dir .myagent/commands",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"

        plan_template = project / ".specify" / "templates" / "plan-template.md"
        content = plan_template.read_text(encoding="utf-8")
        assert "/speckit.plan" in content
        assert "/speckit-plan" not in content

        assert "/speckit.plan" in result.output
        assert "/speckit-plan" not in result.output

    def test_generic_skills_mode_resolves_configured_dir_not_default(
        self, tmp_path
    ):
        """Skills register under the persisted generic directory, never .agents/skills."""
        from specify_cli import resolve_active_skills_dir
        from specify_cli._init_options import save_init_options

        write_integration_json(
            tmp_path, version="1.0.0", integration_key="generic",
            settings={"generic": {"parsed_options": {
                "commands_dir": ".myagent/skills", "skills": True,
            }}},
        )
        save_init_options(
            tmp_path, {"ai": "generic", "ai_skills": True}
        )
        assert resolve_active_skills_dir(tmp_path) == tmp_path / ".myagent/skills"
        assert not (tmp_path / ".agents" / "skills").exists()

    def test_complete_file_inventory_ps(self, tmp_path):
        """Every file produced by specify init --integration generic --integration-options=--commands-dir ... --script ps."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-generic-ps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--integration-options=--commands-dir .myagent/commands",
                "--script", "ps",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file() and ".git" not in p.parts
        )
        expected = sorted([
            ".myagent/commands/speckit.analyze.md",
            ".myagent/commands/speckit.checklist.md",
            ".myagent/commands/speckit.clarify.md",
            ".myagent/commands/speckit.constitution.md",
            ".myagent/commands/speckit.converge.md",
            ".myagent/commands/speckit.implement.md",
            ".myagent/commands/speckit.plan.md",
            ".myagent/commands/speckit.specify.md",
            ".myagent/commands/speckit.tasks.md",
            ".myagent/commands/speckit.taskstoissues.md",
            ".specify/init-options.json",
            ".specify/integration.json",
            ".specify/integrations/generic.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/.gitignore",
            ".specify/memory/.constitution-template.json",
            ".specify/memory/constitution.md",
            ".specify/scripts/powershell/check-prerequisites.ps1",
            ".specify/scripts/powershell/common.ps1",
            ".specify/scripts/powershell/create-new-feature.ps1",
            ".specify/scripts/powershell/resolve-template.ps1",
            ".specify/scripts/powershell/setup-plan.ps1",
            ".specify/scripts/powershell/setup-tasks.ps1",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
            ".specify/workflows/speckit/workflow.yml",
            ".specify/workflows/workflow-registry.json",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
