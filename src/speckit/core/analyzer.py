"""
Consistency analysis for spec-kit.

This module provides tools to check consistency across artifacts
(specification, plan, tasks).
"""

from datetime import datetime

from speckit.llm import LiteLLMProvider
from speckit.schemas import (
    AnalysisReport,
    AnalysisIssue,
    Specification,
    TaskBreakdown,
    TechnicalPlan,
)
from speckit.templates import render_template


class ConsistencyAnalyzer:
    """
    Analyzes consistency across spec-kit artifacts.

    Checks for:
    - Traceability (all requirements have implementing tasks)
    - Completeness (all components have tasks)
    - Consistency (terminology, file paths, dependencies)
    """

    def __init__(self, llm: LiteLLMProvider):
        """
        Initialize consistency analyzer.

        Args:
            llm: LLM provider for analysis
        """
        self.llm = llm

    def analyze(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        tasks: TaskBreakdown,
    ) -> AnalysisReport:
        """
        Analyze consistency across all artifacts.

        Args:
            specification: Feature specification
            plan: Technical plan
            tasks: Task breakdown

        Returns:
            AnalysisReport with issues and recommendations
        """
        # Render prompt template (use mode='json' for datetime serialization)
        prompt = render_template(
            "analyze.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            tasks=tasks.model_dump(mode="json"),
        )

        # Generate analysis using structured output
        report = self.llm.complete_structured(
            prompt=prompt,
            response_model=AnalysisReport,
            system="You are a quality assurance analyst checking artifact consistency.",
        )

        # Set metadata
        report.feature_id = specification.feature_id
        report.created_at = datetime.now()

        # Add any automatic checks
        auto_issues = self._run_automatic_checks(specification, plan, tasks)
        report.issues.extend(auto_issues)

        return report

    async def analyze_async(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        tasks: TaskBreakdown,
    ) -> AnalysisReport:
        """Async version of analyze()."""
        prompt = render_template(
            "analyze.jinja2",
            specification=specification.model_dump(mode="json"),
            plan=plan.model_dump(mode="json"),
            tasks=tasks.model_dump(mode="json"),
        )

        report = await self.llm.complete_structured_async(
            prompt=prompt,
            response_model=AnalysisReport,
            system="You are a quality assurance analyst checking artifact consistency.",
        )

        report.feature_id = specification.feature_id
        report.created_at = datetime.now()

        auto_issues = self._run_automatic_checks(specification, plan, tasks)
        report.issues.extend(auto_issues)

        return report

    def _run_automatic_checks(
        self,
        specification: Specification,
        plan: TechnicalPlan,
        tasks: TaskBreakdown,
    ) -> list[AnalysisIssue]:
        """Run automatic consistency checks."""
        issues = []

        # Check: Feature IDs match
        if specification.feature_id != plan.feature_id:
            issues.append(
                AnalysisIssue(
                    severity="error",
                    category="inconsistent",
                    message="Feature ID mismatch between specification and plan",
                    location="plan.feature_id",
                    suggestion=f"Update plan feature_id to '{specification.feature_id}'",
                )
            )

        if specification.feature_id != tasks.feature_id:
            issues.append(
                AnalysisIssue(
                    severity="error",
                    category="inconsistent",
                    message="Feature ID mismatch between specification and tasks",
                    location="tasks.feature_id",
                    suggestion=f"Update tasks feature_id to '{specification.feature_id}'",
                )
            )

        # Check: All user stories have at least one implementing task
        story_ids = {story.id for story in specification.user_stories}
        task_story_ids = {task.user_story_id for task in tasks.tasks if task.user_story_id}

        unimplemented_stories = story_ids - task_story_ids
        if unimplemented_stories:
            issues.append(
                AnalysisIssue(
                    severity="warning",
                    category="incomplete",
                    message=f"User stories without implementing tasks: {', '.join(unimplemented_stories)}",
                    location="tasks",
                    suggestion="Add tasks that implement these user stories",
                )
            )

        # Check: No circular dependencies in tasks
        if self._has_circular_dependencies(tasks):
            issues.append(
                AnalysisIssue(
                    severity="error",
                    category="inconsistent",
                    message="Circular dependencies detected in task breakdown",
                    location="tasks.dependencies",
                    suggestion="Review and fix task dependencies to remove cycles",
                )
            )

        # Check: All task dependencies reference valid task IDs
        valid_task_ids = {task.id for task in tasks.tasks}
        for task in tasks.tasks:
            invalid_deps = set(task.dependencies) - valid_task_ids
            if invalid_deps:
                issues.append(
                    AnalysisIssue(
                        severity="error",
                        category="inconsistent",
                        message=f"Task {task.id} has invalid dependencies: {', '.join(invalid_deps)}",
                        location=f"tasks.{task.id}.dependencies",
                        suggestion="Remove invalid dependency references",
                    )
                )

        # Check: No duplicate task IDs
        task_id_counts: dict[str, int] = {}
        for task in tasks.tasks:
            task_id_counts[task.id] = task_id_counts.get(task.id, 0) + 1
        duplicate_ids = [tid for tid, count in task_id_counts.items() if count > 1]
        if duplicate_ids:
            issues.append(
                AnalysisIssue(
                    severity="error",
                    category="inconsistent",
                    message=f"Duplicate task IDs found: {', '.join(duplicate_ids)}",
                    location="tasks",
                    suggestion="Ensure all task IDs are unique",
                )
            )

        # Check: No duplicate phase IDs
        phase_id_counts: dict[str, int] = {}
        for phase in tasks.phases:
            phase_id_counts[phase.id] = phase_id_counts.get(phase.id, 0) + 1
        duplicate_phase_ids = [pid for pid, count in phase_id_counts.items() if count > 1]
        if duplicate_phase_ids:
            issues.append(
                AnalysisIssue(
                    severity="warning",
                    category="inconsistent",
                    message=f"Duplicate phase IDs found: {', '.join(duplicate_phase_ids)}",
                    location="tasks.phases",
                    suggestion="Ensure all phase IDs are unique",
                )
            )

        return issues

    def _has_circular_dependencies(self, tasks: TaskBreakdown) -> bool:
        """Check if the task dependency graph has cycles."""
        # Build adjacency list
        deps = {task.id: set(task.dependencies) for task in tasks.tasks}

        # DFS-based cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {task_id: WHITE for task_id in deps}

        def has_cycle(node: str) -> bool:
            colors[node] = GRAY
            for neighbor in deps.get(node, []):
                if neighbor not in colors:
                    continue
                if colors[neighbor] == GRAY:
                    return True
                if colors[neighbor] == WHITE and has_cycle(neighbor):
                    return True
            colors[node] = BLACK
            return False

        for task_id in deps:
            if colors[task_id] == WHITE:
                if has_cycle(task_id):
                    return True

        return False
