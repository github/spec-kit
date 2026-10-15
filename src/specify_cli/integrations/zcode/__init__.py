"""ZCode integration — skills-based agent (Z.AI).

ZCode uses the ``.zcode/skills/speckit-<name>/SKILL.md`` layout, matching
the Claude Code skill format. Skills are invoked in chat with
``$speckit-<name>``. Z.AI recommends skills (over simple ``/`` commands)
for template- and script-driven workflows such as spec-kit.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ..base import IntegrationOption, SkillsIntegration


class ZcodeIntegration(SkillsIntegration):
    """Integration for ZCode CLI (Z.AI)."""

    key = "zcode"
    invocation_prefix = "$"
    skills_invocation_only = True
    config = {
        "name": "ZCode",
        "folder": ".zcode/",
        "commands_subdir": "skills",
        "install_url": "https://zcode.z.ai/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".zcode/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for ZCode)",
            ),
        ]

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
        """Build CLI arguments for non-interactive ``zcode`` execution.

        ``SkillsIntegration``'s default appends ``--model``, which the ZCode
        CLI does not define. Its argument parser is strict, so a dispatched
        step exits 1 with ``Unknown option '--model'`` whenever a ``model``
        is configured. ``model`` is deliberately dropped: ZCode has no
        per-invocation model flag and switches models in-session with
        ``/model``. ``-p`` and ``--output-format json`` are both valid.
        """
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if output_json:
            args.extend(["--output-format", "json"])
        return args
