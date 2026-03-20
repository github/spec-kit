"""Bootstrap module for Mistral Vibe agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap, remove_tracked_files


class Vibe(AgentBootstrap):
    """Bootstrap for Mistral Vibe."""

    AGENT_DIR = ".vibe"
    COMMANDS_SUBDIR = "prompts"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Mistral Vibe agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path, *, force: bool = False) -> None:
        """Remove Mistral Vibe agent files from the project.

        Only removes individual tracked files — directories are never
        deleted.  Raises ``AgentFileModifiedError`` if any tracked file
        was modified and *force* is ``False``.
        """
        remove_tracked_files(project_path, self.manifest.id, force=force)
