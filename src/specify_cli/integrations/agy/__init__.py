"""Antigravity (agy) integration — skills-based agent.

Antigravity uses ``.agent/skills/speckit-<name>/SKILL.md`` layout.
Explicit command support was deprecated in version 1.20.5;
``--skills`` defaults to ``True``.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class AgyIntegration(SkillsIntegration):
    """Integration for Antigravity IDE."""

    key = "agy"
    config = {
        "name": "Antigravity",
        "folder": ".agent/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".agent/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Antigravity since v1.20.5)",
            ),
        ]
