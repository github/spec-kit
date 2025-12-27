"""
Integration test that generates all artifacts for manual analysis.

This test creates a complete project with constitution, specification, plan, and tasks
in a persistent output directory for manual inspection.

Run with: ANTHROPIC_API_KEY=<key> pytest tests/integration/test_full_generation.py -v -s
"""

import os
import shutil
from pathlib import Path

import pytest

from speckit import SpecKit, LLMConfig, SpecKitConfig


# Skip if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)


# Output directory for generated artifacts (persistent, not temp)
OUTPUT_DIR = Path(__file__).parent.parent.parent / "test_output" / "generated_project"


@pytest.fixture(scope="module")
def output_project():
    """Create a persistent output directory for analysis."""
    # Clean and recreate output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create .speckit and specs directories
    (OUTPUT_DIR / ".speckit").mkdir(exist_ok=True)
    (OUTPUT_DIR / "specs").mkdir(exist_ok=True)

    print(f"\n📁 Output directory: {OUTPUT_DIR}")
    return OUTPUT_DIR


@pytest.fixture(scope="module")
def kit(output_project):
    """Create a SpecKit instance for the output project."""
    config = SpecKitConfig(
        project_path=output_project,
        llm=LLMConfig(
            model="claude-3-5-haiku-latest",
            temperature=0.7,
            max_tokens=8192,  # More tokens for complete generation
            timeout=180,
        ),
    )
    return SpecKit(output_project, config=config)


class TestFullGeneration:
    """Generate all artifacts for a complete feature."""

    def test_01_generate_constitution(self, kit, output_project):
        """Step 1: Generate project constitution."""
        print("\n\n" + "="*80)
        print("STEP 1: Generating Constitution")
        print("="*80)

        constitution = kit.constitution(
            project_name="TaskMaster Pro",
            principles=[
                "Clean, maintainable code with clear separation of concerns",
                "Test-driven development with comprehensive coverage",
                "Type-safe code using modern Python type hints",
                "RESTful API design following best practices",
                "Security-first approach for all user data",
            ]
        )

        # Save constitution
        path = kit.save(constitution)

        print(f"\n✅ Constitution saved to: {path}")
        print(f"\n📋 Constitution Preview:")
        print("-" * 40)
        markdown = constitution.to_markdown()
        print(markdown[:2000] + "..." if len(markdown) > 2000 else markdown)

        assert path.exists()
        assert constitution.project_name == "TaskMaster Pro"

    def test_02_generate_specification(self, kit, output_project):
        """Step 2: Generate feature specification."""
        print("\n\n" + "="*80)
        print("STEP 2: Generating Specification")
        print("="*80)

        feature_description = """
        Create a comprehensive task management system with the following capabilities:

        1. Task CRUD Operations:
           - Users can create tasks with title, description, due date, and priority
           - Tasks can be organized into projects and categories
           - Support for task tags and labels

        2. Task States:
           - Tasks can be in states: pending, in_progress, completed, archived
           - State transitions should be validated
           - Track state change history

        3. User Features:
           - Assign tasks to team members
           - Comment on tasks
           - Receive notifications for due dates and mentions

        4. Search and Filter:
           - Full-text search across tasks
           - Filter by status, priority, assignee, project
           - Sort by various fields

        5. API:
           - RESTful API for all operations
           - Proper authentication and authorization
           - Rate limiting for API endpoints
        """

        spec = kit.specify(feature_description, feature_id="001-task-management")

        # Save specification
        path = kit.save(spec)

        print(f"\n✅ Specification saved to: {path}")
        print(f"\n📋 Specification Preview:")
        print("-" * 40)
        markdown = spec.to_markdown()
        print(markdown[:3000] + "..." if len(markdown) > 3000 else markdown)

        assert path.exists()
        assert spec.feature_id == "001-task-management"
        assert spec.feature_name is not None
        assert len(spec.user_stories) > 0

    def test_03_generate_plan(self, kit, output_project):
        """Step 3: Generate technical plan."""
        print("\n\n" + "="*80)
        print("STEP 3: Generating Technical Plan")
        print("="*80)

        # Load the specification we created
        spec = kit.load_specification("001-task-management")
        assert spec is not None, "Specification not found - run test_02 first"

        # Generate plan
        plan = kit.plan(spec)

        # Save plan
        path = kit.save(plan)

        print(f"\n✅ Plan saved to: {path}")
        print(f"\n📋 Technical Plan Preview:")
        print("-" * 40)
        markdown = plan.to_markdown()
        print(markdown[:3000] + "..." if len(markdown) > 3000 else markdown)

        assert path.exists()
        assert plan.feature_id == "001-task-management"
        assert plan.architecture_overview is not None

    def test_04_generate_tasks(self, kit, output_project):
        """Step 4: Generate task breakdown."""
        print("\n\n" + "="*80)
        print("STEP 4: Generating Task Breakdown")
        print("="*80)

        # Load the plan we created
        plan = kit.load_plan("001-task-management")
        assert plan is not None, "Plan not found - run test_03 first"

        # Generate tasks
        tasks = kit.tasks(plan)

        # Save tasks
        path = kit.save(tasks)

        print(f"\n✅ Tasks saved to: {path}")
        print(f"\n📋 Tasks Preview:")
        print("-" * 40)
        markdown = tasks.to_markdown()
        print(markdown[:3000] + "..." if len(markdown) > 3000 else markdown)

        assert path.exists()
        assert tasks.feature_id == "001-task-management"

    def test_05_analyze_artifacts(self, kit, output_project):
        """Step 5: Analyze consistency of all artifacts."""
        print("\n\n" + "="*80)
        print("STEP 5: Analyzing Artifact Consistency")
        print("="*80)

        # Load all artifacts
        spec = kit.load_specification("001-task-management")
        plan = kit.load_plan("001-task-management")
        tasks = kit.load_tasks("001-task-management")

        assert spec is not None, "Specification not found"
        assert plan is not None, "Plan not found"
        assert tasks is not None, "Tasks not found"

        # Analyze consistency
        report = kit.analyze(spec, plan, tasks)

        # Save report
        report_path = output_project / "specs" / "001-task-management" / "analysis.md"
        report_path.write_text(report.to_markdown())

        print(f"\n✅ Analysis saved to: {report_path}")
        print(f"\n📋 Analysis Report:")
        print("-" * 40)
        print(report.to_markdown())

        assert report.feature_id == "001-task-management"

    def test_06_print_summary(self, output_project):
        """Print summary of all generated files."""
        print("\n\n" + "="*80)
        print("GENERATION COMPLETE - FILE SUMMARY")
        print("="*80)

        print(f"\n📁 All files saved to: {output_project}")
        print("\n📄 Generated files:")

        for path in sorted(output_project.rglob("*")):
            if path.is_file():
                rel_path = path.relative_to(output_project)
                size = path.stat().st_size
                print(f"   {rel_path} ({size:,} bytes)")

        print("\n" + "="*80)
        print("You can now inspect the generated files in:")
        print(f"   {output_project}")
        print("="*80)
