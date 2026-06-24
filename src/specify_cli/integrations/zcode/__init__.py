"""ZCode integration — skills-based agent (Z.AI).

ZCode uses the ``.zcode/skills/speckit-<name>/SKILL.md`` layout, matching
the Claude Code skill format. Skills are invoked in chat with
``$speckit-<name>``. Z.AI recommends skills (over simple ``/`` commands)
for template- and script-driven workflows such as spec-kit.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class ZcodeIntegration(SkillsIntegration):
    """Integration for ZCode CLI (Z.AI)."""

    key = "zcode"
    config = {
        "name": "ZCode",
        "folder": ".zcode/",
        "commands_subdir": "skills",
        "install_url": "https://zcode.z.ai/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".zcode/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "ZCODE.md"
    multi_install_safe = True

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for ZCode)",
            ),
        ]
