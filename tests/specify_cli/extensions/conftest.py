"""Shared fixtures for the mirrored extension command tests."""
from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
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


@pytest.fixture(
    params=[
        ({"name": "Example", "description": "No version"}, "Example (vunknown)"),
        ({"version": "1.2.3", "description": "No name"}, "example (v1.2.3)"),
        ({"name": "Example", "version": "1.2.3"}, "Example (v1.2.3)"),
        ({"name": "Example", "version": "[/red]", "description": "Markup"}, "Example (v[/red])"),
    ],
    ids=["no-version", "no-name", "no-description", "markup"],
)
def incomplete_catalog_entry(request, tmp_path, monkeypatch):
    """Serve an incomplete entry and a healthy sibling from the real cache.

    Returns the header expected for the incomplete entry.
    """
    from specify_cli.extensions import ExtensionCatalog

    entry, header = request.param

    # tmp_path, not temp_dir: monkeypatch restores the cwd only after
    # temp_dir's rmtree, which Windows refuses while the cwd is inside it.
    project_dir = tmp_path / "project"
    (project_dir / ".specify").mkdir(parents=True)
    monkeypatch.chdir(project_dir)
    monkeypatch.setenv("SPECKIT_CATALOG_URL", ExtensionCatalog.DEFAULT_CATALOG_URL)
    catalog = ExtensionCatalog(project_dir)
    catalog.cache_dir.mkdir(parents=True)
    catalog.cache_file.write_text(json.dumps({
        "schema_version": "1.0",
        "extensions": {
            "example": entry,
            "healthy": {"name": "Healthy", "description": "Complete entry", "version": "2.0.0"},
        },
    }), encoding="utf-8")
    catalog.cache_metadata_file.write_text(json.dumps({
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "catalog_url": ExtensionCatalog.DEFAULT_CATALOG_URL,
    }), encoding="utf-8")

    def no_network(*args, **kwargs):
        pytest.fail("The fresh catalog cache must be used")

    monkeypatch.setattr(ExtensionCatalog, "_open_url", no_network)
    return header
