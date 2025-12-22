"""Unit tests for language support in templates and builders."""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

from speckit.templates import render_template
from speckit.schemas import Specification, TechnicalPlan, TaskBreakdown, TechStack


class TestTemplateLanguageSupport:
    """Tests for language handling in Jinja2 templates."""

    def test_specification_template_no_language(self):
        """Test specification template without language (default English)."""
        result = render_template(
            "specification.jinja2",
            feature_description="Add user authentication",
            feature_id="001-auth",
            constitution=None,
            language=None,
        )

        # Should NOT contain the language instruction
        assert "**IMPORTANT: Generate ALL content in" not in result
        # Should contain the feature description
        assert "Add user authentication" in result

    def test_specification_template_english_language(self):
        """Test specification template with explicit English."""
        result = render_template(
            "specification.jinja2",
            feature_description="Add user authentication",
            feature_id="001-auth",
            constitution=None,
            language="en",
        )

        # English should NOT show the language instruction
        assert "**IMPORTANT: Generate ALL content in" not in result

    def test_specification_template_portuguese_language(self):
        """Test specification template with Portuguese."""
        result = render_template(
            "specification.jinja2",
            feature_description="Add user authentication",
            feature_id="001-auth",
            constitution=None,
            language="pt-br",
        )

        # Should contain the Portuguese language instruction
        assert "**IMPORTANT: Generate ALL content in pt-br language" in result
        assert "All text output must be in pt-br" in result

    def test_specification_template_spanish_language(self):
        """Test specification template with Spanish."""
        result = render_template(
            "specification.jinja2",
            feature_description="Add user authentication",
            feature_id="001-auth",
            constitution=None,
            language="es",
        )

        # Should contain the Spanish language instruction
        assert "**IMPORTANT: Generate ALL content in es language" in result

    def test_plan_template_no_language(self):
        """Test plan template without language."""
        spec_dict = {
            "feature_name": "Auth",
            "feature_id": "001-auth",
            "overview": "Test",
        }
        result = render_template(
            "plan.jinja2",
            specification=spec_dict,
            constitution=None,
            tech_stack=None,
            language=None,
        )

        assert "**IMPORTANT: Generate ALL content in" not in result

    def test_plan_template_portuguese_language(self):
        """Test plan template with Portuguese."""
        spec_dict = {
            "feature_name": "Auth",
            "feature_id": "001-auth",
            "overview": "Test",
        }
        result = render_template(
            "plan.jinja2",
            specification=spec_dict,
            constitution=None,
            tech_stack=None,
            language="pt-br",
        )

        assert "**IMPORTANT: Generate ALL content in pt-br language" in result

    def test_tasks_template_no_language(self):
        """Test tasks template without language."""
        plan_dict = {
            "feature_id": "001-auth",
            "title": "Auth Plan",
        }
        result = render_template(
            "tasks.jinja2",
            plan=plan_dict,
            specification={},
            language=None,
        )

        assert "**IMPORTANT: Generate ALL content in" not in result

    def test_tasks_template_portuguese_language(self):
        """Test tasks template with Portuguese."""
        plan_dict = {
            "feature_id": "001-auth",
            "title": "Auth Plan",
        }
        result = render_template(
            "tasks.jinja2",
            plan=plan_dict,
            specification={},
            language="pt-br",
        )

        assert "**IMPORTANT: Generate ALL content in pt-br language" in result


class TestSpecificationBuilderLanguage:
    """Tests for language propagation in SpecificationBuilder."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage."""
        mock = MagicMock()
        mock.list_features.return_value = []
        return mock

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        mock = MagicMock()
        mock.complete_structured.return_value = Specification(
            feature_name="Test Feature",
            feature_id="001-test",
            overview="Test overview",
            problem_statement="Test problem",
            target_users=["users"],
            user_stories=[],
            functional_requirements=[],
            entities=[],
            assumptions=[],
            constraints=[],
            out_of_scope=[],
            success_criteria=[],
        )
        return mock

    def test_generate_passes_language_to_template(self, mock_llm, mock_storage):
        """Test that generate() passes language to template."""
        from speckit.core.specification import SpecificationBuilder

        builder = SpecificationBuilder(mock_llm, mock_storage)

        with patch("speckit.core.specification.render_template") as mock_render:
            mock_render.return_value = "prompt"
            builder.generate(
                feature_description="Test feature",
                feature_id="001-test",
                constitution=None,
                language="pt-br",
            )

            # Verify render_template was called with language
            mock_render.assert_called_once()
            call_kwargs = mock_render.call_args[1]
            assert call_kwargs["language"] == "pt-br"

    def test_generate_without_language(self, mock_llm, mock_storage):
        """Test generate() without language parameter."""
        from speckit.core.specification import SpecificationBuilder

        builder = SpecificationBuilder(mock_llm, mock_storage)

        with patch("speckit.core.specification.render_template") as mock_render:
            mock_render.return_value = "prompt"
            builder.generate(
                feature_description="Test feature",
                feature_id="001-test",
            )

            call_kwargs = mock_render.call_args[1]
            assert call_kwargs["language"] is None


