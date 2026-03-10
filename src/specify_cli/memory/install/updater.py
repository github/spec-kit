"""
Update mechanism for SpecKit global installation.

Handles delta updates and rollback support.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from ..logging import get_logger
from .config_merger import ConfigMerger
from .ollama_checker import OllamaChecker


class UpdateManager:
    """Manages SpecKit memory extension updates."""

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize update manager.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"
        self.config_dir = self.global_home / "spec-kit"
        self.version_file = self.config_dir / ".version"

        self.config_merger = ConfigMerger(global_home)

    def get_current_version(self) -> str:
        """Get currently installed version.

        Returns:
            Version string or "0.0.0" if not found
        """
        if self.version_file.exists():
            try:
                data = json.loads(self.version_file.read_text())
                return data.get("version", "0.0.0")
            except Exception:
                return "0.0.0"
        return "0.0.0"

    def apply_update(
        self,
        new_version: str,
        changes: Dict[str, any],
        auto_accept: bool = False
    ) -> bool:
        """Apply delta update to installation.

        Args:
            new_version: New version to install
            changes: Dict describing changes
            auto_accept: Skip confirmation prompts

        Returns:
            True if update successful
        """
        current_version = self.get_current_version()

        self.logger.info(f"Updating: {current_version} → {new_version}")

        # Backup current version
        backup_path = self.config_merger.backup_existing_config()

        # Apply changes
        success = self._apply_delta_changes(changes)

        if success:
            # Update version file
            self.version_file.parent.mkdir(parents=True, exist_ok=True)
            self.version_file.write_text(json.dumps({
                "version": new_version,
                "updated_at": datetime.now().isoformat()
            }))

            self.logger.info(f"Updated to version {new_version}")
            return True
        else:
            # Rollback on failure
            if backup_path.exists():
                self._rollback(backup_path)
            return False

    def _apply_delta_changes(self, changes: Dict[str, any]) -> bool:
        """Apply only changed files (delta update).

        Args:
            changes: Dict with "added", "modified", "removed" keys

        Returns:
            True if successful
        """
        try:
            # Add new files
            for file_path in changes.get("added", []):
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                # TODO: Copy file from source

            # Modify existing files
            for file_path in changes.get("modified", []):
                # TODO: Apply delta to file
                pass

            # Remove deleted files
            for file_path in changes.get("removed", []):
                Path(file_path).unlink(missing_ok=True)

            return True

        except Exception as e:
            self.logger.error(f"Error applying changes: {e}")
            return False

    def rollback(self, backup_path: Path) -> bool:
        """Rollback to backup version.

        Args:
            backup_path: Path to backup

        Returns:
            True if rollback successful
        """
        try:
            # Restore from backup
            if (backup_path / "config").exists():
                import shutil
                if self.config_dir.exists():
                    shutil.rmtree(self.config_dir)
                shutil.copytree(backup_path / "config", self.config_dir)

            self.logger.info(f"Rolled back to: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def check_for_updates(self) -> Optional[Dict]:
        """Check if updates are available.

        Returns:
            Update info or None
        """
        # TODO: Check GitHub for new releases
        # For now, return None (no updates available)
        return None
