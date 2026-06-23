"""Oh My Pi (omp) coding agent integration."""

from __future__ import annotations

from ..base import MarkdownIntegration


class OmpIntegration(MarkdownIntegration):
    key = "omp"
    config = {
        "name": "Oh My Pi",
        "folder": ".omp/",
        "commands_subdir": "commands",
        "install_url": "https://www.npmjs.com/package/@oh-my-pi/pi-coding-agent",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".omp/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "AGENTS.md"

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--mode", "json"])
        return args
