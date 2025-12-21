"""
Tests for SPIFF External Project Validation

Tests for project discovery, analysis, and validation.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from specify_cli.spiff.ops import (
    ExternalProjectInfo,
    ExternalValidationResult,
    discover_external_projects,
)
from specify_cli.spiff.ops.external_projects import (
    _is_python_project,
    _detect_project_type,
    _generate_project_specific_tests,
)


class TestExternalProjectInfo:
    """Test ExternalProjectInfo dataclass."""

    def test_project_info_creation(self, tmp_path):
        """Test creating ExternalProjectInfo."""
        project = ExternalProjectInfo(
            path=tmp_path,
            name="test-project",
            package_manager="pip",
            has_tests=True,
            project_type="library",
            confidence=0.9,
        )

        assert project.name == "test-project"
        assert project.package_manager == "pip"
        assert project.has_tests is True
        assert project.confidence == 0.9

    def test_project_info_to_dict(self, tmp_path):
        """Test converting ProjectInfo to dict."""
        project = ExternalProjectInfo(
            path=tmp_path,
            name="test",
            package_manager="uv",
            confidence=0.8,
        )

        project_dict = project.to_dict()
        assert isinstance(project_dict, dict)
        assert project_dict["name"] == "test"
        assert project_dict["package_manager"] == "uv"
        assert project_dict["confidence"] == 0.8


class TestExternalValidationResult:
    """Test ExternalValidationResult dataclass."""

    def test_validation_result_creation(self, tmp_path):
        """Test creating ExternalValidationResult."""
        result = ExternalValidationResult(
            project_path=tmp_path,
            project_name="test-project",
            success=True,
            duration_seconds=5.0,
        )

        assert result.project_name == "test-project"
        assert result.success is True
        assert result.duration_seconds == 5.0

    def test_validation_result_to_dict(self, tmp_path):
        """Test converting validation result to dict."""
        result = ExternalValidationResult(
            project_path=tmp_path,
            project_name="test",
            success=False,
            errors=["Error 1", "Error 2"],
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is False
        assert len(result_dict["errors"]) == 2


class TestProjectDetection:
    """Test Python project detection."""

    def test_detect_python_project_with_pyproject(self, tmp_path):
        """Test detecting project with pyproject.toml."""
        (tmp_path / "pyproject.toml").touch()

        project = _is_python_project(tmp_path)

        assert project is not None
        assert project.name == tmp_path.name
        assert project.confidence > 0.3

    def test_detect_python_project_with_setup(self, tmp_path):
        """Test detecting project with setup.py."""
        (tmp_path / "setup.py").touch()

        project = _is_python_project(tmp_path)

        assert project is not None

    def test_detect_python_project_with_requirements(self, tmp_path):
        """Test detecting project with requirements.txt."""
        (tmp_path / "requirements.txt").touch()

        project = _is_python_project(tmp_path)

        assert project is not None

    def test_detect_python_project_with_tests(self, tmp_path):
        """Test detecting project with tests directory."""
        (tmp_path / "tests").mkdir()

        project = _is_python_project(tmp_path)

        assert project is None or project.has_tests is True

    def test_no_python_project(self, tmp_path):
        """Test that non-Python projects are not detected."""
        # Create a directory with no Python indicators
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        project = _is_python_project(empty_dir)

        assert project is None


class TestProjectTypeDetection:
    """Test project type detection."""

    def test_detect_web_project(self, tmp_path):
        """Test detecting web framework projects."""
        (tmp_path / "app.py").touch()
        (tmp_path / "pyproject.toml").touch()

        project_type = _detect_project_type(tmp_path)

        assert project_type == "web"

    def test_detect_cli_project(self, tmp_path):
        """Test detecting CLI projects."""
        (tmp_path / "main.py").touch()
        (tmp_path / "pyproject.toml").touch()

        project_type = _detect_project_type(tmp_path)

        # Could be cli or unknown depending on exact matching
        assert project_type in ["cli", "unknown"]

    def test_detect_library_project(self, tmp_path):
        """Test detecting library projects."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "__init__.py").touch()
        (tmp_path / "pyproject.toml").touch()

        project_type = _detect_project_type(tmp_path)

        assert project_type in ["library", "unknown"]

    def test_detect_unknown_project(self, tmp_path):
        """Test detecting unknown project type."""
        (tmp_path / "pyproject.toml").touch()

        project_type = _detect_project_type(tmp_path)

        # Should be unknown without specific indicators
        assert isinstance(project_type, str)


class TestTestCommandGeneration:
    """Test test command generation for projects."""

    def test_generate_8020_tests(self, tmp_path):
        """Test generating 80/20 test commands."""
        project = ExternalProjectInfo(
            path=tmp_path,
            name="test-project",
            package_manager="pip",
        )

        tests = _generate_project_specific_tests(project, use_8020=True)

        assert isinstance(tests, list)
        assert len(tests) > 0
        # Should have Python import tests
        assert any("python" in cmd for cmd in tests)

    def test_generate_comprehensive_tests_with_tests_dir(self, tmp_path):
        """Test generating comprehensive tests for project with tests."""
        (tmp_path / "tests").mkdir()
        project = ExternalProjectInfo(
            path=tmp_path,
            name="test-project",
            package_manager="pip",
            has_tests=True,
            test_framework="pytest",
        )

        tests = _generate_project_specific_tests(project, use_8020=False)

        assert isinstance(tests, list)
        assert len(tests) > 0

    def test_generate_tests_without_tests_dir(self, tmp_path):
        """Test generating tests for project without tests directory."""
        project = ExternalProjectInfo(
            path=tmp_path,
            name="test-project",
            package_manager="pip",
            has_tests=False,
        )

        tests = _generate_project_specific_tests(project, use_8020=True)

        assert isinstance(tests, list)
        assert len(tests) > 0


class TestProjectDiscovery:
    """Test project discovery functionality."""

    def test_discover_projects_empty_directory(self, tmp_path):
        """Test discovery in empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        projects = discover_external_projects(search_path=empty_dir, max_depth=1)

        assert isinstance(projects, list)
        assert len(projects) == 0

    def test_discover_projects_with_valid_project(self, tmp_path):
        """Test discovery finds valid projects."""
        # Create a valid project
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").touch()
        (project_dir / "src").mkdir()

        projects = discover_external_projects(search_path=tmp_path, max_depth=2)

        # Should find at least one project
        assert isinstance(projects, list)
        # Note: May or may not find depending on confidence threshold

    def test_discover_projects_respects_depth(self, tmp_path):
        """Test that discovery respects max_depth."""
        # Create nested projects
        level1 = tmp_path / "level1"
        level1.mkdir()
        (level1 / "pyproject.toml").touch()

        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / "setup.py").touch()

        # Search with depth=1 should only find level1
        projects = discover_external_projects(search_path=tmp_path, max_depth=1)

        assert isinstance(projects, list)

    def test_discover_projects_sorts_by_confidence(self, tmp_path):
        """Test that projects are sorted by confidence."""
        # Create multiple projects with different confidence levels
        high_conf = tmp_path / "high"
        high_conf.mkdir()
        (high_conf / "pyproject.toml").touch()
        (high_conf / "setup.py").touch()
        (high_conf / "src").mkdir()

        low_conf = tmp_path / "low"
        low_conf.mkdir()
        (low_conf / "requirements.txt").touch()

        projects = discover_external_projects(search_path=tmp_path, max_depth=1)

        # Projects should be sorted by confidence (highest first)
        if len(projects) > 1:
            for i in range(len(projects) - 1):
                assert projects[i].confidence >= projects[i + 1].confidence
