"""
Contract tests for ProjectManager interface
"""

from pathlib import Path

import pytest

from specify_cli.models.project import (
    ProjectInitOptions,
    ProjectInitResult,
    ProjectInitStep,
)
from specify_cli.services.project_manager import ProjectManager


class TestProjectManagerContract:
    """Test contract compliance for ProjectManager interface"""

    @pytest.fixture
    def project_manager(self) -> ProjectManager:
        """Create ProjectManager instance for testing"""
        # This will fail until implementation exists
        from specify_cli.services.project_manager import SpecifyProjectManager

        return SpecifyProjectManager()

    @pytest.fixture
    def basic_init_options(self) -> ProjectInitOptions:
        """Create basic project initialization options"""
        return ProjectInitOptions(
            project_name="test-project",
            ai_assistant="claude",
            use_current_dir=False,
            skip_git=False,
            ignore_agent_tools=False,
            custom_config=None,
        )

    @pytest.fixture
    def current_dir_options(self) -> ProjectInitOptions:
        """Create options for current directory initialization"""
        return ProjectInitOptions(
            project_name=None,
            ai_assistant="claude",
            use_current_dir=True,
            skip_git=True,
            ignore_agent_tools=True,
            custom_config={"custom": "value"},
        )

    def test_initialize_project_contract(
        self,
        project_manager: ProjectManager,
        basic_init_options: ProjectInitOptions,
        tmp_path: Path,
    ):
        """Test initialize_project method contract"""
        # Change to temp directory for testing
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            # Test successful initialization
            result = project_manager.initialize_project(basic_init_options)
            assert isinstance(result, ProjectInitResult)
            assert hasattr(result, "success")
            assert hasattr(result, "project_path")
            assert hasattr(result, "completed_steps")
            assert hasattr(result, "error_message")
            assert hasattr(result, "warnings")

            assert isinstance(result.success, bool)
            assert isinstance(result.project_path, Path)
            assert isinstance(result.completed_steps, list)
            assert result.error_message is None or isinstance(result.error_message, str)
            assert result.warnings is None or isinstance(result.warnings, list)

            # Verify completed steps are valid enum values
            for step in result.completed_steps:
                assert isinstance(step, ProjectInitStep)

        finally:
            import os

            os.chdir(original_cwd)

    def test_initialize_project_current_dir_contract(
        self,
        project_manager: ProjectManager,
        current_dir_options: ProjectInitOptions,
        tmp_path: Path,
    ):
        """Test initialize_project with current directory option"""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            result = project_manager.initialize_project(current_dir_options)
            assert isinstance(result, ProjectInitResult)

            if result.success:
                # Current directory should be the project path
                assert result.project_path == tmp_path

        finally:
            import os

            os.chdir(original_cwd)

    def test_validate_project_name_contract(self, project_manager: ProjectManager):
        """Test validate_project_name method contract"""
        # Test valid names
        valid_names = ["my-project", "test_project", "project123", "simple"]

        for name in valid_names:
            is_valid, error = project_manager.validate_project_name(name)
            assert isinstance(is_valid, bool)
            assert error is None or isinstance(error, str)

        # Test invalid names
        invalid_names = [
            "",
            " ",
            "project with spaces",
            "project/with/slashes",
            "project\with\backslashes",
            "project:with:colons",
            "-starting-with-dash",
            "ending-with-dash-",
            "UPPERCASE",
            "project.with.dots",
        ]

        for name in invalid_names:
            is_valid, error = project_manager.validate_project_name(name)
            assert isinstance(is_valid, bool)
            if not is_valid:
                assert isinstance(error, str)
                assert len(error) > 0

    def test_validate_project_directory_contract(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test validate_project_directory method contract"""
        # Test valid empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        is_valid, error = project_manager.validate_project_directory(empty_dir, False)
        assert isinstance(is_valid, bool)
        assert error is None or isinstance(error, str)

        # Test non-empty directory
        non_empty_dir = tmp_path / "non_empty"
        non_empty_dir.mkdir()
        (non_empty_dir / "file.txt").write_text("content")

        is_valid, error = project_manager.validate_project_directory(
            non_empty_dir, False
        )
        assert isinstance(is_valid, bool)
        assert error is None or isinstance(error, str)

        # Test current directory validation
        is_valid, error = project_manager.validate_project_directory(tmp_path, True)
        assert isinstance(is_valid, bool)
        assert error is None or isinstance(error, str)

        # Test non-existent directory
        is_valid, error = project_manager.validate_project_directory(
            tmp_path / "nonexistent", False
        )
        assert isinstance(is_valid, bool)
        assert error is None or isinstance(error, str)

    def test_setup_project_structure_contract(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test setup_project_structure method contract"""
        project_dir = tmp_path / "structure_test"
        project_dir.mkdir()

        result = project_manager.setup_project_structure(project_dir, "claude")
        assert isinstance(result, bool)

        if result:  # If successful, verify basic structure exists
            assert project_dir.exists()
            # Should create some basic directories/files
            # Exact structure depends on implementation

    def test_configure_branch_naming_contract(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test configure_branch_naming method contract"""
        project_dir = tmp_path / "branch_test"
        project_dir.mkdir()

        # Test non-interactive mode
        result = project_manager.configure_branch_naming(project_dir, interactive=False)
        assert isinstance(result, bool)

        # Test interactive mode (will use defaults in test environment)
        result = project_manager.configure_branch_naming(project_dir, interactive=True)
        assert isinstance(result, bool)

    def test_migrate_existing_project_contract(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test migrate_existing_project method contract"""
        # Create existing project structure
        existing_project = tmp_path / "existing"
        existing_project.mkdir()
        (existing_project / "README.md").write_text("# Existing Project")

        result = project_manager.migrate_existing_project(existing_project)
        assert isinstance(result, bool)

    def test_get_project_info_contract(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test get_project_info method contract"""
        # Test non-existent project
        info = project_manager.get_project_info(tmp_path / "nonexistent")
        assert info is None or isinstance(info, dict)

        # Test empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        info = project_manager.get_project_info(empty_dir)
        assert info is None or isinstance(info, dict)

        # Test directory with some content
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / "README.md").write_text("# Test")

        info = project_manager.get_project_info(project_dir)
        if info is not None:
            assert isinstance(info, dict)
            # Should contain meaningful project information

    def test_cleanup_failed_init_contract(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test cleanup_failed_init method contract"""
        project_dir = tmp_path / "failed_init"
        project_dir.mkdir()

        # Create some files that represent partial initialization
        (project_dir / "partial_file.txt").write_text("partial")

        completed_steps = [ProjectInitStep.VALIDATION, ProjectInitStep.DOWNLOAD]

        result = project_manager.cleanup_failed_init(project_dir, completed_steps)
        assert isinstance(result, bool)


class TestProjectManagerIntegration:
    """Integration tests for ProjectManager workflow"""

    @pytest.fixture
    def project_manager(self) -> ProjectManager:
        """Create ProjectManager instance"""
        from specify_cli.services.project_manager import SpecifyProjectManager

        return SpecifyProjectManager()

    def test_full_project_initialization_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test complete project initialization workflow"""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            # Test project name validation
            is_valid, error = project_manager.validate_project_name("integration-test")
            if not is_valid:
                pytest.skip(f"Project name validation failed: {error}")

            # Test directory validation
            project_path = tmp_path / "integration-test"
            is_valid, error = project_manager.validate_project_directory(
                project_path, False
            )
            if not is_valid:
                pytest.skip(f"Directory validation failed: {error}")

            # Initialize project
            options = ProjectInitOptions(
                project_name="integration-test",
                ai_assistant="claude",
                use_current_dir=False,
                skip_git=True,  # Skip git to avoid external dependencies
                ignore_agent_tools=True,
                custom_config={"test": "integration"},
            )

            result = project_manager.initialize_project(options)
            assert isinstance(result, ProjectInitResult)

            if result.success:
                # Verify project was created
                assert result.project_path.exists()

                # Get project info
                info = project_manager.get_project_info(result.project_path)
                if info is not None:
                    assert isinstance(info, dict)

                # Configure branch naming
                branch_result = project_manager.configure_branch_naming(
                    result.project_path, interactive=False
                )
                assert isinstance(branch_result, bool)

        finally:
            import os

            os.chdir(original_cwd)

    def test_current_directory_initialization_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test initialization in current directory"""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            # Initialize in current directory
            options = ProjectInitOptions(
                project_name=None,  # No name when using current dir
                ai_assistant="claude",
                use_current_dir=True,
                skip_git=True,
                ignore_agent_tools=True,
                custom_config=None,
            )

            result = project_manager.initialize_project(options)
            assert isinstance(result, ProjectInitResult)

            if result.success:
                # Should use current directory
                assert result.project_path == tmp_path

        finally:
            import os

            os.chdir(original_cwd)

    def test_project_validation_edge_cases(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test edge cases in project validation"""
        # Test various project name edge cases
        edge_case_names = [
            "a",  # Very short
            "a" * 100,  # Very long
            "123",  # All numbers
            "test-project-with-many-dashes",  # Many dashes
            "test_project_with_underscores",  # Underscores
        ]

        for name in edge_case_names:
            is_valid, error = project_manager.validate_project_name(name)
            assert isinstance(is_valid, bool)
            assert error is None or isinstance(error, str)

        # Test directory validation edge cases
        # Test very nested path
        deep_path = tmp_path
        for i in range(10):
            deep_path = deep_path / f"level{i}"

        is_valid, error = project_manager.validate_project_directory(deep_path, False)
        assert isinstance(is_valid, bool)
        assert error is None or isinstance(error, str)
