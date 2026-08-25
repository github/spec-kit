"""Docker Agent integration — skills-based Docker CLI agent.

Docker Agent discovers project skills from ``.agents/skills``. Runtime
configuration is owned by Docker Agent and is not managed by Spec Kit.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

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
        """Build a headless Docker Agent invocation for workflow dispatch."""
        # The zero-config form is handled by dispatch_command(), which sends
        # the prompt through stdin instead of using an agent-file position.
        args = [*self._agent_command(), "--exec"]
        if output_json:
            args.append("--json")
        if model:
            args.extend(["--model", model])
        return args

    def dispatch_command(
        self,
        command_name: str,
        args: str = "",
        *,
        project_root: Path | None = None,
        model: str | None = None,
        timeout: int = 600,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Dispatch a command, including Docker Agent's zero-config mode.

        Docker Agent's first positional argument is an agent file or registry
        reference. With no extra arguments, send the Spec Kit prompt through
        stdin instead of accidentally treating it as an agent reference.
        """
        prompt = self.build_command_invocation(command_name, args)
        exec_args = [*self._agent_command(), "--exec"]
        if not stream:
            exec_args.append("--json")
        input_text: str | None = prompt
        if model:
            exec_args.extend(["--model", model])

        resolved = shutil.which(exec_args[0])
        if resolved:
            exec_args[0] = resolved
        run_kwargs: dict[str, Any] = {
            "text": True,
            "cwd": str(project_root) if project_root else None,
            "input": input_text,
        }
        if stream:
            result = subprocess.run(exec_args, check=False, **run_kwargs)
            return {"exit_code": result.returncode, "stdout": "", "stderr": ""}
        result = subprocess.run(
            exec_args,
            capture_output=True,
            timeout=timeout,
            check=False,
            **run_kwargs,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
