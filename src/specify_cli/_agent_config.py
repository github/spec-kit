"""Agent configuration constants derived from the integration registry."""
from __future__ import annotations

from typing import Any


def _build_agent_config() -> dict[str, dict[str, Any]]:
    from .integrations import INTEGRATION_REGISTRY
    config: dict[str, dict[str, Any]] = {}
    for key, integration in INTEGRATION_REGISTRY.items():
        if integration.config:
            config[key] = dict(integration.config)
    return config


AGENT_CONFIG: dict[str, dict[str, Any]] = _build_agent_config()

DEFAULT_INIT_INTEGRATION = "copilot"

AI_ASSISTANT_ALIASES: dict[str, str] = {
    "kiro": "kiro-cli",
}


def _build_ai_assistant_help() -> str:
    non_generic_agents = sorted(agent for agent in AGENT_CONFIG if agent != "generic")
    base_help = (
        f"AI assistant to use: {', '.join(non_generic_agents)}, "
        "or generic (requires --ai-commands-dir)."
    )
    if not AI_ASSISTANT_ALIASES:
        return base_help
    alias_phrases = []
    for alias, target in sorted(AI_ASSISTANT_ALIASES.items()):
        alias_phrases.append(f"'{alias}' as an alias for '{target}'")
    if len(alias_phrases) == 1:
        aliases_text = alias_phrases[0]
    else:
        aliases_text = ", ".join(alias_phrases[:-1]) + " and " + alias_phrases[-1]
    return base_help + " Use " + aliases_text + "."


AI_ASSISTANT_HELP: str = _build_ai_assistant_help()

SCRIPT_TYPE_CHOICES: dict[str, str] = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}
