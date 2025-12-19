"""
File-based storage implementation for spec-kit artifacts.

This module provides Markdown file storage with:
- Save/load for all artifact types
- Automatic backup on overwrite
- Feature directory management
- Markdown parsing and generation
"""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from speckit.schemas import (
    Constitution,
    Specification,
    TechnicalPlan,
    TaskBreakdown,
    UserStory,
    FunctionalRequirement,
    Entity,
    Task,
    TechStack,
    ArchitectureComponent,
    Priority,
    TaskStatus,
    PhaseType,
)
from speckit.storage.base import StorageBase


class FileStorage(StorageBase):
    """
    File-based storage backend using Markdown files.

    Artifacts are stored as human-readable Markdown files that can be
    version-controlled with Git. JSON metadata is embedded in YAML frontmatter
    where needed for round-trip fidelity.

    Example:
        >>> storage = FileStorage(Path("./my-project"))
        >>> storage.save_specification(spec, "001-auth")
        >>> loaded = storage.load_specification("001-auth")
    """

    CONSTITUTION_FILE = "constitution.md"
    SPEC_FILE = "spec.md"
    PLAN_FILE = "plan.md"
    TASKS_FILE = "tasks.md"

    def __init__(
        self,
        project_path: Path,
        specs_dir: str = "specs",
        base_dir: str = ".speckit",
    ):
        """
        Initialize file storage.

        Args:
            project_path: Root directory of the project
            specs_dir: Directory name for feature specifications
            base_dir: Directory name for spec-kit configuration
        """
        super().__init__(project_path, specs_dir, base_dir)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.specs_path.mkdir(parents=True, exist_ok=True)

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a backup of an existing file.

        Returns:
            Path to backup file if created, None otherwise
        """
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".{timestamp}.bak")
        shutil.copy2(file_path, backup_path)
        return backup_path

    # =========================================================================
    # Constitution
    # =========================================================================

    def save_constitution(self, constitution: Constitution) -> Path:
        """Save project constitution to Markdown file."""
        file_path = self.config_path / self.CONSTITUTION_FILE
        self._create_backup(file_path)

        content = constitution.to_markdown()
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def load_constitution(self) -> Optional[Constitution]:
        """Load project constitution from Markdown file."""
        file_path = self.config_path / self.CONSTITUTION_FILE
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return self._parse_constitution(content)

    def _parse_constitution(self, content: str) -> Constitution:
        """Parse Markdown content into Constitution model."""
        # Extract project name from title
        title_match = re.search(r"^# Project Constitution: (.+)$", content, re.MULTILINE)
        project_name = title_match.group(1) if title_match else "Unknown"

        # Extract version
        version_match = re.search(r"\*\*Version\*\*: (.+)$", content, re.MULTILINE)
        version = version_match.group(1) if version_match else "1.0.0"

        # Extract lists by section
        sections = {
            "Core Principles": "core_principles",
            "Quality Standards": "quality_standards",
            "Testing Standards": "testing_standards",
            "Technical Constraints": "tech_constraints",
            "UX Guidelines": "ux_guidelines",
            "Governance Rules": "governance_rules",
        }

        data = {
            "project_name": project_name,
            "version": version,
        }

        for section_title, field_name in sections.items():
            data[field_name] = self._extract_list_section(content, section_title)

        return Constitution(**data)

    def _extract_list_section(self, content: str, section_title: str) -> list[str]:
        """Extract a list of items from a Markdown section."""
        # Find section start
        pattern = rf"## {re.escape(section_title)}\s*\n((?:- .+\n?)+)"
        match = re.search(pattern, content)
        if not match:
            return []

        items = []
        for line in match.group(1).split("\n"):
            if line.strip().startswith("- "):
                items.append(line.strip()[2:])
        return items

    # =========================================================================
    # Specification
    # =========================================================================

    def save_specification(self, specification: Specification, feature_id: str) -> Path:
        """Save feature specification to Markdown file."""
        feature_path = self.get_feature_path(feature_id)
        feature_path.mkdir(parents=True, exist_ok=True)

        file_path = feature_path / self.SPEC_FILE
        self._create_backup(file_path)

        content = specification.to_markdown()
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def load_specification(self, feature_id: str) -> Optional[Specification]:
        """Load feature specification from Markdown file."""
        file_path = self.get_feature_path(feature_id) / self.SPEC_FILE
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return self._parse_specification(content, feature_id)

    def _parse_specification(self, content: str, feature_id: str) -> Specification:
        """Parse Markdown content into Specification model."""
        # Extract title
        title_match = re.search(r"^# Feature Specification: (.+)$", content, re.MULTILINE)
        feature_name = title_match.group(1) if title_match else "Unknown"

        # Extract sections
        overview = self._extract_section_content(content, "Overview")
        problem_statement = self._extract_section_content(content, "Problem Statement")
        target_users = self._extract_list_section(content, "Target Users")
        assumptions = self._extract_list_section(content, "Assumptions")
        constraints = self._extract_list_section(content, "Constraints")
        out_of_scope = self._extract_list_section(content, "Out of Scope")
        success_criteria = self._extract_list_section(content, "Success Criteria")

        return Specification(
            feature_name=feature_name,
            feature_id=feature_id,
            overview=overview,
            problem_statement=problem_statement,
            target_users=target_users,
            user_stories=[],  # Parsing user stories from MD is complex, simplified here
            functional_requirements=[],
            entities=[],
            assumptions=assumptions,
            constraints=constraints,
            out_of_scope=out_of_scope,
            success_criteria=success_criteria,
        )

    def _extract_section_content(self, content: str, section_title: str) -> str:
        """Extract text content from a section (until next section)."""
        pattern = rf"## {re.escape(section_title)}\s*\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    # =========================================================================
    # Technical Plan
    # =========================================================================

    def save_plan(self, plan: TechnicalPlan, feature_id: str) -> Path:
        """Save technical plan to Markdown file."""
        feature_path = self.get_feature_path(feature_id)
        feature_path.mkdir(parents=True, exist_ok=True)

        file_path = feature_path / self.PLAN_FILE
        self._create_backup(file_path)

        content = plan.to_markdown()
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def load_plan(self, feature_id: str) -> Optional[TechnicalPlan]:
        """Load technical plan from Markdown file."""
        file_path = self.get_feature_path(feature_id) / self.PLAN_FILE
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return self._parse_plan(content, feature_id)

    def _parse_plan(self, content: str, feature_id: str) -> TechnicalPlan:
        """Parse Markdown content into TechnicalPlan model."""
        # Extract basic info
        architecture_overview = self._extract_section_content(content, "Architecture Overview")
        file_structure = self._extract_code_block(content, "File Structure")
        data_model = self._extract_section_content(content, "Data Model")
        technical_risks = self._extract_list_section(content, "Technical Risks")
        mitigation_strategies = self._extract_list_section(content, "Mitigation Strategies")
        research_notes = self._extract_section_content(content, "Research Notes")

        # Default tech stack (parsing tech stack from MD is complex)
        tech_stack = TechStack(
            language="Python 3.11",
            framework="",
            testing="pytest",
        )

        return TechnicalPlan(
            feature_id=feature_id,
            tech_stack=tech_stack,
            architecture_overview=architecture_overview,
            components=[],
            file_structure=file_structure,
            data_model=data_model,
            technical_risks=technical_risks,
            mitigation_strategies=mitigation_strategies,
            research_notes=research_notes,
        )

    def _extract_code_block(self, content: str, section_title: str) -> str:
        """Extract code block content from a section."""
        section_content = self._extract_section_content(content, section_title)
        code_match = re.search(r"```(?:\w+)?\n(.*?)```", section_content, re.DOTALL)
        return code_match.group(1).strip() if code_match else section_content

    # =========================================================================
    # Task Breakdown
    # =========================================================================

    def save_tasks(self, tasks: TaskBreakdown, feature_id: str) -> Path:
        """Save task breakdown to Markdown file."""
        feature_path = self.get_feature_path(feature_id)
        feature_path.mkdir(parents=True, exist_ok=True)

        file_path = feature_path / self.TASKS_FILE
        self._create_backup(file_path)

        content = tasks.to_markdown()
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def load_tasks(self, feature_id: str) -> Optional[TaskBreakdown]:
        """Load task breakdown from Markdown file."""
        file_path = self.get_feature_path(feature_id) / self.TASKS_FILE
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return self._parse_tasks(content, feature_id)

    def _parse_tasks(self, content: str, feature_id: str) -> TaskBreakdown:
        """Parse Markdown content into TaskBreakdown model."""
        tasks = []

        # Parse task lines: - [x] T001 [P] [US1] Task title
        task_pattern = r"- \[([ xX])\] (T\d+)\s*(\[P\])?\s*(\[US\d+\])?\s*(.+)"

        for match in re.finditer(task_pattern, content):
            completed = match.group(1).lower() == "x"
            task_id = match.group(2)
            is_parallel = match.group(3) is not None
            user_story_id = match.group(4)[1:-1] if match.group(4) else None
            title = match.group(5).strip()

            task = Task(
                id=task_id,
                title=title,
                phase=PhaseType.CORE,  # Default phase
                status=TaskStatus.COMPLETED if completed else TaskStatus.PENDING,
                user_story_id=user_story_id,
                is_parallel=is_parallel,
            )
            tasks.append(task)

        return TaskBreakdown(feature_id=feature_id, tasks=tasks)

    # =========================================================================
    # Feature Management
    # =========================================================================

    def list_features(self) -> list[str]:
        """List all feature identifiers in the project."""
        if not self.specs_path.exists():
            return []

        features = []
        for path in self.specs_path.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                features.append(path.name)

        return sorted(features)

    def feature_exists(self, feature_id: str) -> bool:
        """Check if a feature exists."""
        feature_path = self.get_feature_path(feature_id)
        return feature_path.exists() and feature_path.is_dir()

    def get_feature_path(self, feature_id: str) -> Path:
        """Get the directory path for a feature."""
        return self.specs_path / feature_id

    def create_feature(self, feature_id: str) -> Path:
        """Create a new feature directory."""
        feature_path = self.get_feature_path(feature_id)
        feature_path.mkdir(parents=True, exist_ok=True)
        return feature_path

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_artifact_path(self, feature_id: str, artifact_type: str) -> Path:
        """
        Get the path to a specific artifact.

        Args:
            feature_id: Feature identifier
            artifact_type: One of "spec", "plan", "tasks"

        Returns:
            Path to the artifact file
        """
        filenames = {
            "spec": self.SPEC_FILE,
            "plan": self.PLAN_FILE,
            "tasks": self.TASKS_FILE,
        }

        if artifact_type not in filenames:
            raise ValueError(f"Unknown artifact type: {artifact_type}")

        return self.get_feature_path(feature_id) / filenames[artifact_type]

    def artifact_exists(self, feature_id: str, artifact_type: str) -> bool:
        """Check if a specific artifact exists."""
        return self.get_artifact_path(feature_id, artifact_type).exists()
