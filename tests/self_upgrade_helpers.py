"""Shared fixtures and helpers for `specify self upgrade` tests.

These helpers patch subprocess, PATH lookup, and release-tag resolution so
the focused test modules stay isolated from the real environment.
"""

import errno
import importlib.metadata
import json
import os
import subprocess
import urllib.error
from unittest.mock import patch

from typer.testing import CliRunner

import specify_cli
from specify_cli import app
from specify_cli._version import (
    _InstallMethod,
    _UpgradePlan,
    _assemble_installer_argv,
    _detect_install_method,
    _verify_upgrade,
)
from tests.conftest import strip_ansi
from tests.http_helpers import mock_urlopen_response

__all__ = (
    "SENTINEL_GH_TOKEN",
    "SENTINEL_GITHUB_TOKEN",
    "_InstallMethod",
    "_UpgradePlan",
    "_assemble_installer_argv",
    "_completed_process",
    "_detect_install_method",
    "_verify_upgrade",
    "app",
    "errno",
    "importlib",
    "json",
    "mock_urlopen_response",
    "os",
    "patch",
    "runner",
    "specify_cli",
    "strip_ansi",
    "subprocess",
    "urllib",
)

runner = CliRunner()

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
