"""Shared fixtures for the mirrored extension command tests."""
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
def valid_manifest_data():
    """Return valid extension manifest data."""
    return {
        "schema_version": "1.0",
        "extension": {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "description": "A test extension",
            "author": "Test Author",
            "repository": "https://github.com/test/test-ext",
            "license": "MIT",
        },
        "requires": {
            "speckit_version": ">=0.1.0",
            "commands": ["speckit.tasks"],
        },
        "provides": {
            "commands": [
                {
                    "name": "speckit.test-ext.hello",
                    "file": "commands/hello.md",
                    "description": "Test command",
                }
            ]
        },
        "hooks": {
            "after_tasks": {
                "command": "speckit.test-ext.hello",
                "optional": True,
                "prompt": "Run test?",
            }
        },
        "tags": ["testing", "example"],
    }


@pytest.fixture
def extension_dir(temp_dir, valid_manifest_data):
    """Create a complete extension directory structure."""
    ext_dir = temp_dir / "test-ext"
    ext_dir.mkdir()

    with open(ext_dir / "extension.yml", "w") as manifest_file:
        yaml.dump(valid_manifest_data, manifest_file)

    commands_dir = ext_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "hello.md").write_text(
        """---
description: "Test hello command"
---

# Test Hello Command

$ARGUMENTS
"""
    )

    return ext_dir


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project directory."""
    project = temp_dir / "project"
    project.mkdir()
    (project / ".specify").mkdir()
    return project
