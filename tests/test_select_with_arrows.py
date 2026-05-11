"""Tests for select_with_arrows function.

These tests patch ``infrakit_cli.get_key`` directly (rather than the underlying
``readchar.readkey``) so they remain stable across platforms — ``readchar``
maps key codes differently on macOS vs Linux, and the high-level ``get_key``
shields us from that.
"""

from unittest.mock import patch

from infrakit_cli import select_with_arrows


class TestSelectWithArrows:
    """Test suite for select_with_arrows function."""

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_first_option(self, mock_console, mock_get_key):
        """Test selecting first option with Enter."""
        mock_get_key.side_effect = ["enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2", "opt3": "Option 3"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt1"

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_navigate_down(self, mock_console, mock_get_key):
        """Test navigating down and selecting."""
        mock_get_key.side_effect = ["down", "enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2", "opt3": "Option 3"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt2"

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_navigate_up(self, mock_console, mock_get_key):
        """Test navigating up and selecting."""
        mock_get_key.side_effect = ["down", "down", "up", "enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2", "opt3": "Option 3"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt2"

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_wrap_around_down(self, mock_console, mock_get_key):
        """Test wrapping around when navigating past last option."""
        mock_get_key.side_effect = ["down", "down", "enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:")
        # After 2 downs from opt1: opt1 -> opt2 -> opt1 (wraps)
        assert result == "opt1"

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_wrap_around_up(self, mock_console, mock_get_key):
        """Test wrapping around when navigating before first option."""
        mock_get_key.side_effect = ["up", "enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt2"  # Should wrap to last

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_single_option(self, mock_console, mock_get_key):
        """Test with single option."""
        mock_get_key.side_effect = ["enter"]

        options = {"only": "Only Option"}
        result = select_with_arrows(options, "Select:")
        assert result == "only"

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_ignores_invalid_keys(self, mock_console, mock_get_key):
        """Test that unrecognised keys are ignored."""
        # Any string that's not 'up'/'down'/'enter'/'escape' is treated as
        # a no-op by select_with_arrows's inner loop.
        mock_get_key.side_effect = ["x", "y", "enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt1"

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_with_default(self, mock_console, mock_get_key):
        """Test with default key specified."""
        mock_get_key.side_effect = ["enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:", default_key="opt2")
        assert result == "opt2"

    @patch("infrakit_cli.get_key")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_invalid_default(self, mock_console, mock_get_key):
        """Test with invalid default key falls back to first."""
        mock_get_key.side_effect = ["enter"]

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:", default_key="invalid")
        assert result == "opt1"
