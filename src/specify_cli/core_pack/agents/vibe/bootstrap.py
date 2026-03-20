"""Bootstrap module for Mistral Vibe agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap


class Vibe(AgentBootstrap):
    """Bootstrap for Mistral Vibe."""

    AGENT_DIR = ".vibe"
    COMMANDS_SUBDIR = "prompts"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Mistral Vibe agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path) -> None:
        """Remove Mistral Vibe agent files from the project."""
        import shutil
        agent_dir = project_path / self.AGENT_DIR
        if agent_dir.is_dir():
            shutil.rmtree(agent_dir)
