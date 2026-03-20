"""Bootstrap module for Kimi Code agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap, record_installed_files, remove_tracked_files


class Kimi(AgentBootstrap):
    """Bootstrap for Kimi Code."""

    AGENT_DIR = ".kimi"
    COMMANDS_SUBDIR = "skills"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Kimi Code agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)
        # Record installed files for tracked teardown
        installed = [p for p in commands_dir.rglob("*") if p.is_file()]
        record_installed_files(project_path, self.manifest.id, installed)

    def teardown(self, project_path: Path, *, force: bool = False) -> None:
        """Remove Kimi Code agent files from the project.

        Only removes individual tracked files — directories are never
        deleted.  Raises ``AgentFileModifiedError`` if any tracked file
        was modified and *force* is ``False``.
        """
        remove_tracked_files(project_path, self.manifest.id, force=force)
