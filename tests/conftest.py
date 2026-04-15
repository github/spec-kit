"""Shared test helpers for the Spec Kit test suite."""

import os
import re
import shutil
import subprocess
import sys

import pytest

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _has_working_bash() -> bool:
    """Check whether a functional native bash is available.

    On Windows, only Git-for-Windows bash (MSYS2/MINGW) is accepted.
    The WSL launcher (System32\\bash.exe) is rejected because it runs in
    a separate Linux filesystem and cannot handle native Windows paths
    used by the test fixtures.

    Set SPECKIT_TEST_BASH=1 to force-enable bash tests regardless.
    """
    if os.environ.get("SPECKIT_TEST_BASH") == "1":
        return True
    bash_path = shutil.which("bash")
    if bash_path is None:
        return False
    # On Windows, reject the WSL launcher early (avoids WSL init prompts
    # and the 5 s timeout) and only accept MSYS/MINGW/CYGWIN bash.
    if sys.platform == "win32":
        if "system32" in bash_path.lower():
            return False
        try:
            u = subprocess.run(
                [bash_path, "-c", "uname -s"],
                capture_output=True, text=True, timeout=5,
            )
            kernel = u.stdout.strip().upper()
            if not any(k in kernel for k in ("MSYS", "MINGW", "CYGWIN")):
                return False
        except (OSError, subprocess.TimeoutExpired):
            return False
    try:
        r = subprocess.run(
            [bash_path, "-c", "echo ok"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or "ok" not in r.stdout:
            return False
    except (OSError, subprocess.TimeoutExpired):
        return False
    return True


requires_bash = pytest.mark.skipif(
    not _has_working_bash(), reason="working bash not available"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from Rich-formatted CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)
