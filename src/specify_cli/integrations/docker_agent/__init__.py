"""Docker Agent integration — skills-based Docker CLI agent.

Docker Agent discovers project skills from ``.agents/skills``. Runtime
configuration is owned by Docker Agent and is not managed by Spec Kit.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ..base import IntegrationOption, SkillsIntegration


class DockerAgentIntegration(SkillsIntegration):
    """Integration for Docker Agent."""

    key = "docker-agent"
    config = {
        "name": "Docker Agent",
        "folder": ".agents/",
        "commands_subdir": "skills",
        "install_url": "https://docs.docker.com/ai/docker-agent/getting-started/installation/",
        # Docker Agent is exposed as either `docker-agent` or `docker agent`.
        # The init command documents --ignore-agent-tools for the plugin form,
        # because the generic preflight check looks up the integration key.
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    # Docker Agent shares the ``.agents/skills`` layout with Codex and Zed.
    # Keep co-installation opt-in until shared manifest ownership is supported.
    multi_install_safe = False

    # Docker Agent hooks are configured in the selected agent YAML under
    # ``agents.<name>.hooks``. Spec Kit does not edit that user-owned file, so
    # hooks are intentionally not exposed through the integration event system.

    def _agent_command(self) -> list[str]:
        """Return the available Docker Agent command form."""

        # The shared executable override supports both a standalone
        # ``docker-agent`` binary and the Docker CLI plugin form.
        executable = self._resolve_executable()

        if executable != self.key:
            if Path(executable).name in {"docker", "docker.exe"}:
                return [executable, "agent", "run"]
            return [executable, "run"]
        if shutil.which("docker-agent"):
            return ["docker-agent", "run"]
        return ["docker", "agent", "run"]


    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for Docker Agent)",
            )
        )
        return opts

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build a headless Docker Agent invocation with an agent config."""
        args = [*self._agent_command(), "--exec"]

        # Extra args carry the required agent source (for example
        # ``./agent.yaml``) and any Docker Agent CLI flags. The shared helper
        # also preserves shell-style quoting when splitting multiple args.
        self._apply_extra_args_env_var(args)

        args.append(prompt)
        if output_json:
            args.append("--json")
        if model:
            args.extend(["--model", model])
        return args
