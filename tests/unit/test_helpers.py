"""Tests for helper functions."""

import os
import subprocess

from specify_cli import (
    _github_auth_headers,
    _github_token,
    run_command,
)


class TestGithubTokenHelpers:
    """Test suite for GitHub token helper functions."""

    def test_github_token_from_cli_arg(self):
        """Test that CLI token takes precedence."""
        # Act
        result = _github_token("cli_token")

        # Assert
        assert result == "cli_token"

    def test_github_token_from_gh_token_env(self, mocker):
        """Test token from GH_TOKEN environment variable."""
        # Arrange
        mocker.patch.dict(os.environ, {"GH_TOKEN": "env_token"})

        # Act
        result = _github_token()

        # Assert
        assert result == "env_token"

    def test_github_token_from_github_token_env(self, mocker):
        """Test token from GITHUB_TOKEN environment variable."""
        # Arrange
        mocker.patch.dict(os.environ, {"GITHUB_TOKEN": "github_env_token"}, clear=True)

        # Act
        result = _github_token()

        # Assert
        assert result == "github_env_token"

    def test_github_token_cli_overrides_env(self, mocker):
        """Test that CLI token overrides environment variables."""
        # Arrange
        mocker.patch.dict(os.environ, {"GH_TOKEN": "env_token"})

        # Act
        result = _github_token("cli_token")

        # Assert
        assert result == "cli_token"

    def test_github_token_returns_none_when_empty(self):
        """Test that empty/whitespace tokens return None."""
        # Assert
        assert _github_token("") is None
        assert _github_token("   ") is None
        assert _github_token("\n") is None

    def test_github_token_strips_whitespace(self):
        """Test that tokens are stripped of whitespace."""
        # Act
        result = _github_token("  token_with_spaces  ")

        # Assert
        assert result == "token_with_spaces"

    def test_github_auth_headers_with_token(self):
        """Test auth headers with valid token."""
        # Act
        headers = _github_auth_headers("test_token_123")

        # Assert
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token_123"

    def test_github_auth_headers_without_token(self):
        """Test auth headers without token returns empty dict."""
        # Act
        headers = _github_auth_headers(None)

        # Assert
        assert headers == {}

    def test_github_auth_headers_with_empty_token(self):
        """Test auth headers with empty token returns empty dict."""
        # Act
        headers = _github_auth_headers("")

        # Assert
        assert headers == {}


class TestRunCommand:
    """Test suite for run_command function."""

    def test_run_command_success(self, mocker):
        """Test successful command execution."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "test"], returncode=0, stdout=""
        )

        # Act
        result = run_command(["echo", "test"], check_return=False)

        # Assert
        assert result is None
        mock_run.assert_called_once()

    def test_run_command_with_capture(self, mocker):
        """Test command execution with output capture."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "test"], returncode=0, stdout="test output\n"
        )

        # Act
        result = run_command(["echo", "test"], capture=True, check_return=False)

        # Assert
        assert result == "test output"
        mock_run.assert_called_once()

    def test_run_command_failure_without_check(self, mocker):
        """Test command failure with check_return=False."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["false"], returncode=1, stdout=""
        )

        # Act
        result = run_command(["false"], check_return=False)

        # Assert
        assert result is None
        mock_run.assert_called_once()

    def test_run_command_with_shell(self, mocker):
        """Test command execution with shell=True."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args="echo test", returncode=0, stdout=""
        )

        # Act
        run_command(["echo test"], shell=True, check_return=False)

        # Assert
        call_args = mock_run.call_args
        assert call_args.kwargs.get("shell") is True
