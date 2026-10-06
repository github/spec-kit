"""Amp CLI integration."""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration


class AmpIntegration(MarkdownIntegration):
    key = "amp"
    config = {
        "name": "Amp",
        "folder": ".agents/",
        "commands_subdir": "commands",
        "install_url": "https://ampcode.com/manual#install",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/commands",
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
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> list[str] | None:
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable()]
        # Operator-injected extra args go before --execute: the flag takes the
        # prompt as an optional inline value, so anything appended between the
        # two would be consumed as the message instead.
        self._apply_extra_args_env_var(args)

        args.extend(["--execute", prompt])

        if output_json:
            # Amp's structured output is --stream-json (Claude Code-compatible
            # stream JSON), valid only alongside --execute.
            args.append("--stream-json")

        # `model` is deliberately dropped: Amp has no model-selection flag.
        # `-m/--mode` takes an agent mode (low/medium/high/ultra or a plugin
        # mode), not a model identifier, so forwarding the caller's model onto
        # it would silently select the wrong thing.
        return args
