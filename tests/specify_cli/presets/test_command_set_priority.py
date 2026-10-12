from __future__ import annotations

from pathlib import Path

from specify_cli.presets import (
    PresetManager,
)
from tests.conftest import strip_ansi
from tests.specify_cli.presets._helpers import (
    install_constitution_sync_preset,
    install_self_test_preset,
    make_convention_constitution_preset as _make_convention_constitution_preset,
)


class TestPresetSetPriority:
    """Test preset set-priority CLI command."""

    def test_set_priority_changes_priority(self, project_dir, pack_dir):
        """Test set-priority command changes preset priority."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset with default priority
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Verify default priority
        assert manager.registry.get("test-pack")["priority"] == 10

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "priority changed: 10 → 5" in plain

        # Reload registry to see updated value
        manager2 = PresetManager(project_dir)
        assert manager2.registry.get("test-pack")["priority"] == 5

    def test_set_priority_reconciles_generated_constitution(
        self, project_dir, temp_dir
    ):
        """Changing priority rematerializes an unchanged generated constitution."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        manager = PresetManager(project_dir)
        install_constitution_sync_preset(manager)
        install_self_test_preset(manager)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5", priority=20
        )
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert "preset:self-test" in memory.read_text()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(
                app,
                ["preset", "set-priority", "convention-constitution", "1"],
            )

        assert result.exit_code == 0, result.output
        assert memory.read_text() == "# Convention Constitution\n"

    def test_set_priority_same_value_no_change(self, project_dir, pack_dir):
        """Test set-priority with same value shows already set message."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset with priority 5
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=5)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "already has priority 5" in plain

    def test_set_priority_repairs_corrupted_bool(self, project_dir, pack_dir):
        """A corrupted boolean priority must be repaired, not skipped.

        ``isinstance(True, int)`` is True and ``True == 1`` in Python, so a
        stored ``True`` priority would short-circuit the ``already has
        priority 1`` skip path and never get rewritten to a real int —
        contradicting the comment that promises corrupted values are
        repaired. The guard must exclude bools (like normalize_priority).
        """
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=5)
        # Inject a corrupted boolean priority (True == 1).
        manager.registry.update("test-pack", {"priority": True})

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "1"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        # The corrupted bool must be repaired, not reported as already-set.
        assert "already has priority" not in plain
        assert "priority changed" in plain

        # The stored value is now a real int, not a bool.
        reloaded = PresetManager(project_dir).registry.get("test-pack")
        assert reloaded["priority"] == 1
        assert not isinstance(reloaded["priority"], bool)

    def test_set_priority_invalid_value(self, project_dir, pack_dir):
        """Test set-priority rejects invalid priority values."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        # Install preset
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "0"])

        assert result.exit_code == 1, result.output
        assert "Priority must be a positive integer" in result.output

    def test_set_priority_not_installed(self, project_dir):
        """Test set-priority fails for non-installed preset."""
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "nonexistent", "5"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower()
