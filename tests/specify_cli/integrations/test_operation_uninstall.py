"""Shared uninstall contracts independent of the CLI adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specify_cli.integrations._operation_uninstall import (
    IntegrationUninstallError,
    IntegrationUninstallRequest,
    uninstall_integration,
)
from tests.specify_cli.integrations._helpers import _init_project


def test_explicit_project_uninstall_does_not_change_launch_directory(tmp_path):
    project = _init_project(tmp_path, "claude")
    launch = Path.cwd()
    result = uninstall_integration(IntegrationUninstallRequest(project, "claude"))
    assert result.key == "claude"
    assert result.removed
    assert not result.skipped
    assert Path.cwd() == launch
    assert not (project / ".specify/integration.json").exists()
    assert (project / ".specify/templates").exists()


def test_project_with_no_integration_is_a_noop(tmp_path):
    (tmp_path / ".specify").mkdir()
    result = uninstall_integration(IntegrationUninstallRequest(tmp_path))
    assert result.key is None
    assert not result.removed


def test_project_marker_is_validated_by_the_shared_operation(tmp_path):
    with pytest.raises(IntegrationUninstallError) as caught:
        uninstall_integration(IntegrationUninstallRequest(tmp_path))
    assert caught.value.code == "not_a_spec_kit_project"


def test_wrong_key_is_a_typed_error_without_mutation(tmp_path):
    project = _init_project(tmp_path, "claude")
    state = project / ".specify/integration.json"
    before = state.read_bytes()
    with pytest.raises(IntegrationUninstallError) as caught:
        uninstall_integration(IntegrationUninstallRequest(project, "copilot"))
    assert caught.value.code == "not_installed"
    assert state.read_bytes() == before


def test_complete_cleanup_failure_retains_integration_metadata(tmp_path, monkeypatch):
    project = _init_project(tmp_path, "claude")

    def fail(*args, **kwargs):
        raise OSError("contribution cleanup failed")

    monkeypatch.setattr("specify_cli.extensions.ExtensionManager.unregister_agent_artifacts", fail)
    with pytest.raises(IntegrationUninstallError, match="contribution cleanup failed"):
        uninstall_integration(IntegrationUninstallRequest(
            project, "claude", require_complete=True,
        ))
    state = json.loads((project / ".specify/integration.json").read_text())
    assert "claude" in state["installed_integrations"]
    assert (project / ".specify/integrations/claude.manifest.json").exists()


def test_strict_generic_dangling_output_keeps_recovery_state(tmp_path):
    from specify_cli._operation_destroy import DestroyError, DestroyRequest, destroy_project
    from tests.specify_cli.test_operation_destroy import symlink, write

    project = _init_project(tmp_path, "generic", "--commands-dir .custom/commands")
    write(project, ".specify/init-options.json",
          b'{"ai":"generic","integration":"generic","allow_symlinks":true,"commands_dir":".custom/commands"}')
    relative = ".custom/commands/speckit.sample.md"
    write(project, ".specify/extensions/.registry", json.dumps({
        "extensions": {"sample": {
            "registered_commands": {"generic": ["speckit.sample"]},
            "generic_artifact_hashes": {relative: "a" * 64},
        }},
    }).encode())
    output = project / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    symlink(output, output.parent / "missing")
    with pytest.raises(DestroyError):
        destroy_project(DestroyRequest(project, confirmed=True, force=True))
    assert output.is_symlink()
    assert (project / ".specify/integration.json").exists()
    assert (project / ".specify/integrations/generic.manifest.json").exists()
    registry = json.loads((project / ".specify/extensions/.registry").read_text())
    assert registry["extensions"]["sample"]["generic_artifact_hashes"] == {relative: "a" * 64}


@pytest.mark.parametrize("kind", ["presets", "extensions"])
def test_strict_skipped_skill_symlink_keeps_registration_and_allows_retry(tmp_path, kind):
    from specify_cli._operation_destroy import DestroyError, DestroyRequest, destroy_project
    from tests.specify_cli.test_operation_destroy import symlink, write

    project = _init_project(tmp_path, "claude")
    write(project, ".specify/init-options.json", b'{"ai":"claude","allow_symlinks":true}')
    skills = {"claude": ["speckit-sample"]} if kind == "presets" else ["speckit-sample"]
    registry_path = write(project, f".specify/{kind}/.registry", json.dumps({
        kind: {"sample": {"registered_skills": skills}},
    }).encode())
    target = write(project, "retained-skill/SKILL.md",
                   f"---\nmetadata:\n  source: {kind[:-1]}:sample\n---\nOwned\n".encode()).parent
    link = project / ".claude/skills/speckit-sample"
    symlink(link, target, directory=True)
    with pytest.raises(DestroyError, match="preserved"):
        destroy_project(DestroyRequest(project, confirmed=True))
    assert (project / ".specify/integration.json").exists()
    assert (project / ".specify/integrations/claude.manifest.json").exists()
    assert json.loads(registry_path.read_text())[kind]["sample"]["registered_skills"] == skills
    link.unlink()
    link.mkdir()
    (link / "SKILL.md").write_bytes((target / "SKILL.md").read_bytes())
    destroy_project(DestroyRequest(project, confirmed=True))
    assert not (project / ".specify").exists()


def test_strict_late_options_failure_restores_state_and_allows_retry(tmp_path, monkeypatch):
    from specify_cli._operation_destroy import DestroyRequest, destroy_project
    from specify_cli.integrations import _helpers

    project = _init_project(tmp_path, "claude")
    paths = [
        project / ".specify/integration.json", project / ".specify/init-options.json",
        project / ".specify/integrations/claude.manifest.json",
    ]
    before = {path: path.read_bytes() for path in paths}
    clear = _helpers._clear_init_options_for_integration

    def fail(*args):
        clear(*args)
        raise PermissionError("late options write failed")

    with monkeypatch.context() as fault:
        fault.setattr(_helpers, "_clear_init_options_for_integration", fail)
        with pytest.raises(IntegrationUninstallError, match="late options write failed"):
            uninstall_integration(IntegrationUninstallRequest(project, "claude", require_complete=True))
    assert {path: path.read_bytes() for path in paths} == before
    destroy_project(DestroyRequest(project, confirmed=True))
    assert not (project / ".specify").exists()


@pytest.mark.parametrize("exit_code", [0, 3])
def test_teardown_system_exit_is_a_typed_error_with_recovery_state(tmp_path, monkeypatch, exit_code):
    from specify_cli.integrations import get_integration
    from specify_cli.integrations.manifest import IntegrationManifest

    project = _init_project(tmp_path, "claude")
    record = IntegrationManifest.load("claude", project)
    before = record.manifest_path.read_bytes()

    def teardown(root, manifest, **kwargs):
        manifest.uninstall(root, **kwargs)
        raise SystemExit(exit_code)

    monkeypatch.setattr(get_integration("claude"), "teardown", teardown)
    with pytest.raises(IntegrationUninstallError, match="exited"):
        uninstall_integration(IntegrationUninstallRequest(project, "claude", require_complete=True))
    assert record.manifest_path.read_bytes() == before
    assert (project / ".specify/integration.json").exists()
