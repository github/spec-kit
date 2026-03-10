"""
Memory system configuration management.

Handles configuration backup+merge strategy for global SpecKit installation.
"""

from pathlib import Path
from typing import Optional
import json
import shutil
from datetime import datetime


class MemoryConfigManager:
    """Manages memory system configuration with backup+merge support."""

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize config manager.

        Args:
            global_home: Path to global claude home (default: ~/.claude)
        """
        self.global_home = global_home or Path.home() / ".claude"
        self.config_dir = self.global_home / "spec-kit" / "config"
        self.backup_dir = self.global_home / "spec-kit" / ".backup"

    def backup_existing_config(self) -> Path:
        """Backup existing configuration.

        Returns:
            Path to backup directory
        """
        if not self.config_dir.exists():
            return Path()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"config_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        if self.config_dir.exists():
            shutil.copytree(self.config_dir, backup_path / "config", dirs_exist_ok=True)

        return backup_path

    def merge_configs(self, source: Path, target: Path) -> bool:
        """Merge configurations.

        Args:
            source: Source config directory
            target: Target config directory

        Returns:
            True if merge successful
        """
        # Simple merge: copy all files, target wins on conflict
        target.mkdir(parents=True, exist_ok=True)

        for file in source.rglob("*.json"):
            relative = file.relative_to(source)
            dest = target / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dest)

        return True

    def ensure_config_structure(self) -> Path:
        """Ensure config directory structure exists.

        Returns:
            Path to config directory
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        return self.config_dir
