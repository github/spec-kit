"""Devin for Terminal integration — skills-based agent.

Devin uses the ``.devin/skills/speckit-<name>/SKILL.md`` layout and
reads project context from ``AGENTS.md`` at the repo root. The CLI
binary is ``devin`` and skills are invoked via ``/<name>`` inside an
interactive ``devin`` session.

See: https://cli.devin.ai/docs/extensibility/skills/overview
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class DevinIntegration(SkillsIntegration):
    """Integration for Cognition AI's Devin for Terminal."""

    key = "devin"
    config = {
        "name": "Devin for Terminal",
        "folder": ".devin/",
        "commands_subdir": "skills",
        "install_url": "https://cli.devin.ai/docs",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".devin/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    context_file = "AGENTS.md"

    # Devin has no structured JSON output flag.
    exec_json_args = ()

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Devin)",
            ),
        ]