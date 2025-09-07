"""
Integration test for branch naming patterns workflow (T012)
"""

from pathlib import Path
from typing import Any, Dict, List

import pytest

from specify_cli.models.config import BranchNamingConfig, ProjectConfig, TemplateConfig
from specify_cli.services.config_service import ConfigService


class TestBranchNamingPatterns:
    """Integration tests for end-to-end branch naming pattern workflows"""

    @pytest.fixture
    def config_service(self) -> ConfigService:
        """Create ConfigService instance"""
        from specify_cli.services.config_service import TomlConfigService

        return TomlConfigService()

    @pytest.fixture
    def project_with_branch_config(self, tmp_path: Path) -> Path:
        """Create project with comprehensive branch naming configuration"""
        project_dir = tmp_path / "branch_test_project"
        project_dir.mkdir()

        config_dir = project_dir / ".specify"
        config_dir.mkdir()

        config_file = config_dir / "config.toml"
        config_file.write_text("""
[project]
name = "branch-test-project"

[project.branch_naming]
default_pattern = "feature/{feature-name}"
patterns = [
    "feature/{feature-name}",
    "bugfix/{bug-id}",
    "hotfix/{version}",
    "task/{task-id}",
    "epic/{epic-name}"
]

[project.template_settings]
ai_assistant = "claude"
template_cache_enabled = true
""")
        return project_dir

    def test_branch_pattern_validation_workflow(self, config_service: ConfigService):
        """Test comprehensive branch pattern validation workflow"""
        # Test valid patterns covering different spec-kit scenarios
        valid_patterns = [
            # Basic patterns
            "feature/{feature-name}",
            "bugfix/{bug-id}",
            "hotfix/{version}",
            # Task-based patterns
            "task/{task-id}",
            "task/{task-name}",
            # Multi-level patterns
            "feature/{epic}/{feature-name}",
            "team/{team-name}/{feature-name}",
            # Descriptive patterns
            "bugfix/{bug-id}-{description}",
            "feature/{feature-name}-{version}",
            # Simple patterns
            "main",
            "develop",
            "staging",
            # Custom type patterns
            "research/{topic}",
            "prototype/{name}",
            "docs/{section}",
        ]

        for pattern in valid_patterns:
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert isinstance(is_valid, bool), (
                f"Validation failed for pattern: {pattern}"
            )
            if not is_valid:
                pytest.fail(f"Expected valid pattern '{pattern}' was invalid: {error}")

        # Test invalid patterns
        invalid_patterns = [
            "",  # Empty
            " ",  # Whitespace only
            "{unclosed",  # Unclosed variable
            "unclosed}",  # Unopened variable
            "{{double}}",  # Double braces
            "spaces in branch",  # Spaces
            "UPPERCASE",  # Uppercase
            "dots.in.name",  # Dots
            "/leading-slash",  # Leading slash
            "trailing-slash/",  # Trailing slash
            "double//slash",  # Double slashes
            "branch:with:colons",  # Colons
            "branch\\with\\backslashes",  # Backslashes
        ]

        for pattern in invalid_patterns:
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert isinstance(is_valid, bool)
            if is_valid:
                pytest.fail(f"Expected invalid pattern '{pattern}' was marked as valid")
            assert isinstance(error, str)
            assert len(error) > 0

    def test_branch_name_expansion_workflows(self, config_service: ConfigService):
        """Test branch name expansion for different spec-kit workflows"""
        # Feature development workflow
        feature_cases: List[Dict[str, Any]] = [
            {
                "pattern": "feature/{feature-name}",
                "context": {"feature-name": "user-authentication"},
                "expected": "feature/user-authentication",
            },
            {
                "pattern": "feature/{epic}/{feature-name}",
                "context": {"epic": "user-management", "feature-name": "login"},
                "expected": "feature/user-management/login",
            },
            {
                "pattern": "feature/{feature-name}-{version}",
                "context": {"feature-name": "api-redesign", "version": "v2"},
                "expected": "feature/api-redesign-v2",
            },
        ]

        # Bug fixing workflow
        bugfix_cases: List[Dict[str, Any]] = [
            {
                "pattern": "bugfix/{bug-id}",
                "context": {"bug-id": "BUG-123"},
                "expected": "bugfix/BUG-123",
            },
            {
                "pattern": "bugfix/{bug-id}-{description}",
                "context": {"bug-id": "BUG-456", "description": "login-error"},
                "expected": "bugfix/BUG-456-login-error",
            },
        ]

        # Task-based workflow
        task_cases: List[Dict[str, Any]] = [
            {
                "pattern": "task/{task-id}",
                "context": {"task-id": "TASK-789"},
                "expected": "task/TASK-789",
            },
            {
                "pattern": "task/{task-name}",
                "context": {"task-name": "setup-ci"},
                "expected": "task/setup-ci",
            },
        ]

        # Hotfix workflow
        hotfix_cases: List[Dict[str, Any]] = [
            {
                "pattern": "hotfix/{version}",
                "context": {"version": "1.2.3"},
                "expected": "hotfix/1.2.3",
            },
            {
                "pattern": "hotfix/v{version}-{patch}",
                "context": {"version": "2.1.0", "patch": "security"},
                "expected": "hotfix/v2.1.0-security",
            },
        ]

        # Test all workflow cases
        all_cases = feature_cases + bugfix_cases + task_cases + hotfix_cases

        for case in all_cases:
            result = config_service.expand_branch_name(case["pattern"], case["context"])
            assert isinstance(result, str)
            assert result == case["expected"], (
                f"Pattern: {case['pattern']}, Context: {case['context']}, Expected: {case['expected']}, Got: {result}"
            )

    def test_branch_pattern_configuration_workflow(
        self, config_service: ConfigService, tmp_path: Path
    ):
        """Test complete branch pattern configuration workflow"""
        project_dir = tmp_path / "config_workflow_test"
        project_dir.mkdir()

        # Create configuration with various patterns
        config = ProjectConfig(
            name="config-workflow-test",
            branch_naming=BranchNamingConfig(
                default_pattern="feature/{feature-name}",
                patterns=[
                    "feature/{feature-name}",
                    "bugfix/{bug-id}",
                    "hotfix/{version}",
                    "task/{task-id}",
                    "epic/{epic-name}/{feature-name}",
                    "team/{team}/{task-name}",
                ],
            ),
            template_settings=TemplateConfig(
                ai_assistant="claude",
                custom_templates_dir=None,
                template_cache_enabled=True,
                template_variables={},
            ),
        )

        # Save configuration
        save_result = config_service.save_project_config(project_dir, config)
        assert save_result is True

        # Load configuration back
        loaded_config = config_service.load_project_config(project_dir)
        assert loaded_config is not None

        # Verify patterns are preserved
        assert loaded_config.branch_naming.default_pattern == "feature/{feature-name}"
        assert len(loaded_config.branch_naming.patterns) == 6
        assert "epic/{epic-name}/{feature-name}" in loaded_config.branch_naming.patterns

        # Test pattern validation for loaded patterns
        for pattern in loaded_config.branch_naming.patterns:
            is_valid, error = config_service.validate_branch_pattern(pattern)
            assert is_valid, f"Loaded pattern '{pattern}' should be valid: {error}"

        # Test expansion for loaded patterns
        test_expansions = [
            (
                loaded_config.branch_naming.default_pattern,
                {"feature-name": "test"},
                "feature/test",
            ),
            (
                "epic/{epic-name}/{feature-name}",
                {"epic-name": "user-auth", "feature-name": "login"},
                "epic/user-auth/login",
            ),
            (
                "team/{team}/{task-name}",
                {"team": "backend", "task-name": "api-refactor"},
                "team/backend/api-refactor",
            ),
        ]

        for pattern, context, expected in test_expansions:
            result = config_service.expand_branch_name(pattern, context)
            assert result == expected

    def test_branch_naming_edge_cases_workflow(self, config_service: ConfigService):
        """Test edge cases in branch naming workflow"""
        # Test empty context
        result = config_service.expand_branch_name("feature/{feature-name}", {})
        assert isinstance(result, str)
        # Implementation should handle missing variables gracefully

        # Test extra variables in context
        result = config_service.expand_branch_name(
            "feature/{feature-name}",
            {"feature-name": "test", "extra-var": "ignored", "another": "value"},
        )
        assert result == "feature/test"

        # Test special characters in variable values
        special_char_cases: List[Dict[str, Any]] = [
            {
                "pattern": "feature/{feature-name}",
                "context": {"feature-name": "api-v2"},
                "expected": "feature/api-v2",
            },
            {
                "pattern": "bugfix/{bug-id}",
                "context": {"bug-id": "BUG_123"},
                "expected": "bugfix/BUG_123",
            },
            {
                "pattern": "task/{task-name}",
                "context": {"task-name": "setup-environment"},
                "expected": "task/setup-environment",
            },
        ]

        for case in special_char_cases:
            result = config_service.expand_branch_name(case["pattern"], case["context"])
            assert result == case["expected"]

    def test_branch_naming_integration_with_templates(
        self, config_service: ConfigService, tmp_path: Path
    ):
        """Test branch naming integration with template configuration"""
        project_dir = tmp_path / "template_integration"
        project_dir.mkdir()

        # Create config with template variables that could be used in branch names
        config = ProjectConfig(
            name="template-integration",
            branch_naming=BranchNamingConfig(
                default_pattern="feature/{feature-name}",
                patterns=["feature/{feature-name}", "team/{team-name}/{task}"],
            ),
            template_settings=TemplateConfig(
                ai_assistant="claude",
                custom_templates_dir=None,
                template_cache_enabled=True,
                template_variables={
                    "team": "development-team",
                    "project": "spec-kit",
                    "version": "1.0.0",
                },
            ),
        )

        config_service.save_project_config(project_dir, config)
        config_service.load_project_config(project_dir)

        # Test that template variables don't interfere with branch naming
        branch_result = config_service.expand_branch_name(
            "feature/{feature-name}", {"feature-name": "template-integration"}
        )
        assert branch_result == "feature/template-integration"

        # Test branch pattern that could use template-like syntax
        branch_result = config_service.expand_branch_name(
            "team/{team-name}/{task}", {"team-name": "backend", "task": "refactor"}
        )
        assert branch_result == "team/backend/refactor"

    def test_complex_branch_naming_scenarios(self, config_service: ConfigService):
        """Test complex real-world branch naming scenarios"""
        # Multi-team development scenarios
        team_scenarios: List[Dict[str, Any]] = [
            {
                "pattern": "team/{team}/feature/{feature}",
                "context": {"team": "frontend", "feature": "user-dashboard"},
                "expected": "team/frontend/feature/user-dashboard",
            },
            {
                "pattern": "team/{team}/bugfix/{bug-id}",
                "context": {"team": "backend", "bug-id": "API-456"},
                "expected": "team/backend/bugfix/API-456",
            },
        ]

        # Release management scenarios
        release_scenarios: List[Dict[str, Any]] = [
            {
                "pattern": "release/{version}/feature/{feature}",
                "context": {"version": "2.0", "feature": "new-api"},
                "expected": "release/2.0/feature/new-api",
            },
            {
                "pattern": "release/{version}/hotfix/{patch}",
                "context": {"version": "1.5", "patch": "security"},
                "expected": "release/1.5/hotfix/security",
            },
        ]

        # Epic-based development scenarios
        epic_scenarios: List[Dict[str, Any]] = [
            {
                "pattern": "epic/{epic}/story/{story}",
                "context": {"epic": "user-management", "story": "login-flow"},
                "expected": "epic/user-management/story/login-flow",
            },
            {
                "pattern": "epic/{epic}/task/{task-id}",
                "context": {"epic": "payment-system", "task-id": "TASK-789"},
                "expected": "epic/payment-system/task/TASK-789",
            },
        ]

        all_scenarios = team_scenarios + release_scenarios + epic_scenarios

        for scenario in all_scenarios:
            # Validate pattern first
            is_valid, error = config_service.validate_branch_pattern(
                scenario["pattern"]
            )
            assert is_valid, (
                f"Pattern should be valid: {scenario['pattern']}, Error: {error}"
            )

            # Test expansion
            result = config_service.expand_branch_name(
                scenario["pattern"], scenario["context"]
            )
            assert result == scenario["expected"], f"Scenario failed: {scenario}"
