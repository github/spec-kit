import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
from specify_cli.backend.system import check_tool, run_command, ensure_executable_scripts

def test_check_tool_exists():
    """Test check_tool returns True for existing tool."""
    with patch("shutil.which", return_value="/usr/bin/git"):
        assert check_tool("git") is True

def test_check_tool_missing():
    """Test check_tool returns False for missing tool."""
    with patch("shutil.which", return_value=None):
        assert check_tool("nonexistent_tool") is False

def test_run_command_success():
    """Test run_command executes successfully."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        run_command(["ls", "-la"], check_return=True)
        mock_run.assert_called_once()

def test_ensure_executable_scripts(tmp_path):
    """Test ensure_executable_scripts adds execute permissions."""
    # Create a dummy script
    scripts_dir = tmp_path / ".specify" / "scripts"
    scripts_dir.mkdir(parents=True)
    script_file = scripts_dir / "test.sh"
    with open(script_file, "wb") as f:
        f.write(b"#!/bin/sh\necho hello")

    # Remove execute permissions
    script_file.chmod(0o644)

    ensure_executable_scripts(tmp_path)

    # Check if execute bit is set (0o100 is user execute)
    st = script_file.stat()
    assert st.st_mode & 0o100
