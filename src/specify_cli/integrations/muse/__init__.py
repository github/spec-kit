"""Muse Code integration — skills-based agent (Meta).

Muse Code discovers project skills from
``.agents/skills/speckit-<name>/SKILL.md`` and invokes them via their
slash shortcut (``/speckit-<command>``).

See: https://dev.meta.ai/docs/muse-code
"""

from __future__ import annotations

from ..base import IntegrationOption, SkillsIntegration


class MuseIntegration(SkillsIntegration):
    """Integration for Muse Code CLI."""

    key = "muse"
    config = {
        "name": "Muse Code",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://dev.meta.ai/docs/muse-code",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    # Muse Code shares the ``.agents/skills`` layout with Codex and Zed.
    # Keep co-installation opt-in until shared manifest ownership is supported.
    multi_install_safe = False

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Muse Code)",
            ),
        ]

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        # Muse Code uses ``muse exec "<prompt>"`` for non-interactive mode.
        # Resolve argv[0] via the shared executable resolver so operators can
        # override the binary with SPECKIT_INTEGRATION_MUSE_EXECUTABLE.
        args: list[str] = [self._resolve_executable(), "exec", prompt]
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        if output_json:
            args.append("--json")
        return args
