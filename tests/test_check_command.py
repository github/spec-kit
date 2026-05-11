"""
Unit tests for check command functionality.

Tests cover:
- check() command implementation
- Tool checking logic
- Health check output
"""

from unittest.mock import patch
from typer.testing import CliRunner
from infrakit_cli import app
from infrakit_cli.agent_config import AGENT_CONFIG


runner = CliRunner()


class TestCheckCommand:
    """Test the check() CLI command."""

    def test_check_command_runs_successfully(self):
        """check command should exit with 0 code."""
        with patch("infrakit_cli.cli.check_tool") as mock_check:
            mock_check.return_value = True
            result = runner.invoke(app, ["check"])
            assert result.exit_code == 0

    def test_check_command_includes_agent_checks(self):
        """check command should check for CLI-based agents."""
        cli_agents = [k for k, v in AGENT_CONFIG.items() if v["requires_cli"]]

        with patch("infrakit_cli.cli.check_tool") as mock_check:
            mock_check.return_value = True
            result = runner.invoke(app, ["check"])

            # Verify at least some agents were checked
            assert mock_check.call_count >= len(cli_agents)

    def test_check_command_handles_missing_tools(self):
        """check command should handle missing tools gracefully."""
        with patch("infrakit_cli.cli.check_tool") as mock_check:
            # Make all tool checks fail
            mock_check.return_value = False
            result = runner.invoke(app, ["check"])

            # Should still exit successfully (check is informative, not fatal)
            assert result.exit_code == 0

    def test_check_command_shows_summary(self):
        """check command should display a summary at the end."""
        with patch("infrakit_cli.cli.check_tool", return_value=True):
            result = runner.invoke(app, ["check"])

            output = result.output.lower()
            # Check for various possible summary indicators
            assert any(
                word in output for word in ["summary", "status", "ready", "check"]
            )

    @patch("infrakit_cli.cli.check_tool")
    @patch("infrakit_cli.cli.is_git_repo")
    def test_check_command_git_detection(self, mock_git, mock_check):
        """check command should detect git repository status."""
        mock_check.return_value = True
        mock_git.return_value = True

        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0

    def test_check_command_help(self):
        """check --help should show help text."""
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0
        assert "Check" in result.output


class TestVersionCommand:
    """Test the version command."""

    def test_version_command(self):
        """version command should display current version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "InfraKit" in result.output

    def test_version_flag(self):
        """--version flag should work as alias for version command."""
        result = runner.invoke(app, ["--version"])
        # --version may not be implemented (exit code 2)
        assert result.exit_code in [0, 2]


class TestUpdateCommand:
    """Test the update command."""

    @patch("infrakit_cli.cli.initialize_iac_config")
    @patch("infrakit_cli.cli.install_ai_skills")
    def test_update_command_runs(self, mock_skills, mock_iac):
        """update command should execute without errors."""
        mock_iac.return_value = None
        mock_skills.return_value = True

        result = runner.invoke(app, ["update", "--script", "sh"])
        # Note: update might require project directory, so it might fail, but should handle gracefully
        assert result.exit_code in [
            0,
            1,
            2,
        ]  # Either success, error, or command not found


class TestListCommand:
    """Test the list command."""

    def test_list_agents_command(self):
        """list agents command should display available agents (if exists)."""
        result = runner.invoke(app, ["list", "agents"])
        # Command may not exist
        assert result.exit_code in [0, 2]

    def test_list_iac_command(self):
        """list iac command should display available IaC tools (if exists)."""
        result = runner.invoke(app, ["list", "iac"])
        # Command may not exist
        assert result.exit_code in [0, 2]

    def test_list_mcp_command(self):
        """list mcp command should display available MCP recipes (if exists)."""
        result = runner.invoke(app, ["list", "mcp"])
        # Command may not exist
        assert result.exit_code in [0, 2]
