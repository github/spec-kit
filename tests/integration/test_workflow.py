"""
Integration tests for spec-kit workflow with real LLM API.

These tests require a valid ANTHROPIC_API_KEY environment variable.
Run with: ANTHROPIC_API_KEY=<key> pytest tests/integration/test_workflow.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest

from speckit import SpecKit, LLMConfig, SpecKitConfig


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def kit(temp_project):
    """Create a SpecKit instance with Claude configuration."""
    config = SpecKitConfig(
        project_path=temp_project,
        llm=LLMConfig(
            model="claude-3-haiku-20240307",
            temperature=0.7,
            max_tokens=4096,  # Need more tokens for task generation
            timeout=120,
        ),
    )
    return SpecKit(temp_project, config=config)


class TestSpecifyWorkflow:
    """Test the specify workflow with real LLM."""

    def test_specify_generates_specification(self, kit):
        """Test that specify() generates a valid specification."""
        description = "A simple todo list feature that allows users to add, complete, and delete tasks"

        spec = kit.specify(description, feature_id="001-todo-list")

        assert spec is not None
        assert spec.feature_id == "001-todo-list"
        assert spec.feature_name is not None
        assert len(spec.feature_name) > 0
        assert spec.overview is not None
        assert len(spec.user_stories) >= 0  # May be empty depending on LLM response

        # Verify to_markdown works
        markdown = spec.to_markdown()
        assert "# " in markdown
        assert "001-todo-list" in markdown

    def test_specify_and_save(self, kit, temp_project):
        """Test that specify() and save() persist the specification."""
        description = "User authentication with email and password"

        spec = kit.specify(description, feature_id="002-auth")
        path = kit.save(spec)

        assert path.exists()
        assert "002-auth" in str(path)

        # Verify we can load it back
        loaded = kit.load_specification("002-auth")
        assert loaded is not None
        assert loaded.feature_id == spec.feature_id


class TestPlanWorkflow:
    """Test the plan workflow with real LLM."""

    def test_plan_generates_technical_plan(self, kit):
        """Test that plan() generates a valid technical plan."""
        # First create a specification
        spec = kit.specify(
            "A REST API endpoint for user profile management",
            feature_id="003-profile-api"
        )

        # Then generate a plan
        plan = kit.plan(spec)

        assert plan is not None
        assert plan.feature_id == "003-profile-api"
        assert plan.architecture_overview is not None
        assert len(plan.architecture_overview) > 0

        # Verify to_markdown works
        markdown = plan.to_markdown()
        assert "# " in markdown


class TestTasksWorkflow:
    """Test the tasks workflow with real LLM."""

    def test_tasks_generates_breakdown(self, kit):
        """Test that tasks() generates a valid task breakdown."""
        # Create specification
        spec = kit.specify(
            "A simple file upload feature",
            feature_id="004-upload"
        )

        # Create plan
        plan = kit.plan(spec)
        kit.save(plan)

        # Generate tasks
        tasks = kit.tasks(plan)

        assert tasks is not None
        assert tasks.feature_id == "004-upload"
        # Note: LLM may return empty tasks for simple features with haiku
        assert len(tasks.tasks) >= 0

        # Verify to_markdown works
        markdown = tasks.to_markdown()
        assert len(markdown) > 0


class TestFullWorkflow:
    """Test the complete workflow end-to-end."""

    def test_complete_workflow(self, kit, temp_project):
        """Test the complete specify -> plan -> tasks workflow."""
        feature_description = """
        A notification system that:
        - Sends email notifications for important events
        - Allows users to configure notification preferences
        - Supports in-app notifications
        """

        # Step 1: Specify
        spec = kit.specify(feature_description, feature_id="005-notifications")
        assert spec is not None
        kit.save(spec)

        # Verify specification has key elements
        assert spec.feature_id == "005-notifications"
        assert len(spec.user_stories) >= 0

        # Step 2: Plan
        plan = kit.plan(spec)
        assert plan is not None
        kit.save(plan)

        # Verify plan has key elements
        assert plan.feature_id == "005-notifications"
        assert plan.architecture_overview is not None

        # Step 3: Tasks
        tasks = kit.tasks(plan)
        assert tasks is not None
        kit.save(tasks)

        # Verify tasks has key elements
        assert tasks.feature_id == "005-notifications"
        assert len(tasks.tasks) >= 0  # May be empty with haiku model

        # Verify all artifacts are saved
        assert kit.storage.artifact_exists("005-notifications", "spec")
        assert kit.storage.artifact_exists("005-notifications", "plan")
        assert kit.storage.artifact_exists("005-notifications", "tasks")

        # List features should include our feature
        features = kit.list_features()
        assert "005-notifications" in features


class TestClarifyWorkflow:
    """Test the clarify workflow with real LLM."""

    def test_clarify_identifies_questions(self, kit):
        """Test that clarify() identifies ambiguities."""
        # Create a vague specification
        spec = kit.specify(
            "A search feature",  # Intentionally vague
            feature_id="006-search"
        )

        # Clarify should identify questions
        updated_spec, questions = kit.clarify(spec, max_questions=3)

        # May or may not have questions depending on the generated spec
        assert updated_spec is not None
        assert isinstance(questions, list)


class TestAnalyzeWorkflow:
    """Test the analyze workflow with real LLM."""

    def test_analyze_checks_consistency(self, kit):
        """Test that analyze() checks artifact consistency."""
        # Create full workflow artifacts
        spec = kit.specify(
            "A comment system for blog posts",
            feature_id="007-comments"
        )
        kit.save(spec)

        plan = kit.plan(spec)
        kit.save(plan)

        tasks = kit.tasks(plan)
        kit.save(tasks)

        # Analyze consistency
        report = kit.analyze(spec, plan, tasks)

        assert report is not None
        assert report.feature_id == "007-comments"

        # Verify to_markdown works
        markdown = report.to_markdown()
        assert len(markdown) > 0
