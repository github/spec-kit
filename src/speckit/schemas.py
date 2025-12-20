"""
Pydantic models for all spec-kit workflow artifacts.

This module defines the data models for:
- Configuration (enums, config models)
- Workflow artifacts (Constitution, Specification, TechnicalPlan, TaskBreakdown)
- LLM responses and generated artifacts
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enumerations
# =============================================================================


class Priority(str, Enum):
    """MoSCoW prioritization for requirements and user stories."""

    MUST = "must"  # P1 - Critical for MVP
    SHOULD = "should"  # P2 - Important but not blocking
    COULD = "could"  # P3 - Nice to have
    WONT = "wont"  # Explicitly excluded from scope


class TaskStatus(str, Enum):
    """Status of implementation tasks."""

    PENDING = "pending"  # Not started
    IN_PROGRESS = "in_progress"  # Currently being worked on
    COMPLETED = "completed"  # Done and validated
    BLOCKED = "blocked"  # Waiting on dependency
    SKIPPED = "skipped"  # Intentionally not done


class PhaseType(str, Enum):
    """Implementation phases for task organization."""

    SETUP = "setup"  # Project initialization
    TESTS = "tests"  # Test infrastructure
    CORE = "core"  # Core functionality
    INTEGRATION = "integration"  # Component integration
    POLISH = "polish"  # Refinements and docs


class FeatureStatus(str, Enum):
    """Status of a feature in the spec-driven workflow."""

    DRAFT = "draft"  # Initial specification
    CLARIFIED = "clarified"  # Ambiguities resolved
    PLANNED = "planned"  # Technical plan complete
    TASKED = "tasked"  # Tasks generated
    IN_PROGRESS = "in_progress"  # Implementation started
    COMPLETED = "completed"  # All tasks done


# =============================================================================
# Constitution Models
# =============================================================================


class Constitution(BaseModel):
    """Project-level principles and standards."""

    project_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"

    # Principle categories
    core_principles: list[str] = Field(default_factory=list)
    quality_standards: list[str] = Field(default_factory=list)
    testing_standards: list[str] = Field(default_factory=list)
    tech_constraints: list[str] = Field(default_factory=list)
    ux_guidelines: list[str] = Field(default_factory=list)
    governance_rules: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Export constitution to Markdown format."""
        lines = [
            f"# Project Constitution: {self.project_name}",
            "",
            f"**Version**: {self.version}",
            f"**Created**: {self.created_at.isoformat()}",
            f"**Updated**: {self.updated_at.isoformat()}",
            "",
            "## Core Principles",
            "",
        ]
        for principle in self.core_principles:
            lines.append(f"- {principle}")

        lines.extend(["", "## Quality Standards", ""])
        for standard in self.quality_standards:
            lines.append(f"- {standard}")

        lines.extend(["", "## Testing Standards", ""])
        for standard in self.testing_standards:
            lines.append(f"- {standard}")

        lines.extend(["", "## Technical Constraints", ""])
        for constraint in self.tech_constraints:
            lines.append(f"- {constraint}")

        lines.extend(["", "## UX Guidelines", ""])
        for guideline in self.ux_guidelines:
            lines.append(f"- {guideline}")

        lines.extend(["", "## Governance Rules", ""])
        for rule in self.governance_rules:
            lines.append(f"- {rule}")

        return "\n".join(lines)


# =============================================================================
# Specification Models
# =============================================================================


class UserStory(BaseModel):
    """User story in standard format with acceptance criteria."""

    id: str  # e.g., "US-001"
    as_a: str  # User role
    i_want: str  # Desired action
    so_that: str  # Business value
    priority: Priority
    acceptance_criteria: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Export user story to Markdown format."""
        lines = [
            f"### {self.id}: {self.i_want}",
            "",
            f"**Priority**: {self.priority.value.upper()}",
            "",
            f"As a **{self.as_a}**, I want **{self.i_want}**, so that **{self.so_that}**.",
            "",
            "**Acceptance Criteria**:",
            "",
        ]
        for criterion in self.acceptance_criteria:
            lines.append(f"- {criterion}")
        return "\n".join(lines)


class FunctionalRequirement(BaseModel):
    """Functional requirement with rationale."""

    id: str  # e.g., "FR-001"
    title: str
    description: str
    rationale: str
    priority: Priority
    acceptance_criteria: list[str] = Field(default_factory=list)
    related_stories: list[str] = Field(default_factory=list)  # Links to UserStory.id

    def to_markdown(self) -> str:
        """Export functional requirement to Markdown format."""
        lines = [
            f"### {self.id}: {self.title}",
            "",
            f"**Priority**: {self.priority.value.upper()}",
            "",
            self.description,
            "",
            f"**Rationale**: {self.rationale}",
            "",
            "**Acceptance Criteria**:",
            "",
        ]
        for criterion in self.acceptance_criteria:
            lines.append(f"- {criterion}")
        if self.related_stories:
            lines.extend(["", f"**Related Stories**: {', '.join(self.related_stories)}"])
        return "\n".join(lines)


class Entity(BaseModel):
    """Domain entity for data modeling."""

    name: str
    description: str
    attributes: list[str] = Field(default_factory=list)  # Field descriptions
    relationships: list[str] = Field(default_factory=list)  # Links to other entities

    def to_markdown(self) -> str:
        """Export entity to Markdown format."""
        lines = [
            f"### {self.name}",
            "",
            self.description,
            "",
            "**Attributes**:",
            "",
        ]
        for attr in self.attributes:
            lines.append(f"- {attr}")
        if self.relationships:
            lines.extend(["", "**Relationships**:", ""])
            for rel in self.relationships:
                lines.append(f"- {rel}")
        return "\n".join(lines)


class Specification(BaseModel):
    """Complete feature specification."""

    feature_name: str
    feature_id: str  # e.g., "001-python-library"
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"

    # Content sections
    overview: str = ""
    problem_statement: str = ""
    target_users: list[str] = Field(default_factory=list)

    # Structured requirements
    user_stories: list[UserStory] = Field(default_factory=list)
    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    entities: list[Entity] = Field(default_factory=list)

    # Constraints and scope
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)

    # Clarification tracking
    clarifications_needed: list[str] = Field(default_factory=list)
    clarifications_resolved: list[dict] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Export specification to Markdown format."""
        lines = [
            f"# Feature Specification: {self.feature_name}",
            "",
            f"**Feature ID**: {self.feature_id}",
            f"**Version**: {self.version}",
            f"**Created**: {self.created_at.isoformat()}",
            "",
            "## Overview",
            "",
            self.overview,
            "",
            "## Problem Statement",
            "",
            self.problem_statement,
            "",
            "## Target Users",
            "",
        ]
        for user in self.target_users:
            lines.append(f"- {user}")

        lines.extend(["", "## User Stories", ""])
        for story in self.user_stories:
            lines.append(story.to_markdown())
            lines.append("")

        lines.extend(["## Functional Requirements", ""])
        for req in self.functional_requirements:
            lines.append(req.to_markdown())
            lines.append("")

        lines.extend(["## Key Entities", ""])
        for entity in self.entities:
            lines.append(entity.to_markdown())
            lines.append("")

        lines.extend(["## Assumptions", ""])
        for assumption in self.assumptions:
            lines.append(f"- {assumption}")

        lines.extend(["", "## Constraints", ""])
        for constraint in self.constraints:
            lines.append(f"- {constraint}")

        lines.extend(["", "## Out of Scope", ""])
        for item in self.out_of_scope:
            lines.append(f"- {item}")

        lines.extend(["", "## Success Criteria", ""])
        for criterion in self.success_criteria:
            lines.append(f"- {criterion}")

        return "\n".join(lines)


# =============================================================================
# Technical Plan Models
# =============================================================================


