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
        """Remove Tabnine CLI agent files from the project."""
        import shutil
        agent_dir = project_path / self.AGENT_DIR
        if agent_dir.is_dir():
            shutil.rmtree(agent_dir)
