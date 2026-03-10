"""
Backup system for memory files.

Automatically backs up memory files before significant operations.
"""

import shutil
import gzip
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from collections import OrderedDict

from .logging import get_logger


class MemoryBackup:
    """Manages memory file backups."""

    # Maximum number of backups to keep per project
    MAX_BACKUPS = 10

    # Compress backups larger than this size (bytes)
    COMPRESSION_THRESHOLD = 10240  # 10KB

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize backup system.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"
        self.backup_dir = self.global_home / "memory" / "backups"

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        project_id: str,
        file_types: Optional[List[str]] = None
    ) -> Optional[Path]:
        """Create backup for project memory files.

        Args:
            project_id: Project identifier
            file_types: List of file types to backup (default: all)

        Returns:
            Path to backup directory or None if failed
        """
        if file_types is None:
            file_types = ["lessons", "patterns", "architecture", "projects-log", "handoff"]

        # Create backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{project_id}_{timestamp}"

        try:
            backup_path.mkdir(parents=True, exist_ok=True)

            # Copy each file
            for file_type in file_types:
                source = self._get_file_path(project_id, file_type)

                if source.exists():
                    dest = backup_path / source.name

                    # Copy file
                    shutil.copy2(source, dest)

                    # Compress if large
                    if dest.stat().st_size > self.COMPRESSION_THRESHOLD:
                        self._compress_file(dest)

            # Create backup manifest
            self._create_manifest(backup_path, project_id, file_types)

            # Clean old backups
            self._cleanup_old_backups(project_id)

            return backup_path

        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")

            # Cleanup failed backup
            if backup_path.exists():
                shutil.rmtree(backup_path)

            return None

    def restore_backup(
        self,
        project_id: str,
        backup_timestamp: str,
        file_types: Optional[List[str]] = None
    ) -> bool:
        """Restore files from backup.

        Args:
            project_id: Project identifier
            backup_timestamp: Backup timestamp (e.g., "20250310_120000")
            file_types: List of file types to restore (default: all)

        Returns:
            True if successful
        """
        backup_path = self.backup_dir / f"{project_id}_{backup_timestamp}"

        if not backup_path.exists():
            self.logger.error(f"Backup not found: {backup_path}")
            return False

        if file_types is None:
            file_types = ["lessons", "patterns", "architecture", "projects-log", "handoff"]

        try:
            for file_type in file_types:
                backup_file = backup_path / f"{self._get_filename(file_type)}"

                # Check for compressed version
                if not backup_file.exists():
                    backup_file = backup_path / f"{self._get_filename(file_type)}.gz"

                if backup_file.exists():
                    dest = self._get_file_path(project_id, file_type)

                    # Decompress if needed
                    if backup_file.suffix == ".gz":
                        self._decompress_file(backup_file, dest)
                    else:
                        shutil.copy2(backup_file, dest)

            return True

        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False

    def list_backups(self, project_id: str) -> List[Dict[str, any]]:
        """List available backups for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of backup info dicts
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith(project_id):
                # Extract timestamp
                parts = backup_dir.name.split("_")
                if len(parts) >= 2:
                    timestamp = "_".join(parts[1:])

                    # Get size
                    size = sum(
                        f.stat().st_size
                        for f in backup_dir.rglob("*")
                        if f.is_file()
                    )

                    backups.append({
                        "timestamp": timestamp,
                        "path": str(backup_dir),
                        "size_bytes": size
                    })

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)

        return backups

    def _cleanup_old_backups(self, project_id: str) -> None:
        """Remove old backups beyond MAX_BACKUPS limit.

        Args:
            project_id: Project identifier
        """
        backups = self.list_backups(project_id)

        if len(backups) > self.MAX_BACKUPS:
            # Remove oldest backups
            for backup in backups[self.MAX_BACKUPS:]:
                backup_path = Path(backup["path"])

                try:
                    shutil.rmtree(backup_path)
                    self.logger.info(f"Removed old backup: {backup_path}")
                except Exception as e:
                    self.logger.warning(f"Error removing old backup: {e}")

    def _compress_file(self, file_path: Path) -> None:
        """Compress file with gzip.

        Args:
            file_path: Path to file
        """
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")

        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove uncompressed file
        file_path.unlink()

    def _decompress_file(
        self,
        compressed_path: Path,
        dest_path: Path
    ) -> None:
        """Decompress gzip file.

        Args:
            compressed_path: Path to compressed file
            dest_path: Destination path
        """
        with gzip.open(compressed_path, 'rb') as f_in:
            with open(dest_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def _create_manifest(
        self,
        backup_path: Path,
        project_id: str,
        file_types: List[str]
    ) -> None:
        """Create backup manifest file.

        Args:
            backup_path: Path to backup directory
            project_id: Project identifier
            file_types: List of backed up file types
        """
        manifest = {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "file_types": file_types,
            "backup_path": str(backup_path)
        }

        manifest_path = backup_path / "manifest.json"

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

    def _get_file_path(self, project_id: str, file_type: str) -> Path:
        """Get path to memory file.

        Args:
            project_id: Project identifier
            file_type: Type of memory file

        Returns:
            Path to file
        """
        filename = self._get_filename(file_type)

        if project_id == ".global":
            return self.global_home / "memory" / "projects" / ".global" / filename
        else:
            return self.global_home / "memory" / "projects" / project_id / filename

    def _get_filename(self, file_type: str) -> str:
        """Get filename for file type.

        Args:
            file_type: Type of memory file

        Returns:
            Filename
        """
        filenames = {
            "lessons": "lessons.md",
            "patterns": "patterns.md",
            "architecture": "architecture.md",
            "projects-log": "projects-log.md",
            "handoff": "handoff.md"
        }

        return filenames.get(file_type, f"{file_type}.md")


class AutoBackup:
    """Automatic backup before write operations."""

    def __init__(self, backup_system: MemoryBackup):
        """Initialize auto-backup.

        Args:
            backup_system: MemoryBackup instance
        """
        self.backup_system = backup_system
        self._last_backup = None

    def backup_before_write(
        self,
        project_id: str,
        file_type: str
    ) -> Optional[Path]:
        """Backup before writing to file.

        Args:
            project_id: Project identifier
            file_type: File type being written

        Returns:
            Backup path or None
        """
        # Check if we've backed up recently (within last hour)
        # to avoid excessive backups during bulk operations

        return self.backup_system.create_backup(
            project_id=project_id,
            file_types=[file_type]
        )
