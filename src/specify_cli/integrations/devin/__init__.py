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

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build non-interactive CLI args for Devin for Terminal.

        Devin supports ``devin -p <prompt>`` for single-turn execution
        and ``--model`` for model selection, but its CLI has no flag
        for structured JSON output. Return ``None`` when JSON output
        is requested so the dispatcher cleanly raises
        ``NotImplementedError`` instead of invoking Devin with an
        unsupported ``--output-format`` flag. ``requires_cli=True``
        is kept on the integration for tool detection.
        """
        if output_json:
            return None
        args = [self.key, "-p", prompt]
        if model:
            args.extend(["--model", model])
        return args

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