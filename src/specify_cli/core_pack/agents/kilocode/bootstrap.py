"""Bootstrap module for Kilo Code agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap


class Kilocode(AgentBootstrap):
    """Bootstrap for Kilo Code."""

    AGENT_DIR = ".kilocode"
    COMMANDS_SUBDIR = "workflows"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Kilo Code agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path) -> None:
        """Remove Kilo Code agent files from the project."""
        import shutil
        agent_dir = project_path / self.AGENT_DIR
        if agent_dir.is_dir():
            shutil.rmtree(agent_dir)
