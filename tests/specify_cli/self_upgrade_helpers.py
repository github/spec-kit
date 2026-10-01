"""Shared fixtures and helpers for `specify self upgrade` tests.

These helpers patch subprocess, PATH lookup, and release-tag resolution so
the focused test modules stay isolated from the real environment.
"""

import os
import subprocess

import pytest
from typer.testing import CliRunner

from specify_cli._version import (
    _InstallMethod,
    _UpgradePlan,
    _assemble_installer_argv,
    _detect_install_method,
    _verify_upgrade,
)
from tests.conftest import strip_ansi
from tests.http_helpers import mock_urlopen_response, route_opener_open_through_urlopen

__all__ = (
    "SENTINEL_GH_TOKEN",
    "SENTINEL_GITHUB_TOKEN",
    "_InstallMethod",
    "_UpgradePlan",
    "_assemble_installer_argv",
    "_completed_process",
    "_detect_install_method",
    "_verify_upgrade",
    "mock_urlopen_response",
    "requires_posix",
    "route_opener_open_through_urlopen",
    "runner",
    "strip_ansi",
)

runner = CliRunner()

# Some installer error-path tests create a relative `./uv` fixture, `chdir`
# into the tmp dir, and assert POSIX executable-bit semantics (chmod / X_OK).
# None of that maps cleanly onto Windows: `os.access(path, X_OK)` ignores the
# mode bits, and pytest cannot rmtree a tmp dir that is still the cwd, so the
# fixtures raise PermissionError during teardown. Skip these on Windows — the
# realistic absolute-path and bare-PATH-command branches stay covered there.
requires_posix = pytest.mark.skipif(
    os.name == "nt",
    reason="relative-path / executable-bit semantics are POSIX-only",
)

SENTINEL_GH_TOKEN = "SENTINEL-GH-TOKEN-VALUE"
SENTINEL_GITHUB_TOKEN = "SENTINEL-GITHUB-TOKEN-VALUE"


def _completed_process(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess:
    """Build a subprocess.CompletedProcess for installer / verification calls."""
    return subprocess.CompletedProcess(
        args=["mocked"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )
