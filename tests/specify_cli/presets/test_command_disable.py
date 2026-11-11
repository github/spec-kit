from __future__ import annotations

from pathlib import Path

from specify_cli.presets import (
    PresetManager,
)
from tests.specify_cli.presets._helpers import create_pack as _create_pack


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

    def test_disable_fails_when_remaining_wrapper_is_invalid(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """Disabling a preset re-reconciles every script name it declared.
        If disabling it uncovers a remaining active wrapper that fails
        chain validation, the command must report failure instead of
        reporting "disabled" success while the stale, still-executable
        script is left in place (#4709 review)."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        core = project_dir / ".specify" / "templates" / "scripts" / "shared-script.sh"
        core.parent.mkdir(parents=True, exist_ok=True)
        core.write_text("echo core\n")

        manager = PresetManager(project_dir)

        # A wrap layer with no $CORE_SCRIPT placeholder: valid to install
        # (install only warns), but any chain that still includes it when
        # resolved fails validation.
        bad_wrap_pack = _create_pack(
            temp_dir, valid_pack_data, "bad-wrap-pack", "echo no placeholder\n",
            strategy="wrap", template_type="script", template_name="shared-script",
        )
        manager.install_from_directory(bad_wrap_pack, "0.1.5", priority=5)

        # A replace preset for the same script name, at lower precedence.
        # While it's enabled, it terminates the chain itself above the bad
        # wrap's own validation point only in the sense that both layers
        # are already present and already warn at this install step too --
        # disabling it is what we're exercising below.
        good_pack = _create_pack(
            temp_dir, valid_pack_data, "good-pack", "echo good\n",
            template_type="script", template_name="shared-script",
        )
        manager.install_from_directory(good_pack, "0.1.5", priority=20)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(app, ["preset", "disable", "good-pack"])

        assert result.exit_code == 1, result.output
        assert "could not be reconciled" in result.output.lower()
        # The registry change itself still stands -- good-pack really is
        # disabled -- only the script side failed to converge.
        assert PresetManager(project_dir).registry.get("good-pack")["enabled"] is False
