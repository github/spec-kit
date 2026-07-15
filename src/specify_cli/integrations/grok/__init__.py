"""Grok Build integration — skills-based agent.

Grok Build discovers project skills from ``.grok/skills/speckit-<name>/SKILL.md``
(and also scans ``.agents/skills/``). Spec Kit installs into the native
``.grok/skills`` tree so skills take highest local priority.
"""

from __future__ import annotations

from ..base import SkillsIntegration


class GrokIntegration(SkillsIntegration):
    """Integration for xAI Grok Build CLI."""

    key = "grok"
    config = {
        "name": "Grok Build",
        "folder": ".grok/",
        "commands_subdir": "skills",
        "install_url": "https://docs.x.ai/build/overview",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".grok/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True
