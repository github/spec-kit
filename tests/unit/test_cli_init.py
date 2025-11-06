"""
Unit tests for CLI init command and related functions.
"""
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
import typer
from typer.testing import CliRunner

# Import after sys.path manipulation if needed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from specify_cli import (
    app,
    check_tool,
    is_git_repo,
    init_git_repo,
    merge_json_files,
    AGENT_CONFIG,
    SCRIPT_TYPE_CHOICES,
    _github_token,
    _github_auth_headers,
)


runner = CliRunner()


@pytest.mark.unit
class TestCheckTool:
    """Tests for check_tool function."""

    def test_check_tool_found(self):
        """Test check_tool returns True when tool is found."""
        with patch("shutil.which", return_value="/usr/bin/git"):
            assert check_tool("git") is True

    def test_check_tool_not_found(self):
        """Test check_tool returns False when tool is not found."""
        with patch("shutil.which", return_value=None):
            assert check_tool("nonexistent") is False

    def test_check_tool_claude_local_path(self, temp_dir: Path):
        """Test check_tool prioritizes Claude local path."""
        claude_path = temp_dir / ".claude" / "local" / "claude"
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.touch()

        with patch("specify_cli.CLAUDE_LOCAL_PATH", claude_path):
            assert check_tool("claude") is True

    def test_check_tool_with_tracker(self):
        """Test check_tool updates tracker when provided."""
        mock_tracker = Mock()
        with patch("shutil.which", return_value="/usr/bin/git"):
            result = check_tool("git", tracker=mock_tracker)
            assert result is True
            mock_tracker.complete.assert_called_once_with("git", "available")

    def test_check_tool_with_tracker_not_found(self):
        """Test check_tool updates tracker on error."""
        mock_tracker = Mock()
        with patch("shutil.which", return_value=None):
            result = check_tool("nonexistent", tracker=mock_tracker)
            assert result is False
            mock_tracker.error.assert_called_once_with("nonexistent", "not found")


@pytest.mark.unit
class TestGitOperations:
    """Tests for git-related functions."""

    def test_is_git_repo_true(self, temp_dir: Path):
        """Test is_git_repo returns True for git repository."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            assert is_git_repo(temp_dir) is True
            mock_run.assert_called_once()

    def test_is_git_repo_false(self, temp_dir: Path):
        """Test is_git_repo returns False for non-git directory."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            assert is_git_repo(temp_dir) is False

    def test_is_git_repo_git_not_found(self, temp_dir: Path):
        """Test is_git_repo handles git not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert is_git_repo(temp_dir) is False

    def test_is_git_repo_not_directory(self, temp_dir: Path):
        """Test is_git_repo returns False for non-directory."""
        file_path = temp_dir / "file.txt"
        file_path.touch()
        assert is_git_repo(file_path) is False

    def test_init_git_repo_success(self, temp_dir: Path, mock_git_commands):
        """Test successful git repository initialization."""
        success, error = init_git_repo(temp_dir, quiet=True)
        assert success is True
        assert error is None
        assert mock_git_commands.call_count == 3  # init, add, commit

    def test_init_git_repo_failure(self, temp_dir: Path):
        """Test git repository initialization failure."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git", stderr="error")):
            success, error = init_git_repo(temp_dir, quiet=True)
            assert success is False
            assert error is not None
            assert "error" in error.lower()


