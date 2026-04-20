"""Antigravity (agy) integration — skills-based agent.

Antigravity uses ``.agents/skills/speckit-<name>/SKILL.md`` layout (starting in v1.19.5).
Explicit command support was deprecated in version 1.20.5.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..base import SkillsIntegration

if TYPE_CHECKING:
    from ..manifest import IntegrationManifest



class AgyIntegration(SkillsIntegration):
    """Integration for Antigravity IDE."""

    key = "agy"
    config = {
        "name": "Antigravity",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        import click

        click.secho(
            "Warning: The .agents/ layout requires Antigravity v1.19.5 or newer. "
            "Please ensure your agy installation is up to date.",
            fg="yellow",
            err=True,
        )
        return super().setup(project_root, manifest, parsed_options=parsed_options, **opts)
