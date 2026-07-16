"""Grok Build integration — skills-based agent.

Grok Build discovers project skills from ``.grok/skills/speckit-<name>/SKILL.md``
(and also scans ``.agents/skills/``). Spec Kit installs into the native
``.grok/skills`` tree so skills take highest local priority.
"""

from __future__ import annotations

from ..base import SkillsIntegration


class GrokIntegration(SkillsIntegration):
    """Integration for xAI Grok Build CLI."""

    key = "grok"
    config = {
        "name": "Grok Build",
        "folder": ".grok/",
        "commands_subdir": "skills",
        "install_url": "https://docs.x.ai/build/overview",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".grok/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build CLI arguments for non-interactive ``grok`` execution.

        Mandatory headless flag:

        * ``--always-approve`` — auto-approve tool executions so workflow
          dispatch and ``dispatch_command()`` are not blocked at permission
          gates (same role as Cursor's ``--force`` / Copilot's ``--yolo``).
        """
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [
            self._resolve_executable(),
            "-p",
            prompt,
            "--always-approve",
        ]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args
