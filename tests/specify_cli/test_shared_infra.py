"""Scoped project operations owned by shared infrastructure."""

import errno
import hashlib
import json
import os
import shutil

import pytest

from specify_cli.file_helper import (
    FileHelper,
    PathEscapeError,
    SymlinkDeniedError,
    UnsupportedPathError,
)
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.shared_infra import install_shared_infra, refresh_shared_templates


class Console:
    def print(self, *args, **kwargs):
        pass


@pytest.fixture
def shared_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    core = tmp_path / "core"
    scripts = core / "scripts" / "bash"
    scripts.mkdir(parents=True)
    (scripts / "common.sh").write_text("# bundled\n")
    (scripts / "common.sh").chmod(0o755)
    templates = core / "templates"
    templates.mkdir()
    (templates / "plan-template.md").write_text("# bundled plan\n")
    return project, core


def install(project, core, **kwargs):
    return install_shared_infra(
        project, "sh", version="test", core_pack=core, repo_root=core,
        console=Console(), **kwargs,
    )


@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("relative", [
    ".specify/scripts/bash/common.sh",
    ".specify/templates/plan-template.md",
    ".specify/.gitignore",
])
def test_deny_linked_destination_errors_instead_of_skipping(shared_project, relative, force):
    project, core = shared_project
    destination = project / relative
    destination.parent.mkdir(parents=True)
    target = project / "custom"
    target.write_text("custom\n")
    destination.symlink_to(target)

    with pytest.raises(SymlinkDeniedError):
        install(project, core, force=force)

    assert destination.is_symlink()
    assert target.read_text() == "custom\n"
    assert not (project / ".specify/integrations/speckit.manifest.json").exists()


def allow(project):
    (project / ".specify").mkdir(exist_ok=True)
    (project / ".specify/init-options.json").write_text('{"allow_symlinks": true}\n')
    return FileHelper(project, allow_symlinks=True)


@pytest.mark.parametrize("relative,kind", [
    (".specify/scripts/bash/common.sh", "leaf"),
    (".specify/scripts/bash/common.sh", "parent"),
    (".specify/templates/plan-template.md", "leaf"),
    (".specify/templates/plan-template.md", "parent"),
    (".specify/.gitignore", "leaf"),
])
@pytest.mark.parametrize("mode", ["missing-only", "refresh", "customized", "recovered", "force"])
def test_allowed_links_preserve_overwrite_and_manifest_decisions(shared_project, relative, kind, mode):
    project, core = shared_project
    files = allow(project)
    install(project, core, files=files)
    destination = project / relative
    if kind == "parent":
        target_dir = project / "user-target"
        destination.parent.rename(target_dir)
        destination.parent.symlink_to(target_dir, target_is_directory=True)
        target = target_dir / destination.name
        link = destination.parent
    else:
        target = project / "user-target"
        destination.rename(target)
        destination.symlink_to(target)
        link = destination
    original = target.read_text()
    if mode in {"customized", "recovered", "force"}:
        target.write_text("user customization\n")
        original = target.read_text()
    if mode == "recovered":
        (project / ".specify/integrations/speckit.manifest.json").unlink()
        install(project, core, files=files)
    if relative.endswith("common.sh"):
        (core / "scripts/bash/common.sh").write_text("# replacement\n")
        replacement = "# replacement\n"
    elif relative.endswith("plan-template.md"):
        (core / "templates/plan-template.md").write_text("# replacement plan\n")
        replacement = "# replacement plan\n"
    else:
        from specify_cli.shared_infra import SPECIFY_GITIGNORE_CONTENT
        replacement = SPECIFY_GITIGNORE_CONTENT

    install(
        project, core, files=files, force=mode == "force",
        refresh_managed=mode in {"refresh", "customized", "recovered"},
    )
    assert link.is_symlink()
    expected = replacement if mode in {"refresh", "force"} else original
    assert target.read_text() == expected
    manifest = IntegrationManifest.load("speckit", project, files=files)
    assert relative in manifest.files
    assert all(not key.startswith("user-target") for key in manifest.files)
    if mode != "customized":
        assert manifest.files[relative] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert manifest.is_recovered(relative) == (mode == "recovered")
    if relative.endswith("common.sh") and mode in {"refresh", "force"} and os.name != "nt":
        assert target.stat().st_mode & 0o777 == 0o755


