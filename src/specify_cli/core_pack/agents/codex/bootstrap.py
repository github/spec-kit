"""Bootstrap module for Codex CLI agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap, remove_tracked_files


class Codex(AgentBootstrap):
    """Bootstrap for Codex CLI."""

    AGENT_DIR = ".agents"
    COMMANDS_SUBDIR = "skills"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Codex CLI agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path, *, force: bool = False) -> None:
        """Remove Codex CLI agent files from the project.

        Only removes individual tracked files — directories are never
        deleted.  Raises ``AgentFileModifiedError`` if any tracked file
        was modified and *force* is ``False``.
        """
        remove_tracked_files(project_path, self.manifest.id, force=force)
