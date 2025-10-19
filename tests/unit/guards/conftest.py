import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_registry_file(temp_project_dir):
    """Create a mock .guards/registry.json file."""
    guards_dir = temp_project_dir / ".guards"
    guards_dir.mkdir()
    registry_file = guards_dir / "registry.json"
    registry_file.write_text('{"guards": [], "next_id": 1}')
    return registry_file


@pytest.fixture
def sample_guard_type_manifest():
    """Return a sample guard type manifest dictionary."""
    return {
        "name": "unit-pytest",
        "version": "1.0.0",
        "description": "Unit testing with pytest",
        "category": "unit",
        "scaffolder": "scaffolder.py",
        "scaffolder_class": "UnitPytestScaffolder",
        "templates_dir": "templates",
        "file_patterns": ["test_*.py", "conftest.py"],
        "runtime_dependencies": ["pytest"],
        "ai_guidance": "Use for Python unit tests with pytest framework."
    }
