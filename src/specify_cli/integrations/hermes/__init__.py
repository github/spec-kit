"""Hermes Agent integration — skills-based agent.

Hermes Agent (https://github.com/NousResearch/hermes-agent) is an open-source
AI agent framework by Nous Research.  It stores skills in
``~/.hermes/skills/`` (user-global) rather than a project-local directory.

Usage::

    specify init my-project --integration hermes
    specify init --here --ai hermes
"""

from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from typing import Any

from ..base import IntegrationOption, SkillsIntegration
from ..manifest import IntegrationManifest


class HermesIntegration(SkillsIntegration):
    """Integration for Hermes Agent skills.

    Hermes loads skills from ``~/.hermes/skills/`` (user home directory)
    rather than a project-local path.  Skills are installed in both
    locations so they are available to Hermes globally while still being
    tracked in the project manifest for clean uninstall.
    """

    key = "hermes"
    config = {
        "name": "Hermes Agent",
        "folder": ".hermes/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/NousResearch/hermes-agent",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".hermes/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _hermes_home_skills_dir() -> Path:
        """Return ``~/.hermes/skills/`` — the global skills directory."""
        return Path.home() / ".hermes" / "skills"

    # -- Options -----------------------------------------------------------

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Hermes Agent)",
            ),
        ]

    # -- Skills directory --------------------------------------------------

    def skills_dest(self, project_root: Path) -> Path:
        """Return the project-local skills directory."""
        return project_root / ".hermes" / "skills"

    # -- Setup -------------------------------------------------------------

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Install command templates as Hermes skills.

        Delegates to ``super().setup()`` for the project-local
        ``.hermes/skills/`` (tracked by the manifest for clean uninstall),
        then also writes each skill to the global ``~/.hermes/skills/``
        where Hermes discovers them at runtime.
        """
        # Let the parent class handle project-local installation
        created = super().setup(
            project_root, manifest,
            parsed_options=parsed_options,
            **opts,
        )

        # Also write each skill to the global Hermes skills directory
        global_skills_dir = self._hermes_home_skills_dir()
        global_skills_dir.mkdir(parents=True, exist_ok=True)

        for skill_md in created:
            # Only copy SKILL.md files under the project skills directory
            try:
                skill_md.resolve().relative_to(
                    self.skills_dest(project_root).resolve()
                )
            except ValueError:
                continue
            if skill_md.name != "SKILL.md":
                continue

            skill_name = skill_md.parent.name  # e.g. "speckit-plan"
            global_skill_dir = global_skills_dir / skill_name
            global_skill_dir.mkdir(parents=True, exist_ok=True)
            global_dest = global_skill_dir / "SKILL.md"

            content = skill_md.read_bytes()
            normalized = content.replace(b"\r\n", b"\n")
            global_dest.write_bytes(normalized)

        return created

    # -- Uninstall ---------------------------------------------------------

    def teardown(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """Uninstall integration files and clean up global skills."""
        # Remove managed context section from AGENTS.md
        self.remove_context_section(project_root)

        # Remove project-local files via manifest
        removed, skipped = manifest.uninstall(project_root, force=force)

        # Also remove global Hermes skills for speckit
        global_skills_dir = self._hermes_home_skills_dir()
        if global_skills_dir.is_dir():
            for skill_dir in global_skills_dir.iterdir():
                if skill_dir.is_dir() and skill_dir.name.startswith("speckit-"):
                    rmtree(skill_dir, ignore_errors=True)

        return removed, skipped

    # -- CLI dispatch ------------------------------------------------------

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build Hermes CLI invocation for programmatic dispatch.

        Uses ``hermes chat -Q -q`` for one-shot queries in quiet mode,
        mapping slash-command invocations to the appropriate skill-based
        dispatch.
        """
        args = [self.key, "chat", "-Q"]

        if model:
            args.extend(["-m", model])
        if output_json:
            args.append("--json")

        # If prompt starts with a slash command, pass it directly
        # so Hermes can dispatch to the appropriate skill.
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["-s", command])
                if remainder:
                    args.extend(["-q", remainder])
            else:
                args.extend(["-q", prompt])
        else:
            args.extend(["-q", prompt])

        return args
