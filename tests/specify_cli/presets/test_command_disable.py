from __future__ import annotations

from pathlib import Path

from specify_cli.presets import (
    PresetManager,
)


class TestPresetDisable:
    """Test preset enable/disable CLI commands."""

    def test_disable_preset(self, project_dir, pack_dir):
        """Test disable command sets enabled=False."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Verify initially enabled
        assert manager.registry.get("test-pack").get("enabled", True) is True

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "disabled" in result.output.lower()

        # Reload registry to see updated value
        manager2 = PresetManager(project_dir)
        assert manager2.registry.get("test-pack")["enabled"] is False

    def test_disable_already_disabled(self, project_dir, pack_dir):
        """Test disable on already disabled preset shows warning."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset and disable it
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manager.registry.update("test-pack", {"enabled": False})

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "already disabled" in result.output.lower()

    def test_disable_not_installed(self, project_dir):
        """Test disable fails for non-installed preset."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "nonexistent"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower()

    def test_disable_corrupted_registry_entry(self, project_dir, pack_dir):
        """Test disable fails gracefully for corrupted registry entry."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset then corrupt the registry entry
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manager.registry.data["presets"]["test-pack"] = "corrupted-string"
        manager.registry._save()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "test-pack"])

        assert result.exit_code == 1
        assert "corrupted state" in result.output.lower()
