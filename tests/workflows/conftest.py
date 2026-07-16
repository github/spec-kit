"""Shared fixtures for workflow tests."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=(sys.platform == "win32"))


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project with ``.specify/workflows/`` directory."""
    workflows_dir = temp_dir / ".specify" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir
