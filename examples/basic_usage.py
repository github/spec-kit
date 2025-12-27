"""
Basic usage example for spec-kit.

This example demonstrates the core workflow:
1. Initialize SpecKit with a project
2. Generate a specification from natural language
3. Create a technical plan
4. Generate implementation tasks

Requirements:
- Set OPENAI_API_KEY or another LLM provider's API key
- Or use Ollama for local LLM (no API key needed)
"""

from pathlib import Path

from speckit import SpecKit
from speckit.config import LLMConfig


def main():
    # Initialize SpecKit with current directory
    # Uses environment variables for LLM config by default
    kit = SpecKit(".")

    # Or with explicit configuration
    # kit = SpecKit(
    #     ".",
    #     llm_config=LLMConfig(
    #         model="ollama/llama3.1",  # Use local Ollama
    #         temperature=0.7,
    #     )
    # )

    # 1. Generate a specification from natural language
    print("Generating specification...")
    spec = kit.specify("""
        Add user authentication with:
        - Email/password login
        - Password reset via email
        - Session management with JWT
        - Role-based access control (admin, user)
    """)

    print(f"\nGenerated specification: {spec.feature_name}")
    print(f"Feature ID: {spec.feature_id}")
    print(f"User stories: {len(spec.user_stories)}")
    for story in spec.user_stories:
        print(f"  - [{story.priority.value.upper()}] {story.i_want}")

    # Save the specification
    spec_path = kit.save(spec)
    print(f"\nSaved to: {spec_path}")

    # 2. Generate a technical plan
    print("\nGenerating technical plan...")
    plan = kit.plan(spec)

    print(f"\nTech stack: {plan.tech_stack.language}")
    print(f"Components: {len(plan.components)}")
    for comp in plan.components:
        print(f"  - {comp.name}: {comp.file_path}")

    # Save the plan
    plan_path = kit.save(plan)
    print(f"\nSaved to: {plan_path}")

    # 3. Generate implementation tasks
    print("\nGenerating tasks...")
    tasks = kit.tasks(plan)

    print(f"\nTotal tasks: {len(tasks.tasks)}")
    progress = tasks.get_progress()
    print(f"Progress: {progress}")

    # Get tasks ready to execute
    ready_tasks = tasks.get_next_tasks()
    print(f"\nTasks ready to start: {len(ready_tasks)}")
    for task in ready_tasks[:5]:  # Show first 5
        parallel = "[P]" if task.is_parallel else "   "
        print(f"  {parallel} {task.id}: {task.title}")

    # Save the tasks
    tasks_path = kit.save(tasks)
    print(f"\nSaved to: {tasks_path}")

    # View the generated markdown
    print("\n" + "=" * 60)
    print("SPECIFICATION MARKDOWN")
    print("=" * 60)
    print(spec.to_markdown()[:2000] + "...")


if __name__ == "__main__":
    main()
