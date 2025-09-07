"""
Integration test for TOML configuration loading workflow (T010)
These tests MUST FAIL initially - services don't exist yet (TDD approach)
"""
import pytest
from pathlib import Path
from typing import Dict, Any

# These imports WILL FAIL initially - this is expected in TDD
from specify_cli.services.config_service import ConfigService
from specify_cli.models.config import ProjectConfig, BranchNamingConfig, TemplateConfig


class TestTOMLConfigurationLoading:
    """Integration tests for end-to-end TOML configuration loading and management"""
    
    @pytest.fixture
    def config_service(self) -> ConfigService:
        """Create ConfigService instance"""
        from specify_cli.services.config_service import TomlConfigService
        return TomlConfigService()
    
    @pytest.fixture
    def complex_project_structure(self, tmp_path: Path) -> Path:
        """Create complex project structure with nested configs"""
        project_root = tmp_path / "complex_project"
        project_root.mkdir()
        
        # Main project config
        main_config_dir = project_root / ".specify"
        main_config_dir.mkdir()
        
        main_config = main_config_dir / "config.toml"
        main_config.write_text("""
# Project configuration for spec-kit integration testing

[project]
name = "complex-spec-project"

[project.branch_naming]
default_pattern = "feature/{feature-name}"
patterns = [
    "feature/{feature-name}",
    "bugfix/{bug-id}-{description}", 
    "hotfix/v{version}",
    "epic/{epic-name}",
    "task/{task-id}"
]


[project.template_settings]
ai_assistant = "claude"
custom_templates_dir = "./custom_templates"
template_cache_enabled = true

[project.template_settings.template_variables]
team = "spec-development-team"
organization = "spec-kit"
license = "MIT"
author = "Integration Test Suite"
""")
        
        # Global user config  
        global_config_dir = tmp_path / "global_config" / ".specify"
        global_config_dir.mkdir(parents=True)
        
        global_config = global_config_dir / "config.toml"
        global_config.write_text("""
# Global user configuration for spec-kit

[project]
name = "default-project"

[project.branch_naming]
default_pattern = "task/{task-name}"
patterns = ["task/{task-name}", "feature/{feature-name}"]

[project.template_settings]
ai_assistant = "claude"
template_cache_enabled = false

[project.template_settings.template_variables]
author = "Global Test User"
team = "default-team"
organization = "user-org"
""")
        
        # Override config (simulates local overrides)
        override_config = main_config_dir / "local.toml"
        override_config.write_text("""
# Local development overrides

[project.template_settings]
template_cache_enabled = false  # Override for local dev

[project.template_settings.template_variables]
author = "Local Dev User"  # Override global setting
environment = "development"
""")
        
        return project_root, global_config_dir.parent

    def test_complex_configuration_loading(self, config_service: ConfigService, complex_project_structure: tuple):
        """Test loading complex nested TOML configuration"""
        project_root, global_root = complex_project_structure
        
        # Mock global config location
        import os
        os.environ['SPEC_KIT_GLOBAL_CONFIG'] = str(global_root)
        
        try:
            # Load project configuration
            config = config_service.load_project_config(project_root)
            assert config is not None
            assert isinstance(config, ProjectConfig)
            
            # Verify main project settings
            assert config.name == "complex-spec-project"
            
            # Verify branch naming configuration
            assert isinstance(config.branch_naming, BranchNamingConfig)
            assert config.branch_naming.default_pattern == "feature/{feature-name}"
            assert len(config.branch_naming.patterns) == 5
            assert "bugfix/{bug-id}-{description}" in config.branch_naming.patterns
            assert "hotfix/v{version}" in config.branch_naming.patterns
            
            # Verify patterns include various branch types
            assert "epic/{epic-name}" in config.branch_naming.patterns
            assert "task/{task-id}" in config.branch_naming.patterns
            
            # Verify template settings
            assert isinstance(config.template_settings, TemplateConfig)
            assert config.template_settings.ai_assistant == "claude"
            assert config.template_settings.custom_templates_dir == "./custom_templates"
            assert config.template_settings.template_cache_enabled is True
            
            # Verify template variables
            assert config.template_settings.template_variables["team"] == "spec-development-team"
            assert config.template_settings.template_variables["organization"] == "spec-kit"
            assert config.template_settings.template_variables["author"] == "Integration Test Suite"
            
        finally:
            if 'SPEC_KIT_GLOBAL_CONFIG' in os.environ:
                del os.environ['SPEC_KIT_GLOBAL_CONFIG']

    def test_global_configuration_loading(self, config_service: ConfigService, complex_project_structure: tuple):
        """Test loading global user configuration"""
        project_root, global_root = complex_project_structure
        
        import os
        os.environ['HOME'] = str(global_root)
        
        try:
            # Load global configuration
            global_config = config_service.load_global_config()
            
            if global_config is not None:  # Implementation may return None
                assert isinstance(global_config, ProjectConfig)
                assert global_config.template_settings.ai_assistant == "claude"
                assert global_config.template_settings.template_variables["author"] == "Global Test User"
                assert global_config.template_settings.template_variables["organization"] == "user-org"
                
        finally:
            if 'HOME' in os.environ:
                del os.environ['HOME']

    def test_merged_configuration_loading(self, config_service: ConfigService, complex_project_structure: tuple):
        """Test merged configuration with global and project settings"""
        project_root, global_root = complex_project_structure
        
        import os
        os.environ['HOME'] = str(global_root)
        
        try:
            # Get merged configuration
            merged_config = config_service.get_merged_config(project_root)
            assert isinstance(merged_config, ProjectConfig)
            
            # Project settings should override global settings
            assert merged_config.name == "complex-spec-project"
            assert merged_config.branch_naming.default_pattern == "feature/{feature-name}"
            
            # Should have project-specific template variables
            assert merged_config.template_settings.template_variables["team"] == "spec-development-team"
            assert merged_config.template_settings.template_variables["organization"] == "spec-kit"
            
        finally:
            if 'HOME' in os.environ:
                del os.environ['HOME']

    def test_configuration_validation_workflow(self, config_service: ConfigService):
        """Test configuration validation in complete workflow"""
        # Test valid branch patterns
        valid_patterns = [
            "feature/{feature-name}",
            "bugfix/{bug-id}-{description}",
            "hotfix/v{version}", 
            "task/{task-id}",
            "{type}/{name}",
            "simple-branch-name"
        ]
        
        for pattern in valid_patterns:
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert isinstance(is_valid, bool), f"Pattern validation failed for: {pattern}"
            if not is_valid:
                pytest.fail(f"Expected valid pattern '{pattern}' was invalid: {error}")
        
        # Test invalid branch patterns
        invalid_patterns = [
            "",
            " ",
            "{unclosed",
            "unclosed}",
            "{{double-open}",
            "{double-close}}",
            "spaces in name",
            "UPPERCASE",
            "dots.in.name",
            "/leading-slash",
            "trailing-slash/",
            "double//slash"
        ]
        
        for pattern in invalid_patterns:
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert isinstance(is_valid, bool)
            if is_valid:
                pytest.fail(f"Expected invalid pattern '{pattern}' was marked as valid")
            assert isinstance(error, str)
            assert len(error) > 0

    def test_branch_name_expansion_workflow(self, config_service: ConfigService):
        """Test branch name expansion with various patterns and contexts"""
        test_cases = [
            {
                "pattern": "feature/{feature-name}",
                "context": {"feature-name": "user-authentication"},
                "expected": "feature/user-authentication"
            },
            {
                "pattern": "bugfix/{bug-id}-{description}",
                "context": {"bug-id": "BUG-123", "description": "login-error"},
                "expected": "bugfix/BUG-123-login-error"
            },
            {
                "pattern": "hotfix/v{version}",
                "context": {"version": "1.2.3"},
                "expected": "hotfix/v1.2.3"
            },
            {
                "pattern": "{type}/{name}-{iteration}",
                "context": {"type": "prototype", "name": "api-redesign", "iteration": "v2"},
                "expected": "prototype/api-redesign-v2"
            },
            {
                "pattern": "task/{task-id}",
                "context": {"task-id": "TASK-456"},
                "expected": "task/TASK-456"
            }
        ]
        
        for case in test_cases:
            result = config_service.expand_branch_name(case["pattern"], case["context"])
            assert isinstance(result, str)
            assert result == case["expected"], f"Pattern: {case['pattern']}, Context: {case['context']}, Expected: {case['expected']}, Got: {result}"

    def test_configuration_persistence_workflow(self, config_service: ConfigService, tmp_path: Path):
        """Test complete configuration save/load/backup/restore workflow"""
        project_dir = tmp_path / "persistence_test"
        project_dir.mkdir()
        
        # Create test configuration
        test_config = ProjectConfig(
            name="persistence-test",
            branch_naming=BranchNamingConfig(
                default_pattern="workflow/{workflow-name}",
                patterns=["workflow/{workflow-name}", "test/{test-type}", "migrate/{version}"]
            ),
            template_settings=TemplateConfig(
                ai_assistant="claude",
                custom_templates_dir="./templates",
                template_cache_enabled=True,
                template_variables={
                    "persistence": "test",
                    "workflow": "config-management"
                }
            )
        )
        
        # Save configuration
        save_result = config_service.save_project_config(project_dir, test_config)
        assert save_result is True
        
        # Verify config file exists
        config_file = project_dir / ".specify" / "config.toml"
        assert config_file.exists()
        
        # Load configuration back
        loaded_config = config_service.load_project_config(project_dir)
        assert loaded_config is not None
        assert loaded_config.name == "persistence-test"
        assert loaded_config.branch_naming.default_pattern == "workflow/{workflow-name}"
        assert loaded_config.template_settings.template_variables["persistence"] == "test"
        
        # Create backup
        backup_path = config_service.backup_config(project_dir)
        assert isinstance(backup_path, Path)
        assert backup_path.exists()
        
        # Modify original configuration
        modified_config = ProjectConfig(
            name="modified-test",
            branch_naming=BranchNamingConfig(
                default_pattern="modified/{name}",
                patterns=["modified/{name}"],
            ),
            template_settings=TemplateConfig(
                ai_assistant="gemini",
                custom_templates_dir=None,
                template_cache_enabled=False,
                template_variables={"modified": "true"}
            )
        )
        
        save_result = config_service.save_project_config(project_dir, modified_config)
        assert save_result is True
        
        # Verify modification
        modified_loaded = config_service.load_project_config(project_dir)
        assert modified_loaded.name == "modified-test"
        assert modified_loaded.template_settings.ai_assistant == "gemini"
        
        # Restore from backup
        restore_result = config_service.restore_config(project_dir, backup_path)
        if restore_result:  # Only check if restore succeeded
            restored_config = config_service.load_project_config(project_dir)
            assert restored_config.name == "persistence-test"
            assert restored_config.branch_naming.default_pattern == "workflow/{workflow-name}"

    def test_configuration_error_handling(self, config_service: ConfigService, tmp_path: Path):
        """Test configuration error handling and edge cases"""
        # Test missing configuration directory
        empty_project = tmp_path / "empty_project"
        empty_project.mkdir()
        
        config = config_service.load_project_config(empty_project)
        assert config is None
        
        # Test corrupted TOML file
        corrupted_project = tmp_path / "corrupted_project"
        corrupted_project.mkdir()
        config_dir = corrupted_project / ".specify"
        config_dir.mkdir()
        
        corrupted_config = config_dir / "config.toml"
        corrupted_config.write_text("""
[project
name = "missing-bracket"
invalid toml content
""")
        
        # Should handle corrupted file gracefully
        config = config_service.load_project_config(corrupted_project)
        # Implementation may return None or raise exception - both are acceptable

    def test_complex_branch_pattern_workflow(self, config_service: ConfigService):
        """Test complex branch pattern validation and expansion scenarios"""
        # Test nested variable substitution
        complex_patterns = {
            "epic/{epic-name}/feature/{feature-name}": {
                "context": {"epic-name": "user-management", "feature-name": "login"},
                "expected": "epic/user-management/feature/login"
            },
            "release/{version}/hotfix/{hotfix-id}": {
                "context": {"version": "2.1.0", "hotfix-id": "security-patch"},
                "expected": "release/2.1.0/hotfix/security-patch"
            },
            "{team}/{developer}/{task-type}-{task-id}": {
                "context": {
                    "team": "backend",
                    "developer": "alice",
                    "task-type": "bugfix",
                    "task-id": "AUTH-789"
                },
                "expected": "backend/alice/bugfix-AUTH-789"
            }
        }
        
        for pattern, test_data in complex_patterns.items():
            # Validate pattern
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert is_valid, f"Pattern should be valid: {pattern}, Error: {error}"
            
            # Expand pattern
            result = config_service.expand_branch_name(pattern, test_data["context"])
            assert result == test_data["expected"], f"Pattern: {pattern}, Expected: {test_data['expected']}, Got: {result}"