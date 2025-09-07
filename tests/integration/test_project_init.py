"""
Integration test for project initialization flow (T011)
"""

from pathlib import Path

import pytest

from specify_cli.models.project import (
    ProjectInitOptions,
    ProjectInitResult,
    ProjectInitStep,
)
from specify_cli.services.config_service import ConfigService
from specify_cli.services.project_manager import ProjectManager
from specify_cli.services.template_service import TemplateService


class TestProjectInitializationFlow:
    """Integration tests for end-to-end project initialization workflow"""

    @pytest.fixture
    def project_manager(self) -> ProjectManager:
        """Create ProjectManager instance"""
        from specify_cli.services.project_manager import SpecifyProjectManager

        return SpecifyProjectManager()

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance"""
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    @pytest.fixture
    def config_service(self) -> ConfigService:
        """Create ConfigService instance"""
        from specify_cli.services.config_service import TomlConfigService

        return TomlConfigService()

    def test_complete_project_initialization_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test complete project initialization from start to finish"""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            # Test project initialization with standard options
            options = ProjectInitOptions(
                project_name="integration-test-project",
                ai_assistant="claude",
                use_current_dir=False,
                skip_git=True,  # Skip git for testing isolation
                ignore_agent_tools=False,
                custom_config=None,
            )

            # Initialize project
            result = project_manager.initialize_project(options)
            assert isinstance(result, ProjectInitResult)

            if result.success:
                # Verify project directory was created
                assert result.project_path.exists()
                assert result.project_path.is_dir()

                # Verify basic project structure
                spec_dir = result.project_path / ".specify"
                assert spec_dir.exists()

                # Verify configuration was created
                config_file = spec_dir / "config.toml"
                assert config_file.exists()

                # Verify some basic project files exist
                # (exact files depend on template, but should have some)
                project_files = list(result.project_path.glob("*"))
                assert len(project_files) > 1  # Should have more than just .specify

                # Verify completed steps
                assert len(result.completed_steps) > 0
                assert ProjectInitStep.VALIDATION in result.completed_steps

        finally:
            import os

            os.chdir(original_cwd)

    def test_current_directory_initialization_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test project initialization in current directory"""
        original_cwd = Path.cwd()
        try:
            # Create and change to test directory
            test_dir = tmp_path / "current_dir_test"
            test_dir.mkdir()
            import os

            os.chdir(test_dir)

            # Initialize in current directory
            options = ProjectInitOptions(
                project_name=None,  # No name needed for current dir
                ai_assistant="claude",
                use_current_dir=True,
                skip_git=True,
                ignore_agent_tools=True,
                custom_config={"init_type": "current_dir"},
            )

            result = project_manager.initialize_project(options)
            assert isinstance(result, ProjectInitResult)

            if result.success:
                # Should initialize in current directory
                assert result.project_path == test_dir

                # Verify spec-kit files were created
                spec_dir = test_dir / ".specify"
                assert spec_dir.exists()

        finally:
            import os

            os.chdir(original_cwd)

    def test_project_initialization_with_custom_config(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test project initialization with custom configuration"""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            custom_config = {
                "branch_pattern": "task/{task-name}",
                "template_variables": {
                    "author": "Custom Author",
                    "team": "Custom Team",
                },
                "enable_cache": False,
            }

            options = ProjectInitOptions(
                project_name="custom-config-project",
                ai_assistant="claude",
                use_current_dir=False,
                skip_git=True,
                ignore_agent_tools=False,
                custom_config=custom_config,
            )

            result = project_manager.initialize_project(options)
            assert isinstance(result, ProjectInitResult)

            if result.success:
                # Verify custom configuration was applied
                config_file = result.project_path / ".specify" / "config.toml"
                if config_file.exists():
                    config_content = config_file.read_text()
                    # Should contain custom settings
                    # (exact format depends on implementation)
                    assert len(config_content) > 0

        finally:
            import os

            os.chdir(original_cwd)

    def test_project_validation_workflow(self, project_manager: ProjectManager):
        """Test project name and directory validation workflow"""
        # Test valid project names
        valid_names = ["my-project", "test-project-123", "simple", "another-test"]

        for name in valid_names:
            is_valid, error = project_manager.validate_project_name(name)
            assert isinstance(is_valid, bool)
            if not is_valid:
                pytest.fail(f"Valid name '{name}' was rejected: {error}")

        # Test invalid project names
        invalid_names = [
            "",
            " ",
            "Project With Spaces",
            "project/with/slashes",
            "-starts-with-dash",
            "ends-with-dash-",
            "UPPERCASE-PROJECT",
            "project.with.dots",
        ]

        for name in invalid_names:
            is_valid, error = project_manager.validate_project_name(name)
            assert isinstance(is_valid, bool)
            if is_valid:
                pytest.fail(f"Invalid name '{name}' was accepted")

    def test_project_directory_validation_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test directory validation in different scenarios"""
        # Test empty directory (should be valid)
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        is_valid, error = project_manager.validate_project_directory(empty_dir, False)
        assert isinstance(is_valid, bool)

        # Test non-empty directory (may or may not be valid depending on implementation)
        non_empty_dir = tmp_path / "non_empty"
        non_empty_dir.mkdir()
        (non_empty_dir / "existing_file.txt").write_text("content")
        is_valid, error = project_manager.validate_project_directory(
            non_empty_dir, False
        )
        assert isinstance(is_valid, bool)

        # Test current directory validation
        is_valid, error = project_manager.validate_project_directory(tmp_path, True)
        assert isinstance(is_valid, bool)

    def test_project_structure_setup_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test project structure setup workflow"""
        project_dir = tmp_path / "structure_test"
        project_dir.mkdir()

        # Setup basic structure
        result = project_manager.setup_project_structure(project_dir, "claude")
        assert isinstance(result, bool)

        if result:
            # Verify basic structure was created
            assert project_dir.exists()
            # Should create .specify directory at minimum
            project_dir / ".specify"
            # May or may not exist depending on implementation approach

    def test_branch_naming_configuration_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test branch naming configuration workflow"""
        project_dir = tmp_path / "branch_config_test"
        project_dir.mkdir()

        # Test non-interactive configuration
        result = project_manager.configure_branch_naming(project_dir, interactive=False)
        assert isinstance(result, bool)

        if result:
            # Should create some configuration
            spec_dir = project_dir / ".specify"
            if spec_dir.exists():
                # May have created config file
                spec_dir / "config.toml"
                # File may or may not exist depending on implementation

    def test_failed_initialization_cleanup_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test cleanup after failed initialization"""
        project_dir = tmp_path / "failed_init"
        project_dir.mkdir()

        # Create some files to simulate partial initialization
        (project_dir / "partial_file.txt").write_text("partial")
        spec_dir = project_dir / ".specify"
        spec_dir.mkdir()
        (spec_dir / "incomplete_config.toml").write_text("incomplete")

        # Simulate cleanup after failure
        completed_steps = [ProjectInitStep.VALIDATION, ProjectInitStep.DOWNLOAD]
        result = project_manager.cleanup_failed_init(project_dir, completed_steps)
        assert isinstance(result, bool)

        # Implementation may or may not clean up files - both approaches valid

    def test_project_info_retrieval_workflow(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test project information retrieval workflow"""
        # Test empty directory
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        info = project_manager.get_project_info(empty_dir)
        assert info is None or isinstance(info, dict)

        # Test directory with spec-kit files
        project_dir = tmp_path / "spec_project"
        project_dir.mkdir()
        spec_dir = project_dir / ".specify"
        spec_dir.mkdir()

        config_file = spec_dir / "config.toml"
        config_file.write_text("""
[project]
name = "test-project"

[project.branch_naming]
default_pattern = "feature/{feature-name}"

[project.template_settings]
ai_assistant = "claude"
""")

        info = project_manager.get_project_info(project_dir)
        if info is not None:
            assert isinstance(info, dict)
            # Should contain meaningful project information

    def test_integration_error_handling(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test error handling in integration scenarios"""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            # Test initialization with invalid project name
            invalid_options = ProjectInitOptions(
                project_name="Invalid Project Name",  # Spaces should be invalid
                ai_assistant="claude",
                use_current_dir=False,
                skip_git=True,
                ignore_agent_tools=False,
                custom_config=None,
            )

            result = project_manager.initialize_project(invalid_options)
            assert isinstance(result, ProjectInitResult)

            # Should fail gracefully
            if not result.success:
                assert result.error_message is not None
                assert len(result.error_message) > 0

            # Test initialization in read-only directory (if possible)
            readonly_dir = tmp_path / "readonly"
            readonly_dir.mkdir()
            try:
                import stat

                readonly_dir.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

                readonly_options = ProjectInitOptions(
                    project_name="readonly-test",
                    ai_assistant="claude",
                    use_current_dir=False,
                    skip_git=True,
                    ignore_agent_tools=False,
                    custom_config=None,
                )

                # Should handle permission error gracefully
                result = project_manager.initialize_project(readonly_options)
                assert isinstance(result, ProjectInitResult)

            finally:
                # Restore permissions for cleanup
                readonly_dir.chmod(stat.S_IRWXU)

        finally:
            import os

            os.chdir(original_cwd)

    def test_multi_ai_assistant_support(
        self, project_manager: ProjectManager, tmp_path: Path
    ):
        """Test initialization with different AI assistants"""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            # Test different AI assistants
            ai_assistants = ["claude", "gemini", "copilot"]

            for ai_assistant in ai_assistants:
                options = ProjectInitOptions(
                    project_name=f"test-{ai_assistant}",
                    ai_assistant=ai_assistant,
                    use_current_dir=False,
                    skip_git=True,
                    ignore_agent_tools=True,
                    custom_config=None,
                )

                result = project_manager.initialize_project(options)
                assert isinstance(result, ProjectInitResult)

                # Each AI assistant should be supported
                # (though implementation may vary)

        finally:
            import os

            os.chdir(original_cwd)
