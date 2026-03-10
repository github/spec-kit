"""
Configuration backup and merge utility for SpecKit Memory installation.

Handles existing configs with backup + merge strategy.
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from ..logging import get_logger


class ConfigMerger:
    """Manages configuration backup and merging."""

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize config merger.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
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

        # Copy entire config directory
        if self.config_dir.exists():
            shutil.copytree(self.config_dir, backup_path / "config", dirs_exist_ok=True)

        self.logger.info(f"Config backed up to: {backup_path}")
        return backup_path

    def merge_configs(
        self,
        source_config: Dict,
        existing_config: Optional[Dict] = None
    ) -> Dict:
        """Merge source config with existing config.

        Args:
            source_config: New configuration
            existing_config: Existing configuration (if any)

        Returns:
            Merged configuration
        """
        if existing_config is None:
            # No existing config, return source as-is
            return source_config.copy()

        # Smart merge: source wins on conflicts
        merged = existing_config.copy()
        merged.update(source_config)

        return merged

    def process_config_conflicts(
        self,
        conflicts: List[Dict]
    ) -> List[Dict]:
        """Process configuration conflicts with user guidance.

        Args:
            conflicts: List of conflict descriptions

        Returns:
            List of resolved conflicts
        """
        resolved = []

        for conflict in conflicts:
            # In automated mode, use smart defaults
            # "source wins" for new configs
            resolved.append({
                **conflict,
                "resolution": "source_wins",
                "reason": "Automated: new configuration takes precedence"
            })

        return resolved

    def create_migration_plan(
        self,
        old_config: Dict,
        new_config: Dict
    ) -> List[str]:
        """Create migration plan from old to new config.

        Args:
            old_config: Old configuration
            new_config: New configuration

        Returns:
            List of migration steps
        """
        steps = []

        # Find changed keys
        old_keys = set(old_config.keys())
        new_keys = set(new_config.keys())

        added = new_keys - old_keys
        removed = old_keys - new_keys
        modified = old_keys & new_keys

        if added:
            steps.append(f"Add new keys: {', '.join(added)}")

        if removed:
            steps.append(f"Remove keys: {', '.join(removed)}")

        if modified:
            steps.append(f"Update keys: {', '.join(modified)}")

        return steps
