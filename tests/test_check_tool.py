"""Tests for check_tool function."""

from unittest.mock import patch


from infrakit_cli import check_tool, StepTracker


class TestCheckTool:
    """Test suite for check_tool function."""

    @patch("infrakit_cli.shutil.which")
    def test_check_tool_found(self, mock_which):
        """Test check_tool returns True when tool is found."""
        mock_which.return_value = "/usr/bin/git"

        result = check_tool("git")
        assert result is True

    @patch("infrakit_cli.shutil.which")
    def test_check_tool_not_found(self, mock_which):
        """Test check_tool returns False when tool is not found."""
        mock_which.return_value = None

        result = check_tool("nonexistent-tool")
        assert result is False

    @patch("infrakit_cli.shutil.which")
    def test_check_tool_with_tracker(self, mock_which):
        """Test check_tool with StepTracker."""
        mock_which.return_value = "/usr/bin/git"
        tracker = StepTracker("Test")
        tracker.add("git", "Git")

        result = check_tool("git", tracker)
        assert result is True

    @patch("infrakit_cli.shutil.which")
    def test_check_tool_with_tracker_not_found(self, mock_which):
        """Test check_tool with tracker when tool not found."""
        mock_which.return_value = None
        tracker = StepTracker("Test")
        tracker.add("nonexistent", "Nonexistent Tool")

        result = check_tool("nonexistent", tracker)
        assert result is False

    @patch("infrakit_cli.shutil.which")
    def test_check_tool_empty_string(self, mock_which):
        """Test check_tool with empty string."""
        mock_which.return_value = None

        result = check_tool("")
        assert result is False

    @patch("infrakit_cli.shutil.which")
    def test_check_tool_with_path(self, mock_which):
        """Test check_tool finds tool at specific path."""
        mock_which.return_value = "/usr/local/bin/custom-tool"

        result = check_tool("custom-tool")
        assert result is True
        mock_which.assert_called_once_with("custom-tool")
