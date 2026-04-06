"""Tests for select_with_arrows function."""

from unittest.mock import MagicMock, patch

import pytest

from infrakit_cli import select_with_arrows


class TestSelectWithArrows:
    """Test suite for select_with_arrows function."""

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_first_option(self, mock_console, mock_readkey):
        """Test selecting first option with Enter."""
        mock_readkey.side_effect = ["\r"]  # Enter key

        options = {"opt1": "Option 1", "opt2": "Option 2", "opt3": "Option 3"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt1"

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_navigate_down(self, mock_console, mock_readkey):
        """Test navigating down and selecting."""
        mock_readkey.side_effect = ["\x1b[B", "\r"]  # Down arrow, Enter

        options = {"opt1": "Option 1", "opt2": "Option 2", "opt3": "Option 3"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt2"

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_navigate_up(self, mock_console, mock_readkey):
        """Test navigating up and selecting."""
        mock_readkey.side_effect = [
            "\x1b[B",
            "\x1b[B",
            "\x1b[A",
            "\r",
        ]  # Down, Down, Up, Enter

        options = {"opt1": "Option 1", "opt2": "Option 2", "opt3": "Option 3"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt2"

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_wrap_around_down(self, mock_console, mock_readkey):
        """Test wrapping around when navigating past last option."""
        mock_readkey.side_effect = ["\x1b[B", "\x1b[B", "\r"]  # Down 2 times, Enter

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:")
        # After 2 downs from opt1: opt1 -> opt2 -> opt1 (wraps)
        assert result == "opt1"

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_wrap_around_up(self, mock_console, mock_readkey):
        """Test wrapping around when navigating before first option."""
        mock_readkey.side_effect = ["\x1b[A", "\r"]  # Up, Enter

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt2"  # Should wrap to last

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_single_option(self, mock_console, mock_readkey):
        """Test with single option."""
        mock_readkey.side_effect = ["\r"]

        options = {"only": "Only Option"}
        result = select_with_arrows(options, "Select:")
        assert result == "only"

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_ignores_invalid_keys(self, mock_console, mock_readkey):
        """Test that invalid keys are ignored."""
        mock_readkey.side_effect = ["x", "y", "\r"]  # Invalid keys then Enter

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:")
        assert result == "opt1"

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_with_default(self, mock_console, mock_readkey):
        """Test with default key specified."""
        mock_readkey.side_effect = ["\r"]

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:", default_key="opt2")
        assert result == "opt2"

    @patch("infrakit_cli.readchar.readkey")
    @patch("infrakit_cli.console")
    def test_select_with_arrows_invalid_default(self, mock_console, mock_readkey):
        """Test with invalid default key falls back to first."""
        mock_readkey.side_effect = ["\r"]

        options = {"opt1": "Option 1", "opt2": "Option 2"}
        result = select_with_arrows(options, "Select:", default_key="invalid")
        assert result == "opt1"
