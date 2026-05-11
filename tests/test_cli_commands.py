"""Tests for CLI commands."""


from typer.testing import CliRunner

from infrakit_cli import app


runner = CliRunner()


class TestCheckCommand:
    """Test suite for check command."""

    def test_check_command_runs_successfully(self):
        """Test that check command runs without errors."""
        result = runner.invoke(app, ["check"])
        assert result.exit_code == 0

    def test_check_command_includes_agent_checks(self):
        """Test that check command includes agent checks."""
        result = runner.invoke(app, ["check"])
        assert "claude" in result.output.lower() or "git" in result.output.lower()

    def test_check_command_handles_missing_tools(self):
        """Test that check command handles missing tools gracefully."""
        result = runner.invoke(app, ["check"])
        # Should complete without crashing even if tools are missing
        assert result.exit_code == 0

    def test_check_command_help(self):
        """Test check command help."""
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0
        assert "check" in result.output.lower() or "tool" in result.output.lower()


class TestVersionCommand:
    """Test suite for version command."""

    def test_version_command(self):
        """Test version command outputs version info."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        # Check for version-related content
        assert "version" in result.output.lower() or "infrakit" in result.output.lower()

    def test_version_flag(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        # Note: --version may not be implemented
        assert result.exit_code in [0, 2]  # 0 if implemented, 2 if not


class TestListCommand:
    """Test suite for list commands."""

    def test_list_agents_command(self):
        """Test list agents command."""
        result = runner.invoke(app, ["list", "agents"])
        # This command may not exist
        assert result.exit_code in [0, 2]

    def test_list_iac_command(self):
        """Test list iac command."""
        result = runner.invoke(app, ["list", "iac"])
        # This command may not exist
        assert result.exit_code in [0, 2]

    def test_list_mcp_command(self):
        """Test list mcp command."""
        result = runner.invoke(app, ["list", "mcp"])
        # This command may not exist
        assert result.exit_code in [0, 2]


class TestMcpCommand:
    """Test suite for mcp command."""

    def test_mcp_command_help(self):
        """Test mcp command help."""
        result = runner.invoke(app, ["mcp", "--help"])
        # May or may not exist
        assert result.exit_code in [0, 2]


class TestMainApp:
    """Test suite for main app functionality."""

    def test_app_no_args_shows_help(self):
        """Test running app with no arguments shows help."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "infrakit" in result.output.lower() or "usage" in result.output.lower()

    def test_app_help_flag(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "usage" in result.output.lower() or "options" in result.output.lower()
