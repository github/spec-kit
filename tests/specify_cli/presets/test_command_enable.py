from __future__ import annotations

from pathlib import Path

from specify_cli.presets import (
    PresetManager,
)
from tests.specify_cli.presets._helpers import (
    install_constitution_sync_preset,
    install_self_test_preset,
    make_convention_constitution_preset as _make_convention_constitution_preset,
)


class TestPresetEnable:
    """Test preset enable/disable CLI commands."""

    def test_enable_preset(self, project_dir, pack_dir):
        """Test enable command sets enabled=True."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset and disable it
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manager.registry.update("test-pack", {"enabled": False})

        # Verify disabled
        assert manager.registry.get("test-pack")["enabled"] is False

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "enable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "enabled" in result.output.lower()

        # Reload registry to see updated value
        manager2 = PresetManager(project_dir)
        assert manager2.registry.get("test-pack")["enabled"] is True

    def test_enable_disable_reconciles_generated_constitution(
        self, project_dir, temp_dir
    ):
        """Enable and disable rematerialize the winning constitution layer."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5", priority=1
        )
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Convention Constitution\n"
        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            disabled = runner.invoke(
                app, ["preset", "disable", "convention-constitution"]
            )

        assert disabled.exit_code == 0, disabled.output
        assert "preset:self-test" in memory.read_text()

        with patch.object(Path, "cwd", return_value=project_dir):
            enabled = runner.invoke(
                app, ["preset", "enable", "convention-constitution"]
            )

        assert enabled.exit_code == 0, enabled.output
        assert memory.read_text() == "# Convention Constitution\n"

    def test_stack_changes_do_not_create_missing_constitution(
        self, project_dir, pack_dir
    ):
        """Stack changes for non-providers do not seed a missing constitution."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        PresetManager(project_dir).install_from_directory(pack_dir, "0.1.5")
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        runner = CliRunner()

        for args in (
            ["preset", "set-priority", "test-pack", "5"],
            ["preset", "disable", "test-pack"],
            ["preset", "enable", "test-pack"],
        ):
            with patch.object(Path, "cwd", return_value=project_dir):
                result = runner.invoke(app, args)
            assert result.exit_code == 0, result.output
            assert not memory.exists()

    def test_enable_already_enabled(self, project_dir, pack_dir):
        """Test enable on already enabled preset shows warning."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset (enabled by default)
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "enable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "already enabled" in result.output.lower()

    def test_enable_not_installed(self, project_dir):
        """Test enable fails for non-installed preset."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "enable", "nonexistent"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower()

    def test_enable_corrupted_registry_entry(self, project_dir, pack_dir):
        """Test enable fails gracefully for corrupted registry entry."""
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
            result = runner.invoke(app, ["preset", "enable", "test-pack"])

        assert result.exit_code == 1
        assert "corrupted state" in result.output.lower()
