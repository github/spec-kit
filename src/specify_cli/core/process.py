"""
specify_cli.core.process - Process execution utilities

Helpers for running subprocesses with logging and error handling.
"""

import subprocess
import sys
from typing import Optional
from pathlib import Path

from .shell import colour

__all__ = [
    "run_command",
    "run_logged",
]


def run_command(
    cmd: list[str],
    check_return: bool = True,
    capture: bool = False,
    shell: bool = False,
    cwd: Optional[Path] = None,
) -> Optional[str]:
    """
    Execute a command and optionally capture output.

    Args:
        cmd: Command as list of strings
        check_return: Raise CalledProcessError if exit code != 0
        capture: If True, return stdout; if False, stream to console
        shell: If True, execute as shell command string
        cwd: Working directory for command execution

    Returns:
        Captured output (str) if capture=True, else None

    Raises:
        subprocess.CalledProcessError: If check_return=True and command fails
    """
    try:
        if shell:
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            result = subprocess.run(
                cmd_str,
                shell=True,
                check=check_return,
                capture_output=capture,
                text=True,
                cwd=cwd,
            )
        else:
            result = subprocess.run(
                cmd,
                check=check_return,
                capture_output=capture,
                text=True,
                cwd=cwd,
            )

        if capture:
            return result.stdout.strip() if result.stdout else ""
        return None

    except subprocess.CalledProcessError as e:
        colour(f"Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}", "red")
        if e.stderr:
            colour(f"Error: {e.stderr}", "red")
        raise


def run_logged(
    cmd: list[str],
    label: str = "",
    capture: bool = False,
    check: bool = True,
    cwd: Optional[Path] = None,
) -> Optional[str]:
    """
    Execute a command with optional logging prefix.

    Args:
        cmd: Command as list of strings
        label: Optional label to print before running command
        capture: If True, return stdout
        check: If True, raise on non-zero exit
        cwd: Working directory

    Returns:
        Captured output if capture=True, else None
    """
    if label:
        colour(f"→ {label}", "cyan")

    return run_command(cmd, check_return=check, capture=capture, cwd=cwd)
