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
        # SHAI takes headless prompt text from positional arguments, stdin or
        # `shai agent <name> <prompt>`, but every route goes to its auto-fix
        # agent (`handle_fix` in shai-cli/src/main.rs of ovh/shai), and
        # `.shai/commands` is never loaded, so no route runs an installed
        # Spec Kit command. Positional arguments collect `-p` and `--model`
        # too (`trailing_var_arg`/`allow_hyphen_values`), so the inherited
        # `shai -p <prompt>` handed that literal text to the auto-fix agent,
        # which exits 0, and workflow steps reported success without running
        # the command (#2416). Opt out of CLI dispatch and let those steps
        # fail instead.
        self.validate_runtime_config(integration_args, integration_options)
        return None