@pytest.mark.parametrize("kind", ["leaf", "parent"])
@pytest.mark.parametrize("mode", ["managed", "customized", "recovered", "force"])
def test_template_only_refresh_preserves_allowed_link_and_ownership(shared_project, kind, mode):
    project, core = shared_project
    files = allow(project)
    install(project, core, files=files)
    relative = ".specify/templates/plan-template.md"
    destination = project / relative
    target = project / "target"
    if kind == "leaf":
        destination.rename(target)
        destination.symlink_to(target)
        link = destination
    else:
        destination.parent.rename(target)
        destination.parent.symlink_to(target, target_is_directory=True)
        target /= destination.name
        link = destination.parent
    if mode in {"customized", "recovered", "force"}:
        target.write_text("user plan\n")
    if mode == "recovered":
        manifest = IntegrationManifest.load("speckit", project, files=files)
        manifest.record_existing(relative, recovered=True)
        manifest.save()
    original = target.read_text()
    (core / "templates/plan-template.md").write_text("replacement plan\n")
    refresh_shared_templates(
        project, version="test", core_pack=core, repo_root=core, console=Console(),
        invoke_separator=".", files=files, force=mode == "force",
    )
    assert link.is_symlink()
    assert target.read_text() == ("replacement plan\n" if mode in {"managed", "force"} else original)
    manifest = IntegrationManifest.load("speckit", project, files=files)
    assert manifest.is_recovered(relative) == (mode == "recovered")


@pytest.mark.parametrize("allow_links", [False, True])
@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("relative", [
    ".specify/scripts/bash/common.sh",
    ".specify/scripts/bash/stale.sh",
    ".specify/scripts/powershell/common.ps1",
    ".specify/templates/obsolete-template.md",
    ".specify/templates/vscode-settings.json",
    ".specify/templates/.hidden-template.md",
    ".specify/.gitignore",
])
@pytest.mark.parametrize("kind", ["contained", "dangling", "external", "cycle"])
def test_template_refresh_does_not_access_unselected_manifest_entries(
    shared_project, tmp_path, monkeypatch, allow_links, force, relative, kind,
):
    from pathlib import Path

    project, core = shared_project
    files = FileHelper(project, allow_symlinks=allow_links)
    install(project, core, files=files)
    destination = project / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("original unrelated\n")
    manifest = IntegrationManifest.load("speckit", project, files=files)
    manifest.record_existing(relative, recovered=True)
    manifest.save()
    before_hashes = manifest.files
    before_recovered = manifest.recovered_files
    destination.unlink()
    target = project / "unrelated-target"
    if kind == "contained":
        target.write_text("original unrelated\n")
    elif kind == "external":
        target = tmp_path / "outside"
        target.write_text("original unrelated\n")
    elif kind == "cycle":
        target = destination
    destination.symlink_to(target)
    link_identity = destination.lstat().st_ino
    link_target = os.readlink(destination)
    (core / "templates/plan-template.md").write_text("replacement plan\n")
    (core / "templates/vscode-settings.json").write_text("{}")
    (core / "templates/.hidden-template.md").write_text("hidden\n")
    original_stat = FileHelper.stat
    original_read = FileHelper.read_bytes

    def check_selected(path):
        absolute = Path(path) if Path(path).is_absolute() else project / path
        assert absolute != destination, "Template refresh accessed an unrelated entry"

    def checked_stat(helper, path, **kwargs):
        check_selected(path)
        return original_stat(helper, path, **kwargs)

    def checked_read(helper, path):
        check_selected(path)
        return original_read(helper, path)

    monkeypatch.setattr(FileHelper, "stat", checked_stat)
    monkeypatch.setattr(FileHelper, "read_bytes", checked_read)
    refresh_shared_templates(
        project, version="test", core_pack=core, repo_root=core, console=Console(),
        invoke_separator=".", files=files, force=force,
    )

    assert (project / ".specify/templates/plan-template.md").read_text() == "replacement plan\n"
    assert destination.is_symlink()
    assert destination.lstat().st_ino == link_identity
    assert os.readlink(destination) == link_target
    if kind in {"contained", "external"}:
        assert target.read_text() == "original unrelated\n"
    after = IntegrationManifest.load("speckit", project, files=files)
    assert after.files[relative] == before_hashes[relative]
    assert after.recovered_files == before_recovered