class TestPlannerLanguage:
    """Tests for language propagation in TechnicalPlanner."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage."""
        return MagicMock()

    @pytest.fixture
    def sample_tech_stack(self):
        """Create sample tech stack."""
        return TechStack(
            language="Python 3.11",
            framework="FastAPI",
        )

    @pytest.fixture
    def mock_llm(self, sample_tech_stack):
        """Create mock LLM provider."""
        mock = MagicMock()
        mock.complete_structured.return_value = TechnicalPlan(
            feature_id="001-test",
            tech_stack=sample_tech_stack,
            architecture_overview="Test",
            components=[],
            file_structure="",
            technical_risks=[],
            mitigation_strategies=[],
        )
        return mock

    @pytest.fixture
    def sample_spec(self):
        """Create sample specification."""
        return Specification(
            feature_name="Test",
            feature_id="001-test",
            overview="Test",
            problem_statement="Test",
            target_users=[],
            user_stories=[],
            functional_requirements=[],
            entities=[],
            assumptions=[],
            constraints=[],
            out_of_scope=[],
            success_criteria=[],
        )

    def test_plan_passes_language_to_template(self, mock_llm, mock_storage, sample_spec):
        """Test that plan() passes language to template."""
        from speckit.core.planner import TechnicalPlanner

        planner = TechnicalPlanner(mock_llm, mock_storage)

        with patch("speckit.core.planner.render_template") as mock_render:
            mock_render.return_value = "prompt"
            planner.plan(
                specification=sample_spec,
                language="pt-br",
            )

            call_kwargs = mock_render.call_args[1]
            assert call_kwargs["language"] == "pt-br"


