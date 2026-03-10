"""
Migration tool for existing SpecKit configurations.

Handles migration from old configs to new format.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..logging import get_logger
from .config_merger import ConfigMerger


class ConfigMigrator:
    """Migrates existing SpecKit configurations to new format."""

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize config migrator.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"
        self.config_merger = ConfigMerger(global_home)

    def detect_old_configs(self) -> List[Path]:
        """Detect old SpecKit configurations in projects.

        Returns:
            List of paths to old config files
        """
        old_configs = []

        # Search common project locations
        search_paths = [
            self.global_home / "projects",
            Path.home() / "Projects",
            Path.home() / "IdeaProjects",
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            for project_dir in search_path.iterdir():
                if project_dir.is_dir():
                    # Look for .spec-kit directory
                    spec_kit_dir = project_dir / ".spec-kit"
                    if spec_kit_dir.exists():
                        config_file = spec_kit_dir / "config.json"
                        if config_file.exists():
                            old_configs.append(config_file)

        return old_configs

    def migrate_config(
        self,
        old_config_path: Path,
        new_project_id: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict:
        """Migrate a single config to new format.

        Args:
            old_config_path: Path to old config.json
            new_project_id: Optional new project ID to use
            dry_run: If True, only show what would happen

        Returns:
            Migration result
        """
        try:
            with open(old_config_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)

            # Extract project info
            project_id = new_project_id or old_config.get("project_id", old_config_path.parent.parent.name)
            project_name = old_config.get("project_name", project_id)

            # New format
            new_config = {
                "project_id": project_id,
                "project_name": project_name,
                "memory_enabled": True,
                "created_at": datetime.now().isoformat(),
                "memory_config": {
                    "auto_save": True,
                    "vector_memory": False,
                    "skillsmp_search": True,
                    "context_optimization": True
                },
                "paths": {
                    "memory": ".claude/memory/",
                    "lessons": "lessons.md",
                    "patterns": "paths.md",
                    "architecture": "architecture.md",
                    "projects_log": "projects-log.md",
                    "handoff": "handoff.md"
                },
                "_migrated_from": str(old_config_path)
            }

            if dry_run:
                return {
                    "status": "dry_run",
                    "old_config": old_config,
                    "new_config": new_config,
                    "config_path": old_config_path
                }

            # Write new format
            memory_config_dir = self.global_home / "memory" / "projects" / project_id
            memory_config_dir.mkdir(parents=True, exist_ok=True)

            new_config_path = memory_config_dir / ".spec-kit" / "project.json"
            new_config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(new_config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2)

            return {
                "status": "success",
                "old_config": old_config,
                "new_config": new_config,
                "old_path": str(old_config_path),
                "new_path": str(new_config_path)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "config_path": str(old_config_path)
            }

    def migrate_all(
        self,
        dry_run: bool = False
    ) -> List[Dict]:
        """Migrate all detected old configs.

        Args:
            dry_run: If True, only show what would happen

        Returns:
            List of migration results
        """
        old_configs = self.detect_old_configs()

        results = []

        for config_path in old_configs:
            result = self.migrate_config(config_path, dry_run=dry_run)
            results.append(result)

            self.logger.info(f"Migrated: {config_path}")

        return results
