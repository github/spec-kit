"""Cursor IDE integration.

Cursor Agent uses the ``.cursor/skills/speckit-<name>/SKILL.md`` layout.
Commands are deprecated; ``--skills`` defaults to ``True``.

The IDE/skills flow is the primary path and works without the
``cursor-agent`` CLI being installed (``requires_cli=False``).  Workflow
dispatch via ``cursor-agent -p --trust --approve-mcps --force <prompt>``
is offered as an opt-in capability — the presence of ``build_exec_args()``
is what indicates dispatch support, mirroring ``CopilotIntegration``.
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
        # IDE-first integration: ``specify init --integration cursor-agent`` must
        # work without the ``cursor-agent`` CLI installed (the IDE flow
        # uses skills directly).  Workflow dispatch additionally requires
        # the CLI on PATH, but that's enforced at dispatch time via
        # ``shutil.which`` rather than as a hard ``specify init`` precheck.
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".cursor/skills",
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
        """Build CLI arguments for non-interactive ``cursor-agent`` execution.

        Always returns argv (no ``requires_cli`` guard) so workflow
        dispatch is supported even though the integration's ``config``
        sets ``requires_cli=False`` to keep the IDE-only flow unblocked.
        This mirrors ``CopilotIntegration``: dispatch support is signalled
        by overriding ``build_exec_args()``, not by the ``requires_cli``
        flag (which is reserved for the ``specify init`` precheck).

        Mandatory headless flags:

        * ``-p`` — print/headless mode (access to all tools)
        * ``--trust`` — bypass Workspace Trust prompt (CLI exits non-zero
          otherwise)
        * ``--approve-mcps`` — auto-approve MCP server loading (otherwise
          MCP servers stay ``not loaded (needs approval)`` and tool calls
          to them are silently dropped)
        * ``--force`` — auto-approve tool invocations (shell/write/MCP),
          matching the implicit "trusted environment" semantics that other
          integrations (``claude -p``, ``codex --exec``) get by default

        Together these are the minimum set required to make
        ``specify workflow run speckit --input integration=cursor-agent``
        behave the same way as it does for ``claude`` / ``codex``.
        Verified locally: with ``--approve-mcps --force`` the agent can
        call any configured MCP server (e.g. ``dingtalk-doc``) and write
        files during ``/speckit-*`` skill execution; without them the run
        either drops tool calls or exits non-zero on the first approval
        prompt.
        """
        args = [
            self._resolve_executable(),
            "-p",
            "--trust",
            "--approve-mcps",
            "--force",
            prompt,
        ]
        self._apply_extra_args_env_var(args)
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
