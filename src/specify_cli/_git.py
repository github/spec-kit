import os
import subprocess
from pathlib import Path
from typing import Optional


class GitService:
    """Pure git operations — no console output."""

    def is_repo(self, path: Path = None) -> bool:
        if path is None:
            path = Path.cwd()
        if not path.is_dir():
            return False
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True,
                capture_output=True,
                cwd=path,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def init_repo(self, project_path: Path) -> tuple[bool, Optional[str]]:
        """Initialize a git repo. Returns (success, error_message_or_None). Never prints."""
        original_cwd = Path.cwd()
        try:
            os.chdir(project_path)
            subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            # Only commit if there is something staged
            status = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                capture_output=True,
            )
            if status.returncode != 0:
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit from Specify template"],
                    check=True, capture_output=True, text=True,
                )
            return True, None
        except (subprocess.CalledProcessError, OSError) as e:
            if isinstance(e, subprocess.CalledProcessError):
                error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
                if e.stderr:
                    error_msg += f"\nError: {e.stderr.strip()}"
                elif e.stdout:
                    error_msg += f"\nOutput: {e.stdout.strip()}"
            else:
                error_msg = str(e)
            return False, error_msg
        finally:
            try:
                os.chdir(original_cwd)
            except Exception:
                pass


_git_service = GitService()
