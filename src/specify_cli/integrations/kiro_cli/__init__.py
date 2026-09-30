"""Kiro CLI integration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration


# Kiro CLI file-based prompts do NOT support any argument-substitution syntax,
# so a raw "$ARGUMENTS" token would reach the model verbatim and break the
# prompt (issue #1926, kirodotdev/Kiro#4141). Use a prose fallback so the
# rendered prompt instructs the model to take its argument from the user's
# next message.
_KIRO_ARG_FALLBACK = "(the user will provide the argument in this conversation)"


class KiroCliIntegration(MarkdownIntegration):
    key = "kiro-cli"
    # Kiro CLI keeps everything under a static, isolated agent root
    # (``.kiro/`` with commands in ``.kiro/prompts``) that no other
    # integration writes to, so it is safe to install alongside others
    # (issue #3471). IntegrationBase defaults this to False; declaring it
    # True here is the actual behavior change this integration opts into.
    # The registry's multi-install-safe contract tests enforce that
    # isolation for every integration setting this flag.
    multi_install_safe = True
    config = {
        "name": "Kiro CLI",
        "folder": ".kiro/",
        "commands_subdir": "prompts",
        "install_url": "https://kiro.dev/docs/cli/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".kiro/prompts",
        "format": "markdown",
        "args": _KIRO_ARG_FALLBACK,
        "extension": ".md",
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
        """Build CLI arguments for headless ``kiro-cli chat`` execution.

        The inherited ``kiro-cli -p <prompt>`` exits 2 at argument parsing
        (``unexpected argument '-p'``). Kiro CLI runs one prompt headless
        through ``chat --no-interactive`` with the prompt as its positional
        input, and a ``/speckit.*`` input there runs the matching
        ``.kiro/prompts`` file. Headless mode cannot ask for tool approval, so
        without ``--trust-all-tools`` every file write is denied while the run
        still exits 0 (same role as Copilot's ``--yolo`` / Cursor's
        ``--force``). Kiro has no ``json`` output format; its structured output
        is ``--output-format stream-json`` (JSON Lines).
        """
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "chat", "--no-interactive", "--trust-all-tools"]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "stream-json"])
        args.append(prompt)
        return args
