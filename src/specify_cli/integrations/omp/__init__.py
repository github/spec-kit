"""Oh My Pi (omp) coding agent integration."""

from __future__ import annotations

import re
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

    # OMP's parser (args.ts / flag-tables.ts in can1357/oh-my-pi) is not
    # POSIX-strict: value-taking flags consume the *next* token, even one that
    # looks like a flag, and `--=...` is normalized to the `--` terminator.
    # To keep generated flags and the prompt intact, ``integration_args`` is
    # limited to (a) known valueless flags and (b) self-contained
    # ``--name=value`` tokens. Valueless flags are accepted only in their bare
    # form: OMP ignores an inline value, so ``--yolo=false`` enables yolo.
    _VALUELESS_FLAGS = frozenset({
        "--allow-home", "--continue", "--from-claude", "--from-codex",
        "--no-session", "--no-tools", "--no-lsp", "--no-pty",
        "--hide-thinking", "--advisor", "--wait-async", "--external-thinking",
        "--prewalk", "--no-prewalk", "--plan-yolo", "--print-thoughts",
        "--no-extensions", "--no-skills", "--no-rules", "--no-context-files",
        "--no-title", "--no-ui", "--auto-approve", "--yolo",
    })
    # OMP splits ``--name=value`` at ``=`` and enables these flags regardless
    # of the inline value (``--help=false`` still prints help and exits).
    # ``--export``/``--alias`` replace prompt execution (the prompt becomes an
    # output filename, or alias installation returns early) and ``--mode`` is
    # owned by the adapter, so they are rejected in equals-form too.
    _RESERVED_FLAG_NAMES = frozenset({
        "--help", "--version", "--print", "--export", "--alias", "--mode",
    })
    _EQUALS_FLAG_RE = re.compile(r"^--[A-Za-z][A-Za-z0-9-]*=")

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
        args.extend(["--mode", "json" if output_json else "text"])
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
        if "--" in (integration_args or ()):
            raise ValueError(
                "OMP 'integration_args' must not contain the '--' option "
                "terminator; it would turn generated options and the prompt "
                "into positional arguments."
            )
        if any(
            value == "--model" or value.startswith("--model=")
            for value in integration_args or ()
        ):
            raise ValueError(
                "OMP model selection must use the command-step 'model' field, "
                "not a '--model' flag in 'integration_args'."
            )

        for value in integration_args or ():
            flag_name, has_inline_value, _ = value.partition("=")
            if has_inline_value and flag_name in self._VALUELESS_FLAGS:
                # OMP splits at '=' and enables the boolean, dropping the
                # inline value: '--yolo=false' still turns on auto-approval.
                raise ValueError(
                    f"OMP 'integration_args' value {value!r} is not allowed: "
                    f"{flag_name!r} does not take a value and OMP enables it "
                    f"regardless of the inline value. Pass {flag_name!r} "
                    "on its own to enable it, or omit it to leave it off."
                )
            if (
                value in self._VALUELESS_FLAGS
                or self._EQUALS_FLAG_RE.match(value)
                and flag_name not in self._RESERVED_FLAG_NAMES
            ):
                continue
            raise ValueError(
                f"OMP 'integration_args' value {value!r} is not allowed. Use a "
                "known valueless flag (for example '--no-session') or pass "
                "flag values inline as '--name=value'; bare value-taking "
                "flags, positional text, '@file' references and '--=' forms "
                "can consume or reorder the generated options and prompt."
            )

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
