"""Docker Agent integration — skills-based Docker CLI agent.

Docker Agent discovers project skills from ``.agents/skills`` when the selected
agent configuration enables local skills and filesystem reads. Runtime
configuration is owned by Docker Agent and is not managed by Spec Kit.
"""

from __future__ import annotations

import os
import shlex
from collections.abc import Mapping, Sequence
from typing import Any

from specify_cli._utils import docker_agent_command

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

    _RUNTIME_OPTION_FLAGS = {
        "agent": "--agent",
        "model": "--model",
        "safety": "--safety",
    }
    _SAFETY_MODES = {"strict", "balanced", "restricted", "autonomous"}

    # Docker Agent hooks are configured in the selected agent YAML under
    # ``agents.<name>.hooks``. Spec Kit does not edit that user-owned file, so
    # hooks are intentionally not exposed through the integration event system.

    def _agent_command(self) -> list[str]:
        """Return the available Docker Agent command form."""

        # The shared executable override supports both a standalone
        # ``docker-agent`` binary and the Docker CLI plugin form.
        executable = self._resolve_executable()
        command = docker_agent_command(
            None if executable == self.key else executable
        )
        if command is None:
            # Preserve the normal executable-shaped argv for dispatch callers;
            # preflight and the subprocess runner report the unavailable CLI.
            return [executable, "run"]
        return command

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
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
    ) -> list[str] | None:
        """Build a headless Docker Agent invocation with an agent config."""
        self.validate_runtime_config(integration_args, integration_options)
        runtime_args = list(integration_args or ())
        extra_env_name = "SPECKIT_INTEGRATION_DOCKER_AGENT_EXTRA_ARGS"
        extra_args = os.environ.get(extra_env_name, "").strip()
        if not runtime_args and not extra_args:
            raise ValueError(
                "Docker Agent requires an agent configuration reference. "
                "Set per-step 'integration_args', for example "
                "integration_args: ['./agent.yaml'], or use the legacy "
                f"{extra_env_name}=./agent.yaml environment variable."
            )
        # Validate only the argument shape here: require a first positional
        # agent reference and reject malformed quoting or a leading option.
        # The reference may be a local file or a registry reference, so its
        # existence and validity are intentionally left to Docker Agent.
        if not runtime_args:
            try:
                first_arg = shlex.split(extra_args)[0]
            except (IndexError, ValueError) as exc:
                raise ValueError(
                    f"{extra_env_name} must start with an agent configuration "
                    "reference, for example ./agent.yaml"
                ) from exc
            if first_arg.startswith("-"):
                raise ValueError(
                    f"{extra_env_name} must start with an agent configuration "
                    "reference, for example ./agent.yaml"
                )

        args = [*self._agent_command(), "--exec"]

        # Per-step positional arguments come first. For Docker Agent the sole
        # positional value is the local/registry/alias agent reference.
        args.extend(runtime_args)

        # Extra args carry the required agent source (for example
        # ``./agent.yaml``) and any Docker Agent CLI flags. The shared helper
        # also preserves shell-style quoting when splitting multiple args.
        self._apply_extra_args_env_var(args)

        for option, value in (integration_options or {}).items():
            args.extend([self._RUNTIME_OPTION_FLAGS[option], value])

        if output_json:
            args.append("--json")
        if model:
            args.extend(["--model", model])

        # Stop Cobra flag parsing before the user prompt so values such as
        # ``--help`` or ``--json`` are passed as messages, not CLI options.
        # For example, the complete argv is
        # ``docker-agent run --exec ./agent.yaml --agent root -- --help``;
        # everything before ``--`` is parsed by Docker Agent, while ``--help``
        # is passed to the configured agent as the user message.
        args.extend(["--", prompt])

        return args

    def validate_runtime_config(
        self,
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
    ) -> None:
        """Validate Docker Agent's per-step agent reference and CLI options."""
        runtime_args = list(integration_args or ())
        if not all(isinstance(value, str) and value.strip() for value in runtime_args):
            raise ValueError(
                "Docker Agent 'integration_args' values must be non-empty strings."
            )
        if len(runtime_args) > 1:
            raise ValueError(
                "Docker Agent accepts at most one per-step 'integration_args' "
                "value: the agent configuration reference."
            )
        if runtime_args and runtime_args[0].startswith("-"):
            raise ValueError(
                "Docker Agent 'integration_args' must start with an agent "
                "configuration reference, for example ./agent.yaml."
            )

        options = integration_options or {}
        if not all(isinstance(name, str) for name in options):
            raise ValueError(
                "Docker Agent 'integration_options' keys must be strings."
            )
        unknown = sorted(set(options) - self._RUNTIME_OPTION_FLAGS.keys())
        if unknown:
            names = ", ".join(repr(name) for name in unknown)
            allowed = ", ".join(sorted(self._RUNTIME_OPTION_FLAGS))
            raise ValueError(
                f"Docker Agent received unknown integration option(s): {names}. "
                f"Supported options: {allowed}."
            )

        for name, value in options.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Docker Agent integration option {name!r} must be a "
                    "non-empty string."
                )
        safety = options.get("safety")
        if safety is not None and safety not in self._SAFETY_MODES:
            allowed = ", ".join(sorted(self._SAFETY_MODES))
            raise ValueError(
                f"Docker Agent integration option 'safety' must be one of: "
                f"{allowed}."
            )
