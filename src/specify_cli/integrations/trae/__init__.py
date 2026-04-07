"""Trae IDE integration. — skills-based agent.

Trae IDE uses ``.trae/skills/speckit-<name>/SKILL.md`` layout.
Explicit command support was deprecated in version 1.20.5;
``--skills`` defaults to ``True``.
"""

from __future__ import annotations
from ..base import IntegrationOption, SkillsIntegration


class TraeIntegration(SkillsIntegration):
    """Integration for Trae IDE."""

    key = "trae"
    config = {
        "name": "Trae",
        "folder": ".trae/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".trae/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "SKILL.md",
    }
    context_file = ".trae/rules/project_rules.md"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for trae since v0.5.1)",
            ),
        ]
