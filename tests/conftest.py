"""
Pytest configuration and fixtures for Spectrena tests.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from git import Repo


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory that's cleaned up after test."""
    yield tmp_path
    # Cleanup happens automatically with tmp_path


@pytest.fixture
def git_repo(temp_dir):
    """Create a temporary git repository."""
    repo = Repo.init(temp_dir)

    # Configure git user for commits
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    (temp_dir / "README.md").write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return repo


@pytest.fixture
def spectrena_project(temp_dir, git_repo):
    """Create a Spectrena project structure."""
    # Create .spectrena directory
    config_dir = temp_dir / ".spectrena"
    config_dir.mkdir(exist_ok=True)

    # Create templates directory
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Create specs directory
    specs_dir = temp_dir / "specs"
    specs_dir.mkdir(exist_ok=True)

    # Create minimal config
    config_file = config_dir / "config.yml"
    config_file.write_text("""spec_id:
  template: "{NNN}-{slug}"
  padding: 3
  numbering_source: "directory"
""")

    return temp_dir


@pytest.fixture
def sample_spec(spectrena_project):
    """Create a sample spec for testing."""
    specs_dir = spectrena_project / "specs"
    spec_dir = specs_dir / "001-sample-feature"
    spec_dir.mkdir()

    spec_file = spec_dir / "spec.md"
    spec_file.write_text("""# Specification: Sample Feature

**Spec ID**: 001-sample-feature
**Component**: CORE
**Weight**: STANDARD
**Status**: DRAFT

## Problem Statement

Sample problem statement.

## Solution Overview

Sample solution.
""")

    return spec_dir


@pytest.fixture
def sample_plan(sample_spec):
    """Create a sample plan.md with tech stack."""
    plan_file = sample_spec / "plan.md"
    plan_file.write_text("""# Technical Plan

## Tech Stack

### Languages
- Python 3.11+
- TypeScript

### Frameworks
- FastAPI
- React

### Databases
- PostgreSQL
- Redis

### Tools
- Docker
- pytest

## Architecture

Sample architecture description.
""")

    return plan_file


class CliRunner:
    """Helper for running CLI commands in tests."""

    def __init__(self, cwd: Path):
        self.cwd = cwd

    def run(self, *args, check=True, **kwargs):
        """Run a command with subprocess."""
        import subprocess

        result = subprocess.run(
            args,
            cwd=self.cwd,
            capture_output=True,
            text=True,
            check=False,
            **kwargs
        )

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                args,
                result.stdout,
                result.stderr
            )

        return result


@pytest.fixture
def cli_runner(spectrena_project):
    """Provide a CLI runner for testing commands."""
    return CliRunner(spectrena_project)
