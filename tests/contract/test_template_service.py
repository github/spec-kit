"""
Contract tests for TemplateService interface
"""

from pathlib import Path

import pytest

from specify_cli.models.project import TemplateContext, TemplateFile
from specify_cli.services.template_service import TemplateService


class TestTemplateServiceContract:
    """Test contract compliance for TemplateService interface"""

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance for testing"""
        # This will fail until implementation exists
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    @pytest.fixture
    def sample_context(self) -> TemplateContext:
        """Create sample template context"""
        return TemplateContext(
            project_name="test-project",
            ai_assistant="claude",
            branch_type="feature",
            feature_name="auth-system",
            additional_vars={"author": "test-user", "version": "1.0.0"},
        )

    @pytest.fixture
    def temp_template_dir(self, tmp_path: Path) -> Path:
        """Create temporary template directory structure"""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create sample template files
        (template_dir / "readme.md.j2").write_text(
            "# {{ project_name }}\n\nAuthor: {{ author }}\nAI: {{ ai_assistant }}"
        )
        (template_dir / "config.toml.j2").write_text(
            '[project]\nname = "{{ project_name }}"\nversion = "{{ version }}"'
        )

        return template_dir

    def test_load_template_package_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ):
        """Test load_template_package method contract"""
        # Test successful loading
        result = template_service.load_template_package("claude", temp_template_dir)
        assert isinstance(result, bool)
        assert result is True

        # Test invalid assistant
        result = template_service.load_template_package("invalid-ai", temp_template_dir)
        assert isinstance(result, bool)

        # Test non-existent directory
        result = template_service.load_template_package(
            "claude", temp_template_dir / "nonexistent"
        )
        assert isinstance(result, bool)
        assert result is False

    def test_render_template_contract(
        self,
        template_service: TemplateService,
        sample_context: TemplateContext,
        temp_template_dir: Path,
    ):
        """Test render_template method contract"""
        # Load templates first
        template_service.load_template_package("claude", temp_template_dir)

        # Test successful rendering
        result = template_service.render_template("readme.md.j2", sample_context)
        assert isinstance(result, str)
        assert "test-project" in result
        assert "claude" in result

        # Test non-existent template
        with pytest.raises(FileNotFoundError):
            template_service.render_template("nonexistent.j2", sample_context)

    def test_render_project_templates_contract(
        self,
        template_service: TemplateService,
        sample_context: TemplateContext,
        temp_template_dir: Path,
        tmp_path: Path,
    ):
        """Test render_project_templates method contract"""
        # Load templates first
        template_service.load_template_package("claude", temp_template_dir)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Test rendering all templates
        result = template_service.render_project_templates(sample_context, output_dir)
        assert isinstance(result, list)
        assert len(result) > 0

        for template_file in result:
            assert isinstance(template_file, TemplateFile)
            assert hasattr(template_file, "template_path")
            assert hasattr(template_file, "output_path")
            assert hasattr(template_file, "content")
            assert hasattr(template_file, "is_executable")
            assert isinstance(template_file.content, str)
            assert isinstance(template_file.is_executable, bool)

    def test_validate_template_syntax_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ):
        """Test validate_template_syntax method contract"""
        valid_template = temp_template_dir / "readme.md.j2"

        # Test valid template
        is_valid, error = template_service.validate_template_syntax(valid_template)
        assert isinstance(is_valid, bool)
        assert is_valid is True
        assert error is None or isinstance(error, str)

        # Test invalid template
        invalid_template = temp_template_dir / "invalid.j2"
        invalid_template.write_text("{{ unclosed_var")

        is_valid, error = template_service.validate_template_syntax(invalid_template)
        assert isinstance(is_valid, bool)
        assert is_valid is False
        assert isinstance(error, str)

        # Test non-existent template
        is_valid, error = template_service.validate_template_syntax(
            temp_template_dir / "nonexistent.j2"
        )
        assert isinstance(is_valid, bool)
        assert is_valid is False
        assert isinstance(error, str)

    def test_get_template_variables_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ):
        """Test get_template_variables method contract"""
        template_path = temp_template_dir / "readme.md.j2"

        variables = template_service.get_template_variables(template_path)
        assert isinstance(variables, list)
        assert all(isinstance(var, str) for var in variables)

        # Should find variables from our test template
        expected_vars = {"project_name", "author", "ai_assistant"}
        found_vars = set(variables)
        assert expected_vars.issubset(found_vars)

    def test_set_custom_template_dir_contract(
        self, template_service: TemplateService, temp_template_dir: Path
    ):
        """Test set_custom_template_dir method contract"""
        # Test setting valid directory
        result = template_service.set_custom_template_dir(temp_template_dir)
        assert isinstance(result, bool)
        assert result is True

        # Test resetting to None
        result = template_service.set_custom_template_dir(None)
        assert isinstance(result, bool)
        assert result is True

        # Test invalid directory
        result = template_service.set_custom_template_dir(
            temp_template_dir / "nonexistent"
        )
        assert isinstance(result, bool)
        assert result is False


class TestTemplateServiceIntegration:
    """Integration tests for TemplateService workflow"""

    @pytest.fixture
    def template_service(self) -> TemplateService:
        """Create TemplateService instance"""
        from specify_cli.services.template_service import JinjaTemplateService

        return JinjaTemplateService()

    def test_full_template_workflow(
        self, template_service: TemplateService, tmp_path: Path
    ):
        """Test complete template processing workflow"""
        # Setup
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        (template_dir / "project.md.j2").write_text(
            "# {{ project_name }}\n\nFeature: {{ feature_name }}\nBranch: {{ branch_type }}/{{ feature_name }}"
        )

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        context = TemplateContext(
            project_name="integration-test",
            ai_assistant="claude",
            branch_type="feature",
            feature_name="integration",
            additional_vars={},
        )

        # Workflow: load -> validate -> render
        assert template_service.load_template_package("claude", template_dir)

        template_path = template_dir / "project.md.j2"
        is_valid, _ = template_service.validate_template_syntax(template_path)
        assert is_valid

        content = template_service.render_template("project.md.j2", context)
        assert "integration-test" in content
        assert "feature/integration" in content

        # Test batch rendering
        templates = template_service.render_project_templates(context, output_dir)
        assert len(templates) >= 1
        assert any("project.md" in tf.output_path for tf in templates)
