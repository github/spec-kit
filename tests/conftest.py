"""Pytest configuration and fixtures."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

# Import module directly to avoid dependency issues
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        temp_path = Path(temp_dir)
        os.chdir(temp_path)
        yield temp_path
        os.chdir(original_cwd)


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_console():
    """Create a mock console for testing."""
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def mock_check_tool():
    """Mock check_tool function."""
    with patch('specify_cli.check_tool') as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_download_template():
    """Mock download_and_extract_template function."""
    with patch('specify_cli.download_and_extract_template') as mock:
        mock.return_value = Path(tempfile.mkdtemp())
        yield mock