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

    CANONICAL_TO_NATIVE = {
        "session_start": "SessionStart",
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "session_end": "SessionEnd",
        "user_prompt_submit": "UserPromptSubmit",
        "stop": "Stop",
    }
    events_config_file = ".devin/hooks.v1.json"
    # Devin's hooks.v1.json is a root event map ({"PreToolUse": [...]}) with no
    # top-level "hooks" wrapper (U2), unlike the settings.json formats. The
    # json-root-nested writer/remover operate directly on the root event keys.
    events_format = "json-root-nested"

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
        for structured JSON output. When ``output_json`` is requested,
        Devin is still dispatched normally and returns plain-text
        stdout instead of structured JSON. ``requires_cli=True`` is
        kept on the integration for tool detection.
        """
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        return args

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        # Compose with super() so the base class declares --events for this
        # event-capable integration; otherwise --integration-options
        # "--events false" is rejected as unknown (#8).
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Devin)",
            ),
        )
        return opts
