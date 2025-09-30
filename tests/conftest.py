"""Shared pytest fixtures and configuration."""

import shutil
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """Provide Typer CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture
def temp_project_dir():
    """Create temporary directory for test projects."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_git(mocker):
    """Mock git operations for testing."""
    mock = mocker.patch("subprocess.run")
    mock.return_value.returncode = 0
    mock.return_value.stdout = b"mock output"
    return mock


@pytest.fixture
def sample_templates():
    """Provide access to template files for testing."""
    return Path(__file__).parent.parent / "templates"
