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

    def fail(*args):
        raise OSError("contribution cleanup failed")

    monkeypatch.setattr("specify_cli.extensions.ExtensionManager.unregister_agent_artifacts", fail)
    with pytest.raises(IntegrationUninstallError, match="contribution cleanup failed"):
        uninstall_integration(IntegrationUninstallRequest(
            project, "claude", require_complete=True,
        ))
    state = json.loads((project / ".specify/integration.json").read_text())
    assert "claude" in state["installed_integrations"]
    assert (project / ".specify/integrations/claude.manifest.json").exists()
