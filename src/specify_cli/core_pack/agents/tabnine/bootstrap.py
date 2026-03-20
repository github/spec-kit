"""Bootstrap module for Tabnine CLI agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap


class Tabnine(AgentBootstrap):
    """Bootstrap for Tabnine CLI."""

    AGENT_DIR = ".tabnine/agent"
    COMMANDS_SUBDIR = "commands"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Tabnine CLI agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path) -> None:
        """Remove Tabnine CLI agent files from the project.

        Removes the agent/ subdirectory under .tabnine/ to preserve
        any other Tabnine configuration.
        """
        import shutil
        agent_subdir = project_path / self.AGENT_DIR
        if agent_subdir.is_dir():
            shutil.rmtree(agent_subdir)
        # Remove .tabnine/ only if now empty
        tabnine_dir = project_path / ".tabnine"
        if tabnine_dir.is_dir() and not any(tabnine_dir.iterdir()):
            tabnine_dir.rmdir()
