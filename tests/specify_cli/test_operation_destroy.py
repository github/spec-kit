"""Ownership, policy, and lifecycle evidence for project-local uninstall."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli._operation_destroy import (
    CONSTITUTION,
    DestroyError,
    DestroyRequest,
    destroy_project,
    plan_destroy,
)
from specify_cli.integrations.manifest import IntegrationManifest


def write(root, relative, content=b"generated\n"):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def manifest(root, key="copilot", relative=".github/skills/speckit-plan/SKILL.md"):
    record = IntegrationManifest(key, root)
    record.record_file(relative, b"generated\n")
    record.save()
    state_path = root / ".specify/integration.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    installed = state.get("installed_integrations", [])
    default = state.get("integration", key)
    if default not in installed:
        installed.insert(0, default)
    if key not in installed:
        installed.append(key)
    write(root, ".specify/integration.json", json.dumps({
        "integration": default, "installed_integrations": installed,
    }).encode())
    return record


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def symlink(path, target, *, directory=False):
    try:
        path.symlink_to(target, target_is_directory=directory)
    except OSError as exc:
        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows symlink privilege unavailable")
        raise


@pytest.mark.parametrize("constitution", [False, True])
def test_uninstall_multiple_manifests_and_preserve_unrelated_files(tmp_path, constitution):
    manifest(tmp_path)
    manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    write(tmp_path, ".specify/cache/data")
    write(tmp_path, "specs/001-feature/spec.md", b"specification")
    write(tmp_path, ".github/skills/user/SKILL.md", b"user skill")
    write(tmp_path, "src/main.py", b"source")
    if constitution:
        write(tmp_path, CONSTITUTION, b"# Principles\r\n\xef\xbb\xbf")
    expected = snapshot(tmp_path)
    expected = {
        path: content for path, content in expected.items()
        if (not path.startswith(".specify/") or path == CONSTITUTION)
        and "speckit-plan" not in path
    }

    result = destroy_project(DestroyRequest(tmp_path, confirmed=True, preserve_all=True))

    assert snapshot(tmp_path) == expected
    assert not (tmp_path / ".claude").exists()
    assert (tmp_path / ".specify").exists() is constitution
    assert result.preserved == ((CONSTITUTION, "specs") if constitution else ("specs",))
    assert not destroy_project(DestroyRequest(tmp_path, preserve_all=True)).removed


@pytest.mark.parametrize("confirmed,force", [(False, False), (False, True), (True, False), (True, True)])
def test_preview_never_mutates_and_reports_modified_file(tmp_path, confirmed, force):
    record = manifest(tmp_path)
    relative = next(iter(record.files))
    write(tmp_path, relative, b"customized")
    before = snapshot(tmp_path)

    result = destroy_project(DestroyRequest(tmp_path, confirmed=confirmed, force=force, dry_run=True))

    assert relative in result.removed
    assert result.requires_force == (relative,)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("force", [False, True])
def test_force_never_implies_confirmation(tmp_path, force):
    manifest(tmp_path)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="confirm with --yes") as caught:
        destroy_project(DestroyRequest(tmp_path, force=force))
    assert caught.value.code == "confirmation_required"
    assert snapshot(tmp_path) == before


def test_modified_files_block_before_any_deletion_and_force_removes_them(tmp_path):
    manifest(tmp_path)
    changed = write(tmp_path, ".github/skills/speckit-plan/SKILL.md", b"modified")
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError) as caught:
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert caught.value.code == "modified_files"
    assert snapshot(tmp_path) == before
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert not changed.exists()
    assert not (tmp_path / ".specify").exists()


@pytest.mark.parametrize("relative", [
    "../outside", "/outside", ".git/config", "specs/../source.py",
    ".GIT/config", "C:\\outside", ".", ".github/../README.md", ".specify",
])
def test_unsafe_manifest_paths_block_every_deletion(tmp_path, relative):
    record = manifest(tmp_path)
    path = record.manifest_path
    data = json.loads(path.read_text())
    data["files"][relative] = "a" * 64
    path.write_text(json.dumps(data))
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("content", [
    b"broken", b"[]", b"\xff", b"{}", b'{"integration":"copilot","files":[]}',
    b'{"integration":"copilot","files":{"x":"invalid"}}',
    b'{"integration":"copilot","files":{},"ownership_modes":{"x":"partial"}}',
])
def test_corrupt_manifest_blocks_cleanup(tmp_path, content):
    record = manifest(tmp_path)
    record.manifest_path.write_bytes(content)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("kind", ["extensions", "presets"])
@pytest.mark.parametrize("content", [b"invalid", b"[]", b"{}", b'{"extensions":[]}'])
def test_corrupt_contribution_registry_blocks_cleanup(tmp_path, kind, content):
    manifest(tmp_path)
    write(tmp_path, f".specify/{kind}/.registry", content)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_declared_integration_requires_manifest(tmp_path):
    write(tmp_path, ".specify/integration.json", b'{"integration":"copilot"}')
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="Missing manifest"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("mode", ["partial", "shared"])
def test_shared_ownership_never_forced(tmp_path, mode):
    record = manifest(tmp_path, relative=".vscode/settings.json")
    record.set_ownership(".vscode/settings.json", mode)
    record.save()
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="Partial/shared"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_symlinked_manifest_parent_is_not_traversed(tmp_path):
    manifest(tmp_path)
    (tmp_path / ".github").rename(tmp_path / "other")
    symlink(tmp_path / ".github", tmp_path / "other", directory=True)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="symlinked directory"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("location", [".specify", ".specify/memory", ".specify/integrations"])
def test_symlinked_configuration_is_rejected(tmp_path, location):
    target = tmp_path / "user-directory"
    target.mkdir()
    write(tmp_path, "user-directory/constitution.md", b"user")
    link = tmp_path / location
    link.parent.mkdir(parents=True, exist_ok=True)
    symlink(link, target, directory=True)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before
    assert link.is_symlink()


def test_allowed_link_deletion_never_touches_external_target(tmp_path):
    write(tmp_path, ".specify/init-options.json", b'{"allow_symlinks":true}')
    external = write(tmp_path, "user-owned", b"must survive")
    symlink(tmp_path / ".specify/cache-link", external)
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert external.read_bytes() == b"must survive"
    assert not (tmp_path / ".specify").exists()


def test_denied_link_deletion_stops_before_changes(tmp_path):
    write(tmp_path, ".specify/file")
    external = write(tmp_path, "user-owned", b"must survive")
    symlink(tmp_path / ".specify/cache-link", external)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="symlink"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_constitution_link_is_preserved_without_touching_target(tmp_path):
    write(tmp_path, ".specify/cache")
    external = write(tmp_path, "principles", b"principles")
    link = tmp_path / CONSTITUTION
    link.parent.mkdir()
    symlink(link, external)
    destroy_project(DestroyRequest(tmp_path, confirmed=True, preserve_constitution=True))
    assert link.is_symlink()
    assert external.read_bytes() == b"principles"


def test_io_failure_reports_progress_and_retains_metadata(tmp_path, monkeypatch):
    record = manifest(tmp_path)
    original_unlink = Path.unlink

    def fail(path, **kwargs):
        if ".github" in path.parts:
            raise PermissionError("locked by editor")
        return original_unlink(path, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail)
    with pytest.raises(DestroyError) as caught:
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert caught.value.code == "destroy_failed"
    assert caught.value.details["removed"] == []
    assert record.manifest_path.exists()


def test_empty_project_and_constitution_only_are_noops(tmp_path):
    assert not destroy_project(DestroyRequest(tmp_path)).removed
    write(tmp_path, CONSTITUTION)
    before = snapshot(tmp_path)
    assert not destroy_project(DestroyRequest(tmp_path, preserve_constitution=True)).removed
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("root", [Path("relative"), Path("missing-root")])
def test_relative_root_is_rejected(root):
    with pytest.raises(DestroyError) as caught:
        plan_destroy(DestroyRequest(root))
    assert caught.value.code == "invalid_project_directory"


@pytest.mark.parametrize("integration,options", [
    ("copilot", None),
    ("claude", None),
    ("gemini", None),
    ("generic", "--commands-dir .custom/commands"),
    ("generic", "--commands-dir .custom/skills --skills"),
])
def test_real_cli_init_destroy_with_extension_and_preset(tmp_path, monkeypatch, integration, options):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    args = [
        "init", "--here", "--force", "--non-interactive", "--ignore-agent-tools",
        "--integration", integration, "--script", "py", "--extension", "git", "--preset", "lean",
    ]
    if options:
        args.append(f"--integration-options={options}")
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    write(tmp_path, CONSTITUTION, b"real principles\r\n")
    write(tmp_path, "specs/001-feature/spec.md", b"feature")
    write(tmp_path, ".github/skills/user-owned/SKILL.md", b"custom")
    before = snapshot(tmp_path)
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert any("git" in path and not path.startswith(".specify") for path in preview.removed)
    assert snapshot(tmp_path) == before

    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True, preserve_all=True))

    assert snapshot(tmp_path) == {
        CONSTITUTION: b"real principles\r\n",
        "specs/001-feature/spec.md": b"feature",
        ".github/skills/user-owned/SKILL.md": b"custom",
    }


@pytest.mark.parametrize("missing_manifest", [True, False])
def test_hermes_uses_its_existing_uninstall_lifecycle(tmp_path, monkeypatch, missing_manifest):
    home = tmp_path / "home"
    home.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    global_skill = write(home, ".hermes/skills/speckit-plan/SKILL.md")
    manifest(project, "hermes", ".hermes/skills/speckit-plan/SKILL.md")
    if missing_manifest:
        (project / ".specify/integrations/hermes.manifest.json").unlink()
        before = snapshot(project)
        with pytest.raises(DestroyError, match="Missing manifest"):
            destroy_project(DestroyRequest(project, confirmed=True))
        assert snapshot(project) == before
        assert global_skill.exists()
    else:
        preview = destroy_project(DestroyRequest(project, dry_run=True))
        assert preview.global_scopes == (str(home / ".hermes/skills"),)
        assert global_skill.exists()
        destroy_project(DestroyRequest(project, confirmed=True))
        assert not global_skill.exists()
        assert not (project / ".specify").exists()


def test_machine_level_trust_is_never_removed(tmp_path, monkeypatch):
    write(tmp_path, ".specify/integration-trust.json", b'{"grants":[]}')
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="machine-level"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("state", [
    b"{}",
    b'{"installed_integrations":"copilot"}', b'{"installed_integrations":[null]}',
    b'{"integration":42}', b'{"default_integration":""}',
    b'{"integration_state_schema":2}',
])
def test_invalid_integration_state_blocks_every_deletion(tmp_path, state):
    write(tmp_path, ".specify/integration.json", state)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_legacy_init_options_cannot_hide_missing_manifest(tmp_path):
    write(tmp_path, ".specify/init-options.json", b'{"ai":"copilot"}')
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="integration.json"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("integration,options", [
    ("none", None),
    ("claude", None),
    ("gemini", None),
    ("copilot", "--commands"),
    ("generic", "--commands-dir .custom/commands"),
    ("generic", "--commands-dir .custom/skills --skills"),
])
def test_real_init_destroy_layouts(tmp_path, monkeypatch, integration, options):
    monkeypatch.chdir(tmp_path)
    args = [
        "init", "--here", "--force", "--non-interactive", "--ignore-agent-tools",
        "--integration", integration, "--script", "py",
    ]
    if options:
        args.append(f"--integration-options={options}")
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    destroy_project(DestroyRequest(tmp_path, confirmed=True, preserve_all=True))
    assert snapshot(tmp_path) == {CONSTITUTION: (tmp_path / CONSTITUTION).read_bytes()}
    assert not destroy_project(DestroyRequest(tmp_path, preserve_all=True)).removed


def test_external_adapter_cleanup_does_not_import_package(tmp_path, monkeypatch):
    manifest(tmp_path, "sample-agent", ".sample/commands/speckit.plan.md")
    write(tmp_path, ".specify/integration.json", b'{"integration":"sample-agent"}')
    write(tmp_path, ".specify/integrations/packages/sample-agent/__init__.py", b"raise RuntimeError()")

    def fail(*args, **kwargs):
        pytest.fail("Executable adapter loading must not occur")

    monkeypatch.setattr("specify_cli.integrations.load_installed_integrations", fail)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="ownership"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_inactive_contribution_commands_and_skill_resources_are_included(tmp_path, kind):
    write(tmp_path, f".specify/{kind}/.registry", json.dumps({
        kind: {"sample": {
            "registered_commands": {"claude": ["speckit.sample.test"]},
            "registered_skills": (
                ["sample-skill"] if kind == "extensions" else {"copilot": ["sample-skill"]}
            ),
        }},
    }).encode())
    write(tmp_path, ".claude/skills/speckit-sample-test/SKILL.md")
    write(tmp_path, ".claude/skills/speckit-sample-test/examples/example.txt")
    prefix = "extension" if kind == "extensions" else "preset"
    write(tmp_path, ".github/skills/sample-skill/SKILL.md",
          f"---\nmetadata:\n  source: {prefix}:sample\n---\nSkill\n".encode())
    write(tmp_path, ".github/skills/sample-skill/resources/tool.py")
    write(tmp_path, ".github/skills/user-owned/SKILL.md", b"user")
    before = snapshot(tmp_path)
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert ".github/skills/sample-skill/resources/tool.py" in preview.removed
    assert ".claude/skills/speckit-sample-test/SKILL.md" in preview.removed
    assert ".claude/skills/speckit-sample-test/examples/example.txt" not in preview.removed
    assert snapshot(tmp_path) == before
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == {
        ".github/skills/user-owned/SKILL.md": b"user",
        ".claude/skills/speckit-sample-test/examples/example.txt": b"generated\n",
    }


@pytest.mark.parametrize("kind", ["extensions", "presets"])
def test_missing_contribution_registry_keeps_ownership_metadata(tmp_path, kind):
    write(tmp_path, f".specify/{kind}/sample/manifest.yml")
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="Missing"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_invalid_policy_blocks_cleanup(tmp_path):
    write(tmp_path, ".specify/init-options.json", b'{"allow_symlinks":"yes"}')
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="JSON boolean"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_external_contribution_layout_never_executes_adapter_code(tmp_path, monkeypatch):
    from specify_cli.agents import CommandRegistrar

    def unexpected_formatter(name):
        pytest.fail("Executed an external adapter")

    monkeypatch.setitem(CommandRegistrar.AGENT_CONFIGS, "sample-agent", {
        "dir": ".sample/commands", "extension": ".md", "format_name": unexpected_formatter,
    })
    write(tmp_path, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {
            "registered_commands": {"sample-agent": ["speckit.sample.test"]},
        }},
    }).encode())
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="external integration"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("hashes", [
    [], {"../outside": "a" * 64}, {".git/config": "a" * 64},
    {".custom/skills/sample/SKILL.md": "invalid"},
])
def test_invalid_generic_hash_records_block_cleanup(tmp_path, hashes):
    write(tmp_path, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {
            "registered_commands": {}, "registered_skills": ["sample"],
            "generic_artifact_hashes": hashes,
        }},
    }).encode())
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_flat_skill_records_preserve_another_agents_unrelated_skill(tmp_path):
    write(tmp_path, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {
            "registered_commands": {},
            "registered_skills": ["speckit-sample-task"],
        }},
    }).encode())
    write(tmp_path, ".github/skills/speckit-sample-task/SKILL.md",
          b"---\nmetadata:\n  source: extension:sample\n---\nOwned\n")
    unrelated = write(tmp_path, ".claude/skills/speckit-sample-task/SKILL.md",
                      b"---\nmetadata:\n  source: user:manual\n---\nUnrelated\n")
    notes = write(tmp_path, ".claude/skills/speckit-sample-task/notes.txt", b"user notes")
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert unrelated.read_bytes().endswith(b"Unrelated\n")
    assert notes.read_bytes() == b"user notes"
    assert not (tmp_path / ".github/skills/speckit-sample-task").exists()


def test_destroy_runs_event_teardown_nondefault_first_and_preserves_user_settings(tmp_path, monkeypatch):
    from specify_cli import events
    from specify_cli.integration_state import write_integration_json
    from specify_cli.integrations import get_integration

    write(tmp_path, ".specify/init-options.json", b'{"ai":"claude","script":"py"}')
    write_integration_json(
        tmp_path, version="1.2.3", integration_key="claude",
        installed_integrations=["claude", "gemini"],
    )
    settings = write(tmp_path, ".claude/settings.json", json.dumps({
        "userSetting": True,
        "hooks": {"PreToolUse": [{"matcher": "*", "hooks": [
            {"type": "command", "command": "user-command"},
        ]}]},
    }).encode())
    for key in ("claude", "gemini"):
        record = manifest(tmp_path, key, f".{key}/skills/speckit-plan/SKILL.md")
        get_integration(key).emit_events(
            tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]},
        )
        record.save()
    dispatcher = tmp_path / ".specify/events.py"
    assert dispatcher.is_file()
    cleanups = []
    original = events._cleanup_shared_dispatcher

    def observe(integration, root, record, **kwargs):
        original(integration, root, record, **kwargs)
        cleanups.append((integration.key, dispatcher.exists()))

    monkeypatch.setattr(events, "_cleanup_shared_dispatcher", observe)
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert cleanups == [("gemini", True), ("claude", False)]
    remaining = json.loads(settings.read_text())
    assert remaining["userSetting"] is True
    assert "user-command" in settings.read_text()
    assert "_speckit" not in settings.read_text()
    assert not (tmp_path / ".specify").exists()


def test_destroy_rejects_added_paths_outside_external_ownership_binding(tmp_path, monkeypatch):
    from specify_cli.integrations.installer import _grant_trust

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    write(root, ".specify/integration.json", b'{"integration":"sample-agent"}')
    record = manifest(root, "sample-agent", ".sample/skills/speckit-plan/SKILL.md")
    package = {
        "id": "sample-agent", "name": "Sample Agent", "version": "1.0.0",
        "description": "sample", "catalog": "local",
        "download_url": "https://example.com/sample.zip", "requires": {},
        "files": {"__init__.py": "a" * 64, "integration.yml": "b" * 64},
        "registrar_config": {
            "dir": ".sample/skills", "extension": "/SKILL.md",
            "format": "markdown", "args": "$ARGUMENTS", "invoke_separator": "-",
        },
    }
    write(root, ".specify/integrations/packages.json", json.dumps({
        "schema_version": "1.0", "packages": {"sample-agent": package},
    }).encode())
    _grant_trust(root, "sample-agent", package, record_ownership=True)
    write(root, "src/app.py", b"application source")
    record.record_existing("src/app.py")
    record.save()
    before = snapshot(root)
    with pytest.raises(DestroyError, match="ownership"):
        destroy_project(DestroyRequest(root, confirmed=True, force=True))
    assert snapshot(root) == before


def test_destroy_preserves_claims_when_native_event_config_is_unreadable(tmp_path):
    from specify_cli.integrations import get_integration

    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    get_integration("claude").emit_events(
        tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]},
    )
    record.save()
    write(tmp_path, ".claude/settings.json", b"{malformed native config")
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="native event cleanup"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_destroy_does_not_purge_a_dispatcher_preserved_by_event_teardown(tmp_path):
    from specify_cli.integrations import get_integration

    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    get_integration("claude").emit_events(
        tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]},
    )
    record.save()
    dispatcher = write(tmp_path, ".specify/events.py", b"# customized dispatcher")
    with pytest.raises(DestroyError, match="retry with --force"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert dispatcher.read_bytes() == b"# customized dispatcher"
    retained = IntegrationManifest.load("claude", tmp_path)
    assert ".specify/events.py" in retained.files
    assert (tmp_path / ".specify/integration.json").exists()


@pytest.mark.parametrize("key", ["claude", "gemini", "codex", "vibe", "opencode", "copilot"])
def test_destroy_cleans_native_event_formats_without_deleting_user_config(tmp_path, key):
    from specify_cli.integrations import get_integration

    integration = get_integration(key)
    config = integration.events_config_file
    is_toml = integration.events_format in {"toml", "toml-vibe"}
    write(tmp_path, config, b"user_setting = true\n" if is_toml else b'{"userSetting":true}')
    record = manifest(tmp_path, key, f".test/{key}/SKILL.md")
    integration.emit_events(tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]})
    record.save()
    assert config in record.files
    result = destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert config in result.updated
    content = (tmp_path / config).read_text()
    assert "user_setting" in content or "userSetting" in content
    assert "__speckit_event__" not in content
    assert "speckit_marker" not in content
    assert "speckit-events.ts" not in content
    assert not (tmp_path / ".specify").exists()


def test_force_can_remove_a_modified_owned_dispatcher_after_native_cleanup(tmp_path):
    from specify_cli.integrations import get_integration

    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    get_integration("claude").emit_events(
        tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]},
    )
    record.save()
    write(tmp_path, ".specify/events.py", b"# customized dispatcher")
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert not (tmp_path / ".specify").exists()


def test_later_cleanup_failure_reports_prior_uninstalls_and_retains_remaining_state(tmp_path, monkeypatch):
    from specify_cli.integration_state import try_read_integration_json
    from specify_cli.integrations import get_integration

    for key in ("claude", "gemini"):
        record = manifest(tmp_path, key, f".{key}/skills/speckit-plan/SKILL.md")
        get_integration(key).emit_events(
            tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]},
        )
        record.save()
    def fail(*args, **kwargs):
        raise PermissionError("late teardown failure")

    monkeypatch.setattr(get_integration("claude"), "teardown", fail)
    with pytest.raises(DestroyError) as caught:
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert caught.value.details["uninstalled_integrations"] == ["gemini"]
    state, error = try_read_integration_json(tmp_path)
    assert error is None
    assert state["installed_integrations"] == ["claude"]
    assert (tmp_path / ".specify/integrations/claude.manifest.json").exists()


@pytest.mark.parametrize("force", [False, True])
def test_destroy_preserves_constitution_claimed_by_integration_manifest(tmp_path, force):
    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    content = b"# Keep these principles\r\n"
    record.record_file(CONSTITUTION, content)
    record.save()
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True, preserve_constitution=True))
    assert preview.preserved == (CONSTITUTION,)
    result = destroy_project(DestroyRequest(
        tmp_path, confirmed=True, force=force, preserve_constitution=True,
    ))
    assert (tmp_path / CONSTITUTION).read_bytes() == content
    assert result.preserved == (CONSTITUTION,)
    assert not (tmp_path / ".specify/integration.json").exists()


def test_destroy_teardown_failure_retains_manifest_and_allows_retry(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    record = manifest(root, "hermes", ".hermes/skills/speckit-plan/SKILL.md")
    record.record_file(CONSTITUTION, b"# Preserve even across failed teardown\n")
    record.save()
    global_skill = write(home, ".hermes/skills/speckit-plan/SKILL.md")
    original = record.manifest_path.read_bytes()
    iterdir = Path.iterdir

    def denied(path):
        if path == home / ".hermes/skills":
            raise PermissionError("simulated unreadable global skills directory")
        return iterdir(path)

    with monkeypatch.context() as failure:
        failure.setattr(Path, "iterdir", denied)
        with pytest.raises(DestroyError, match="unreadable global skills directory"):
            destroy_project(DestroyRequest(root, confirmed=True, preserve_constitution=True))
    assert record.manifest_path.read_bytes() == original
    state = json.loads((root / ".specify/integration.json").read_text())
    assert state["installed_integrations"] == ["hermes"]
    assert global_skill.exists()
    assert (root / CONSTITUTION).read_bytes() == b"# Preserve even across failed teardown\n"
    destroy_project(DestroyRequest(root, confirmed=True, preserve_constitution=True))
    assert not global_skill.exists()
    assert not record.manifest_path.exists()
    assert (root / CONSTITUTION).is_file()


@pytest.mark.parametrize("force", [False, True])
def test_real_hermes_with_extension_previews_and_cleans_declared_home_scope(tmp_path, monkeypatch, force):
    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "project"
    monkeypatch.setattr(Path, "home", lambda: home)
    runner = CliRunner()
    initialized = runner.invoke(app, [
        "init", str(root), "--non-interactive", "--ignore-agent-tools",
        "--integration", "hermes", "--script", "py", "--extension", "git",
    ])
    assert initialized.exit_code == 0, initialized.output
    unrelated = write(home, ".hermes/skills/user-skill/SKILL.md", b"unrelated global skill")
    before = snapshot(tmp_path)
    preview = runner.invoke(app, ["destroy", "--project", str(root), "--dry-run", "--json"])
    assert preview.exit_code == 0, preview.output
    assert preview.stderr == ""
    assert json.loads(preview.stdout)["global_scopes"] == [str(home / ".hermes/skills")]
    global_files = json.loads(preview.stdout)["global_files"]
    assert any("speckit-git-" in name for name in global_files)
    assert all(Path(name).is_relative_to(home / ".hermes/skills") for name in global_files)
    assert snapshot(tmp_path) == before
    destroyed = runner.invoke(app, [
        "destroy", "--project", str(root), "--yes", "--json", *(["--force"] if force else []),
    ])
    assert destroyed.exit_code == 0, destroyed.output
    assert destroyed.stderr == ""
    assert not list((home / ".hermes/skills").glob("speckit-*"))
    assert unrelated.read_bytes() == b"unrelated global skill"
    assert snapshot(root) == {}


def test_destroy_preserves_constitution_claimed_by_multiple_integrations(tmp_path):
    content = b"# Project principles\r\n"
    for key in ("claude", "gemini"):
        record = manifest(tmp_path, key, f".{key}/skills/speckit-plan/SKILL.md")
        record.record_file(CONSTITUTION, content)
        record.save()
    destroy_project(DestroyRequest(
        tmp_path, confirmed=True, force=True, preserve_constitution=True,
    ))
    assert snapshot(tmp_path) == {CONSTITUTION: content}


def test_global_contribution_scope_requires_an_installed_integration(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    write(root, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {
            "registered_commands": {"hermes": ["speckit.sample.check"]},
        }},
    }).encode())
    outside = write(home, ".hermes/skills/speckit-sample-check/SKILL.md", b"unrelated home skill")
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="outside its declared uninstall scope"):
        destroy_project(DestroyRequest(root, confirmed=True, force=True))
    assert snapshot(tmp_path) == before
    assert outside.read_bytes() == b"unrelated home skill"


def test_hermes_contribution_preview_rejects_a_symlinked_global_scope(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    manifest(root, "hermes", ".hermes/skills/speckit-plan/SKILL.md")
    write(root, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {
            "registered_commands": {"hermes": ["speckit.sample.check"]},
        }},
    }).encode())
    outside = home / "unrelated"
    write(home, "unrelated/speckit-sample-check/SKILL.md", b"must survive")
    (home / ".hermes").mkdir()
    symlink(home / ".hermes/skills", outside, directory=True)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="Symlinked"):
        destroy_project(DestroyRequest(root, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_global_contribution_cleanup_must_complete_before_infrastructure_purge(tmp_path, monkeypatch):
    from specify_cli.integrations import get_integration
    from specify_cli.integrations.base import IntegrationBase

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    manifest(root, "hermes", ".hermes/skills/speckit-plan/SKILL.md")
    write(root, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {
            "registered_commands": {"hermes": ["speckit.sample.check"]},
        }},
    }).encode())
    global_skill = write(home, ".hermes/skills/speckit-sample-check/SKILL.md")
    integration = get_integration("hermes")
    monkeypatch.setattr(integration, "teardown", lambda root, record, **kwargs: IntegrationBase.teardown(
        integration, root, record, **kwargs,
    ))
    monkeypatch.setattr(
        "specify_cli.integrations._operation_uninstall.unregister_integration_artifacts",
        lambda *args, **kwargs: (),
    )
    with pytest.raises(DestroyError, match="preserved generated artifacts") as caught:
        destroy_project(DestroyRequest(root, confirmed=True))
    assert str(global_skill) in caught.value.details["paths"]
    assert (root / ".specify/extensions/.registry").exists()
    assert global_skill.exists()


@pytest.mark.parametrize("flags,keep_constitution,keep_specs", [
    ([], False, False),
    (["--preserve-constitution"], True, False),
    (["--preserve-specs"], False, True),
    (["--preserve-constitution", "--preserve-specs"], True, True),
    (["--preserve-all"], True, True),
])
@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("integration,options", [
    ("copilot", None), ("claude", None), ("gemini", None),
    ("generic", "--commands-dir .custom/commands"),
    ("generic", "--commands-dir .custom/skills --skills"),
    ("hermes", None),
])
def test_preservation_matrix_on_initialized_throwaway_projects(
    tmp_path, monkeypatch, flags, keep_constitution, keep_specs, force, integration, options,
):
    from specify_cli.integrations import get_integration

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    root = tmp_path / "project"
    runner = CliRunner()
    args = [
        "init", str(root), "--non-interactive", "--ignore-agent-tools",
        "--integration", integration, "--script", "py", "--extension", "git",
    ]
    if force:
        args += ["--preset", "lean"]
    if options:
        args.append(f"--integration-options={options}")
    initialized = runner.invoke(app, args)
    assert initialized.exit_code == 0, initialized.output
    constitution = write(root, CONSTITUTION, b"# Project principles\r\n")
    spec = write(root, "specs/001-feature/spec.md", b"# Specification\r\n")
    source = write(root, "src/app.py", b"source\n")
    unrelated = write(root, "specs-other/keep.md", b"not part of specs/")
    external = write(tmp_path, "outside-specs/spec.md", b"external specification")
    monkeypatch.setenv("SPECIFY_FEATURE_DIRECTORY", str(external.parent))
    record = IntegrationManifest.load(integration, root)
    # Track both artifacts to prove teardown cannot override the preservation policy.
    record.record_existing(CONSTITUTION)
    record.record_existing("specs/001-feature/spec.md")
    agent = get_integration(integration)
    if agent.supports_events():
        agent.emit_events(root, record, {"pre_tool_use": [{"command": "speckit.git.validate"}]})
    record.save()
    before = snapshot(tmp_path)
    command = [
        "destroy", "--project", str(root), "--json", *flags, *(["--force"] if force else []),
    ]
    preview = runner.invoke(app, [*command, "--dry-run"])
    assert preview.exit_code == 0, preview.output
    assert preview.stderr == ""
    assert snapshot(tmp_path) == before
    destroyed = runner.invoke(app, [*command, "--yes"])
    assert destroyed.exit_code == 0, destroyed.output
    assert destroyed.stderr == ""
    assert constitution.exists() is keep_constitution
    assert spec.exists() is keep_specs
    if keep_constitution:
        assert constitution.read_bytes() == b"# Project principles\r\n"
        assert sorted(path.relative_to(root / ".specify").as_posix()
                      for path in (root / ".specify").rglob("*") if path.is_file()) == ["memory/constitution.md"]
    else:
        assert not (root / ".specify").exists()
    if keep_specs:
        assert spec.read_bytes() == b"# Specification\r\n"
    else:
        assert not (root / "specs").exists()
    assert source.read_bytes() == b"source\n"
    assert unrelated.read_bytes() == b"not part of specs/"
    assert external.read_bytes() == b"external specification"
    assert not (root / ".specify/events.py").exists()
    assert not list((home / ".hermes/skills").glob("speckit-*"))
    after = snapshot(tmp_path)
    repeated = runner.invoke(app, [*command, "--yes"])
    assert repeated.exit_code == 0, repeated.output
    assert json.loads(repeated.stdout)["removed"] == []
    assert snapshot(tmp_path) == after


@pytest.mark.parametrize("preserve,allow_symlinks", [(True, False), (False, False), (False, True)])
def test_specs_symlink_is_never_traversed(tmp_path, preserve, allow_symlinks):
    root = tmp_path / "project"
    root.mkdir()
    write(root, ".specify/init-options.json", json.dumps({"allow_symlinks": allow_symlinks}).encode())
    external = write(tmp_path, "outside/spec.md", b"external specification")
    symlink(root / "specs", external.parent, directory=True)
    before = snapshot(tmp_path)
    request = DestroyRequest(root, confirmed=True, preserve_specs=preserve, force=True)
    if not preserve and not allow_symlinks:
        with pytest.raises(DestroyError, match="symlink"):
            destroy_project(request)
        assert snapshot(tmp_path) == before
    else:
        destroy_project(request)
        assert (root / "specs").is_symlink() is preserve
    assert external.read_bytes() == b"external specification"


def test_default_destroy_does_not_delete_specs_without_project_marker(tmp_path):
    spec = write(tmp_path, "specs/001-feature/spec.md", b"not an initialized project")
    result = destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert not result.removed
    assert spec.read_bytes() == b"not an initialized project"


def test_non_directory_specs_entry_is_not_deleted_by_default(tmp_path):
    write(tmp_path, ".specify/config")
    entry = write(tmp_path, "specs", b"unrelated file")
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="specs must be a directory"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before
    assert entry.read_bytes() == b"unrelated file"


def test_specs_deletion_failure_retains_configuration_and_can_be_retried(tmp_path, monkeypatch):
    from specify_cli.file_helper import FileHelper

    config = write(tmp_path, ".specify/config")
    spec = write(tmp_path, "specs/001-feature/spec.md")
    delete = FileHelper.delete

    def fail(self, path, **kwargs):
        if path == "specs/001-feature/spec.md":
            raise PermissionError("spec is locked")
        return delete(self, path, **kwargs)

    with monkeypatch.context() as failure:
        failure.setattr(FileHelper, "delete", fail)
        with pytest.raises(DestroyError, match="spec is locked"):
            destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert config.exists()
    assert spec.exists()
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert not (tmp_path / ".specify").exists()
    assert not (tmp_path / "specs").exists()


@pytest.mark.parametrize("preserve_constitution,preserve_specs,preserve_all", [
    (True, False, False), (False, True, False), (True, True, False), (False, False, True),
])
def test_preservation_is_independent_of_force_for_modified_integration_files(
    tmp_path, preserve_constitution, preserve_specs, preserve_all,
):
    record = manifest(tmp_path)
    generated = write(tmp_path, next(iter(record.files)), b"user-modified generated command")
    constitution = write(tmp_path, CONSTITUTION, b"principles")
    specs = write(tmp_path, "specs/001-feature/spec.md", b"specification")
    request = DestroyRequest(
        tmp_path, confirmed=True, preserve_constitution=preserve_constitution,
        preserve_specs=preserve_specs, preserve_all=preserve_all,
    )
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError) as caught:
        destroy_project(request)
    assert caught.value.code == "modified_files"
    assert snapshot(tmp_path) == before
    destroy_project(DestroyRequest(
        tmp_path, confirmed=True, force=True, preserve_constitution=preserve_constitution,
        preserve_specs=preserve_specs, preserve_all=preserve_all,
    ))
    assert not generated.exists()
    assert constitution.exists() is (preserve_constitution or preserve_all)
    assert specs.exists() is (preserve_specs or preserve_all)


def test_preserved_specs_are_not_traversed_or_read(tmp_path, monkeypatch):
    write(tmp_path, ".specify/config")
    spec = write(tmp_path, "specs/001-feature/spec.md", b"private specification")
    read_bytes = Path.read_bytes

    def deny_spec_reads(path):
        if path == spec:
            raise PermissionError("preserved specifications must not be read")
        return read_bytes(path)

    with monkeypatch.context() as preservation:
        preservation.setattr(Path, "read_bytes", deny_spec_reads)
        destroy_project(DestroyRequest(tmp_path, confirmed=True, preserve_specs=True))
    assert spec.read_bytes() == b"private specification"
    assert not (tmp_path / ".specify").exists()


@pytest.mark.parametrize("force", [False, True])
def test_tracked_constitution_symlink_preservation(tmp_path, force):
    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    record.record_file(CONSTITUTION, b"original")
    record.save()
    (tmp_path / CONSTITUTION).unlink()
    target = write(tmp_path, "principles.md", b"user principles")
    symlink(tmp_path / CONSTITUTION, target)
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=force, preserve_constitution=True))
    assert (tmp_path / CONSTITUTION).is_symlink()
    assert target.read_bytes() == b"user principles"


def test_dotted_contribution_symlink_is_preflighted_before_uninstall(tmp_path):
    manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    write(tmp_path, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {"registered_commands": {"claude": ["speckit.sample.test"]}}},
    }).encode())
    target = write(tmp_path, "outside/SKILL.md", b"unrelated")
    symlink(tmp_path / ".claude/skills/speckit.sample.test", target.parent, directory=True)
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="symlink"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before
    assert target.read_bytes() == b"unrelated"


def test_legacy_inventory_is_rejected_during_preview_without_changes(tmp_path):
    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    (tmp_path / ".specify/integration.json").unlink()
    write(tmp_path, ".specify/init-options.json", b'{"ai":"claude"}')
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="integration.json"):
        destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert snapshot(tmp_path) == before
    assert record.manifest_path.exists()


def test_modified_dispatcher_is_reported_before_any_integration_uninstalls(tmp_path):
    from specify_cli.integrations import get_integration

    for key in ("claude", "gemini"):
        record = manifest(tmp_path, key, f".{key}/skills/speckit-plan/SKILL.md")
        get_integration(key).emit_events(tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]})
        record.save()
    write(tmp_path, ".specify/events.py", b"# user modified dispatcher")
    before = snapshot(tmp_path)
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert ".specify/events.py" in preview.requires_force
    with pytest.raises(DestroyError) as caught:
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert caught.value.code == "modified_files"
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("kind", ["extensions", "presets"])
@pytest.mark.parametrize("failure", ["file", "directory"])
def test_package_purge_keeps_registry_until_package_is_removed(tmp_path, monkeypatch, kind, failure):
    from specify_cli.file_helper import FileHelper

    registry = write(tmp_path, f".specify/{kind}/.registry", json.dumps({kind: {"sample": {}}}).encode())
    package = write(tmp_path, f".specify/{kind}/sample/payload.txt")
    delete = FileHelper.delete
    blocked = f".specify/{kind}/sample" + ("/payload.txt" if failure == "file" else "")

    def fail(self, path, **kwargs):
        if path == blocked:
            raise PermissionError("package locked")
        return delete(self, path, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(FileHelper, "delete", fail)
        with pytest.raises(DestroyError, match="package locked"):
            destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert registry.exists()
    assert package.parent.exists()
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert not (tmp_path / ".specify").exists()


@pytest.mark.parametrize("newline", [b"\n", b"\r\n"])
def test_regenerated_dispatcher_with_stale_manifest_hash_needs_no_force(tmp_path, newline):
    from specify_cli.integrations import get_integration

    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    get_integration("claude").emit_events(tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]})
    record.save()
    path = record.manifest_path
    data = json.loads(path.read_text())
    data["files"][".specify/events.py"] = "a" * 64
    path.write_text(json.dumps(data))
    dispatcher = tmp_path / ".specify/events.py"
    dispatcher.write_bytes(dispatcher.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", newline))
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert ".specify/events.py" not in preview.requires_force
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert not (tmp_path / ".specify").exists()


@pytest.mark.parametrize("kind", ["partial", "recovered", "unowned"])
def test_unproven_dispatcher_cleanup_is_rejected_before_changes(tmp_path, kind):
    from specify_cli.integrations import get_integration

    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    get_integration("claude").emit_events(tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]})
    if kind == "partial":
        record.set_ownership(".specify/events.py", "partial")
    elif kind == "recovered":
        record.record_existing(".specify/events.py", recovered=True)
    else:
        record.remove(".specify/events.py")
    record.save()
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="dispatcher ownership"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("force", [False, True])
def test_preserve_constitution_uses_actual_case_insensitive_entry(tmp_path, force):
    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    constitution = write(tmp_path, ".specify/Memory/Constitution.md", b"retain actual spelling")
    if not (tmp_path / CONSTITUTION).exists():
        pytest.skip("requires a case-insensitive filesystem")
    record.record_existing(".specify/Memory/Constitution.md")
    record.save()
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=force, preserve_constitution=True))
    assert constitution.read_bytes() == b"retain actual spelling"


@pytest.mark.parametrize("skills", [False, True])
def test_force_destroy_removes_modified_generic_extension_output(tmp_path, monkeypatch, skills):
    monkeypatch.chdir(tmp_path)
    options = "--commands-dir .custom/output" + (" --skills" if skills else "")
    runner = CliRunner()
    result = runner.invoke(app, [
        "init", "--here", "--force", "--non-interactive", "--ignore-agent-tools",
        "--integration", "generic", f"--integration-options={options}", "--extension", "git",
    ])
    assert result.exit_code == 0, result.output
    registry = json.loads((tmp_path / ".specify/extensions/.registry").read_text())
    relative = next(iter(registry["extensions"]["git"]["generic_artifact_hashes"]))
    output = write(tmp_path, relative, b"customized extension output")
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert relative in preview.requires_force
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert snapshot(tmp_path) == before
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert not output.exists()
    assert not (tmp_path / ".specify").exists()


def test_native_config_validation_precedes_all_integration_teardown(tmp_path):
    from specify_cli.integrations import get_integration

    for key in ("claude", "gemini"):
        record = manifest(tmp_path, key, f".{key}/skills/speckit-plan/SKILL.md")
        get_integration(key).emit_events(tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]})
        record.save()
    write(tmp_path, ".claude/settings.json", b"{malformed")
    before = snapshot(tmp_path)
    with pytest.raises(DestroyError, match="native event cleanup"):
        destroy_project(DestroyRequest(tmp_path, dry_run=True))
    with pytest.raises(DestroyError, match="native event cleanup"):
        destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert snapshot(tmp_path) == before


def test_dispatcher_preflight_uses_last_claimants_hash(tmp_path):
    from specify_cli.integrations import get_integration

    for key in ("claude", "gemini"):
        record = manifest(tmp_path, key, f".{key}/skills/speckit-plan/SKILL.md")
        get_integration(key).emit_events(tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]})
        record.save()
    write(tmp_path, ".specify/events.py", b"# old dispatcher")
    earlier = IntegrationManifest.load("gemini", tmp_path)
    earlier.record_existing(".specify/events.py")
    earlier.save()
    before = snapshot(tmp_path)
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert ".specify/events.py" in preview.requires_force
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("integration", ["copilot", "claude", "gemini"])
def test_init_preset_output_needs_no_force_but_user_edits_still_do(tmp_path, monkeypatch, integration):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--non-interactive", "--ignore-agent-tools",
        "--integration", integration, "--preset", "lean",
    ])
    assert result.exit_code == 0, result.output
    assert not destroy_project(DestroyRequest(tmp_path, dry_run=True)).requires_force
    record = IntegrationManifest.load(integration, tmp_path)
    relative = next(name for name in record.files if "speckit" in name and not name.startswith(".specify"))
    original = (tmp_path / relative).read_bytes()
    write(tmp_path, relative, b"user edit")
    assert relative in destroy_project(DestroyRequest(tmp_path, dry_run=True)).requires_force
    write(tmp_path, relative, original)
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert not (tmp_path / ".specify").exists()


def test_specs_directory_failure_preserves_project_marker_for_retry(tmp_path, monkeypatch):
    from specify_cli.file_helper import FileHelper

    config = write(tmp_path, ".specify/config")
    (tmp_path / "specs/empty").mkdir(parents=True)
    delete = FileHelper.delete

    def fail(self, path, **kwargs):
        if path == "specs":
            raise PermissionError("specs directory is locked")
        return delete(self, path, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(FileHelper, "delete", fail)
        with pytest.raises(DestroyError, match="specs directory is locked"):
            destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert config.exists()
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert not (tmp_path / "specs").exists()
    assert not (tmp_path / ".specify").exists()


@pytest.mark.parametrize("override", [False, True])
def test_stacked_preset_skill_ownership_is_resolved_collectively(tmp_path, override):
    import yaml

    entries = {}
    for identifier in ("lower", "winner"):
        entries[identifier] = {"registered_skills": {"copilot": ["speckit-sample"]}}
        write(tmp_path, f".specify/presets/{identifier}/preset.yml", yaml.safe_dump({
            "schema_version": "1.0",
            "preset": {"id": identifier, "name": identifier, "version": "1.0.0", "description": "test"},
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"templates": [
                {"type": "command", "name": "speckit.sample", "file": "commands/sample.md"},
            ]},
        }).encode())
        write(tmp_path, f".specify/presets/{identifier}/commands/sample.md", b"preset command")
    write(tmp_path, ".specify/presets/.registry", json.dumps({"presets": entries}).encode())
    source = "override:speckit.sample" if override else "preset:winner"
    skill = write(tmp_path, ".github/skills/speckit-sample/SKILL.md",
                  f"---\nmetadata:\n  source: {source}\n---\nManaged skill\n".encode())
    preview = destroy_project(DestroyRequest(tmp_path, dry_run=True))
    assert ".github/skills/speckit-sample/SKILL.md" in preview.removed
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert not skill.exists()


@pytest.mark.parametrize("force", [False, True])
def test_case_insensitive_preserved_constitution_link_is_not_followed(tmp_path, force):
    record = manifest(tmp_path, "claude", ".claude/skills/speckit-plan/SKILL.md")
    entry = write(tmp_path, ".specify/Memory/Constitution.md", b"original")
    if not (tmp_path / CONSTITUTION).exists():
        pytest.skip("requires a case-insensitive filesystem")
    record.record_existing(".specify/Memory/Constitution.md")
    record.save()
    entry.unlink()
    target = write(tmp_path, "user-principles.md", b"user data")
    symlink(entry, target)
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=force, preserve_all=True))
    assert entry.is_symlink()
    assert target.read_bytes() == b"user data"


@pytest.mark.parametrize("skills", [False, True])
def test_failed_forced_generic_cleanup_retains_registration_and_can_retry(tmp_path, monkeypatch, skills):
    monkeypatch.chdir(tmp_path)
    options = "--commands-dir .custom/output" + (" --skills" if skills else "")
    result = CliRunner().invoke(app, [
        "init", "--here", "--force", "--non-interactive", "--ignore-agent-tools",
        "--integration", "generic", f"--integration-options={options}", "--extension", "git",
    ])
    assert result.exit_code == 0, result.output
    registry = json.loads((tmp_path / ".specify/extensions/.registry").read_text())
    relative = next(iter(registry["extensions"]["git"]["generic_artifact_hashes"]))
    output = write(tmp_path, relative, b"modified command")
    unlink = Path.unlink

    def fail(path, **kwargs):
        if path == output:
            raise PermissionError("generic output locked")
        return unlink(path, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(Path, "unlink", fail)
        with pytest.raises(DestroyError, match="generic output locked"):
            destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert (tmp_path / ".specify/integration.json").exists()
    assert (tmp_path / ".specify/integrations/generic.manifest.json").exists()
    assert json.loads((tmp_path / ".specify/init-options.json").read_text())["ai"] == "generic"
    assert output.read_bytes() == b"modified command"
    destroy_project(DestroyRequest(tmp_path, confirmed=True, force=True))
    assert not output.exists()
    assert not (tmp_path / ".specify").exists()


def test_dispatcher_earlier_stale_hash_does_not_override_last_owner(tmp_path):
    from specify_cli.integrations import get_integration

    for key in ("claude", "gemini"):
        record = manifest(tmp_path, key, f".{key}/skills/speckit-plan/SKILL.md")
        get_integration(key).emit_events(tmp_path, record, {"pre_tool_use": [{"command": "speckit.test"}]})
        record.save()
    write(tmp_path, ".specify/events.py", b"# managed historical dispatcher")
    last = IntegrationManifest.load("claude", tmp_path)
    last.record_existing(".specify/events.py")
    last.save()
    assert not destroy_project(DestroyRequest(tmp_path, dry_run=True)).requires_force
    destroy_project(DestroyRequest(tmp_path, confirmed=True))
    assert not (tmp_path / ".specify").exists()
