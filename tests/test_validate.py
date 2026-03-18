"""
Unit tests for the specify validate command.

Tests cover:
- Task parsing from tasks.md
- Keyword extraction from task descriptions
- File existence verification
- Spec requirement parsing
- Requirement-to-task traceability
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from specify_cli import (
    _parse_tasks,
    _extract_keywords,
    _verify_task_files,
    _parse_spec_requirements,
    _trace_requirement_to_tasks,
)


@pytest.fixture
def temp_project():
    """Create a temporary project directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


class TestParseTasks:
    """Tests for _parse_tasks."""

    def test_no_tasks_file(self, temp_project):
        tasks = _parse_tasks(temp_project / "tasks.md")
        assert tasks == []

    def test_mixed_tasks(self, temp_project):
        tasks_file = temp_project / "tasks.md"
        tasks_file.write_text(
            "# Tasks\n"
            "- [x] Task 1: Create auth/login.py endpoint\n"
            "- [ ] Task 2: Write tests for auth\n"
            "- [X] Task 3: Update README.md\n"
        )
        tasks = _parse_tasks(tasks_file)
        assert len(tasks) == 3
        assert tasks[0]["completed"] is True
        assert tasks[1]["completed"] is False
        assert tasks[2]["completed"] is True

    def test_empty_file(self, temp_project):
        tasks_file = temp_project / "tasks.md"
        tasks_file.write_text("")
        tasks = _parse_tasks(tasks_file)
        assert tasks == []

    def test_no_checkboxes(self, temp_project):
        tasks_file = temp_project / "tasks.md"
        tasks_file.write_text("# Tasks\nSome text but no checkboxes")
        tasks = _parse_tasks(tasks_file)
        assert tasks == []


class TestExtractKeywords:
    """Tests for _extract_keywords."""

    def test_file_paths(self):
        keywords = _extract_keywords("Create auth/login.py endpoint")
        assert "auth/login.py" in keywords

    def test_snake_case(self):
        keywords = _extract_keywords("Add user_auth module")
        assert "user_auth" in keywords

    def test_camel_case(self):
        keywords = _extract_keywords("Implement UserAuth class")
        assert "UserAuth" in keywords

    def test_no_keywords(self):
        keywords = _extract_keywords("Do the thing")
        assert keywords == []

    def test_dotted_names(self):
        keywords = _extract_keywords("Update config.yaml")
        assert "config.yaml" in keywords


class TestVerifyTaskFiles:
    """Tests for _verify_task_files."""

    def test_files_exist(self, temp_project):
        (temp_project / "src").mkdir()
        (temp_project / "src" / "auth.py").write_text("# auth")
        task = {
            "text": "Create src/auth.py",
            "completed": True,
            "keywords": ["src/auth.py"],
        }
        result = _verify_task_files(temp_project, task)
        assert result["status"] == "pass"
        assert "src/auth.py" in result["files_found"]

    def test_files_missing(self, temp_project):
        task = {
            "text": "Create src/missing.py",
            "completed": True,
            "keywords": ["src/missing.py"],
        }
        result = _verify_task_files(temp_project, task)
        assert result["status"] == "warn"
        assert "src/missing.py" in result["files_missing"]

    def test_incomplete_task_skipped(self, temp_project):
        task = {
            "text": "Create something",
            "completed": False,
            "keywords": [],
        }
        result = _verify_task_files(temp_project, task)
        assert result["status"] == "skip"

    def test_no_file_references(self, temp_project):
        task = {
            "text": "Set up the project",
            "completed": True,
            "keywords": ["UserAuth"],  # Not a file path
        }
        result = _verify_task_files(temp_project, task)
        assert result["status"] == "pass"


class TestParseSpecRequirements:
    """Tests for _parse_spec_requirements."""

    def test_no_spec_file(self, temp_project):
        reqs = _parse_spec_requirements(temp_project / "spec.md")
        assert reqs == []

    def test_requirements_section(self, temp_project):
        spec = temp_project / "spec.md"
        spec.write_text(
            "# Feature\n\n"
            "## Functional Requirements\n\n"
            "- Users can log in with email and password\n"
            "- Passwords are stored securely\n"
            "- Users can reset their password via email\n\n"
            "## Success Criteria\n\n"
            "- Login completes in under 3 seconds\n"
        )
        reqs = _parse_spec_requirements(spec)
        assert len(reqs) == 3
        assert "Users can log in with email and password" in reqs

    def test_no_requirements_section(self, temp_project):
        spec = temp_project / "spec.md"
        spec.write_text("# Feature\n\n## Overview\n\nSome description\n")
        reqs = _parse_spec_requirements(spec)
        assert reqs == []


class TestTraceRequirementToTasks:
    """Tests for _trace_requirement_to_tasks."""

    def test_matching_tasks(self):
        tasks = [
            {"text": "Create login endpoint with email and password validation", "completed": True},
            {"text": "Add password hashing with bcrypt", "completed": True},
            {"text": "Set up database connection", "completed": True},
        ]
        requirement = "Users can log in with email and password"
        matched = _trace_requirement_to_tasks(requirement, tasks)
        assert len(matched) >= 1
        assert any("login" in t.lower() for t in matched)

    def test_no_matching_tasks(self):
        tasks = [
            {"text": "Set up database connection", "completed": True},
            {"text": "Configure CI pipeline", "completed": True},
        ]
        requirement = "Users can reset their password via email"
        matched = _trace_requirement_to_tasks(requirement, tasks)
        assert matched == []

    def test_empty_tasks(self):
        matched = _trace_requirement_to_tasks("Some requirement", [])
        assert matched == []
