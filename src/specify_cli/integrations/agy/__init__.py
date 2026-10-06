"""Antigravity (agy) integration — skills-based agent.

Antigravity uses ``.agents/skills/speckit-<name>/SKILL.md`` layout
(supported in Antigravity CLI v1.0.0+ and Antigravity IDE v2.0.0+).
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from ..base import SkillsIntegration

if TYPE_CHECKING:
    from ..manifest import IntegrationManifest


def _allow_all_tools() -> bool:
    """Return True if agy should run with auto-approved permissions in headless mode.

    Disabled by default for security. Set SPECKIT_AGY_ALLOW_ALL_TOOLS=1 (or
    SPECKIT_INTEGRATION_AGY_ALLOW_ALL_TOOLS=1) to enable.
    """
    for key in (
        "SPECKIT_INTEGRATION_AGY_ALLOW_ALL_TOOLS",
        "SPECKIT_AGY_ALLOW_ALL_TOOLS",
    ):
        val = os.environ.get(key)
        if val is not None and val.strip():
            return val.strip().lower() in ("1", "true", "yes", "on")
    return False


class AgyIntegration(SkillsIntegration):
    """Integration for Antigravity CLI and IDE.

    Inherits hook command normalization and post-processing from
    SkillsIntegration, ensuring slash commands constructed from dotted hook
    names are automatically converted to hyphenated skill invocations.
    """

    key: ClassVar[str] = "agy"
    config: ClassVar[dict[str, Any]] = {
        "name": "Antigravity",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://antigravity.google/",
        "requires_cli": True,
    }
    registrar_config: ClassVar[dict[str, Any]] = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
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
        if _allow_all_tools():
            args.append("--dangerously-skip-permissions")
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        if project_root is not None and str(project_root).strip():
            # agy requires an active workspace directory to discover skills under
            # .agents/skills/ when invoked from workflow directories (see issue #4480, PR #4481).
            args.extend(["--add-dir", str(Path(project_root).resolve())])
        # Honor SPECKIT_INTEGRATION_AGY_EXTRA_ARGS (operator-supplied flags).
        # Positioned before --print because agy consumes all trailing arguments
        # as prompt text (see #4480).
        self._apply_extra_args_env_var(args)
        args.extend(["--print", prompt])
        return args

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        import click

        click.secho(
            "Warning: The .agents/ layout requires Antigravity CLI v1.0.0 or newer "
            "(or Antigravity IDE v2.0.0 or newer). "
            "Please ensure your installation is up to date.",
            fg="yellow",
            err=True,
        )
        return super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
