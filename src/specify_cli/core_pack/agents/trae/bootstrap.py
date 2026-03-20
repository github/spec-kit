"""Bootstrap module for Trae agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap, remove_tracked_files


class Trae(AgentBootstrap):
    """Bootstrap for Trae."""

    AGENT_DIR = ".trae"
    COMMANDS_SUBDIR = "rules"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Trae agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path, *, force: bool = False) -> None:
        """Remove Trae agent files from the project.

        Only removes individual tracked files — directories are never
        deleted.  Raises ``AgentFileModifiedError`` if any tracked file
        was modified and *force* is ``False``.
        """
        remove_tracked_files(project_path, self.manifest.id, force=force)
