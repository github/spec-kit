import subprocess
from pathlib import Path
from unittest.mock import patch
from specify_cli._git import GitService

def test_is_repo_true_in_real_git_repo(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    svc = GitService()
    assert svc.is_repo(tmp_path) is True

def test_is_repo_false_in_plain_dir(tmp_path):
    svc = GitService()
    assert svc.is_repo(tmp_path) is False

def test_init_repo_success(tmp_path):
    svc = GitService()
    ok, err = svc.init_repo(tmp_path)
    assert ok is True
    assert err is None
    assert (tmp_path / ".git").is_dir()

def test_init_repo_returns_error_on_failure():
    svc = GitService()
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["git"])):
        ok, err = svc.init_repo(Path("/nonexistent"))
    assert ok is False
    assert err is not None

def test_init_repo_does_not_print(tmp_path, capsys):
    svc = GitService()
    svc.init_repo(tmp_path)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

def test_backward_compat_is_git_repo(tmp_path):
    from specify_cli import is_git_repo
    assert is_git_repo(tmp_path) is False

def test_backward_compat_init_git_repo(tmp_path):
    from specify_cli import init_git_repo
    ok, err = init_git_repo(tmp_path, quiet=True)
    assert ok is True