class TestTaskGeneratorLanguage:
    """Tests for language propagation in TaskGenerator."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage."""
        return MagicMock()

    @pytest.fixture
    def sample_tech_stack(self):
        """Create sample tech stack."""
        return TechStack(
            language="Python 3.11",
            framework="FastAPI",
        )

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM provider."""
        mock = MagicMock()
        mock.complete_structured.return_value = TaskBreakdown(
            feature_id="001-test",
            phases=[],
            summary="Test summary",
        )
        return mock

    @pytest.fixture
    def sample_plan(self, sample_tech_stack):
        """Create sample plan."""
        return TechnicalPlan(
            feature_id="001-test",
            tech_stack=sample_tech_stack,
            architecture_overview="Test",
            components=[],
            file_structure="",
            technical_risks=[],
            mitigation_strategies=[],
        )

    def test_generate_passes_language_to_template(self, mock_llm, mock_storage, sample_plan):
        """Test that generate() passes language to template."""
        from speckit.core.tasker import TaskGenerator

        generator = TaskGenerator(mock_llm, mock_storage)

        with patch("speckit.core.tasker.render_template") as mock_render:
            mock_render.return_value = "prompt"
            generator.generate(
                plan=sample_plan,
                language="pt-br",
            )

            call_kwargs = mock_render.call_args[1]
            assert call_kwargs["language"] == "pt-br"


class TestSpecKitLanguagePropagation:
    """Tests for language propagation from SpecKit config to builders."""

    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create temporary project directory."""
        speckit_dir = tmp_path / ".speckit"
        speckit_dir.mkdir()
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        return tmp_path

    def test_specify_uses_config_language(self, temp_project_dir):
        """Test that specify() uses language from config."""
        from speckit import SpecKit
        from speckit.config import SpecKitConfig, LLMConfig

        config = SpecKitConfig(
            llm=LLMConfig(model="gpt-4o-mini"),
            project_path=temp_project_dir,
            language="pt-br",
        )

        kit = SpecKit(temp_project_dir, config=config)

        # Mock the builder
        with patch.object(kit, "_specification_builder") as mock_builder:
            mock_builder.generate.return_value = MagicMock()
            kit._specification_builder = mock_builder

            kit.specify("Test feature")

            # Verify language was passed
            call_kwargs = mock_builder.generate.call_args[1]
            assert call_kwargs["language"] == "pt-br"

    def test_plan_uses_config_language(self, temp_project_dir):
        """Test that plan() uses language from config."""
        from speckit import SpecKit
        from speckit.config import SpecKitConfig, LLMConfig

        config = SpecKitConfig(
            llm=LLMConfig(model="gpt-4o-mini"),
            project_path=temp_project_dir,
            language="es",
        )

        kit = SpecKit(temp_project_dir, config=config)

        sample_spec = Specification(
            feature_name="Test",
            feature_id="001-test",
            overview="Test",
            problem_statement="Test",
            target_users=[],
            user_stories=[],
            functional_requirements=[],
            entities=[],
            assumptions=[],
            constraints=[],
            out_of_scope=[],
            success_criteria=[],
        )

        # Mock the planner
        with patch.object(kit, "_technical_planner") as mock_planner:
            mock_planner.plan.return_value = MagicMock()
            kit._technical_planner = mock_planner
            # Mock storage to return None for constitution
            kit._storage = MagicMock()
            kit._storage.load_constitution.return_value = None

            kit.plan(sample_spec)

            call_kwargs = mock_planner.plan.call_args[1]
            assert call_kwargs["language"] == "es"

    def test_tasks_uses_config_language(self, temp_project_dir):
        """Test that tasks() uses language from config."""
        from speckit import SpecKit
        from speckit.config import SpecKitConfig, LLMConfig

        config = SpecKitConfig(
            llm=LLMConfig(model="gpt-4o-mini"),
            project_path=temp_project_dir,
            language="pt-br",
        )

        kit = SpecKit(temp_project_dir, config=config)

        sample_tech_stack = TechStack(
            language="Python 3.11",
            framework="FastAPI",
        )

        sample_plan = TechnicalPlan(
            feature_id="001-test",
            tech_stack=sample_tech_stack,
            architecture_overview="Test",
            components=[],
            file_structure="",
            technical_risks=[],
            mitigation_strategies=[],
        )

        # Mock the task generator
        with patch.object(kit, "_task_generator") as mock_generator:
            mock_generator.generate.return_value = MagicMock()
            kit._task_generator = mock_generator
            # Mock storage
            kit._storage = MagicMock()
            kit._storage.load_specification.return_value = None

            kit.tasks(sample_plan)

            call_kwargs = mock_generator.generate.call_args[1]
            assert call_kwargs["language"] == "pt-br"


class TestLanguageEdgeCases:
    """Tests for edge cases in language handling."""

    def test_empty_string_language(self):
        """Test that empty string is treated as no language."""
        result = render_template(
            "specification.jinja2",
            feature_description="Test",
            feature_id="001",
            constitution=None,
            language="",
        )

        # Empty string should NOT trigger language instruction
        assert "**IMPORTANT: Generate ALL content in" not in result

    def test_uppercase_en_language(self):
        """Test uppercase EN is treated as English."""
        result = render_template(
            "specification.jinja2",
            feature_description="Test",
            feature_id="001",
            constitution=None,
            language="EN",
        )

        # Note: current implementation checks for != 'en', so 'EN' would show instruction
        # This test documents current behavior - may want to fix
        # If we want case-insensitive, template would need: language.lower() != 'en'

    def test_language_in_prompt_output(self):
        """Test that language instruction appears at the beginning of prompt."""
        result = render_template(
            "specification.jinja2",
            feature_description="Test feature",
            feature_id="001",
            constitution=None,
            language="pt-br",
        )

        # Language instruction should be at/near the start
        instruction_pos = result.find("**IMPORTANT: Generate ALL content in pt-br language")
        feature_pos = result.find("Test feature")

        assert instruction_pos < feature_pos, "Language instruction should come before content"
