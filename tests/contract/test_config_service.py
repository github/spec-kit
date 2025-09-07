"""
Contract tests for ConfigService interface
"""

from pathlib import Path

import pytest

from specify_cli.models.config import BranchNamingConfig, ProjectConfig, TemplateConfig
from specify_cli.services.config_service import ConfigService


class TestConfigServiceContract:
    """Test contract compliance for ConfigService interface"""

    @pytest.fixture
    def config_service(self) -> ConfigService:
        """Create ConfigService instance for testing"""
        # This will fail until implementation exists
        from specify_cli.services.config_service import TomlConfigService

        return TomlConfigService()

    @pytest.fixture
    def sample_project_config(self) -> ProjectConfig:
        """Create sample project configuration"""
        return ProjectConfig(
            name="test-project",
            branch_naming=BranchNamingConfig(
                default_pattern="feature/{feature-name}",
                patterns=[
                    "feature/{feature-name}",
                    "bugfix/{bug-id}",
                    "hotfix/{version}",
                    "epic/{epic-name}",
                ],
            ),
            template_settings=TemplateConfig(
                ai_assistant="claude",
                custom_templates_dir=None,
                template_cache_enabled=True,
                template_variables={"author": "test-user", "team": "dev-team"},
            ),
        )

    @pytest.fixture
    def project_with_config(
        self, tmp_path: Path, sample_project_config: ProjectConfig
    ) -> Path:
        """Create temporary project directory with config"""
        sample_project_config = (
            sample_project_config  # Remove once implementation exists
        )

        project_dir = tmp_path / "test-project"
        project_dir.mkdir()

        config_dir = project_dir / ".specify"
        config_dir.mkdir()

        # Create sample config file (TOML format)
        config_file = config_dir / "config.toml"
        config_content = """
[project]
name = "test-project"

[project.branch_naming]
default_pattern = "feature/{feature-name}"
patterns = ["feature/{feature-name}", "bugfix/{bug-id}"]


[project.template_settings]
ai_assistant = "claude"
template_cache_enabled = true

[project.template_settings.template_variables]
author = "test-user"
team = "dev-team"
"""
        config_file.write_text(config_content)
        return project_dir

    def test_load_project_config_contract(
        self, config_service: ConfigService, project_with_config: Path
    ):
        """Test load_project_config method contract"""
        # Test successful loading
        config = config_service.load_project_config(project_with_config)
        assert config is not None
        assert isinstance(config, ProjectConfig)
        assert config.name == "test-project"
        assert isinstance(config.branch_naming, BranchNamingConfig)
        assert isinstance(config.template_settings, TemplateConfig)

        # Test non-existent project
        config = config_service.load_project_config(project_with_config / "nonexistent")
        assert config is None

        # Test project without config
        empty_project = project_with_config.parent / "empty"
        empty_project.mkdir()
        config = config_service.load_project_config(empty_project)
        assert config is None

    def test_save_project_config_contract(
        self,
        config_service: ConfigService,
        sample_project_config: ProjectConfig,
        tmp_path: Path,
    ):
        """Test save_project_config method contract"""
        project_dir = tmp_path / "new-project"
        project_dir.mkdir()

        # Test successful save
        result = config_service.save_project_config(project_dir, sample_project_config)
        assert isinstance(result, bool)
        assert result is True

        # Verify config file was created
        config_file = project_dir / ".specify" / "config.toml"
        assert config_file.exists()

        # Test that saved config can be loaded back
        loaded_config = config_service.load_project_config(project_dir)
        assert loaded_config is not None
        assert loaded_config.name == sample_project_config.name

        # Test save to invalid path
        result = config_service.save_project_config(
            Path("/invalid/path"), sample_project_config
        )
        assert isinstance(result, bool)
        assert result is False

    def test_load_global_config_contract(
        self, config_service: ConfigService, monkeypatch, tmp_path: Path
    ):
        """Test load_global_config method contract"""
        # Mock home directory to use temp directory
        temp_home = tmp_path / "test_home"
        monkeypatch.setenv("HOME", str(temp_home))

        # Test when no global config exists
        config = config_service.load_global_config()
        # Should return None or default config
        assert config is None or isinstance(config, ProjectConfig)

        # Create global config
        if not temp_home.exists():
            temp_home.mkdir()
        global_config_dir = temp_home / ".specify"
        global_config_dir.mkdir(exist_ok=True)

        global_config_file = global_config_dir / "config.toml"
        global_config_file.write_text("""
[project]
name = "global-default"

[project.template_settings]
ai_assistant = "claude"
""")

        config = config_service.load_global_config()
        if config is not None:  # Implementation may return None if no global config
            assert isinstance(config, ProjectConfig)

    def test_save_global_config_contract(
        self,
        config_service: ConfigService,
        sample_project_config: ProjectConfig,
        monkeypatch,
        tmp_path: Path,
    ):
        """Test save_global_config method contract"""
        temp_home = tmp_path / "test_home_save"
        monkeypatch.setenv("HOME", str(temp_home))

        result = config_service.save_global_config(sample_project_config)
        assert isinstance(result, bool)

    def test_get_merged_config_contract(
        self, config_service: ConfigService, project_with_config: Path
    ):
        """Test get_merged_config method contract"""
        config = config_service.get_merged_config(project_with_config)
        assert isinstance(config, ProjectConfig)
        assert config.name == "test-project"

        # Should work even for projects without config (uses defaults)
        empty_project = project_with_config.parent / "empty"
        empty_project.mkdir()
        config = config_service.get_merged_config(empty_project)
        assert isinstance(config, ProjectConfig)

    def test_validate_branch_pattern_contract(self, config_service: ConfigService):
        """Test validate_branch_pattern method contract"""
        # Test valid patterns
        patterns = [
            "feature/{feature-name}",
            "{type}/{name}",
            "simple-branch",
            "{prefix}-{suffix}",
        ]

        for pattern in patterns:
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert isinstance(is_valid, bool)
            assert error is None or isinstance(error, str)

        # Test invalid patterns
        invalid_patterns = ["{unclosed", "invalid{char}", "", "{}"]

        for pattern in invalid_patterns:
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert isinstance(is_valid, bool)
            if not is_valid:
                assert isinstance(error, str)

    def test_expand_branch_name_contract(self, config_service: ConfigService):
        """Test expand_branch_name method contract"""
        # Test simple expansion
        pattern = "feature/{feature-name}"
        context = {"feature-name": "auth-system"}
        result = config_service.expand_branch_name(pattern, context)
        assert isinstance(result, str)
        assert result == "feature/auth-system"

        # Test multiple variables
        pattern = "{type}/{name}-{version}"
        context = {"type": "feature", "name": "api", "version": "v2"}
        result = config_service.expand_branch_name(pattern, context)
        assert isinstance(result, str)
        assert "feature" in result and "api" in result and "v2" in result

        # Test missing variables (should handle gracefully)
        pattern = "feature/{missing-var}"
        context = {"other-var": "value"}
        result = config_service.expand_branch_name(pattern, context)
        assert isinstance(result, str)  # Should not crash

    def test_backup_config_contract(
        self, config_service: ConfigService, project_with_config: Path
    ):
        """Test backup_config method contract"""
        backup_path = config_service.backup_config(project_with_config)
        assert isinstance(backup_path, Path)
        assert backup_path.exists()
        assert backup_path.suffix in [".toml", ".bak", ".backup"]

        # Test backup of non-existent config
        empty_project = project_with_config.parent / "empty"
        empty_project.mkdir()
        backup_path = config_service.backup_config(empty_project)
        # Should handle gracefully - return valid path or raise appropriate exception

    def test_restore_config_contract(
        self, config_service: ConfigService, project_with_config: Path
    ):
        """Test restore_config method contract"""
        # Create backup first
        backup_path = config_service.backup_config(project_with_config)

        # Modify original config
        config_file = project_with_config / ".specify" / "config.toml"
        config_file.write_text("[modified]\ntest = true")

        # Restore from backup
        result = config_service.restore_config(project_with_config, backup_path)
        assert isinstance(result, bool)

        if result:  # If restore succeeded
            # Verify config was restored
            restored_config = config_service.load_project_config(project_with_config)
            assert restored_config is not None
            assert restored_config.name == "test-project"


