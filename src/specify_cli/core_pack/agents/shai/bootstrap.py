"""Bootstrap module for SHAI agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap


class Shai(AgentBootstrap):
    """Bootstrap for SHAI."""

    AGENT_DIR = ".shai"
    COMMANDS_SUBDIR = "commands"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install SHAI agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path) -> None:
        """Remove SHAI agent files from the project."""
        import shutil
        agent_dir = project_path / self.AGENT_DIR
        if agent_dir.is_dir():
            shutil.rmtree(agent_dir)
