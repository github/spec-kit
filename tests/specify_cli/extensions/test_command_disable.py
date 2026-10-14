"""Tests for ``specify extension disable``.

Mirrors ``specify_cli.extensions.command_disable``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionError,
    ExtensionManager,
    ExtensionRegistry,
    HookExecutor,
)
from tests.specify_cli.extensions._helpers import installed_generic_hook_extension


class TestExtensionDisableCLI:
    """CLI tests for ``specify extension disable``."""

    def test_disable_reenable_hint_escapes_extension_id_markup(self, tmp_path):
        """Disable success hints should not parse extension IDs as markup."""

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        extension_id = "[red]bad[/red]"
        installed = [
            {
                "id": extension_id,
                "name": "Bad Extension",
                "version": "1.0.0",
                "description": "Test extension",
                "enabled": True,
            }
        ]

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionRegistry, "get", return_value={"enabled": True}), \
             patch.object(ExtensionRegistry, "update", return_value=None), \
             patch.object(HookExecutor, "get_project_config", return_value={}):
            result = runner.invoke(
                app,
                ["extension", "disable", extension_id],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert "specify extension enable [red]bad[/red]" in result.output

    def test_disable_publication_failure_restores_generic_registry_and_artifact(
        self, tmp_path, extension_dir
    ):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        original_artifact = artifact.read_bytes()
        config = project / ".specify/extensions.yml"
        original_config = config.read_bytes()
        with patch.object(Path, "cwd", return_value=project), \
             patch.object(HookExecutor, "save_project_config", side_effect=OSError("projection failed")):
            result = CliRunner().invoke(app, ["extension", "disable", "test-ext"])
        assert result.exit_code == 1
        assert "projection failed" in result.output
        assert ExtensionManager(project).registry.get("test-ext")["enabled"] is True
        assert artifact.read_bytes() == original_artifact
        assert config.read_bytes() == original_config

    def test_disable_reports_failed_generic_artifact_rollback(self, tmp_path, extension_dir):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        with patch.object(Path, "cwd", return_value=project), \
             patch.object(HookExecutor, "save_project_config", side_effect=OSError("projection failed")), \
             patch.object(ExtensionManager, "register_enabled_extensions_for_agent"):
            result = CliRunner().invoke(app, ["extension", "disable", "test-ext"])
        assert result.exit_code == 1
        assert "rollback failed" in result.output
        assert "did not restore generic" in result.output
        assert not artifact.exists()

    def test_generic_rollback_verifies_owned_artifacts_at_domain_boundary(
        self, tmp_path, extension_dir
    ):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        manager = ExtensionManager(project)
        previous = manager.registry.get("test-ext")
        manager.disable_generic_extension_artifacts("test-ext")
        assert not artifact.exists()
        with patch.object(manager, "register_enabled_extensions_for_agent"):
            with pytest.raises(ExtensionError, match="did not restore generic"):
                manager.restore_generic_extension_after_failed_disable(
                    "test-ext", previous
                )
