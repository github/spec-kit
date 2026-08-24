"""Docker Agent integration — skills-based Docker CLI agent.

Docker Agent discovers project skills from ``.docker-agent/skills``. Runtime
configuration is owned by Docker Agent and is not managed by Spec Kit.
"""

from __future__ import annotations

import shutil

from ..base import SkillsIntegration


class DockerAgentIntegration(SkillsIntegration):
    """Integration for Docker Agent."""

    key = "docker-agent"
    config = {
        "name": "Docker Agent",
        "folder": ".docker-agent/",
        "commands_subdir": "skills",
        "install_url": "https://docs.docker.com/ai/docker-agent/getting-started/installation/",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".docker-agent/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "/SKILL.md",
    }
    multi_install_safe = True

    # Docker Agent hook names are lowercase snake_case and are configured in
    # the agent team's YAML under ``agents.<name>.hooks``.
    CANONICAL_TO_NATIVE = {
        "session_start": "session_start",
        "pre_tool_use": "pre_tool_use",
        "post_tool_use": "post_tool_use",
        "session_end": "session_end",
        "user_prompt_submit": "user_prompt_submit",
        "stop": "stop",
    }


    @staticmethod
    def _agent_command() -> list[str]:
        """Return the available Docker Agent command form."""
        if shutil.which("docker-agent"):
            return ["docker-agent", "run"]
        return ["docker", "agent", "run"]

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
    ) -> list[str] | None:
        """Build a headless Docker Agent invocation for workflow dispatch."""
        args = [*self._agent_command(), "--exec"]
        if output_json:
            args.append("--json")
        self._apply_extra_args_env_var(args)
        if model:
            args.extend(["--model", model])
        args.append(prompt)
        return args
