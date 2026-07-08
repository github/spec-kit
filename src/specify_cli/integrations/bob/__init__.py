"""IBM Bob integration.

Bob 2.0 uses the ``.bob/skills/speckit-<name>/SKILL.md`` layout.
The legacy ``.bob/commands/`` layout (Bob 1.x) is no longer supported.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class BobIntegration(SkillsIntegration):
    """Integration for IBM Bob IDE."""

    key = "bob"
    config = {
        "name": "IBM Bob",
        "folder": ".bob/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".bob/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Bob 2.0)",
            ),
        ]
