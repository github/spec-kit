"""Tests for ``specify extension disable``.

Mirrors ``specify_cli.extensions.command_disable``.
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
