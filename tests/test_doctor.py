"""
Unit tests for the specify doctor command.

Tests cover:
- Healthy project detection (all checks pass)
- Missing project directories (.specify/, specs/, scripts/, templates/, memory/)
- Missing constitution.md
- AI agent folder detection and empty commands directory
- Feature specification completeness (spec.md, plan.md, tasks.md)
- Script existence validation (bash and powershell)
- Extension config validation (extensions.yml, registry.json)
- Git repository detection
- Exit code 1 on errors, 0 on clean
"""

import json
import os
import tempfile
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app, AGENT_CONFIG


runner = CliRunner()


# ===== Fixtures =====

@pytest.fixture
def temp_project():
    """Create a temporary directory simulating a spec-kit project."""
    tmpdir = tempfile.mkdtemp()
    project = Path(tmpdir)
    yield project
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def healthy_project(temp_project):
    """Create a fully healthy spec-kit project structure."""
    # Core directories
    (temp_project / ".specify").mkdir()
    (temp_project / "specs").mkdir()
    (temp_project / "scripts" / "bash").mkdir(parents=True)
    (temp_project / "scripts" / "powershell").mkdir(parents=True)
    (temp_project / "templates").mkdir()
    (temp_project / "memory").mkdir()

    # Constitution
    (temp_project / "memory" / "constitution.md").write_text("# Constitution\n")

    # Scripts
    expected_scripts = ["common", "check-prerequisites", "create-new-feature", "setup-plan", "update-agent-context"]
    for name in expected_scripts:
        (temp_project / "scripts" / "bash" / f"{name}.sh").write_text("#!/bin/bash\n")
        (temp_project / "scripts" / "powershell" / f"{name}.ps1").write_text("# PowerShell\n")

    return temp_project


# ===== Project Structure Tests =====

class TestDoctorProjectStructure:
    """Tests for project directory checks."""

    def test_healthy_project_no_errors(self, healthy_project):
        """A fully set up project should report no errors."""
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "error" not in result.output.lower() or "0 error" in result.output.lower()

    def test_missing_specify_dir(self, temp_project):
        """Missing .specify/ should be reported as an error."""
        os.chdir(temp_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1
        assert "specify" in result.output.lower()

    def test_missing_scripts_dir(self, healthy_project):
        """Missing scripts/ should be reported as an error."""
        shutil.rmtree(healthy_project / "scripts")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "scripts" in result.output.lower()

    def test_missing_templates_dir(self, healthy_project):
        """Missing templates/ should be reported as an error."""
        shutil.rmtree(healthy_project / "templates")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "templates" in result.output.lower()

    def test_missing_memory_dir(self, healthy_project):
        """Missing memory/ should be reported as an error."""
        shutil.rmtree(healthy_project / "memory")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1

    def test_missing_constitution(self, healthy_project):
        """Missing constitution.md should be reported as a warning."""
        (healthy_project / "memory" / "constitution.md").unlink()
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "constitution" in result.output.lower()


# ===== AI Agent Tests =====

class TestDoctorAgentDetection:
    """Tests for AI agent folder detection."""

    def test_no_agent_detected(self, healthy_project):
        """No agent folder should produce an info note."""
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "No AI agent" in result.output or "no ai agent" in result.output.lower()

    def test_agent_with_commands(self, healthy_project):
        """Agent folder with commands should report as healthy."""
        commands_dir = healthy_project / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "test.md").write_text("# Test command\n")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "Claude Code" in result.output

    def test_agent_folder_empty_commands(self, healthy_project):
        """Agent folder without commands should report a warning."""
        (healthy_project / ".claude" / "commands").mkdir(parents=True)
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "warning" in result.output.lower() or "empty" in result.output.lower()


# ===== Feature Specs Tests =====

class TestDoctorFeatureSpecs:
    """Tests for feature specification checks."""

    def test_no_specs_dir(self, healthy_project):
        """No specs/ directory should skip feature checks gracefully."""
        shutil.rmtree(healthy_project / "specs")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "not created yet" in result.output.lower() or "specs" in result.output.lower()

    def test_feature_with_all_artifacts(self, healthy_project):
        """Feature with spec, plan, and tasks should be fully green."""
        feature_dir = healthy_project / "specs" / "001-login"
        feature_dir.mkdir(parents=True)
        (feature_dir / "spec.md").write_text("# Spec\n")
        (feature_dir / "plan.md").write_text("# Plan\n")
        (feature_dir / "tasks.md").write_text("# Tasks\n")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "001-login" in result.output
        assert "spec, plan, tasks all present" in result.output

    def test_feature_missing_tasks(self, healthy_project):
        """Feature missing tasks.md should report an info note."""
        feature_dir = healthy_project / "specs" / "002-signup"
        feature_dir.mkdir(parents=True)
        (feature_dir / "spec.md").write_text("# Spec\n")
        (feature_dir / "plan.md").write_text("# Plan\n")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "002-signup" in result.output
        assert "tasks" in result.output.lower()

    def test_feature_missing_spec(self, healthy_project):
        """Feature missing spec.md should report an error."""
        feature_dir = healthy_project / "specs" / "003-broken"
        feature_dir.mkdir(parents=True)
        (feature_dir / "plan.md").write_text("# Plan\n")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1


# ===== Scripts Tests =====

class TestDoctorScripts:
    """Tests for script health checks."""

    def test_all_scripts_present(self, healthy_project):
        """All scripts present should report ok."""
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0

    def test_missing_bash_script(self, healthy_project):
        """Missing a bash script should report an error."""
        (healthy_project / "scripts" / "bash" / "common.sh").unlink()
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1
        assert "common.sh" in result.output

    def test_missing_powershell_script(self, healthy_project):
        """Missing a PowerShell script should report an error."""
        (healthy_project / "scripts" / "powershell" / "setup-plan.ps1").unlink()
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1
        assert "setup-plan.ps1" in result.output


# ===== Extensions Tests =====

class TestDoctorExtensions:
    """Tests for extension health checks."""

    def test_no_extensions(self, healthy_project):
        """No extensions configured should skip gracefully."""
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "no extensions" in result.output.lower()

    def test_valid_extensions_yml(self, healthy_project):
        """Valid extensions.yml should report as healthy."""
        ext_yml = healthy_project / ".specify" / "extensions.yml"
        ext_yml.write_text("hooks:\n  before_implement:\n    - extension: test\n      enabled: true\n")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "valid YAML" in result.output or "hook" in result.output.lower()

    def test_invalid_extensions_yml(self, healthy_project):
        """Invalid YAML in extensions.yml should report a warning."""
        ext_yml = healthy_project / ".specify" / "extensions.yml"
        ext_yml.write_text(": : : invalid yaml [[[")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "invalid" in result.output.lower() or "warning" in result.output.lower()

    def test_valid_registry(self, healthy_project):
        """Valid registry.json should report installed/enabled counts."""
        reg_dir = healthy_project / ".specify" / "extensions"
        reg_dir.mkdir(parents=True)
        registry = {"test-ext": {"enabled": True}, "other-ext": {"enabled": False}}
        (reg_dir / "registry.json").write_text(json.dumps(registry))
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert "2 installed" in result.output
        assert "1 enabled" in result.output

    def test_corrupt_registry(self, healthy_project):
        """Corrupt registry.json should report an error."""
        reg_dir = healthy_project / ".specify" / "extensions"
        reg_dir.mkdir(parents=True)
        (reg_dir / "registry.json").write_text("not json at all {{{")
        os.chdir(healthy_project)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 1