class TechStack(BaseModel):
    """Technology stack definition."""

    language: str  # e.g., "Python 3.11"
    framework: str = ""  # e.g., "Typer"
    database: Optional[str] = None  # e.g., "PostgreSQL" or None
    orm: Optional[str] = None  # e.g., "SQLAlchemy" or None
    testing: str = "pytest"
    additional_tools: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Export tech stack to Markdown format."""
        lines = [
            "## Technology Stack",
            "",
            f"- **Language**: {self.language}",
            f"- **Framework**: {self.framework}",
        ]
        if self.database:
            lines.append(f"- **Database**: {self.database}")
        if self.orm:
            lines.append(f"- **ORM**: {self.orm}")
        lines.append(f"- **Testing**: {self.testing}")
        if self.additional_tools:
            lines.append(f"- **Additional Tools**: {', '.join(self.additional_tools)}")
        return "\n".join(lines)


class ArchitectureComponent(BaseModel):
    """Component in the system architecture."""

    name: str
    component_type: str  # e.g., "module", "service", "cli"
    description: str
    file_path: str  # e.g., "src/speckit/llm.py"
    dependencies: list[str] = Field(default_factory=list)  # Other component names
    public_interface: list[str] = Field(default_factory=list)  # Exported functions/classes

    def to_markdown(self) -> str:
        """Export component to Markdown format."""
        lines = [
            f"### {self.name}",
            "",
            f"**Type**: {self.component_type}",
            f"**Path**: `{self.file_path}`",
            "",
            self.description,
            "",
        ]
        if self.dependencies:
            lines.append(f"**Dependencies**: {', '.join(self.dependencies)}")
        if self.public_interface:
            lines.extend(["", "**Public Interface**:", ""])
            for item in self.public_interface:
                lines.append(f"- `{item}`")
        return "\n".join(lines)


class TechnicalPlan(BaseModel):
    """Technical implementation plan."""

    feature_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"

    # Technical decisions
    tech_stack: TechStack
    architecture_overview: str = ""
    components: list[ArchitectureComponent] = Field(default_factory=list)

    # Design artifacts
    data_model: str = ""  # Mermaid diagram or description
    file_structure: str = ""  # Directory tree
    api_contracts: str = ""  # API documentation reference

    # Risk management
    technical_risks: list[str] = Field(default_factory=list)
    mitigation_strategies: list[str] = Field(default_factory=list)
    research_notes: str = ""  # Findings from Phase 0

    def to_markdown(self) -> str:
        """Export technical plan to Markdown format."""
        lines = [
            f"# Technical Plan: {self.feature_id}",
            "",
            f"**Version**: {self.version}",
            f"**Created**: {self.created_at.isoformat()}",
            "",
            self.tech_stack.to_markdown(),
            "",
            "## Architecture Overview",
            "",
            self.architecture_overview,
            "",
            "## Components",
            "",
        ]
        for component in self.components:
            lines.append(component.to_markdown())
            lines.append("")

        if self.file_structure:
            lines.extend(["## File Structure", "", "```", self.file_structure, "```", ""])

        if self.data_model:
            lines.extend(["## Data Model", "", self.data_model, ""])

        if self.technical_risks:
            lines.extend(["## Technical Risks", ""])
            for risk in self.technical_risks:
                lines.append(f"- {risk}")
            lines.append("")

        if self.mitigation_strategies:
            lines.extend(["## Mitigation Strategies", ""])
            for strategy in self.mitigation_strategies:
                lines.append(f"- {strategy}")
            lines.append("")

        if self.research_notes:
            lines.extend(["## Research Notes", "", self.research_notes])

        return "\n".join(lines)


# =============================================================================
# Task Models
# =============================================================================


class Task(BaseModel):
    """Atomic implementation task."""

    id: str  # e.g., "T001"
    title: str
    description: str = ""
    phase: str  # Dynamic phase name (e.g., "Setup", "US1", "Foundational")
    phase_label: str = ""  # Display label for the phase (e.g., "User Story 1 - Auth")
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "P2"  # P1 = critical, P2 = important, P3 = nice to have

    # Traceability
    user_story_id: Optional[str] = None  # Links to UserStory.id
    requirement_ids: list[str] = Field(default_factory=list)  # Links to FunctionalRequirement.id

    # Execution details
    file_paths: list[str] = Field(default_factory=list)  # Files to create/modify
    dependencies: list[str] = Field(default_factory=list)  # Task IDs that must complete first
    dependency_reasons: dict[str, str] = Field(default_factory=dict)  # task_id -> reason
    is_parallel: bool = False  # Can run with other parallel tasks

    # Validation
    validation_criteria: list[str] = Field(default_factory=list)
    estimated_complexity: str = "medium"  # "low", "medium", "high"

    def to_markdown(self, include_details: bool = True) -> str:
        """Export task to Markdown format.

        Args:
            include_details: If True, includes multi-line format with description,
                           files, dependencies. If False, returns single line.
        """
        checkbox = "[x]" if self.status == TaskStatus.COMPLETED else "[ ]"
        parallel_marker = "[P] " if self.is_parallel else ""
        story_marker = f"[{self.user_story_id}] " if self.user_story_id else ""
        phase_marker = f"[{self.phase}] " if self.phase else ""

        # Basic line
        line = f"- {checkbox} {self.id} {parallel_marker}{phase_marker}{story_marker}{self.title}"

        if not include_details:
            return line

        # Multi-line format with metadata
        lines = [line]

        if self.description:
            lines.append(f"  > Description: {self.description}")

        if self.file_paths:
            lines.append(f"  > Files: {', '.join(self.file_paths)}")

        if self.dependencies:
            dep_parts = []
            for dep_id in self.dependencies:
                reason = self.dependency_reasons.get(dep_id, "")
                if reason:
                    dep_parts.append(f"{dep_id} ({reason})")
                else:
                    dep_parts.append(dep_id)
            lines.append(f"  > Depends: {', '.join(dep_parts)}")

        if self.priority:
            lines.append(f"  > Priority: {self.priority}")

        return "\n".join(lines)


class Phase(BaseModel):
    """Implementation phase containing related tasks."""

    id: str  # e.g., "phase-1", "us1"
    number: int  # Display order (1, 2, 3...)
    name: str  # e.g., "Setup", "User Story 1 - Authentication"
    purpose: str = ""  # Brief description of what this phase accomplishes
    is_mvp: bool = False  # True if this phase is part of MVP
    checkpoint: str = ""  # Validation checkpoint at end of phase
    user_story_id: Optional[str] = None  # Link to user story if applicable
    priority: str = ""  # P1, P2, P3 if user story phase

    def to_markdown_header(self) -> str:
        """Generate phase header in Markdown format."""
        mvp_marker = " 🎯 MVP" if self.is_mvp else ""
        priority_marker = f" (Priority: {self.priority})" if self.priority else ""
        return f"## Phase {self.number}: {self.name}{priority_marker}{mvp_marker}"


class TaskBreakdown(BaseModel):
    """Complete task breakdown for a feature."""

    feature_id: str
    feature_name: str = ""  # Display name for the feature
    created_at: datetime = Field(default_factory=datetime.now)
    tasks: list[Task] = Field(default_factory=list)
    phases: list[Phase] = Field(default_factory=list)

    # Input/prerequisites info
    input_docs: str = ""  # e.g., "Design documents from `/specs/001-feature/`"
    prerequisites: list[str] = Field(default_factory=list)  # e.g., ["plan.md", "spec.md"]
    tests_requested: bool = False  # Whether tests were explicitly requested

    # Dependency management
    dependency_graph: dict[str, list[str]] = Field(
        default_factory=dict
    )  # task_id -> dependent_task_ids

    # Execution strategy
    implementation_strategy: str = ""  # MVP First, Incremental, etc.
    parallel_opportunities: list[str] = Field(default_factory=list)

    def get_tasks_by_phase(self, phase_id: str) -> list[Task]:
        """Get all tasks in a specific phase."""
        return [task for task in self.tasks if task.phase == phase_id]

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks if task.status == status]

    def get_next_tasks(self) -> list[Task]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        completed_ids = {
            task.id for task in self.tasks if task.status == TaskStatus.COMPLETED
        }
        ready = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            # Check if all dependencies are completed
            if all(dep_id in completed_ids for dep_id in task.dependencies):
                ready.append(task)
        return ready

    def mark_complete(self, task_id: str) -> None:
        """Mark a task as completed."""
        for task in self.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                break

    def get_progress(self) -> dict[str, int]:
        """Get status counts for all tasks."""
        counts: dict[str, int] = {status.value: 0 for status in TaskStatus}
        for task in self.tasks:
            counts[task.status.value] += 1
        return counts

    def to_markdown(self) -> str:
        """Export task breakdown to Markdown format matching tasks-template.md."""
        lines = [
            f"# Tasks: {self.feature_name or self.feature_id}",
            "",
        ]

        # Input and prerequisites
        if self.input_docs:
            lines.append(f"**Input**: {self.input_docs}")
        if self.prerequisites:
            lines.append(f"**Prerequisites**: {', '.join(self.prerequisites)}")
        if not self.tests_requested:
            lines.append(
                "**Tests**: Not explicitly requested - basic unit tests included "
                "for critical functionality."
            )
        lines.append("")

        # Task format documentation
        lines.extend([
            "**Organization**: Tasks are grouped by implementation phase to enable incremental delivery.",
            "",
            "## Format: `[ID] [P?] [Phase] Summary`",
            "",
            "Each task uses multi-line format with description block:",
            "",
            "```markdown",
            "- [ ] T001 [P] [LABEL] Task summary (brief, actionable title)",
            "  > Description: 2-4 sentences explaining what to implement.",
            "  > Files: path/to/file1.py, path/to/file2.tsx",
            "  > Depends: T000 (reason for dependency)",
            "  > Priority: P1",
            "```",
            "",
            "---",
            "",
        ])

        # Phases and tasks
        for phase in sorted(self.phases, key=lambda p: p.number):
            lines.append(phase.to_markdown_header())
            lines.append("")

            if phase.purpose:
                lines.append(f"**Purpose**: {phase.purpose}")
                lines.append("")

            # Get tasks for this phase
            phase_tasks = self.get_tasks_by_phase(phase.id)

            # Separate into test tasks and implementation tasks
            test_tasks = [t for t in phase_tasks if "test" in t.title.lower()]
            impl_tasks = [t for t in phase_tasks if "test" not in t.title.lower()]

            # Test tasks section (if any and tests requested)
            if test_tasks and self.tests_requested:
                lines.append("### Tests (OPTIONAL - only if tests requested) ⚠️")
                lines.append("")
                lines.append("> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**")
                lines.append("")
                for task in test_tasks:
                    lines.append(task.to_markdown())
                    lines.append("")
                # Implementation tasks section (separate header when tests present)
                if impl_tasks:
                    lines.append(f"### Implementation for {phase.name}")
                    lines.append("")
                    for task in impl_tasks:
                        lines.append(task.to_markdown())
                        lines.append("")
            else:
                # No test tasks - render all phase tasks directly
                for task in phase_tasks:
                    lines.append(task.to_markdown())
                    lines.append("")

            # Checkpoint
            if phase.checkpoint:
                lines.append(f"**Checkpoint**: {phase.checkpoint}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Dependencies & Execution Order section
        lines.extend([
            "## Dependencies & Execution Order",
            "",
            "### Phase Dependencies",
            "",
        ])

        for phase in sorted(self.phases, key=lambda p: p.number):
            phase_tasks = self.get_tasks_by_phase(phase.id)
            deps = set()
            for task in phase_tasks:
                for dep in task.dependencies:
                    # Find which phase the dependency belongs to
                    for t in self.tasks:
                        if t.id == dep and t.phase != phase.id:
                            deps.add(t.phase)
            if deps:
                lines.append(f"- **{phase.name}**: Depends on {', '.join(deps)}")
            else:
                lines.append(f"- **{phase.name}**: No dependencies - can start immediately")
        lines.append("")

        # Parallel opportunities
        if self.parallel_opportunities:
            lines.extend(["### Parallel Opportunities", ""])
            for opp in self.parallel_opportunities:
                lines.append(f"- {opp}")
            lines.append("")

        # Implementation strategy
        if self.implementation_strategy:
            lines.extend([
                "## Implementation Strategy",
                "",
                self.implementation_strategy,
                "",
            ])

        # Summary table
        progress = self.get_progress()
        total = len(self.tasks)
        completed = progress.get("completed", 0)

        lines.extend([
            "---",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Total Tasks** | {total} |",
            f"| **Completed Tasks** | {completed} |",
            f"| **Remaining Tasks** | {total - completed} |",
        ])

        # Count tasks by priority
        p1_count = len([t for t in self.tasks if t.priority == "P1"])
        p2_count = len([t for t in self.tasks if t.priority == "P2"])
        p3_count = len([t for t in self.tasks if t.priority == "P3"])
        parallel_count = len([t for t in self.tasks if t.is_parallel])

        lines.extend([
            f"| **P1 (Critical)** | {p1_count} |",
            f"| **P2 (Important)** | {p2_count} |",
            f"| **P3 (Nice to have)** | {p3_count} |",
            f"| **Parallel Opportunities** | {parallel_count} tasks marked [P] |",
            "",
        ])

        # Notes
        lines.extend([
            "---",
            "",
            "## Notes",
            "",
            "- [P] tasks = different files, no dependencies within phase",
            "- Each phase should be independently testable where possible",
            "- Commit after each task or logical group",
            "- Stop at any checkpoint to validate progress",
            "",
        ])

        return "\n".join(lines)


# =============================================================================
# Clarification Models
# =============================================================================


class ClarificationQuestion(BaseModel):
    """Question generated during clarification phase."""

    id: str
    question: str
    context: str = ""  # Why this needs clarification
    options: list[str] = Field(default_factory=list)  # Suggested answers
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None

    def to_markdown(self) -> str:
        """Export question to Markdown format."""
        lines = [f"### {self.id}: {self.question}", ""]
        if self.context:
            lines.extend([f"**Context**: {self.context}", ""])
        if self.options:
            lines.append("**Options**:")
            for i, option in enumerate(self.options, 1):
                lines.append(f"{i}. {option}")
            lines.append("")
        if self.answer:
            lines.append(f"**Answer**: {self.answer}")
        return "\n".join(lines)


# =============================================================================
# Analysis Models
# =============================================================================


class AnalysisIssue(BaseModel):
    """Issue found during consistency analysis."""

    severity: str  # "error", "warning", "info"
    category: str  # "missing", "inconsistent", "incomplete"
    message: str
    location: str = ""  # Where the issue was found
    suggestion: str = ""  # How to fix


class AnalysisReport(BaseModel):
    """Report from consistency analysis across artifacts."""

    feature_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    issues: list[AnalysisIssue] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return len(self.issues) > 0

    @property
    def has_errors(self) -> bool:
        """Check if any error-level issues were found."""
        return any(issue.severity == "error" for issue in self.issues)

    def to_markdown(self) -> str:
        """Export analysis report to Markdown format."""
        lines = [
            f"# Analysis Report: {self.feature_id}",
            "",
            f"**Generated**: {self.created_at.isoformat()}",
            "",
        ]

        if not self.issues:
            lines.extend(["## Status: PASS", "", "No issues found."])
        else:
            error_count = sum(1 for i in self.issues if i.severity == "error")
            warning_count = sum(1 for i in self.issues if i.severity == "warning")
            lines.extend(
                [
                    f"## Status: {'FAIL' if error_count else 'WARNINGS'}",
                    "",
                    f"- Errors: {error_count}",
                    f"- Warnings: {warning_count}",
                    "",
                    "## Issues",
                    "",
                ]
            )
            for issue in self.issues:
                icon = {"error": "[ERROR]", "warning": "[WARN]", "info": "[INFO]"}.get(
                    issue.severity, ""
                )
                lines.append(f"- {icon} **{issue.category}**: {issue.message}")
                if issue.location:
                    lines.append(f"  - Location: {issue.location}")
                if issue.suggestion:
                    lines.append(f"  - Suggestion: {issue.suggestion}")
                lines.append("")

        if self.recommendations:
            lines.extend(["## Recommendations", ""])
            for rec in self.recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)


# =============================================================================
# LLM Response Models
# =============================================================================


class LLMResponse(BaseModel):
    """Standard response from LLM operations."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    content: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)  # Token counts
    raw_response: Optional[Any] = None  # Original API response


class GeneratedArtifact(BaseModel):
    """Result of an LLM-powered generation operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    artifact_type: str  # "specification", "plan", "tasks"
    content: BaseModel  # The generated Pydantic model
    generation_time: float  # Seconds
    model_used: str
    tokens_used: int
    retries: int = 0  # Number of retry attempts
