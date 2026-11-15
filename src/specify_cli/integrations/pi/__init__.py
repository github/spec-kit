"""Pi Coding Agent integration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration


class PiIntegration(MarkdownIntegration):
    key = "pi"
    config = {
        "name": "Pi Coding Agent",
        "folder": ".pi/",
        "commands_subdir": "prompts",
        "install_url": "https://www.npmjs.com/package/@earendil-works/pi-coding-agent",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".pi/prompts",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    multi_install_safe = True

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
        """Build CLI arguments for non-interactive ``pi`` execution.

        ``MarkdownIntegration``'s default requests ``--output-format json``,
        which Pi does not define: it rejects the unknown option and exits 1
        before the prompt runs. Pi selects JSONL events with ``--mode json``,
        the same flag the OMP integration already passes.
        """
        self.validate_runtime_config(integration_args, integration_options)
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--mode", "json"])
        return args
