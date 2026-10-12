"""Command Code integration — skills-based agent.

Command Code loads agent skills from ``.commandcode/skills/speckit-<name>/SKILL.md``
(project) or ``~/.commandcode/skills/`` (personal). Skills are invoked in chat
with ``$speckit-<name>``.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class CommandCodeIntegration(SkillsIntegration):
    """Integration for Command Code CLI."""

    key = "command-code"
    config = {
        "name": "Command Code",
        "folder": ".commandcode/",
        "commands_subdir": "skills",
        "install_url": "https://commandcode.ai/docs",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".commandcode/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Command Code)",
            ),
        ]
