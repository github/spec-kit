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

SCRIPT_TYPE_CHOICES: dict[str, str] = {
    "sh": "POSIX Shell (bash/zsh)",
    "ps": "PowerShell",
    "py": "Python",
}
