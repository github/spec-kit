"""Bootstrap module for Codex CLI agent pack."""

from pathlib import Path
from typing import Any, Dict

from specify_cli.agent_pack import AgentBootstrap


class Codex(AgentBootstrap):
    """Bootstrap for Codex CLI."""

    AGENT_DIR = ".agents"
    COMMANDS_SUBDIR = "skills"

    def setup(self, project_path: Path, script_type: str, options: Dict[str, Any]) -> None:
        """Install Codex CLI agent files into the project."""
        commands_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        commands_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self, project_path: Path) -> None:
        """Remove Codex CLI agent files from the project.

        Only removes the skills/ subdirectory — preserves other .agents/
        content (e.g. Amp commands/) which shares the same parent directory.
        """
        import shutil
        skills_dir = project_path / self.AGENT_DIR / self.COMMANDS_SUBDIR
        if skills_dir.is_dir():
            shutil.rmtree(skills_dir)
        # Remove .agents/ only if now empty
        agents_dir = project_path / self.AGENT_DIR
        if agents_dir.is_dir() and not any(agents_dir.iterdir()):
            agents_dir.rmdir()