@pytest.mark.parametrize("force", [False, True])
def test_template_refresh_still_rejects_selected_denied_link(shared_project, force):
    project, core = shared_project
    files = FileHelper(project)
    install(project, core, files=files)
    manifest = project / ".specify/integrations/speckit.manifest.json"
    before_manifest = manifest.read_bytes()
    destination = project / ".specify/templates/plan-template.md"
    target = project / "selected-target"
    destination.rename(target)
    destination.symlink_to(target)
    before_content = target.read_bytes()

    with pytest.raises(SymlinkDeniedError):
        refresh_shared_templates(
            project, version="test", core_pack=core, repo_root=core, console=Console(),
            invoke_separator=".", files=files, force=force,
        )

    assert target.read_bytes() == before_content
    assert destination.is_symlink()
    assert manifest.read_bytes() == before_manifest


def test_wrapper_reads_policy_afresh_between_invocations(shared_project, monkeypatch):
    import specify_cli
    project, core = shared_project
    monkeypatch.setattr(specify_cli, "_locate_core_pack", lambda: core)
    files = allow(project)
    install(project, core, files=files)
    destination = project / ".specify/templates/plan-template.md"
    target = project / "target"
    destination.rename(target)
    destination.symlink_to(target)
    options = project / ".specify/init-options.json"
    options.write_text('{"allow_symlinks": false}')
    with pytest.raises(SymlinkDeniedError):
        specify_cli._install_shared_infra(project, "sh", force=True)
    options.write_text('{"allow_symlinks": true}')
    specify_cli._install_shared_infra(project, "sh", force=True)
    options.write_text('{"allow_symlinks": false}')
    with pytest.raises(SymlinkDeniedError):
        specify_cli._refresh_shared_templates(project, invoke_separator=".", force=True)
    assert destination.is_symlink()


