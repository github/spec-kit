"""Subprocess + tool-detection helpers shared by the rest of the CLI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .console import console
from .tracker import StepTracker

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

# `claude migrate-installer` removes the original binary from PATH and writes
# an alias at this location; the regular `shutil.which("claude")` check would
# miss it. We special-case this in :func:`check_tool`. See:
# https://github.com/neelneelpurk/infrakit/issues/123
CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"


def run_command(
    cmd: list[str],
    check_return: bool = True,
    capture: bool = False,
    shell: bool = False,
) -> Optional[str]:
    """Run a shell command and optionally return its stdout."""
    try:
        if capture:
            result = subprocess.run(
                cmd, check=check_return, capture_output=True, text=True, shell=shell
            )
            return result.stdout.strip()
        subprocess.run(cmd, check=check_return, shell=shell)
        return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, "stderr") and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None


def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """Return ``True`` if ``tool`` is on ``PATH`` (or the Claude alias exists).

    When a tracker is supplied, the result is recorded against the same key
    as ``tool`` so the live UI updates as the check progresses.
    """
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")
            return True

    found = shutil.which(tool) is not None

    if tracker:
        if found:
            tracker.complete(tool, "available")
        else:
            tracker.error(tool, "not found")

    return found


def find_project_root(start: Path = None) -> Optional[Path]:
    """Walk up from ``start`` (default: cwd) until a directory contains
    ``.infrakit/config.yaml``. Returns ``None`` if no such ancestor exists.
    """
    current = (start or Path.cwd()).resolve()
    while True:
        if (current / ".infrakit" / "config.yaml").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent
