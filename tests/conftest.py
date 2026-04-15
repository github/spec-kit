"""Shared test helpers for the Spec Kit test suite."""

import re
import shutil
import subprocess

import pytest

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _has_working_bash() -> bool:
    """Check whether a functional bash is available (not just a WSL stub)."""
    if shutil.which("bash") is None:
        return False
    try:
        r = subprocess.run(
            ["bash", "-c", "echo ok"],
            capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0 and "ok" in r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return False


requires_bash = pytest.mark.skipif(
    not _has_working_bash(), reason="working bash not available"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from Rich-formatted CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)
