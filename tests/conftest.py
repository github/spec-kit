"""
Pytest configuration and shared fixtures for Spec Kit tests.
"""
import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
import responses
from unittest.mock import Mock, patch


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_project_dir(temp_dir: Path) -> Path:
    """Create a mock project directory structure."""
    project = temp_dir / "test-project"
    project.mkdir(parents=True, exist_ok=True)
    return project


@pytest.fixture
def mock_release_data() -> dict:
    """Mock GitHub release data."""
    return {
        "tag_name": "v1.0.0",
        "name": "Release 1.0.0",
        "assets": [
            {
                "name": "spec-kit-template-claude-sh.zip",
                "browser_download_url": "https://github.com/github/spec-kit/releases/download/v1.0.0/spec-kit-template-claude-sh.zip",
                "size": 1024,
            },
            {
                "name": "spec-kit-template-copilot-sh.zip",
                "browser_download_url": "https://github.com/github/spec-kit/releases/download/v1.0.0/spec-kit-template-copilot-sh.zip",
                "size": 1024,
            },
            {
                "name": "spec-kit-template-claude-ps.zip",
                "browser_download_url": "https://github.com/github/spec-kit/releases/download/v1.0.0/spec-kit-template-claude-ps.zip",
                "size": 1024,
            },
        ],
    }


@pytest.fixture
def mock_github_api(mock_release_data: dict):
    """Mock GitHub API responses."""
    with responses.RequestsMock() as rsps:
        # Mock releases API endpoint
        rsps.add(
            responses.GET,
            "https://api.github.com/repos/github/spec-kit/releases/latest",
            json=mock_release_data,
            status=200,
        )
        yield rsps


@pytest.fixture
def mock_template_zip(temp_dir: Path) -> Path:
    """Create a mock template zip file."""
    import zipfile

    # Create template structure
    template_dir = temp_dir / "template"
    template_dir.mkdir()

    # Create sample files
    (template_dir / "README.md").write_text("# Test Template")
    (template_dir / ".claude").mkdir()
    (template_dir / ".claude" / "commands").mkdir()
    (template_dir / ".claude" / "commands" / "test.md").write_text("Test command")

    # Create scripts directory
    (template_dir / "scripts").mkdir()
    (template_dir / "scripts" / "bash").mkdir()
    (template_dir / "scripts" / "bash" / "test.sh").write_text("#!/bin/bash\necho 'test'")

    # Create .vscode directory with settings
    (template_dir / ".vscode").mkdir()
    settings = {"editor.formatOnSave": True}
    (template_dir / ".vscode" / "settings.json").write_text(json.dumps(settings, indent=2))

    # Create zip file
    zip_path = temp_dir / "template.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file in template_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(template_dir)
                zf.write(file, arcname)

    return zip_path


@pytest.fixture
def mock_agent_config() -> dict:
    """Mock agent configuration."""
    return {
        "claude": {
            "name": "Claude Code",
            "folder": ".claude/",
            "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
            "requires_cli": True,
        },
        "copilot": {
            "name": "GitHub Copilot",
            "folder": ".github/",
            "install_url": None,
            "requires_cli": False,
        },
    }


@pytest.fixture
def mock_guidelines_structure(temp_dir: Path) -> Path:
    """Create mock guidelines directory structure."""
    guidelines_dir = temp_dir / ".guidelines"
    guidelines_dir.mkdir()

    # Create branch-config.json
    branch_config = {
        "version": "1.0",
        "branchNaming": {
            "enabled": True,
            "pattern": "{username}/{repo-name}",
            "components": {
                "username": {"type": "session", "value": "username"},
                "repo-name": {"type": "session", "value": "repository_name"},
            }
        }
    }
    (guidelines_dir / "branch-config.json").write_text(json.dumps(branch_config, indent=2))

    # Create stack-mapping.json
    stack_mapping = {
        "version": "1.0",
        "stacks": [
            {
                "name": "react",
                "paths": ["src/", "components/"],
                "guidelines": "reactjs-guidelines.md"
            }
        ]
    }
    (guidelines_dir / "stack-mapping.json").write_text(json.dumps(stack_mapping, indent=2))

    # Create sample guideline file
    (guidelines_dir / "reactjs-guidelines.md").write_text("# React Guidelines\n\nUse functional components.")

    return guidelines_dir


@pytest.fixture
def mock_console():
    """Mock Rich console for testing output."""
    with patch("specify_cli.console") as mock:
        yield mock


@pytest.fixture
def mock_httpx_client(mock_template_zip: Path):
    """Mock httpx.Client for HTTP requests."""
    mock_client = Mock()

    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = mock_template_zip.read_bytes()

    mock_client.get.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_git_commands():
    """Mock git subprocess commands."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        yield mock_run


@pytest.fixture
def sample_constitution_content() -> str:
    """Sample constitution.md content for testing."""
    return """# Project Constitution

## Purpose
This is a test project.

## Principles
1. Write clean code
2. Test everything
3. Document well
"""


@pytest.fixture
def sample_spec_content() -> str:
    """Sample spec.md content for testing."""
    return """# Feature Specification

## Overview
Test feature implementation

## User Stories
- As a user, I want to test features
- As a developer, I want automated tests

## Acceptance Criteria
- [ ] Tests pass
- [ ] Code is documented
"""


# Marker for slow tests
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
