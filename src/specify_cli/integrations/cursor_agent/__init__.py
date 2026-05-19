"""Cursor IDE integration.

Cursor Agent uses the ``.cursor/skills/speckit-<name>/SKILL.md`` layout.
Commands are deprecated; ``--skills`` defaults to ``True``.

CLI dispatch via ``cursor-agent -p --trust <prompt>`` is supported so
``specify workflow run`` can drive cursor-agent headlessly, in addition
to the existing in-IDE skill flow.
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class CursorAgentIntegration(SkillsIntegration):
    key = "cursor-agent"
    config = {
        "name": "Cursor",
        "folder": ".cursor/",
        "commands_subdir": "skills",
        "install_url": "https://docs.cursor.com/en/cli/overview",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".cursor/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }

    context_file = ".cursor/rules/specify-rules.mdc"
    multi_install_safe = True

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build CLI arguments for non-interactive ``cursor-agent`` execution.

        Uses ``-p`` (print/headless mode, which gives access to all
        tools including write and shell) plus ``--trust`` (bypass the
        Workspace Trust prompt — mandatory for headless execution; the
        CLI exits non-zero without it).
        """
        if not self.config or not self.config.get("requires_cli"):
            return None
        args = [self.key, "-p", "--trust", prompt]
        if model:
            args.extend(["--model", model])
        if output_json:
            args.extend(["--output-format", "json"])
        return args

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (recommended for Cursor)",
            ),
        ]
