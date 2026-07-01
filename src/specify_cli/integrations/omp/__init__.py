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

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        # Diverges from MarkdownIntegration.build_exec_args because OMP's
        # CLI parser treats `-p`/`--print` as a boolean (one-shot mode) and
        # consumes the prompt as a positional argument — see args.ts in
        # can1357/oh-my-pi. JSON output is selected via `--mode json`.
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [self._resolve_executable(), "--print"]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--mode", "json"])
        args.append(prompt)
        return args
