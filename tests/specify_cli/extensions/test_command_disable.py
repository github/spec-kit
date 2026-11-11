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

    def test_disable_reconciles_preset_wrapped_extension_script(
        self, project_dir, temp_dir
    ):
        """A preset's generated chain can wrap an extension-provided script,
        copying the extension's content inline at materialization time.
        Disabling the extension must reconcile that chain so the copied
        content stops running, instead of staying inert after the extension
        is gone (#4709 review)."""
        import yaml

        from specify_cli.extensions import ExtensionManager
        from specify_cli.presets import PresetManager

        ext_dir = temp_dir / "scriptext"
        (ext_dir / "scripts").mkdir(parents=True)
        (ext_dir / "scripts" / "scriptext-task.sh").write_text(
            "#!/usr/bin/env bash\necho FROM-EXTENSION\n", encoding="utf-8"
        )
        ext_manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "scriptext",
                "name": "Script Ext",
                "version": "1.0.0",
                "description": "test",
                "author": "test",
                "repository": "https://example.com",
                "license": "MIT",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "scripts": [
                    {
                        "name": "scriptext-task",
                        "file": "scripts/scriptext-task.sh",
                        "description": "test",
                        "runtimes": ["bash"],
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(ext_manifest_data, f)

        ExtensionManager(project_dir).install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        pack_dir = temp_dir / "wrap-pack"
        (pack_dir / "scripts").mkdir(parents=True)
        (pack_dir / "scripts" / "scriptext-task.sh").write_text(
            "echo WRAP-BEFORE\n$CORE_SCRIPT\n", encoding="utf-8"
        )
        pack_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "wrap-pack",
                "name": "wrap-pack",
                "version": "1.0.0",
                "description": "test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "script",
                        "name": "scriptext-task",
                        "file": "scripts/scriptext-task.sh",
                        "strategy": "wrap",
                    }
                ]
            },
        }
        with open(pack_dir / "preset.yml", "w") as f:
            yaml.dump(pack_data, f)

        preset_manager = PresetManager(project_dir)
        preset_manager.install_from_directory(pack_dir, "0.1.0")

        core_path = project_dir / ".specify" / "scripts" / "bash" / "scriptext-task.speckit-core.sh"
        assert "FROM-EXTENSION" in core_path.read_text(encoding="utf-8")

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "disable", "scriptext"])
        assert result.exit_code == 0, result.output

        # The extension's layer is gone from resolution once disabled, and
        # with no core/bundled replace below the lone wrap layer, the chain
        # resolves empty -- reconciliation must have actually re-run for
        # the stale generated files (including the core copy) to be
        # retired rather than left on disk unchanged.
        assert not core_path.exists()
