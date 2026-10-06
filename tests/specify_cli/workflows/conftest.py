"""Shared fixtures for workflow command tests."""

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
    """Create a mock Spec Kit project with workflow storage."""
    workflows_dir = temp_dir / ".specify" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


@pytest.fixture
def sample_workflow_yaml():
    """Return a valid minimal workflow YAML string."""
    return """
schema_version: "1.0"
workflow:
  id: "test-workflow"
  name: "Test Workflow"
  version: "1.0.0"
  description: "A test workflow"

inputs:
  spec:
    type: string
    required: true
  scope:
    type: string
    default: "full"

steps:
  - id: step-one
    command: speckit.specify
    input:
      args: "{{ inputs.spec }}"

  - id: step-two
    command: speckit.plan
    input:
      args: "{{ steps.step-one.output.command }}"
"""
