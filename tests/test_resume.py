"""
Unit tests for the specify resume command.

Tests cover:
- Feature state detection from spec directories
- Task parsing (completed vs remaining)
- Phase determination logic
- Resume prompt generation
- Edge cases: empty project, no features, all complete
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from specify_cli import _detect_feature_state, _find_features, _generate_resume_prompt


@pytest.fixture
def temp_project():
    """Create a temporary project directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def feature_dir(temp_project):
    """Create a feature directory with basic structure."""
    specs = temp_project / "specs" / "001-user-auth"
    specs.mkdir(parents=True)
    return specs


class TestDetectFeatureState:
    """Tests for _detect_feature_state."""

    def test_empty_feature_dir(self, feature_dir):
        state = _detect_feature_state(feature_dir)
        assert state["name"] == "001-user-auth"
        assert state["spec"] is False
        assert state["plan"] is False
        assert state["tasks"] is False
        assert state["phase"] == "specify"

    def test_spec_only(self, feature_dir):
        (feature_dir / "spec.md").write_text("# Feature Spec\nSome content")
        state = _detect_feature_state(feature_dir)
        assert state["spec"] is True
        assert state["plan"] is False
        assert state["phase"] == "plan"

    def test_spec_and_plan(self, feature_dir):
        (feature_dir / "spec.md").write_text("# Spec\nContent")
        (feature_dir / "plan.md").write_text("# Plan\nContent")
        state = _detect_feature_state(feature_dir)
        assert state["spec"] is True
        assert state["plan"] is True
        assert state["tasks"] is False
        assert state["phase"] == "tasks"

    def test_all_artifacts_with_remaining_tasks(self, feature_dir):
        (feature_dir / "spec.md").write_text("# Spec")
        (feature_dir / "plan.md").write_text("# Plan")
        (feature_dir / "tasks.md").write_text(
            "# Tasks\n"
            "- [x] Task 1: Setup project\n"
            "- [x] Task 2: Create models\n"
            "- [ ] Task 3: Add API endpoints\n"
            "- [ ] Task 4: Write tests\n"
        )
        state = _detect_feature_state(feature_dir)
        assert state["spec"] is True
        assert state["plan"] is True
        assert state["tasks"] is True
        assert state["total_tasks"] == 4
        assert state["completed_tasks"] == 2
        assert len(state["remaining_tasks"]) == 2
        assert state["remaining_tasks"][0] == "Task 3: Add API endpoints"
        assert state["phase"] == "implement"

    def test_all_tasks_complete(self, feature_dir):
        (feature_dir / "spec.md").write_text("# Spec")
        (feature_dir / "plan.md").write_text("# Plan")
        (feature_dir / "tasks.md").write_text(
            "# Tasks\n- [x] Task 1: Setup\n- [X] Task 2: Build\n- [x] Task 3: Test\n"
        )
        state = _detect_feature_state(feature_dir)
        assert state["total_tasks"] == 3
        assert state["completed_tasks"] == 3
        assert state["remaining_tasks"] == []
        assert state["phase"] == "complete"

    def test_empty_spec_file_treated_as_missing(self, feature_dir):
        (feature_dir / "spec.md").write_text("")
        state = _detect_feature_state(feature_dir)
        assert state["spec"] is False
        assert state["phase"] == "specify"

    def test_checklists_detected(self, feature_dir):
        (feature_dir / "spec.md").write_text("# Spec")
        checklists = feature_dir / "checklists"
        checklists.mkdir()
        (checklists / "requirements.md").write_text("# Checklist")
        state = _detect_feature_state(feature_dir)
        assert state["checklists"] is True


class TestFindFeatures:
    """Tests for _find_features."""

    def test_no_specs_dir(self, temp_project):
        features = _find_features(temp_project)
        assert features == []

    def test_empty_specs_dir(self, temp_project):
        (temp_project / "specs").mkdir()
        features = _find_features(temp_project)
        assert features == []

    def test_finds_numbered_features(self, temp_project):
        specs = temp_project / "specs"
        (specs / "001-auth").mkdir(parents=True)
        (specs / "002-dashboard").mkdir(parents=True)
        (specs / "001-auth" / "spec.md").write_text("# Auth Spec")
        features = _find_features(temp_project)
        assert len(features) == 2
        assert features[0]["name"] == "001-auth"
        assert features[1]["name"] == "002-dashboard"

    def test_ignores_non_numbered_dirs(self, temp_project):
        specs = temp_project / "specs"
        (specs / "001-auth").mkdir(parents=True)
        (specs / "templates").mkdir(parents=True)
        (specs / "notes.md").touch()
        features = _find_features(temp_project)
        assert len(features) == 1

    def test_sorted_by_name(self, temp_project):
        specs = temp_project / "specs"
        (specs / "003-api").mkdir(parents=True)
        (specs / "001-auth").mkdir(parents=True)
        (specs / "002-dash").mkdir(parents=True)
        features = _find_features(temp_project)
        assert [f["name"] for f in features] == ["001-auth", "002-dash", "003-api"]


class TestGenerateResumePrompt:
    """Tests for _generate_resume_prompt."""

    def test_prompt_for_specify_phase(self):
        feature = {
            "name": "001-auth",
            "spec": False,
            "plan": False,
            "tasks": False,
            "total_tasks": 0,
            "completed_tasks": 0,
            "remaining_tasks": [],
            "phase": "specify",
        }
        prompt = _generate_resume_prompt(feature, "claude")
        assert "001-auth" in prompt
        assert "/speckit.specify" in prompt
        assert "missing" in prompt

    def test_prompt_for_implement_phase(self):
        feature = {
            "name": "003-api",
            "spec": True,
            "plan": True,
            "tasks": True,
            "total_tasks": 5,
            "completed_tasks": 3,
            "remaining_tasks": ["Add rate limiting", "Write docs"],
            "phase": "implement",
        }
        prompt = _generate_resume_prompt(feature, "claude")
        assert "/speckit.implement" in prompt
        assert "Add rate limiting" in prompt
        assert "Write docs" in prompt
        assert "3/5" in prompt

    def test_prompt_for_complete_phase(self):
        feature = {
            "name": "002-dash",
            "spec": True,
            "plan": True,
            "tasks": True,
            "total_tasks": 3,
            "completed_tasks": 3,
            "remaining_tasks": [],
            "phase": "complete",
        }
        prompt = _generate_resume_prompt(feature, "copilot")
        assert "complete" in prompt.lower()
        assert "Review and finalize" in prompt
