"""
Task generation for spec-kit.

This module provides tools to generate implementation task breakdowns
from technical plans.
"""

from datetime import datetime
from typing import Optional

from speckit.llm import LiteLLMProvider
from speckit.schemas import Phase, Specification, Task, TaskBreakdown, TechnicalPlan
from speckit.storage.base import StorageBase
from speckit.templates import render_template


class TaskGenerator:
    """
    Generates implementation task breakdowns from technical plans.

    Tasks are organized by phase (setup, tests, core, integration, polish)
    and include dependencies for proper execution ordering.
    """

    def __init__(self, llm: LiteLLMProvider, storage: StorageBase):
        """
        Initialize task generator.

        Args:
            llm: LLM provider for generation
            storage: Storage backend for persistence
        """
        self.llm = llm
        self.storage = storage

    def generate(
        self,
        plan: TechnicalPlan,
        specification: Optional[Specification] = None,
        parallel_friendly: bool = True,
        language: Optional[str] = None,
    ) -> TaskBreakdown:
        """
        Generate tasks from a technical plan.

        Args:
            plan: Technical plan to break down
            specification: Optional specification for traceability
            parallel_friendly: If True, maximizes parallel task opportunities
            language: Optional output language (e.g., 'pt-br', 'es', 'en')

        Returns:
            Generated TaskBreakdown model
        """
        # Render prompt template (use mode='json' for datetime serialization)
        prompt = render_template(
            "tasks.jinja2",
            plan=plan.model_dump(mode="json"),
            specification=specification.model_dump(mode="json") if specification else {},
            language=language,
        )

        # Generate tasks using structured output
        breakdown = self.llm.complete_structured(
            prompt=prompt,
            response_model=TaskBreakdown,
            system="You are a technical lead creating implementation task breakdowns.",
        )

        # Ensure feature_id is set correctly
        breakdown.feature_id = plan.feature_id
        breakdown.created_at = datetime.now()

        # Deduplicate tasks and phases (LLM may generate duplicates)
        breakdown.tasks = self._deduplicate_tasks(breakdown.tasks)
        breakdown.phases = self._deduplicate_phases(breakdown.phases)

        # Build dependency graph
        breakdown.dependency_graph = self._build_dependency_graph(breakdown)

        return breakdown

    async def generate_async(
        self,
        plan: TechnicalPlan,
        specification: Optional[Specification] = None,
        parallel_friendly: bool = True,
        language: Optional[str] = None,
    ) -> TaskBreakdown:
        """Async version of generate()."""
        prompt = render_template(
            "tasks.jinja2",
            plan=plan.model_dump(mode="json"),
            specification=specification.model_dump(mode="json") if specification else {},
            language=language,
        )

        breakdown = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=TaskBreakdown,
            system="You are a technical lead creating implementation task breakdowns.",
        )

        breakdown.feature_id = plan.feature_id
        breakdown.created_at = datetime.now()

        # Deduplicate tasks and phases (LLM may generate duplicates)
        breakdown.tasks = self._deduplicate_tasks(breakdown.tasks)
        breakdown.phases = self._deduplicate_phases(breakdown.phases)

        breakdown.dependency_graph = self._build_dependency_graph(breakdown)

        return breakdown

    def _deduplicate_tasks(self, tasks: list[Task]) -> list[Task]:
        """Remove duplicate tasks by ID, keeping the first occurrence."""
        seen_ids: set[str] = set()
        unique_tasks: list[Task] = []
        for task in tasks:
            if task.id not in seen_ids:
                seen_ids.add(task.id)
                unique_tasks.append(task)
        return unique_tasks

    def _deduplicate_phases(self, phases: list[Phase]) -> list[Phase]:
        """Remove duplicate phases by ID, keeping the first occurrence."""
        seen_ids: set[str] = set()
        unique_phases: list[Phase] = []
        for phase in phases:
            if phase.id not in seen_ids:
                seen_ids.add(phase.id)
                unique_phases.append(phase)
        return unique_phases

    def _build_dependency_graph(self, breakdown: TaskBreakdown) -> dict[str, list[str]]:
        """Build a dependency graph from task dependencies."""
        graph = {}
        for task in breakdown.tasks:
            # Find tasks that depend on this task
            dependents = [
                t.id for t in breakdown.tasks if task.id in t.dependencies
            ]
            graph[task.id] = dependents
        return graph
