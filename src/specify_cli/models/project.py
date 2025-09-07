"""
Project-related data models for spec-kit

These models define project context and template variables for the Jinja2 engine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TemplateDict(dict):
    """Custom dict that prioritizes key access over dict methods in Jinja2 templates"""

    def __getattribute__(self, name):
        # If the name is a key in the dict, return the value instead of the method
        if name in self:
            return self[name]
        return super().__getattribute__(name)


@dataclass
class TemplateContext:
    """Context data for template rendering with Jinja2"""

    # Project information
    project_name: str
    project_description: str = ""
    project_path: Optional[Path] = None

    # Branch information
    branch_name: str = ""
    feature_name: str = ""
    task_name: str = ""

    # User/environment information
    author_name: str = ""
    author_email: str = ""
    creation_date: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d")
    )
    creation_year: str = field(default_factory=lambda: str(datetime.now().year))

    # Template-specific variables
    template_variables: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # AI assistant configuration
    ai_assistant: str = "claude"
    ai_context: Dict[str, str] = field(default_factory=dict)

    # Git information
    git_remote_url: str = ""
    git_branch: str = ""

    # Specification information
    spec_number: str = ""
    spec_title: str = ""
    spec_type: str = "feature"  # feature, bugfix, hotfix, epic

    # Backwards compatibility fields for tests
    branch_type: str = ""
    additional_vars: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Handle backwards compatibility and setup computed fields"""
        # Set branch_type based on spec_type for backwards compatibility
        if not self.branch_type and self.spec_type:
            self.branch_type = self.spec_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Jinja2 template rendering"""
        result = {
            # Basic project info
            "project_name": self.project_name,
            "project_description": self.project_description,
            "project_path": str(self.project_path) if self.project_path else "",
            # Branch and feature info
            "branch_name": self.branch_name,
            "feature_name": self.feature_name,
            "task_name": self.task_name,
            # Author and timing
            "author_name": self.author_name,
            "author_email": self.author_email,
            "creation_date": self.creation_date,
            "creation_year": self.creation_year,
            # AI assistant
            "ai_assistant": self.ai_assistant,
            "ai_context": self.ai_context.copy(),
            # Git information
            "git_remote_url": self.git_remote_url,
            "git_branch": self.git_branch,
            # Specification
            "spec_number": self.spec_number,
            "spec_title": self.spec_title,
            "spec_type": self.spec_type,
            # Backwards compatibility
            "branch_type": self.branch_type,
            "additional_vars": TemplateDict(
                self.additional_vars
            ),  # Use TemplateDict to avoid method conflicts
            # Template variables (merged with custom fields and additional_vars)
            **self.template_variables,
            **self.custom_fields,
            # Don't flatten additional_vars to avoid conflicts with dict methods like .items()
        }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateContext":
        """Create TemplateContext from dictionary"""
        # Extract known fields
        known_fields = {
            "project_name",
            "project_description",
            "project_path",
            "branch_name",
            "feature_name",
            "task_name",
            "author_name",
            "author_email",
            "creation_date",
            "creation_year",
            "ai_assistant",
            "ai_context",
            "git_remote_url",
            "git_branch",
            "spec_number",
            "spec_title",
            "spec_type",
        }

        # Separate known fields from custom variables
        context_data = {}
        custom_fields = {}

        for key, value in data.items():
            if key in known_fields:
                context_data[key] = value
            else:
                custom_fields[key] = value

        # Handle project_path conversion
        if "project_path" in context_data and context_data["project_path"]:
            context_data["project_path"] = Path(context_data["project_path"])

        # Set custom fields
        context_data["custom_fields"] = custom_fields

        return cls(**context_data)

    def merge_variables(self, variables: Dict[str, Any]) -> "TemplateContext":
        """Create new context with merged template variables"""
        new_context = TemplateContext(
            project_name=self.project_name,
            project_description=self.project_description,
            project_path=self.project_path,
            branch_name=self.branch_name,
            feature_name=self.feature_name,
            task_name=self.task_name,
            author_name=self.author_name,
            author_email=self.author_email,
            creation_date=self.creation_date,
            creation_year=self.creation_year,
            ai_assistant=self.ai_assistant,
            ai_context=self.ai_context.copy(),
            git_remote_url=self.git_remote_url,
            git_branch=self.git_branch,
            spec_number=self.spec_number,
            spec_title=self.spec_title,
            spec_type=self.spec_type,
            template_variables={**self.template_variables, **variables},
            custom_fields=self.custom_fields.copy(),
        )
        return new_context

    @classmethod
    def create_default(cls, project_name: str) -> "TemplateContext":
        """Create a default template context for a project"""
        return cls(
            project_name=project_name,
            project_description=f"Project: {project_name}",
            author_name="Developer",
            ai_assistant="claude",
        )


@dataclass
class TemplateFile:
    """Represents a rendered template file"""

    template_path: Path
    output_path: str
    content: str
    is_executable: bool = False

    def __post_init__(self):
        """Ensure template_path is Path object"""
        if isinstance(self.template_path, str):
            self.template_path = Path(self.template_path)


class ProjectInitStep(Enum):
    """Steps in project initialization process"""

    VALIDATION = "validation"
    DIRECTORY_CREATION = "directory_creation"
    GIT_INIT = "git_init"
    DOWNLOAD = "download"
    TEMPLATE_RENDER = "template_render"
    CONFIG_SAVE = "config_save"
    BRANCH_CREATION = "branch_creation"
    STRUCTURE_SETUP = "structure_setup"
    FINALIZATION = "finalization"


@dataclass
class ProjectInitOptions:
    """Options for project initialization"""

    project_name: Optional[str]
    ai_assistant: str = "claude"
    use_current_dir: bool = False
    skip_git: bool = False
    ignore_agent_tools: bool = False
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class ProjectInitResult:
    """Result of project initialization"""

    success: bool
    project_path: Path
    completed_steps: List[ProjectInitStep] = field(default_factory=list)
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
