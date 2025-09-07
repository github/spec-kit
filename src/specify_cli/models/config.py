"""
Configuration data models for spec-kit

These models define the structure for project and global configurations,
supporting TOML serialization and validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BranchNamingConfig:
    """Configuration for branch naming patterns"""

    default_pattern: str = "feature/{feature-name}"
    patterns: List[str] = field(
        default_factory=lambda: [
            "feature/{feature-name}",
            "bugfix/{bug-id}",
            "hotfix/{version}",
            "epic/{epic-name}",
        ]
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        return {
            "default_pattern": self.default_pattern,
            "patterns": self.patterns.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BranchNamingConfig":
        """Create instance from dictionary (TOML deserialization)"""
        return cls(
            default_pattern=data.get("default_pattern", "feature/{feature-name}"),
            patterns=data.get(
                "patterns",
                [
                    "feature/{feature-name}",
                    "bugfix/{bug-id}",
                    "hotfix/{version}",
                    "epic/{epic-name}",
                ],
            ),
        )


@dataclass
class TemplateConfig:
    """Configuration for template engine settings"""

    ai_assistant: str = "claude"
    custom_templates_dir: Optional[Path] = None
    template_cache_enabled: bool = True
    template_variables: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        result: Dict[str, Any] = {
            "ai_assistant": self.ai_assistant,
            "template_cache_enabled": self.template_cache_enabled,
        }

        if self.custom_templates_dir:
            result["custom_templates_dir"] = str(self.custom_templates_dir)

        if self.template_variables:
            # Preserve nested dict typing by storing as Any
            result["template_variables"] = dict(self.template_variables)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateConfig":
        """Create instance from dictionary (TOML deserialization)"""
        custom_templates_dir = None
        if "custom_templates_dir" in data and data["custom_templates_dir"]:
            custom_templates_dir = Path(data["custom_templates_dir"])

        return cls(
            ai_assistant=data.get("ai_assistant", "claude"),
            custom_templates_dir=custom_templates_dir,
            template_cache_enabled=data.get("template_cache_enabled", True),
            template_variables=data.get("template_variables", {}),
        )


@dataclass
class ProjectConfig:
    """Main project configuration"""

    name: str
    branch_naming: BranchNamingConfig = field(default_factory=BranchNamingConfig)
    template_settings: TemplateConfig = field(default_factory=TemplateConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for TOML serialization"""
        return {
            "project": {
                "name": self.name,
                "branch_naming": self.branch_naming.to_dict(),
                "template_settings": self.template_settings.to_dict(),
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """Create instance from dictionary (TOML deserialization)"""
        project_data = data.get("project", {})

        branch_naming = BranchNamingConfig()
        if "branch_naming" in project_data:
            branch_naming = BranchNamingConfig.from_dict(project_data["branch_naming"])

        template_settings = TemplateConfig()
        if "template_settings" in project_data:
            template_settings = TemplateConfig.from_dict(
                project_data["template_settings"]
            )

        return cls(
            name=project_data.get("name", ""),
            branch_naming=branch_naming,
            template_settings=template_settings,
        )

    @classmethod
    def create_default(cls, name: str = "default-project") -> "ProjectConfig":
        """Create a default configuration"""
        return cls(
            name=name,
            branch_naming=BranchNamingConfig(),
            template_settings=TemplateConfig(),
        )
