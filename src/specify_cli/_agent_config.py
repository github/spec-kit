"""Agent configuration constants derived from the integration registry."""
from __future__ import annotations

import os
import sys
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

#: Environment variable used to override the fallback integration that
#: ``specify init`` selects in non-interactive sessions.  Follows the existing
#: ``SPECKIT_INTEGRATION_*`` namespace (see ``SPECKIT_INTEGRATION_<KEY>_EXECUTABLE``
#: and ``SPECKIT_INTEGRATION_CATALOG_URL``).
DEFAULT_INIT_INTEGRATION_ENV_VAR = "SPECKIT_INTEGRATION_DEFAULT"


def resolve_default_init_integration() -> str:
    """Return the default init integration, honoring an env-var override.

    Reads :data:`DEFAULT_INIT_INTEGRATION_ENV_VAR`
    (``SPECKIT_INTEGRATION_DEFAULT``).  When it names a registered integration
    key, that key is returned; otherwise the hardcoded
    :data:`DEFAULT_INIT_INTEGRATION` (``"copilot"``) is used.  An invalid value
    emits a warning to stderr rather than silently falling back, so operators
    can tell a typo from an intentional default.
    """
    override = (os.environ.get(DEFAULT_INIT_INTEGRATION_ENV_VAR) or "").strip()
    if not override:
        return DEFAULT_INIT_INTEGRATION
    if override in AGENT_CONFIG:
        return override
    print(
        f"Warning: {DEFAULT_INIT_INTEGRATION_ENV_VAR}='{override}' is not a "
        f"recognized integration; falling back to '{DEFAULT_INIT_INTEGRATION}'. "
        f"Choose from: {', '.join(sorted(AGENT_CONFIG.keys()))}.",
        file=sys.stderr,
    )
    return DEFAULT_INIT_INTEGRATION

SCRIPT_TYPE_CHOICES: dict[str, str] = {
    "sh": "POSIX Shell (bash/zsh)",
    "ps": "PowerShell",
    "py": "Python",
}
