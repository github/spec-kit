"""
Configuration service for managing project and global settings

Provides TOML-based configuration management with backup/restore capabilities.
"""

import re
import shutil
import tomllib
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import tomli_w

from ..models.config import ProjectConfig


class ConfigService(ABC):
    """Abstract interface for configuration management"""

    @abstractmethod
    def load_project_config(self, project_path: Path) -> Optional[ProjectConfig]:
        """Load project configuration from .specify/config.toml"""
        pass

    @abstractmethod
    def save_project_config(self, project_path: Path, config: ProjectConfig) -> bool:
        """Save project configuration to .specify/config.toml"""
        pass

    @abstractmethod
    def load_global_config(self) -> Optional[ProjectConfig]:
        """Load global configuration from ~/.specify/config.toml"""
        pass

    @abstractmethod
    def save_global_config(self, config: ProjectConfig) -> bool:
        """Save global configuration to ~/.specify/config.toml"""
        pass

    @abstractmethod
    def get_merged_config(self, project_path: Path) -> ProjectConfig:
        """Get merged configuration (global defaults + project overrides)"""
        pass

    @abstractmethod
    def validate_branch_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """Validate branch naming pattern"""
        pass

    @abstractmethod
    def expand_branch_name(self, pattern: str, context: Dict[str, str]) -> str:
        """Expand branch name pattern with context variables"""
        pass

    @abstractmethod
    def backup_config(self, project_path: Path) -> Path:
        """Create backup of project configuration"""
        pass

    @abstractmethod
    def restore_config(self, project_path: Path, backup_path: Path) -> bool:
        """Restore configuration from backup"""
        pass


class TomlConfigService(ConfigService):
    """TOML-based configuration service implementation"""

    def __init__(self):
        self._global_config_dir = Path.home() / ".specify"
        self._global_config_file = self._global_config_dir / "config.toml"

    def load_project_config(self, project_path: Path) -> Optional[ProjectConfig]:
        """Load project configuration from .specify/config.toml"""
        config_file = project_path / ".specify" / "config.toml"

        if not config_file.exists():
            return None

        try:
            with open(config_file, "rb") as f:
                data = tomllib.load(f)
            return ProjectConfig.from_dict(data)
        except (OSError, tomllib.TOMLDecodeError, KeyError):
            # Log error in real implementation
            return None

    def save_project_config(self, project_path: Path, config: ProjectConfig) -> bool:
        """Save project configuration to .specify/config.toml"""
        try:
            config_dir = project_path / ".specify"
            config_dir.mkdir(exist_ok=True)

            config_file = config_dir / "config.toml"
            data = config.to_dict()

            with open(config_file, "wb") as f:
                tomli_w.dump(data, f)
            return True
        except (OSError, PermissionError):
            # Log error in real implementation
            return False

    def load_global_config(self) -> Optional[ProjectConfig]:
        """Load global configuration from ~/.specify/config.toml"""
        if not self._global_config_file.exists():
            return None

        try:
            with open(self._global_config_file, "rb") as f:
                data = tomllib.load(f)
            return ProjectConfig.from_dict(data)
        except (OSError, tomllib.TOMLDecodeError, KeyError):
            # Log error in real implementation
            return None

    def save_global_config(self, config: ProjectConfig) -> bool:
        """Save global configuration to ~/.specify/config.toml"""
        try:
            self._global_config_dir.mkdir(exist_ok=True)
            data = config.to_dict()

            with open(self._global_config_file, "wb") as f:
                tomli_w.dump(data, f)
            return True
        except (OSError, PermissionError):
            # Log error in real implementation
            return False

    def get_merged_config(self, project_path: Path) -> ProjectConfig:
        """Get merged configuration (global defaults + project overrides)"""
        # Start with defaults
        merged = ProjectConfig.create_default("merged-config")

        # Apply global config if it exists
        global_config = self.load_global_config()
        if global_config:
            # Merge global settings
            merged.branch_naming = global_config.branch_naming
            merged.template_settings = global_config.template_settings

        # Apply project config if it exists
        project_config = self.load_project_config(project_path)
        if project_config:
            # Project config overrides global/defaults
            merged.name = project_config.name
            merged.branch_naming = project_config.branch_naming
            merged.template_settings = project_config.template_settings
        else:
            # No project config, use project directory name
            merged.name = project_path.name

        return merged

    def validate_branch_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """Validate branch naming pattern"""
        if not pattern:
            return False, "Pattern cannot be empty"

        if not pattern.strip():
            return False, "Pattern cannot be empty or whitespace only"

        if pattern == "{}":
            return False, "Pattern cannot be just empty braces"

        # Check for unclosed braces
        open_count = pattern.count("{")
        close_count = pattern.count("}")
        if open_count != close_count:
            return False, "Mismatched braces in pattern"

        # Check for invalid characters in the pattern itself
        if " " in pattern:
            return False, "Pattern cannot contain spaces"

        if pattern.isupper():
            return False, "Pattern cannot be all uppercase"

        if "." in pattern:
            return False, "Pattern cannot contain dots"

        if pattern.startswith("/") or pattern.endswith("/"):
            return False, "Pattern cannot start or end with slash"

        if "//" in pattern:
            return False, "Pattern cannot contain double slashes"

        if ":" in pattern:
            return False, "Pattern cannot contain colons"

        if "\\" in pattern:
            return False, "Pattern cannot contain backslashes"

        # Check for invalid characters in variable names
        var_pattern = re.compile(r"\{([^}]+)\}")
        matches = var_pattern.findall(pattern)

        for var_name in matches:
            if not var_name:
                return False, "Empty variable name in braces"
            # Allow alphanumeric, hyphens, and underscores in variable names
            if not re.match(r"^[a-zA-Z0-9_-]+$", var_name):
                return False, f"Invalid characters in variable name: {var_name}"

        return True, None

    def expand_branch_name(self, pattern: str, context: Dict[str, str]) -> str:
        """Expand branch name pattern with context variables"""
        result = pattern

        # Find all variables in the pattern
        var_pattern = re.compile(r"\{([^}]+)\}")
        matches = var_pattern.findall(pattern)

        for var_name in matches:
            placeholder = f"{{{var_name}}}"
            value = context.get(var_name, placeholder)  # Keep placeholder if not found
            result = result.replace(placeholder, value)

        return result

    def backup_config(self, project_path: Path) -> Path:
        """Create backup of project configuration"""
        config_file = project_path / ".specify" / "config.toml"

        # Create backup directory (and parent directories)
        backup_dir = project_path / ".specify" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"config_backup_{timestamp}.toml"

        if not config_file.exists():
            # Create empty backup file to satisfy contract
            backup_path.touch()
            return backup_path

        shutil.copy2(config_file, backup_path)
        return backup_path

    def restore_config(self, project_path: Path, backup_path: Path) -> bool:
        """Restore configuration from backup"""
        if not backup_path.exists():
            return False

        try:
            config_dir = project_path / ".specify"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.toml"

            shutil.copy2(backup_path, config_file)
            return True
        except (OSError, PermissionError):
            # Log error in real implementation
            return False
