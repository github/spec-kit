"""Zed editor integration — skills-based agent.

Zed uses the ``.agents/skills/speckit-<name>/SKILL.md`` layout so Spec Kit
commands are exposed as project-local skills that can be invoked from Zed's
slash-command menu.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class ZedIntegration(SkillsIntegration):
    """Integration for Zed editor skills."""

    key = "zed"
    config = {
        "name": "Zed",
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

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return []