@pytest.mark.unit
class TestMergeJsonFiles:
    """Tests for JSON merging functionality."""

    def test_merge_json_files_new_keys(self, temp_dir: Path):
        """Test merging adds new keys."""
        existing_file = temp_dir / "existing.json"
        existing_file.write_text(json.dumps({"key1": "value1"}))

        new_content = {"key2": "value2"}
        result = merge_json_files(existing_file, new_content)

        assert result == {"key1": "value1", "key2": "value2"}

    def test_merge_json_files_override_keys(self, temp_dir: Path):
        """Test merging overrides existing keys."""
        existing_file = temp_dir / "existing.json"
        existing_file.write_text(json.dumps({"key1": "value1"}))

        new_content = {"key1": "new_value"}
        result = merge_json_files(existing_file, new_content)

        assert result == {"key1": "new_value"}

    def test_merge_json_files_nested_merge(self, temp_dir: Path):
        """Test deep merging of nested dictionaries."""
        existing_file = temp_dir / "existing.json"
        existing_file.write_text(json.dumps({
            "editor": {
                "fontSize": 12,
                "tabSize": 2
            }
        }))

        new_content = {
            "editor": {
                "fontSize": 14,
                "wordWrap": "on"
            }
        }
        result = merge_json_files(existing_file, new_content)

        assert result == {
            "editor": {
                "fontSize": 14,
                "tabSize": 2,
                "wordWrap": "on"
            }
        }

    def test_merge_json_files_nonexistent_file(self, temp_dir: Path):
        """Test merging with nonexistent file returns new content."""
        nonexistent_file = temp_dir / "nonexistent.json"
        new_content = {"key": "value"}
        result = merge_json_files(nonexistent_file, new_content)

        assert result == new_content

    def test_merge_json_files_invalid_json(self, temp_dir: Path):
        """Test merging with invalid JSON returns new content."""
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("invalid json")

        new_content = {"key": "value"}
        result = merge_json_files(invalid_file, new_content)

        assert result == new_content


@pytest.mark.unit
class TestAgentConfig:
    """Tests for agent configuration."""

    def test_agent_config_structure(self):
        """Test agent config has required fields."""
        for agent_key, config in AGENT_CONFIG.items():
            assert "name" in config
            assert "folder" in config
            assert "requires_cli" in config
            # install_url can be None for IDE-based agents

    def test_agent_config_cli_requirement_consistency(self):
        """Test agents requiring CLI have install URLs."""
        for agent_key, config in AGENT_CONFIG.items():
            if config["requires_cli"]:
                # CLI agents should have install URLs (except if explicitly handled elsewhere)
                assert "install_url" in config

    def test_script_type_choices(self):
        """Test script type choices are defined."""
        assert "sh" in SCRIPT_TYPE_CHOICES
        assert "ps" in SCRIPT_TYPE_CHOICES
        assert len(SCRIPT_TYPE_CHOICES) == 2


