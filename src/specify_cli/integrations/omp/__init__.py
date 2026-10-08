"""Oh My Pi (omp) coding agent integration."""

from __future__ import annotations
from pathlib import Path

from collections.abc import Mapping, Sequence
from typing import Any

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
    multi_install_safe = True

    _RUNTIME_OPTION_FLAGS = {
        "profile": "--profile",
        "thinking": "--thinking",
        "tools": "--tools",
    }
    _THINKING_LEVELS = {
        "off", "minimal", "low", "medium", "high", "xhigh", "max", "auto",
    }

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
        # Diverges from MarkdownIntegration.build_exec_args because OMP's
        # CLI parser treats `-p`/`--print` as a boolean (one-shot mode) and
        # consumes the prompt as a positional argument — see args.ts in
        # can1357/oh-my-pi. JSON output is selected via `--mode json`.
        if not self.config or not self.config.get("requires_cli"):
            return None
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "--print"]
        self._apply_extra_args_env_var(args)
        args.extend(integration_args or ())
        for option, value in (integration_options or {}).items():
            args.extend([self._RUNTIME_OPTION_FLAGS[option], value])
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--mode", "json"])
        args.append(prompt)
        return args

    def validate_runtime_config(
        self,
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
    ) -> None:
        """Validate OMP per-step CLI flags and named options."""
        if not all(
            isinstance(value, str) and value.strip()
            for value in integration_args or ()
        ):
            raise ValueError("OMP 'integration_args' values must be non-empty strings.")

        options = integration_options or {}
        if not all(isinstance(name, str) for name in options):
            raise ValueError("OMP 'integration_options' keys must be strings.")
        if "model" in options:
            raise ValueError(
                "OMP model selection must use the command-step 'model' field, "
                "not 'integration_options.model'."
            )
        unknown = sorted(set(options) - self._RUNTIME_OPTION_FLAGS.keys())
        if unknown:
            names = ", ".join(repr(name) for name in unknown)
            allowed = ", ".join(sorted(self._RUNTIME_OPTION_FLAGS))
            raise ValueError(
                f"OMP received unknown integration option(s): {names}. "
                f"Supported options: {allowed}."
            )
        for name, value in options.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"OMP integration option {name!r} must be a non-empty string."
                )
        thinking = options.get("thinking")
        if thinking is not None and thinking not in self._THINKING_LEVELS:
            allowed = ", ".join(sorted(self._THINKING_LEVELS))
            raise ValueError(
                f"OMP integration option 'thinking' must be one of: {allowed}."
            )
