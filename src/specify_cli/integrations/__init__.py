"""Integration registry for AI coding assistants.

Each integration is a self-contained subpackage that handles setup/teardown
for a specific AI assistant (Copilot, Claude, Gemini, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import IntegrationBase

# Maps integration key → IntegrationBase instance.
# Populated by later stages as integrations are migrated.
INTEGRATION_REGISTRY: dict[str, IntegrationBase] = {}


def _register(integration: IntegrationBase) -> None:
    """Register an integration instance in the global registry.

    Raises ``ValueError`` for falsy keys and ``KeyError`` for duplicates.
    """
    key = integration.key
    if not key:
        raise ValueError("Cannot register integration with an empty key.")
    if key in INTEGRATION_REGISTRY:
        raise KeyError(f"Integration with key {key!r} is already registered.")
    INTEGRATION_REGISTRY[key] = integration


def get_integration(key: str) -> IntegrationBase | None:
    """Return the integration for *key*, or ``None`` if not registered."""
    return INTEGRATION_REGISTRY.get(key)


# -- Register built-in integrations --------------------------------------

def _register_builtins() -> None:
    """Register all built-in integrations."""
    from .copilot import CopilotIntegration

    _register(CopilotIntegration())


_register_builtins()
