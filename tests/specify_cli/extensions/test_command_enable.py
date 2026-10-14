"""Tests for ``specify extension enable``.

Mirrors ``specify_cli.extensions.command_enable``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionManager,
    ExtensionRegistry,
    HookExecutor,
)
from tests.specify_cli.extensions._helpers import installed_generic_hook_extension


class TestExtensionEnableCLI:
    """CLI tests for ``specify extension enable``."""

    def test_enable_registry_error_escapes_extension_id_markup(self, tmp_path):
        """Registry-corruption errors should render extension IDs literally."""

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
                "enabled": False,
            }
        ]

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionManager, "list_installed", return_value=installed), \
             patch.object(ExtensionRegistry, "get", return_value=None):
            result = runner.invoke(
                app,
                ["extension", "enable", extension_id],
                catch_exceptions=True,
            )

        assert result.exit_code == 1, result.output
        assert "Extension '[red]bad[/red]' not found in registry" in result.output

    def test_enable_publication_failure_restores_generic_disabled_state(
        self, tmp_path, extension_dir
    ):
        project, _, artifact = installed_generic_hook_extension(
            tmp_path, extension_dir, native_hooks=True
        )
        with patch.object(Path, "cwd", return_value=project):
            disabled = CliRunner().invoke(app, ["extension", "disable", "test-ext"])
        assert disabled.exit_code == 0, disabled.output
        assert not artifact.exists()
        config = project / ".specify/extensions.yml"
        original_config = config.read_bytes()
        with patch.object(Path, "cwd", return_value=project), \
             patch.object(HookExecutor, "save_project_config", side_effect=OSError("projection failed")):
            result = CliRunner().invoke(app, ["extension", "enable", "test-ext"])
        assert result.exit_code == 1
        assert "projection failed" in result.output
        assert ExtensionManager(project).registry.get("test-ext")["enabled"] is False, result.output
        assert not artifact.exists()
        assert config.read_bytes() == original_config
