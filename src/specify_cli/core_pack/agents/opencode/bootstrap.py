"""Bootstrap module for opencode agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap, remove_tracked_files


class Opencode(AgentBootstrap):
    """Bootstrap for opencode."""

    AGENT_DIR = ".opencode"
    COMMANDS_SUBDIR = "command"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install opencode agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path, *, force: bool = False) -> None:
        """Remove opencode agent files from the project.

        Only removes individual tracked files — directories are never
        deleted.  Raises ``AgentFileModifiedError`` if any tracked file
        was modified and *force* is ``False``.
        """
        remove_tracked_files(project_path, self.manifest.id, force=force)
