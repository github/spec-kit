import shutil
from pathlib import Path
from unittest.mock import patch
from specify_cli._helpers import check_tool, run_command

def test_check_tool_git_found():
    if shutil.which("git"):
        assert check_tool("git") is True

def test_check_tool_nonexistent_returns_false():
    assert check_tool("__nonexistent_tool_xyz__") is False

def test_run_command_capture():
    result = run_command(["echo", "hello"], capture=True)
    assert result == "hello"

def test_run_command_no_capture_returns_none():
    result = run_command(["true"])
    assert result is None