class TestConfigServiceIntegration:
    """Integration tests for ConfigService workflow"""

    @pytest.fixture
    def config_service(self) -> ConfigService:
        """Create ConfigService instance"""
        from specify_cli.services.config_service import TomlConfigService

        return TomlConfigService()

    def test_full_config_workflow(self, config_service: ConfigService, tmp_path: Path):
        """Test complete configuration workflow"""
        project_dir = tmp_path / "workflow-test"
        project_dir.mkdir()

        # Create and save config
        config = ProjectConfig(
            name="workflow-test",
            branch_naming=BranchNamingConfig(
                default_pattern="task/{task-name}",
                patterns=["task/{task-name}", "feature/{feature-name}"],
            ),
            template_settings=TemplateConfig(
                ai_assistant="claude",
                custom_templates_dir=None,
                template_cache_enabled=True,
                template_variables={"workflow": "test"},
            ),
        )

        # Save config
        assert config_service.save_project_config(project_dir, config)

        # Load and verify
        loaded_config = config_service.load_project_config(project_dir)
        assert loaded_config is not None
        assert loaded_config.name == "workflow-test"

        # Test branch expansion
        expanded = config_service.expand_branch_name(
            loaded_config.branch_naming.default_pattern, {"task-name": "setup-tests"}
        )
        assert expanded == "task/setup-tests"

        # Test backup and restore
        backup_path = config_service.backup_config(project_dir)
        assert backup_path.exists()

        # Test merged config
        merged_config = config_service.get_merged_config(project_dir)
        assert merged_config.name == "workflow-test"