def test_init_current_allow_flag_updates_contained_link_and_persists_bool(shared_project, monkeypatch):
    from typer.testing import CliRunner

    import specify_cli
    project, core = shared_project
    monkeypatch.setattr(specify_cli, "_locate_core_pack", lambda: core)
    (project / ".specify/scripts/bash").mkdir(parents=True)
    (project / ".specify/init-options.json").write_text('{"allow_symlinks": false, "unrelated": "keep"}')
    target = project / "user-script"
    target.write_text("# user\n")
    destination = project / ".specify/scripts/bash/common.sh"
    destination.symlink_to(target)
    result = CliRunner().invoke(specify_cli.app, [
        "init", str(project), "--force", "--integration", "copilot",
        "--script", "sh", "--ignore-agent-tools", "--allow-symlinks",
    ], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert destination.is_symlink()
    assert target.read_text() == "# bundled\n"
    options = json.loads((project / ".specify/init-options.json").read_text())
    assert options["allow_symlinks"] is True
    assert options["unrelated"] == "keep"


@pytest.mark.parametrize("allow_links", [False, True])
def test_trusted_root_alias_ignores_unrelated_links(shared_project, tmp_path, allow_links):
    project, core = shared_project
    root_alias = tmp_path / "root-alias"
    root_alias.symlink_to(project, target_is_directory=True)
    (project / "unrelated").symlink_to(tmp_path / "outside-missing")
    install(root_alias, core, files=FileHelper(root_alias, allow_symlinks=allow_links))
    assert (project / ".specify/scripts/bash/common.sh").read_text() == "# bundled\n"
    assert (project / "unrelated").is_symlink()


@pytest.mark.parametrize("operation", ["install", "refresh"])
@pytest.mark.parametrize("kind", ["leaf", "parent"])
@pytest.mark.parametrize("target_kind", ["external", "dangling", "cycle"])
def test_allow_invalid_destinations_fail_before_writes(shared_project, tmp_path, operation, kind, target_kind):
    project, core = shared_project
    files = allow(project)
    destination = project / ".specify/templates"
    if kind == "leaf":
        destination.mkdir()
        destination /= "plan-template.md"
    if target_kind == "external":
        target = tmp_path / "outside"
        if kind == "parent":
            target.mkdir()
            (target / "keep").write_text("outside\n")
        else:
            target.write_text("outside\n")
        error = PathEscapeError
    elif target_kind == "dangling":
        target = project / "missing"
        error = FileNotFoundError
    else:
        target = destination
        error = UnsupportedPathError
    destination.symlink_to(target, target_is_directory=kind == "parent")

    with pytest.raises(error):
        if operation == "install":
            install(project, core, files=files, force=True)
        else:
            refresh_shared_templates(
                project, version="test", core_pack=core, repo_root=core,
                console=Console(), invoke_separator=".", files=files, force=True,
            )
    assert destination.is_symlink()
    assert not (project / ".specify/integrations/speckit.manifest.json").exists()
    if target_kind == "external":
        assert (target / "keep" if kind == "parent" else target).read_text() == "outside\n"


@pytest.mark.parametrize("kind", ["leaf", "parent"])
@pytest.mark.parametrize("allow_links", [False, True])
def test_manifest_load_hash_save_obey_explicit_helper(shared_project, kind, allow_links):
    project, core = shared_project
    files = allow(project) if allow_links else FileHelper(project)
    install(project, core, files=files)
    manifest_path = project / ".specify/integrations/speckit.manifest.json"
    if kind == "leaf":
        target = project / "saved-manifest.json"
        manifest_path.rename(target)
        manifest_path.symlink_to(target)
        link = manifest_path
    else:
        target_dir = project / "saved-manifests"
        manifest_path.parent.rename(target_dir)
        manifest_path.parent.symlink_to(target_dir, target_is_directory=True)
        target = target_dir / manifest_path.name
        link = manifest_path.parent
    if not allow_links:
        before = target.read_bytes()
        with pytest.raises(SymlinkDeniedError):
            install(project, core, files=files, force=True)
        assert target.read_bytes() == before
    else:
        install(project, core, files=files, force=True)
        data = json.loads(target.read_text())
        for relative, digest in data["files"].items():
            assert digest == hashlib.sha256(files.read_bytes(relative)).hexdigest()
    assert link.is_symlink()


@pytest.mark.parametrize("kind", ["external", "dangling", "cycle"])
@pytest.mark.parametrize("allow_links", [False, True])
def test_manifest_policy_failures_never_recover_as_new(shared_project, tmp_path, kind, allow_links):
    project, core = shared_project
    files = allow(project) if allow_links else FileHelper(project)
    directory = project / ".specify/integrations"
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "speckit.manifest.json"
    target = project / "missing"
    if kind == "external":
        target = tmp_path / "outside.json"
        target.write_text("{}")
    elif kind == "cycle":
        target = destination
    destination.symlink_to(target)
    error = SymlinkDeniedError if not allow_links else {
        "external": PathEscapeError, "dangling": FileNotFoundError, "cycle": UnsupportedPathError,
    }[kind]
    with pytest.raises(error):
        install(project, core, files=files, force=True)
    assert destination.is_symlink()
    assert not (project / ".specify/scripts").exists()


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_scoped_manifest_preserves_native_json_text_format(shared_project, monkeypatch, newline):
    project, core = shared_project
    monkeypatch.setattr("specify_cli.integrations.manifest.os.linesep", newline)
    install(project, core, files=FileHelper(project))
    raw = (project / ".specify/integrations/speckit.manifest.json").read_bytes()
    data = json.loads(raw)
    assert raw == (json.dumps(data, indent=2) + "\n").replace("\n", newline).encode("utf-8")


@pytest.mark.parametrize("phase", ["manifest-load", "managed-hash", "recovered-record"])
def test_link_becoming_dangling_during_read_is_not_swallowed(shared_project, monkeypatch, phase):
    from pathlib import Path
    project, core = shared_project
    files = allow(project)
    install(project, core, files=files)
    manifest_path = project / ".specify/integrations/speckit.manifest.json"
    destination = manifest_path if phase == "manifest-load" else project / ".specify/scripts/bash/common.sh"
    target = project / "target"
    destination.rename(target)
    destination.symlink_to(target)
    if phase == "recovered-record":
        manifest_path.unlink()
    original = FileHelper.read_bytes

    def read_bytes(helper, path):
        absolute = Path(path) if Path(path).is_absolute() else helper.root / path
        if absolute == destination:
            target.unlink()
        return original(helper, path)

    monkeypatch.setattr(FileHelper, "read_bytes", read_bytes)
    with pytest.raises(FileNotFoundError):
        install(project, core, files=files, refresh_managed=phase == "managed-hash")
    assert destination.is_symlink()
    if phase == "recovered-record":
        assert not manifest_path.exists()


@pytest.mark.parametrize("allow_links", [False, True])
@pytest.mark.parametrize("kind", ["contained", "dangling", "external", "cycle"])
def test_stale_leaf_links_are_never_hash_promoted_or_deleted(shared_project, tmp_path, allow_links, kind):
    project, core = shared_project
    files = allow(project) if allow_links else FileHelper(project)
    install(project, core, files=files)
    relative = ".specify/scripts/bash/stale.sh"
    stale = project / relative
    stale.write_text("managed stale\n")
    manifest = IntegrationManifest.load("speckit", project, files=files)
    manifest.record_existing(relative)
    manifest.save()
    stale.unlink()
    target = project / "stale-target"
    if kind == "contained":
        target.write_text("managed stale\n")
    elif kind == "external":
        target = tmp_path / "outside"
        target.write_text("managed stale\n")
    elif kind == "cycle":
        target = stale
    stale.symlink_to(target)
    if not allow_links:
        with pytest.raises(SymlinkDeniedError):
            install(project, core, files=files, force=True)
    else:
        install(project, core, files=files, force=True)
        assert relative in IntegrationManifest.load("speckit", project, files=files).files
    assert stale.is_symlink()
    if kind in {"contained", "external"}:
        assert target.read_text() == "managed stale\n"


@pytest.mark.parametrize("customized,recovered", [(False, False), (True, False), (False, True)])
def test_stale_cleanup_through_allowed_parent_obeys_ownership(shared_project, customized, recovered):
    project, core = shared_project
    files = allow(project)
    install(project, core, files=files)
    directory = project / ".specify/scripts/bash"
    target = project / "script-target"
    directory.rename(target)
    directory.symlink_to(target, target_is_directory=True)
    relative = ".specify/scripts/bash/stale.sh"
    stale = target / "stale.sh"
    stale.write_text("managed stale\n")
    manifest = IntegrationManifest.load("speckit", project, files=files)
    manifest.record_existing(relative, recovered=recovered)
    manifest.save()
    if customized:
        stale.write_text("customized\n")
    install(project, core, files=files, force=True)
    assert directory.is_symlink()
    assert stale.exists() == (customized or recovered)
    assert (relative in IntegrationManifest.load("speckit", project, files=files).files) == (customized or recovered)


@pytest.mark.parametrize("kind", ["leaf", "templates-root", "scripts-root", "nested-parent"])
@pytest.mark.parametrize("new_parents", [False, True])
def test_real_lifecycle_rolls_back_allowed_targets(shared_project, tmp_path, monkeypatch, kind, new_parents):
    from specify_cli.integrations._lifecycle import _transaction

    project, core = shared_project
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    files = allow(project)
    target = project / "user-target"
    target.mkdir()
    (target / "unrelated").write_text("keep\n")
    if kind == "leaf":
        destination = project / ".specify/scripts/bash/common.sh"
        target_file = target / "common.sh"
    elif kind == "templates-root":
        destination = project / ".specify/templates"
        target_file = target / "plan-template.md"
    elif kind == "scripts-root":
        destination = project / ".specify/scripts"
        (target / "bash").mkdir()
        target_file = target / "bash/common.sh"
    else:
        destination = project / ".specify/scripts/bash"
        target_file = target / "common.sh"
    destination.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("original\n")
    target_file.chmod(0o600)
    destination.symlink_to(target_file if kind == "leaf" else target, target_is_directory=kind != "leaf")
    if new_parents:
        nested = core / ("templates" if kind == "templates-root" else "scripts/bash") / "new/nested"
        nested.mkdir(parents=True)
        (nested / "added.sh").write_text("# new\n")
    before = {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}
    directories = {path.relative_to(target) for path in target.rglob("*") if path.is_dir()}
    link_identity = os.readlink(destination)

    with (
        pytest.raises(RuntimeError, match="late failure"),
        _transaction(project, None, None, {}, shared_files=files),
    ):
        install(project, core, files=files, force=True)
        raise RuntimeError("late failure")

    assert destination.is_symlink()
    assert os.readlink(destination) == link_identity
    assert {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()} == before
    assert {path.relative_to(target) for path in target.rglob("*") if path.is_dir()} == directories
    if os.name != "nt":
        assert target_file.stat().st_mode & 0o777 == 0o600


def test_directory_rollback_preserves_unrelated_new_contents(shared_project, tmp_path, monkeypatch):
    from specify_cli.integrations._lifecycle import _transaction
    project, core = shared_project
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    files = allow(project)
    target = project / "target"
    target.mkdir()
    alias = project / ".specify/scripts"
    alias.symlink_to(target, target_is_directory=True)
    nested = core / "scripts/bash/new/nested"
    nested.mkdir(parents=True)
    (nested / "owned.sh").write_text("owned\n")

    with (
        pytest.raises(RuntimeError, match="late failure"),
        _transaction(project, None, None, {}, shared_files=files),
    ):
        install(project, core, files=files)
        (target / "bash/new/nested/unrelated").write_text("unrelated\n")
        raise RuntimeError("late failure")

    assert (target / "bash/new/nested/unrelated").read_text() == "unrelated\n"
    assert not (target / "bash/new/nested/owned.sh").exists()
    assert not (target / "bash/common.sh").exists()
    assert alias.is_symlink()


@pytest.mark.parametrize("fail", [False, True])
def test_directory_observer_context_restores_nested_transactions(shared_project, tmp_path, monkeypatch, fail):
    from specify_cli.integrations._file_changes import (
        directory_change_observer,
        file_change_observer,
    )
    from specify_cli.integrations._lifecycle import _transaction
    project, _ = shared_project
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    other = tmp_path / "other-project"
    other.mkdir()
    def outer_file(*args):
        pass

    def outer_directory(*args):
        pass
    file_token = file_change_observer.set(outer_file)
    directory_token = directory_change_observer.set(outer_directory)
    try:
        with _transaction(project, None, None, {}):
            current_file = file_change_observer.get()
            current_directory = directory_change_observer.get()
            try:
                with _transaction(other, None, None, {}):
                    assert file_change_observer.get() != current_file
                    assert directory_change_observer.get() != current_directory
                    if fail:
                        raise RuntimeError("nested failure")
            except RuntimeError as exc:
                assert str(exc) == "nested failure"
            assert file_change_observer.get() == current_file
            assert directory_change_observer.get() == current_directory
        assert file_change_observer.get() is outer_file
        assert directory_change_observer.get() is outer_directory
    finally:
        directory_change_observer.reset(directory_token)
        file_change_observer.reset(file_token)


def test_directory_cleanup_io_failure_reports_rollback_error(shared_project, tmp_path, monkeypatch):
    from pathlib import Path

    from specify_cli.integrations import _lifecycle, installer
    project, core = shared_project
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    files = allow(project)
    target = project / "target"
    target.mkdir()
    (project / ".specify/scripts").symlink_to(target, target_is_directory=True)
    failed = target / "bash"
    original_rmdir = Path.rmdir
    original_mkdtemp = _lifecycle.tempfile.mkdtemp
    backups = []

    def record_backup(*args, **kwargs):
        directory = original_mkdtemp(*args, **kwargs)
        if kwargs.get("prefix") == "speckit-integration-rollback-":
            backups.append(Path(directory))
        return directory

    def rmdir(path, *args, **kwargs):
        if path == failed:
            raise PermissionError(errno.EACCES, "directory cleanup denied", str(path))
        return original_rmdir(path, *args, **kwargs)

    monkeypatch.setattr(_lifecycle.tempfile, "mkdtemp", record_backup)
    monkeypatch.setattr(Path, "rmdir", rmdir)
    try:
        with (
            pytest.raises(installer.IntegrationInstallError, match="rollback failed.*directory cleanup denied") as error,
            _lifecycle._transaction(project, None, None, {}, shared_files=files),
        ):
            install(project, core, files=files)
            raise RuntimeError("original failure")
        assert "original failure" in str(error.value)
        assert isinstance(error.value.__cause__, RuntimeError)
        assert failed.is_dir()
        assert not (failed / "common.sh").exists()
    finally:
        for backup in backups:
            shutil.rmtree(backup)
