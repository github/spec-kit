"""Shared test helpers for the Spec Kit test suite."""

import re
import sys

import pytest

_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

requires_bash = pytest.mark.skipif(
    sys.platform == "win32", reason="bash not available on Windows"
)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from Rich-formatted CLI output."""
    return _ANSI_ESCAPE_RE.sub("", text)