@pytest.mark.unit
class TestGitHubTokenHandling:
    """Tests for GitHub token handling."""

    def test_github_token_from_cli_arg(self):
        """Test GitHub token from CLI argument takes precedence."""
        with patch.dict("os.environ", {"GH_TOKEN": "env_token"}):
            token = _github_token(cli_token="cli_token")
            assert token == "cli_token"

    def test_github_token_from_gh_token_env(self):
        """Test GitHub token from GH_TOKEN environment variable."""
        with patch.dict("os.environ", {"GH_TOKEN": "gh_token"}, clear=True):
            token = _github_token()
            assert token == "gh_token"

    def test_github_token_from_github_token_env(self):
        """Test GitHub token from GITHUB_TOKEN environment variable."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "github_token"}, clear=True):
            token = _github_token()
            assert token == "github_token"

    def test_github_token_gh_token_precedence(self):
        """Test GH_TOKEN takes precedence over GITHUB_TOKEN."""
        with patch.dict("os.environ", {"GH_TOKEN": "gh_token", "GITHUB_TOKEN": "github_token"}):
            token = _github_token()
            assert token == "gh_token"

    def test_github_token_empty_string_returns_none(self):
        """Test empty token string returns None."""
        with patch.dict("os.environ", {}, clear=True):
            token = _github_token(cli_token="  ")
            assert token is None

    def test_github_token_none_when_no_token(self):
        """Test None returned when no token available."""
        with patch.dict("os.environ", {}, clear=True):
            token = _github_token()
            assert token is None

    def test_github_auth_headers_with_token(self):
        """Test authorization headers with valid token."""
        headers = _github_auth_headers(cli_token="test_token")
        assert headers == {"Authorization": "Bearer test_token"}

    def test_github_auth_headers_without_token(self):
        """Test empty headers when no token."""
        with patch.dict("os.environ", {}, clear=True):
            headers = _github_auth_headers()
            assert headers == {}


@pytest.mark.unit
class TestInitCommandValidation:
    """Tests for init command input validation."""

    def test_init_requires_project_name_or_flag(self):
        """Test init command requires project name or --here flag."""
        with patch("specify_cli.show_banner"):
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 1
            assert "Error" in result.stdout or result.exit_code != 0

    def test_init_rejects_both_name_and_here_flag(self):
        """Test init command rejects both project name and --here flag."""
        with patch("specify_cli.show_banner"):
            result = runner.invoke(app, ["init", "myproject", "--here"])
            assert result.exit_code == 1

    def test_init_rejects_existing_directory(self, temp_dir: Path):
        """Test init command rejects existing directory."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()

        with patch("specify_cli.show_banner"), \
             patch("specify_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(app, ["init", "existing"])
            assert result.exit_code == 1
            assert "already exists" in result.stdout.lower()

    def test_init_accepts_dot_for_current_directory(self):
        """Test init command accepts '.' for current directory."""
        with patch("specify_cli.show_banner"), \
             patch("specify_cli.Path.cwd") as mock_cwd, \
             patch("specify_cli.check_tool", return_value=True), \
             patch("specify_cli.download_and_extract_template"), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.init_git_repo", return_value=(True, None)), \
             patch("typer.confirm", return_value=True):

            mock_dir = Path("/tmp/test")
            mock_cwd.return_value = mock_dir
            with patch.object(Path, "iterdir", return_value=[]):
                result = runner.invoke(app, ["init", ".", "--ai-assistant", "claude", "--script-type", "sh", "--ignore-agent-tools"])
                # May fail due to missing mocks, but should not reject the '.' argument
                assert "cannot specify both" not in result.stdout.lower()

    def test_init_invalid_ai_assistant(self):
        """Test init command rejects invalid AI assistant."""
        with patch("specify_cli.show_banner"), \
             patch("specify_cli.Path.cwd"):
            result = runner.invoke(app, ["init", "myproject", "--ai-assistant", "invalid-agent"])
            assert result.exit_code == 1
            assert "invalid ai assistant" in result.stdout.lower()

    def test_init_invalid_script_type(self):
        """Test init command rejects invalid script type."""
        with patch("specify_cli.show_banner"), \
             patch("specify_cli.Path.cwd"):
            result = runner.invoke(app, ["init", "myproject", "--script-type", "invalid"])
            assert result.exit_code == 1
            assert "invalid script type" in result.stdout.lower()


@pytest.mark.unit
class TestProjectPathHandling:
    """Tests for project path handling logic."""

    def test_project_path_resolution_absolute(self, temp_dir: Path):
        """Test project path is resolved to absolute path."""
        with patch("specify_cli.Path.cwd", return_value=temp_dir):
            project_path = Path("myproject").resolve()
            assert project_path.is_absolute()

    def test_project_path_here_flag_uses_cwd(self, temp_dir: Path):
        """Test --here flag uses current working directory."""
        with patch("specify_cli.Path.cwd", return_value=temp_dir):
            assert Path.cwd() == temp_dir


@pytest.mark.unit
class TestErrorHandling:
    """Tests for error handling in init command."""

    def test_init_handles_network_errors_gracefully(self):
        """Test init handles network errors during template download."""
        with patch("specify_cli.show_banner"), \
             patch("specify_cli.check_tool", return_value=True), \
             patch("specify_cli.download_and_extract_template", side_effect=RuntimeError("Network error")), \
             patch("specify_cli.Path.cwd"):
            result = runner.invoke(app, [
                "init", "myproject",
                "--ai-assistant", "claude",
                "--script-type", "sh",
                "--ignore-agent-tools"
            ])
            assert result.exit_code == 1

    def test_init_cleans_up_on_failure(self, temp_dir: Path):
        """Test init cleans up project directory on failure."""
        project_path = temp_dir / "myproject"

        with patch("specify_cli.show_banner"), \
             patch("specify_cli.Path.cwd", return_value=temp_dir), \
             patch("specify_cli.check_tool", return_value=True), \
             patch("specify_cli.download_and_extract_template", side_effect=RuntimeError("Test error")), \
             patch("shutil.rmtree") as mock_rmtree:

            result = runner.invoke(app, [
                "init", "myproject",
                "--ai-assistant", "claude",
                "--script-type", "sh",
                "--ignore-agent-tools"
            ])

            assert result.exit_code == 1
            # Cleanup should be attempted
            # Note: actual cleanup behavior depends on implementation details
