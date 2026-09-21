"""Tests for ``specify extension set-priority``.

Mirrors ``specify_cli.extensions.command_set_priority``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    ExtensionManager,
)
from tests.conftest import strip_ansi


class TestExtensionSetPriorityCLI:
    """CLI tests for ``specify extension set-priority``."""

    def test_set_priority_changes_priority(self, extension_dir, project_dir):
        """Test set-priority command changes extension priority."""

        runner = CliRunner()

        # Install extension with default priority
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Verify default priority
        assert manager.registry.get("test-ext")["priority"] == 10

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "priority changed: 10 → 5" in plain

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 5

    def test_set_priority_same_value_no_change(self, extension_dir, project_dir):
        """Test set-priority with same value shows already set message."""

        runner = CliRunner()

        # Install extension with priority 5
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=5)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "already has priority 5" in plain

    def test_set_priority_repairs_corrupted_bool(self, extension_dir, project_dir):
        """A corrupted boolean priority must be repaired, not skipped.

        ``isinstance(True, int)`` is True and ``True == 1`` in Python, so a
        stored ``True`` priority would short-circuit the ``already has
        priority 1`` skip path and never get rewritten to a real int —
        contradicting the comment that promises corrupted values are
        repaired. The guard must exclude bools (like normalize_priority).
        """

        runner = CliRunner()

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False, priority=5
        )
        # Inject a corrupted boolean priority (True == 1).
        manager.registry.update("test-ext", {"priority": True})

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "1"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        # The corrupted bool must be repaired, not reported as already-set.
        assert "already has priority" not in plain
        assert "priority changed" in plain

        # The stored value is now a real int, not a bool.
        reloaded = ExtensionManager(project_dir).registry.get("test-ext")
        assert reloaded["priority"] == 1
        assert not isinstance(reloaded["priority"], bool)

    def test_set_priority_invalid_value(self, extension_dir, project_dir):
        """Test set-priority rejects invalid priority values."""

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "0"])

        assert result.exit_code == 1, result.output
        assert "Priority must be a positive integer" in result.output

    def test_set_priority_not_installed(self, project_dir):
        """Test set-priority fails for non-installed extension."""

        runner = CliRunner()

        # Ensure .specify exists
        (project_dir / ".specify").mkdir(parents=True, exist_ok=True)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "nonexistent", "5"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower() or "no extensions installed" in result.output.lower()

    def test_set_priority_by_display_name(self, extension_dir, project_dir):
        """Test set-priority works with extension display name."""

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Use display name "Test Extension" instead of ID "test-ext"
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "Test Extension", "3"])

        assert result.exit_code == 0, result.output
        assert "priority changed" in result.output

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 3
