"""Tests for ``specify extension remove``.

Mirrors ``specify_cli.extensions.command_remove``.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionManager,
    ExtensionRegistry,
)


class TestExtensionRemoveCLI:
    """CLI tests for `specify extension remove` confirmation prompt wording."""

    def _install_ext(self, project_dir, ext_dir):
        """Install extension and return the manager."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)
        return manager

    def test_remove_reconciles_preset_wrapped_extension_script(self, tmp_path):
        """Removing an extension must reconcile any script chain it provided
        content for, the same way disabling it does -- a preset wrapping that
        script has the extension's content copied inline into its generated
        core file, and that copy must not outlive the extension (#4709
        review)."""
        import yaml

        from specify_cli.presets import PresetManager

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        ext_dir = tmp_path / "scriptext"
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

        self._install_ext(project_dir, ext_dir)

        pack_dir = tmp_path / "wrap-pack"
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

        PresetManager(project_dir).install_from_directory(pack_dir, "0.1.0")

        core_path = (
            project_dir / ".specify" / "scripts" / "bash"
            / "scriptext-task.speckit-core.sh"
        )
        assert "FROM-EXTENSION" in core_path.read_text(encoding="utf-8")

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "remove", "scriptext", "--force"]
            )
        assert result.exit_code == 0, result.output
        assert not core_path.exists()

    def test_remove_confirmation_singular_command(self, tmp_path, extension_dir):
        """Confirmation prompt should say '1 command' (singular) when one command registered."""

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manager = self._install_ext(project_dir, extension_dir)
        # Inject registered_commands with 1 entry so cmd_count == 1
        manager.registry.update("test-ext", {"registered_commands": {"claude": ["speckit.test-ext.hello"]}})

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "remove", "test-ext"], input="n\n", catch_exceptions=False
            )

        assert "1 command" in result.output
        assert "1 commands" not in result.output

    def test_remove_confirmation_plural_commands(self, tmp_path, extension_dir):
        """Confirmation prompt should say '2 commands' (plural) when two commands registered."""

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        manager = self._install_ext(project_dir, extension_dir)
        # Inject registered_commands with 2 entries so cmd_count == 2
        manager.registry.update("test-ext", {"registered_commands": {"claude": ["speckit.test-ext.hello", "speckit.test-ext.run"]}})

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app, ["extension", "remove", "test-ext"], input="n\n", catch_exceptions=False
            )

        assert "2 commands" in result.output

    def test_remove_output_escapes_extension_id_markup(self, tmp_path):
        """Removal paths and reinstall hints must not parse extension IDs as markup."""
        from typer.testing import CliRunner

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
             patch.object(ExtensionManager, "get_extension", return_value=SimpleNamespace(commands=[])), \
             patch.object(ExtensionRegistry, "get", return_value={"registered_commands": {}, "registered_skills": []}), \
             patch.object(ExtensionManager, "remove", return_value=True):
            result = runner.invoke(
                app,
                ["extension", "remove", extension_id, "--force"],
                catch_exceptions=True,
            )

        assert result.exit_code == 0, result.output
        assert ".specify/extensions/.backup/[red]bad[/red]/" in result.output
        assert "specify extension add [red]bad[/red]" in result.output
