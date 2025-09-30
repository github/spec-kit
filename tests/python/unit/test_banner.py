"""Tests for banner and UI functions."""

from specify_cli import show_banner


class TestBanner:
    """Test suite for banner display."""

    def test_show_banner_runs_without_error(self, mocker):
        """Test that show_banner executes without errors."""
        # Arrange
        mock_console = mocker.patch("specify_cli.console")

        # Act
        show_banner()

        # Assert
        # Verify console.print was called
        assert mock_console.print.called
        # Banner should print multiple times (banner lines + tagline)
        assert mock_console.print.call_count >= 2
