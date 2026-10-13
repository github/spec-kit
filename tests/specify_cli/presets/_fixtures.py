"""Shared pytest fixtures for preset domain and command suites."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def valid_pack_data():
    """Return valid preset manifest data."""
    return {
        "schema_version": "1.0",
        "preset": {
            "id": "test-pack",
            "name": "Test Preset",
            "version": "1.0.0",
            "description": "A test preset",
            "author": "Test Author",
            "repository": "https://github.com/test/test-pack",
            "license": "MIT",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [
                {
                    "type": "template",
                    "name": "spec-template",
                    "file": "templates/spec-template.md",
                    "description": "Custom spec template",
                    "replaces": "spec-template",
                }
            ]
        },
        "tags": ["testing", "example"],
    }


@pytest.fixture
def pack_dir(temp_dir, valid_pack_data):
    """Create a complete preset directory structure."""
    preset_dir = temp_dir / "test-pack"
    preset_dir.mkdir()
    (preset_dir / "preset.yml").write_text(
        yaml.safe_dump(valid_pack_data), encoding="utf-8"
    )
    templates_dir = preset_dir / "templates"
    templates_dir.mkdir()
    (templates_dir / "spec-template.md").write_text(
        "# Custom Spec Template\n\nThis is a custom template.\n",
        encoding="utf-8",
    )
    return preset_dir


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project directory."""
    project = temp_dir / "project"
    project.mkdir()
    templates_dir = project / ".specify" / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "spec-template.md").write_text(
        "# Core Spec Template\n", encoding="utf-8"
    )
    (templates_dir / "plan-template.md").write_text(
        "# Core Plan Template\n", encoding="utf-8"
    )
    (templates_dir / "commands").mkdir()
    return project
