"""Hermes Agent integration — skills-based agent.

Hermes Agent (https://github.com/NousResearch/hermes-agent) is an open-source
AI agent framework by Nous Research.  It uses the ``.hermes/skills/`` directory
for agent skills, following the same ``speckit-<name>/SKILL.md`` layout as
Claude Code and Codex.

Usage::

    specify init my-project --integration hermes
    specify init --here --ai hermes
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class HermesIntegration(SkillsIntegration):
    """Integration for Hermes Agent skills."""

    key = "hermes"
    config = {
        "name": "Hermes Agent",
        "folder": ".hermes/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/NousResearch/hermes-agent",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".hermes/skills",
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
                help="Install as agent skills (default for Hermes Agent)",
            ),
        ]

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build Hermes CLI invocation for programmatic dispatch.

        Uses ``hermes chat -q`` for one-shot queries, mapping slash-command
        invocations to the appropriate skill-based dispatch.
        """
        args = [self.key, "chat", "-Q"]

        if model:
            args.extend(["-m", model])
        if output_json:
            args.append("--json")

        # If prompt starts with a slash command, pass it directly
        # so Hermes can dispatch to the appropriate skill.
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            args.extend(["-s", command])
            if remainder:
                args.extend(["-q", remainder])
        else:
            args.extend(["-q", prompt])

        return args
