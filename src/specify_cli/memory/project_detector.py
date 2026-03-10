"""
Project auto-detection for global memory system.

Automatically detects current project context and maps to memory storage.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from ..logging import get_logger


class ProjectDetector:
    """Detects current project and maps to memory storage."""

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize project detector.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"

    def detect_current_project(self, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Detect current project context.

        Args:
            cwd: Current working directory (defaults to os.getcwd)

        Returns:
            Dict with project info:
            - project_id: Unique identifier
            - project_name: Human-readable name
            - project_path: Absolute path to project
            - is_git: Whether git repository
            - git_remote: Git remote URL if available
            - memory_path: Path to memory storage
        """
        cwd = cwd or Path.cwd()

        project_info = {
            "project_path": str(cwd),
            "is_git": False,
            "git_remote": None,
        }

        # Check if git repository
        git_dir = self._find_git_dir(cwd)
        if git_dir:
            project_info["is_git"] = True
            project_info["git_root"] = str(git_dir.parent)

            # Try to get remote
            remote = self._get_git_remote(git_dir.parent)
            if remote:
                project_info["git_remote"] = remote

        # Generate project_id and project_name
        project_id, project_name = self._generate_project_identifiers(
            cwd, project_info.get("git_remote")
        )

        project_info["project_id"] = project_id
        project_info["project_name"] = project_name
        project_info["memory_path"] = str(
            self.global_home / "memory" / "projects" / project_id
        )

        return project_info

    def _find_git_dir(self, path: Path) -> Optional[Path]:
        """Find .git directory by traversing up.

        Args:
            path: Starting path

        Returns:
            Path to .git directory or None
        """
        current = Path(path).resolve()

        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.exists():
                return git_dir
            current = current.parent

        return None

    def _get_git_remote(self, git_root: Path) -> Optional[str]:
        """Get git remote URL.

        Args:
            git_root: Path to git repository root

        Returns:
            Remote URL or None
        """
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return None

    def _generate_project_identifiers(
        self,
        cwd: Path,
        git_remote: Optional[str]
    ) -> tuple[str, str]:
        """Generate project_id and project_name.

        Args:
            cwd: Current working directory
            git_remote: Git remote URL if available

        Returns:
            Tuple of (project_id, project_name)
        """
        # If git remote available, use it
        if git_remote:
            # Parse remote URL
            # GitHub: https://github.com/user/repo.git
            # GitLab: https://gitlab.com/user/repo.git
            # SSH: git@github.com:user/repo.git

            # Convert SSH to HTTPS format for parsing
            remote_clean = git_remote
            if remote_clean.startswith("git@"):
                remote_clean = remote_clean.replace(":", "/").replace("git@", "https://")

            parsed = urlparse(remote_clean)

            # Extract user/repo from path
            path_parts = parsed.path.strip("/").replace(".git", "").split("/")

            if len(path_parts) >= 2:
                user, repo = path_parts[0], path_parts[1]
                project_id = f"{user}-{repo}"
                project_name = repo
                return project_id, project_name

        # Fallback to directory name
        dir_name = cwd.name
        project_id = dir_name.lower().replace(" ", "-").replace("_", "-")

        # Remove special characters
        project_id = "".join(c for c in project_id if c.isalnum() or c == "-")

        project_name = dir_name

        return project_id, project_name

    def ensure_project_memory_structure(
        self,
        project_id: str,
        memory_path: Path
    ) -> bool:
        """Ensure memory directory structure exists for project.

        Args:
            project_id: Project identifier
            memory_path: Path to memory storage

        Returns:
            True if successful
        """
        try:
            memory_path = Path(memory_path)
            memory_path.mkdir(parents=True, exist_ok=True)

            # Create .spec-kit directory for project config
            spec_kit_dir = memory_path / ".spec-kit"
            spec_kit_dir.mkdir(exist_ok=True)

            return True

        except Exception as e:
            self.logger.error(f"Error creating memory structure: {e}")
            return False

    def list_all_projects(self) -> list[Dict[str, Any]]:
        """List all projects with memory.

        Returns:
            List of project info dicts
        """
        projects_dir = self.global_home / "memory" / "projects"

        if not projects_dir.exists():
            return []

        projects = []

        for project_path in projects_dir.iterdir():
            if project_path.is_dir():
                # Read project config if exists
                config_file = project_path / ".spec-kit" / "project.json"

                project_info = {
                    "project_id": project_path.name,
                    "memory_path": str(project_path),
                    "has_config": config_file.exists()
                }

                if config_file.exists():
                    try:
                        import json
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            project_info.update(config)
                    except Exception:
                        pass

                projects.append(project_info)

        return projects
