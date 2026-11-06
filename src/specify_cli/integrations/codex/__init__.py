"""Codex CLI integration — skills-based agent.

Codex uses the ``.agents/skills/speckit-<name>/SKILL.md`` layout.
Commands are deprecated; ``--skills`` defaults to ``True``.
"""

from __future__ import annotations
import re
from pathlib import Path

from collections.abc import Mapping, Sequence
from typing import Any

from ..base import (
    IntegrationOption,
    SkillsIntegration,
    check_dispatch_settings,
    requested_dispatch_settings,
)

# ``model_context_window`` is a TOML integer that Codex reads as an i64.
_CONTEXT_WINDOW = re.compile(r"[1-9][0-9]*")
_MAX_CONTEXT_WINDOW = 2**63 - 1


class CodexIntegration(SkillsIntegration):
    """Integration for OpenAI Codex CLI."""

    key = "codex"
    config = {
        "name": "Codex CLI",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    dev_no_symlink = True
    multi_install_safe = True
    supported_dispatch_settings = frozenset({"reasoning_effort", "context_size"})

    CANONICAL_TO_NATIVE = {
        "session_start": "SessionStart",
        "pre_tool_use": "PreToolUse",
        "post_tool_use": "PostToolUse",
        "session_end": "SessionEnd",
        "user_prompt_submit": "UserPromptSubmit",
        "stop": "Stop",
    }
    events_config_file = ".codex/config.toml"
    events_format = "toml"

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
        project_root: Path | None = None,
        reasoning_effort: str | None = None,
        context_size: str | None = None,
    ) -> list[str] | None:
        # Codex uses ``codex exec "prompt"`` for non-interactive mode.
        # Resolve argv[0] via the shared executable resolver so operators can
        # override the binary with SPECKIT_INTEGRATION_CODEX_EXECUTABLE.
        self.validate_runtime_config(integration_args, integration_options)
        settings = requested_dispatch_settings(
            reasoning_effort=reasoning_effort, context_size=context_size
        )
        if settings:
            check_dispatch_settings(self, settings, via="build_exec_args")
        args: list[str] = [self._resolve_executable(), "exec", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        # ``-c`` values are parsed as TOML. The checked value cannot contain
        # quotes, backslashes, or control characters, so it forms a valid
        # basic string as-is.
        if reasoning_effort is not None:
            args.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])
        if context_size is not None:
            args.extend(["-c", f"model_context_window={context_size}"])
        if output_json:
            args.append("--json")
        return args

    def validate_dispatch_setting(self, name: str, value: str) -> None:
        """Require ``context_size`` to be a token count Codex can parse.

        The value can be captured agent output, so the error does not repeat it.
        """
        if name == "context_size" and (
            _CONTEXT_WINDOW.fullmatch(value) is None
            or int(value) > _MAX_CONTEXT_WINDOW
        ):
            raise ValueError(
                "Codex 'context_size' must be a positive integer token count "
                "(model_context_window) without leading zeros, at most "
                f"{_MAX_CONTEXT_WINDOW}."
            )

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Codex)",
            )
        )
        return opts
