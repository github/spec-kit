"""MiniMax Code integration — skills-based agent.

MiniMax Code discovers project skills from
``.minimax/skills/speckit-<name>/SKILL.md`` and invokes them via their
slash shortcut (``/speckit-<command>``).

See: https://github.com/MiniMax-AI/minimax-code
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import IntegrationOption, SkillsIntegration


class McodeIntegration(SkillsIntegration):
    """Integration for MiniMax Code CLI."""

    key = "mcode"
    config = {
        "name": "MiniMax Code",
        "folder": ".minimax/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/MiniMax-AI/minimax-code",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".minimax/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for MiniMax Code)",
            )
        )
        return opts

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> list[str] | None:
        self.validate_runtime_config(
            integration_args,
            integration_options,
        )
        args = [self._resolve_executable(), "exec", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args
