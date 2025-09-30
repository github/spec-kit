"""Tests for git operations."""

import subprocess
from pathlib import Path

from specify_cli import init_git_repo, is_git_repo


class TestIsGitRepo:
    """Test suite for is_git_repo function."""

    def test_is_git_repo_true(self, mocker, tmp_path):
        """Test is_git_repo returns True for git repository."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "rev-parse", "--is-inside-work-tree"],
            returncode=0,
            stdout=b"true\n",
        )

        # Act
        result = is_git_repo(tmp_path)

        # Assert
        assert result is True
        mock_run.assert_called_once()

    def test_is_git_repo_false(self, mocker, tmp_path):
        """Test is_git_repo returns False for non-git directory."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git"])

        # Act
        result = is_git_repo(tmp_path)

        # Assert
        assert result is False

    def test_is_git_repo_false_when_not_directory(self, tmp_path):
        """Test is_git_repo returns False when path is not a directory."""
        # Arrange
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        # Act
        result = is_git_repo(file_path)

        # Assert
        assert result is False

    def test_is_git_repo_uses_cwd_when_no_path(self, mocker, tmp_path):
        """Test is_git_repo uses current directory when path not provided."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "rev-parse", "--is-inside-work-tree"],
            returncode=0,
            stdout=b"true\n",
        )
        mock_cwd = mocker.patch("pathlib.Path.cwd")
        mock_cwd.return_value = tmp_path

        # Act
        result = is_git_repo()

        # Assert
        assert result is True
        mock_cwd.assert_called_once()


class TestInitGitRepo:
    """Test suite for init_git_repo function."""

    def test_init_git_repo_success(self, mocker, tmp_path):
        """Test successful git repository initialization."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "init"], returncode=0, stdout=b"Initialized"
        )
        mock_chdir = mocker.patch("os.chdir")

        # Act
        result = init_git_repo(tmp_path, quiet=True)

        # Assert
        assert result is True
        # init_git_repo calls git init, git add ., and git commit
        assert mock_run.call_count == 3
        # Verify chdir was called to change to project directory and back
        assert mock_chdir.call_count == 2

    def test_init_git_repo_failure(self, mocker, tmp_path):
        """Test failed git repository initialization."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "init"])
        mock_chdir = mocker.patch("os.chdir")

        # Act
        result = init_git_repo(tmp_path, quiet=True)

        # Assert
        assert result is False
        # Still changes back to original directory even on failure
        assert mock_chdir.call_count == 2

    def test_init_git_repo_quiet_mode(self, mocker, tmp_path):
        """Test git init in quiet mode doesn't print output."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "init"], returncode=0, stdout=b""
        )
        mock_chdir = mocker.patch("os.chdir")
        mock_console = mocker.patch("specify_cli.console")

        # Act
        result = init_git_repo(tmp_path, quiet=True)

        # Assert
        assert result is True
        # Console should not be used in quiet mode
        mock_console.print.assert_not_called()

    def test_init_git_repo_restores_cwd_on_exception(self, mocker, tmp_path):
        """Test that current directory is restored even on exception."""
        # Arrange
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = Exception("Unexpected error")
        mock_chdir = mocker.patch("os.chdir")
        original_cwd = Path.cwd()

        # Act & Assert
        try:
            init_git_repo(tmp_path, quiet=True)
        except Exception:
            pass

        # Verify chdir was called to restore original directory
        # First call changes to project dir, second restores
        assert mock_chdir.call_count == 2
        # Last call should restore to original directory
        assert mock_chdir.call_args_list[-1][0][0] == original_cwd
