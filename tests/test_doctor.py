"""
Unit tests for the specify doctor command.

Tests cover:
- Template integrity checks
- Agent configuration checks
- Script permission checks
- Constitution existence checks
- Feature artifact completeness checks
- Edge cases: empty project, missing directories
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path

from specify_cli import (
    _check_templates,
    _check_agent_config,
    _check_scripts,
    _check_constitution,
    _check_features,
)


@pytest.fixture
def temp_project():
    """Create a temporary project directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def initialized_project(temp_project):
    """Create a project with .specify and templates directories."""
    (temp_project / ".specify").mkdir()
    templates = temp_project / "templates"
    templates.mkdir()
    for name in [
        "spec-template.md",
        "plan-template.md",
        "tasks-template.md",
        "constitution-template.md",
        "checklist-template.md",
    ]:
        (templates / name).write_text(f"# {name}\nTemplate content")
    return temp_project


class TestCheckTemplates:
    """Tests for _check_templates."""

    def test_all_templates_present(self, initialized_project):
        results = _check_templates(initialized_project)
        assert len(results) == 5
        assert all(r["status"] == "pass" for r in results)

    def test_missing_template(self, initialized_project):
        (initialized_project / "templates" / "spec-template.md").unlink()
        results = _check_templates(initialized_project)
        spec_result = [r for r in results if r["name"] == "spec-template.md"][0]
        assert spec_result["status"] == "fail"

    def test_empty_template(self, initialized_project):
        (initialized_project / "templates" / "plan-template.md").write_text("")
        results = _check_templates(initialized_project)
        plan_result = [r for r in results if r["name"] == "plan-template.md"][0]
        assert plan_result["status"] == "warn"

    def test_no_templates_dir(self, temp_project):
        results = _check_templates(temp_project)
        assert all(r["status"] == "fail" for r in results)


class TestCheckAgentConfig:
    """Tests for _check_agent_config."""

    def test_no_init_options(self, temp_project):
        results = _check_agent_config(temp_project)
        assert len(results) == 1
        assert results[0]["status"] == "warn"
        assert "no AI agent configured" in results[0]["message"]

    def test_claude_agent_configured(self, temp_project):
        specify_dir = temp_project / ".specify"
        specify_dir.mkdir(parents=True)
        (specify_dir / "init-options.json").write_text(
            json.dumps({"ai_assistant": "claude"})
        )
        claude_dir = temp_project / ".claude" / "commands"
        claude_dir.mkdir(parents=True)
        (claude_dir / "speckit.specify.md").write_text("# Specify")
        (claude_dir / "speckit.plan.md").write_text("# Plan")

        results = _check_agent_config(temp_project)
        assert any(r["status"] == "pass" and "Claude Code" in r["name"] for r in results)
        assert any(r["status"] == "pass" and "command files" in r["name"] for r in results)

    def test_agent_dir_missing(self, temp_project):
        specify_dir = temp_project / ".specify"
        specify_dir.mkdir(parents=True)
        (specify_dir / "init-options.json").write_text(
            json.dumps({"ai_assistant": "claude"})
        )
        results = _check_agent_config(temp_project)
        assert any(r["status"] == "fail" for r in results)


class TestCheckScripts:
    """Tests for _check_scripts."""

    def test_no_scripts_dir(self, temp_project):
        results = _check_scripts(temp_project)
        assert len(results) == 1
        assert results[0]["status"] == "warn"

    def test_executable_scripts(self, temp_project):
        bash_dir = temp_project / "scripts" / "bash"
        bash_dir.mkdir(parents=True)
        script = bash_dir / "test.sh"
        script.write_text("#!/bin/bash\necho hello")
        script.chmod(0o755)

        results = _check_scripts(temp_project)
        bash_result = [r for r in results if r["name"] == "bash scripts"][0]
        assert bash_result["status"] == "pass"

    def test_non_executable_scripts(self, temp_project):
        bash_dir = temp_project / "scripts" / "bash"
        bash_dir.mkdir(parents=True)
        script = bash_dir / "test.sh"
        script.write_text("#!/bin/bash\necho hello")
        script.chmod(0o644)

        results = _check_scripts(temp_project)
        bash_result = [r for r in results if r["name"] == "bash scripts"][0]
        assert bash_result["status"] == "warn"
        assert "not executable" in bash_result["message"]


class TestCheckConstitution:
    """Tests for _check_constitution."""

    def test_no_constitution(self, temp_project):
        results = _check_constitution(temp_project)
        assert results[0]["status"] == "warn"
        assert "no constitution" in results[0]["message"]

    def test_constitution_exists(self, temp_project):
        (temp_project / "constitution.md").write_text("# Constitution\nOur principles are clear.")
        results = _check_constitution(temp_project)
        assert results[0]["status"] == "pass"
        assert "words" in results[0]["message"]

    def test_empty_constitution(self, temp_project):
        (temp_project / "constitution.md").write_text("")
        results = _check_constitution(temp_project)
        assert results[0]["status"] == "warn"
        assert "empty" in results[0]["message"]


class TestCheckFeatures:
    """Tests for _check_features."""

    def test_no_specs_dir(self, temp_project):
        results = _check_features(temp_project)
        assert results == []

    def test_complete_feature(self, temp_project):
        feature = temp_project / "specs" / "001-auth"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text("# Spec")
        (feature / "plan.md").write_text("# Plan")
        (feature / "tasks.md").write_text("# Tasks")

        results = _check_features(temp_project)
        assert len(results) == 1
        assert results[0]["status"] == "pass"

    def test_incomplete_feature(self, temp_project):
        feature = temp_project / "specs" / "002-dash"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text("# Spec")

        results = _check_features(temp_project)
        assert len(results) == 1
        assert results[0]["status"] == "warn"
        assert "plan ✗" in results[0]["message"]
        assert "tasks ✗" in results[0]["message"]
