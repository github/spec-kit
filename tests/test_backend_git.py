from unittest.mock import patch, MagicMock
from pathlib import Path
from specify_cli.backend.git import is_git_repo, init_git_repo
import subprocess

def test_is_git_repo_true():
    """Test is_git_repo returns True when inside a git repo."""
    with patch("subprocess.run") as mock_run:
        with patch("pathlib.Path.is_dir", return_value=True):
            mock_run.return_value.returncode = 0
            assert is_git_repo(Path("/some/path")) is True

def test_is_git_repo_false():
    """Test is_git_repo returns False when not inside a git repo."""
    with patch("subprocess.run") as mock_run:
        with patch("pathlib.Path.is_dir", return_value=True):
            # Mock subprocess.run to raise CalledProcessError which is one of the caught exceptions
            mock_run.side_effect = subprocess.CalledProcessError(1, ["git", "rev-parse"])
            assert is_git_repo(Path("/some/path")) is False

def test_init_git_repo_success():
    """Test init_git_repo calls correct git commands."""
    with patch("subprocess.run") as mock_run:
        with patch("os.chdir") as mock_chdir:
            with patch("pathlib.Path.cwd", return_value=Path("/original")):
                mock_run.return_value.returncode = 0
                success, error = init_git_repo(Path("/some/path"), quiet=True)
                assert success is True
                assert error is None
                assert mock_run.call_count >= 3  # init, add, commit
