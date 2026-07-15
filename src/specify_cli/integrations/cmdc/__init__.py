"""Command Code (cmdc) integration — skills-based agent.

Command Code uses the ``.commandcode/skills/speckit-<name>/SKILL.md`` layout
following the agentskills.io spec. Commands are invoked as ``/speckit-<name>``
slash commands within the Command Code interactive session.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class CmcIntegration(SkillsIntegration):
    """Integration for Command Code CLI."""

    key = "cmdc"
    config = {
        "name": "Command Code",
        "folder": ".commandcode/",
        "commands_subdir": "skills",
        "install_url": "https://commandcode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".commandcode/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    dev_no_symlink = True
    multi_install_safe = True

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Command Code)",
            ),
        ]

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """CMDC uses ``cmdc -p "prompt"`` for non-interactive mode.

        The ``-p`` / ``--print`` flag runs cmdc in headless mode,
        outputting the response and exiting.  The ``--model`` flag
        selects a specific model when provided.
        """
        args: list[str] = [self._resolve_executable(), "-p", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        return args
