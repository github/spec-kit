"""OpenHands CLI integration using project-local Agent Skills."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from ..base import IntegrationOption, SkillsIntegration


class OpenhandsIntegration(SkillsIntegration):
    """Install isolated skills and dispatch tasks through OpenHands headless mode."""

    key = "openhands"
    config = {
        "name": "OpenHands",
        "folder": ".openhands/",
        "commands_subdir": "skills",
        "install_url": "https://github.com/OpenHands/OpenHands-CLI",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".openhands/skills",
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
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> list[str] | None:
        self.validate_runtime_config(integration_args, integration_options)
        if model:
            raise ValueError(
                "OpenHands CLI does not support --model. Configure the model in "
                "OpenHands settings, or set LLM_MODEL and "
                "SPECKIT_INTEGRATION_OPENHANDS_EXTRA_ARGS=--override-with-envs."
            )
        args = [self._resolve_executable(), "--headless", "-t", prompt]
        self._apply_extra_args_env_var(args)
        if output_json:
            args.append("--json")
        return args

    def post_process_skill_content(self, content: str) -> str:
        """Make slash invocations deterministic through OpenHands keyword triggers."""
        content = super().post_process_skill_content(content)
        if not content.startswith("---\n"):
            return content
        parts = content.split("---\n", 2)
        if len(parts) != 3:
            return content
        metadata = yaml.safe_load(parts[1])
        if not isinstance(metadata, dict) or not metadata.get("name"):
            return content
        triggers = metadata.setdefault("triggers", [])
        trigger = f"/{metadata['name']}"
        if trigger not in triggers:
            triggers.append(trigger)
        return "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n" + parts[2]

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        return super().options() + [
            IntegrationOption(
                "--skills",
                is_flag=True,
                default=True,
                help="Install as agent skills (default for OpenHands)",
            ),
        ]
