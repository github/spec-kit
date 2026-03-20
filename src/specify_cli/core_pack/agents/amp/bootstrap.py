"""Bootstrap module for Amp agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap


class Amp(AgentBootstrap):
    """Bootstrap for Amp."""

    AGENT_DIR = ".agents"
    COMMANDS_SUBDIR = "commands"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Amp agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path) -> None:
        """Remove Amp agent files from the project.

        Only removes the commands/ subdirectory — preserves other .agents/
        content (e.g. Codex skills/) which shares the same parent directory.
        """
        import shutil
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        if commands_dir.is_dir():
            shutil.rmtree(commands_dir)
        # Remove .agents/ only if now empty
        agents_dir = project_path / self.AGENT_DIR
        if agents_dir.is_dir() and not any(agents_dir.iterdir()):
            agents_dir.rmdir()
