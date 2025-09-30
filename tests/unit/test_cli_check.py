"""Tests for specify check command."""


from specify_cli import app


class TestCheckCommand:
    """Test suite for specify check command."""

    def test_check_command_runs_successfully(self, runner):
        """Test that check command executes without errors."""
        # Act
        result = runner.invoke(app, ["check"])

        # Assert
        assert result.exit_code == 0
        assert "Checking for installed tools" in result.stdout

    def test_check_command_reports_git(self, runner):
        """Test check command mentions git."""
        # Act
        result = runner.invoke(app, ["check"])

        # Assert
        assert result.exit_code == 0
        assert "git" in result.stdout.lower()

    def test_check_command_shows_ready_message(self, runner):
        """Test that check shows ready message."""
        # Act
        result = runner.invoke(app, ["check"])

        # Assert
        assert result.exit_code == 0
        assert "ready to use" in result.stdout.lower()

    def test_check_command_lists_ai_tools(self, runner):
        """Test that check mentions AI tools."""
        # Act
        result = runner.invoke(app, ["check"])

        # Assert
        assert result.exit_code == 0
        # Should mention at least some AI tools
        ai_tools_mentioned = (
            "claude" in result.stdout.lower()
            or "gemini" in result.stdout.lower()
            or "cursor" in result.stdout.lower()
        )
        assert ai_tools_mentioned


class TestCheckToolFunction:
    """Test suite for check_tool helper function."""

    def test_check_existing_tool(self, mocker):
        """Test checking for tool that exists."""
        # Arrange
        from specify_cli import check_tool

        mock_which = mocker.patch("shutil.which")
        mock_which.return_value = "/usr/bin/git"

        # Act
        result = check_tool("git", "Install git")

        # Assert
        assert result is True

    def test_check_missing_tool(self, mocker):
        """Test checking for tool that does not exist."""
        # Arrange
        from specify_cli import check_tool

        mock_which = mocker.patch("shutil.which")
        mock_which.return_value = None

        # Act
        result = check_tool("nonexistent-tool", "Install hint")

        # Assert
        assert result is False

    def test_check_claude_with_local_installation(self, mocker):
        """Test Claude check with local installation after migrate-installer."""
        # Arrange
        from specify_cli import check_tool

        mock_which = mocker.patch("shutil.which")
        mock_which.return_value = None
        mock_path = mocker.patch("pathlib.Path.exists")
        mock_path.return_value = True
        mock_is_file = mocker.patch("pathlib.Path.is_file")
        mock_is_file.return_value = True

        # Act
        result = check_tool("claude", "Install Claude")

        # Assert
        assert result is True
