"""SHAI CLI integration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import MarkdownIntegration


class ShaiIntegration(MarkdownIntegration):
    key = "shai"
    config = {
        "name": "SHAI",
        "folder": ".shai/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/ovh/shai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".shai/commands",
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
        # SHAI has no argv form that runs a prompt. Its CLI collects every
        # argument, `-p` and `--model` included, as text for its auto-fix
        # agent (`trailing_var_arg`/`allow_hyphen_values` in
        # shai-cli/src/main.rs of ovh/shai), which then exits 0, so the
        # inherited `shai -p <prompt>` let workflow steps report success
        # without running the command (#2416). Headless prompts are read from
        # stdin only, and `.shai/commands` is never loaded, so opt out of
        # CLI dispatch and let those steps fail instead.
        self.validate_runtime_config(integration_args, integration_options)
        return None
