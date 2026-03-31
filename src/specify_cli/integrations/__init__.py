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

    # Stage 3 — standard markdown integrations
    from .claude import ClaudeIntegration
    from .qwen import QwenIntegration
    from .opencode import OpencodeIntegration
    from .junie import JunieIntegration
    from .kilocode import KilocodeIntegration
    from .auggie import AuggieIntegration
    from .roo import RooIntegration
    from .codebuddy import CodebuddyIntegration
    from .qodercli import QodercliIntegration
    from .amp import AmpIntegration
    from .shai import ShaiIntegration
    from .bob import BobIntegration
    from .trae import TraeIntegration
    from .pi import PiIntegration
    from .iflow import IflowIntegration

    _register(ClaudeIntegration())
    _register(QwenIntegration())
    _register(OpencodeIntegration())
    _register(JunieIntegration())
    _register(KilocodeIntegration())
    _register(AuggieIntegration())
    _register(RooIntegration())
    _register(CodebuddyIntegration())
    _register(QodercliIntegration())
    _register(AmpIntegration())
    _register(ShaiIntegration())
    _register(BobIntegration())
    _register(TraeIntegration())
    _register(PiIntegration())
    _register(IflowIntegration())

    # Hyphenated package names — use importlib for kiro-cli and cursor-agent
    import importlib

    kiro_mod = importlib.import_module(".kiro-cli", __package__)
    _register(kiro_mod.KiroCliIntegration())

    from .windsurf import WindsurfIntegration
    from .vibe import VibeIntegration

    _register(WindsurfIntegration())
    _register(VibeIntegration())

    cursor_mod = importlib.import_module(".cursor-agent", __package__)
    _register(cursor_mod.CursorAgentIntegration())


_register_builtins()
