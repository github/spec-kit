"""
Git service for repository operations

Provides git repository management functionality including initialization,
branch management, staging, commits, and repository information.
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class GitService(ABC):
    """Abstract interface for git operations"""

    @abstractmethod
    def init_repository(self, project_path: Path) -> bool:
        """Initialize a git repository in the specified path"""
        pass

    @abstractmethod
    def create_branch(self, branch_name: str, project_path: Path) -> bool:
        """Create a new branch with the given name"""
        pass

    @abstractmethod
    def checkout_branch(self, branch_name: str, project_path: Path) -> bool:
        """Switch to the specified branch"""
        pass

    @abstractmethod
    def add_files(
        self, project_path: Path, file_patterns: Optional[List[str]] = None
    ) -> bool:
        """Add files to the staging area. If file_patterns is None, adds all files"""
        pass

    @abstractmethod
    def commit_changes(self, message: str, project_path: Path) -> bool:
        """Commit staged changes with the given message"""
        pass

    @abstractmethod
    def is_git_repository(self, project_path: Path) -> bool:
        """Check if the specified path is inside a git repository"""
        pass

    @abstractmethod
    def get_current_branch(self, project_path: Path) -> Optional[str]:
        """Get the name of the current branch"""
        pass

    @abstractmethod
    def get_remote_url(self, project_path: Path) -> Optional[str]:
        """Get the remote origin URL"""
        pass


class CommandLineGitService(GitService):
    """Implementation using command-line git via subprocess"""

    def init_repository(self, project_path: Path) -> bool:
        """Initialize a git repository in the specified path"""
        try:
            # Initialize git repository
            subprocess.run(
                ["git", "init"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Add all files
            subprocess.run(
                ["git", "add", "."],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Create initial commit
            subprocess.run(
                ["git", "commit", "-m", "Initial commit from Specify-X template"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )

            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_branch(self, branch_name: str, project_path: Path) -> bool:
        """Create a new branch with the given name"""
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def checkout_branch(self, branch_name: str, project_path: Path) -> bool:
        """Switch to the specified branch"""
        try:
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def add_files(
        self, project_path: Path, file_patterns: Optional[List[str]] = None
    ) -> bool:
        """Add files to the staging area. If file_patterns is None, adds all files"""
        try:
            if file_patterns is None:
                # Add all files
                subprocess.run(
                    ["git", "add", "."],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                # Add specific files/patterns
                for pattern in file_patterns:
                    subprocess.run(
                        ["git", "add", pattern],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def commit_changes(self, message: str, project_path: Path) -> bool:
        """Commit staged changes with the given message"""
        try:
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def is_git_repository(self, project_path: Path) -> bool:
        """Check if the specified path is inside a git repository"""
        if not project_path.is_dir():
            return False

        try:
            # Use git command to check if inside a work tree
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_current_branch(self, project_path: Path) -> Optional[str]:
        """Get the name of the current branch"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def get_remote_url(self, project_path: Path) -> Optional[str]:
        """Get the remote origin URL"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
