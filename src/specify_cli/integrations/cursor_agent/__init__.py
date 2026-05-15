"""Cursor IDE integration.

Cursor Agent uses the ``.cursor/skills/speckit-<name>/SKILL.md`` layout.
Commands are deprecated; ``--skills`` defaults to ``True``.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class CursorAgentIntegration(SkillsIntegration):
    key = "cursor-agent"
    config = {
        "name": "Cursor",
        "folder": ".cursor/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".cursor/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }

    context_file = ".cursor/rules/specify-rules.mdc"
    multi_install_safe = True

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (recommended for Cursor)",
            ),
        ]
