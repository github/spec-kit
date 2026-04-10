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
    """Register all built-in integrations.

    Package directories use Python-safe identifiers (e.g. ``kiro_cli``,
    ``cursor_agent``).  The user-facing integration key stored in
    ``IntegrationBase.key`` stays hyphenated (``"kiro-cli"``,
    ``"cursor-agent"``) to match the actual CLI tool / binary name that
    users install and invoke.
    """
    # -- Imports (alphabetical) -------------------------------------------
    from .agy import AgyIntegration
    from .amp import AmpIntegration
    from .auggie import AuggieIntegration
    from .bob import BobIntegration
    from .claude import ClaudeIntegration
    from .codebuddy import CodebuddyIntegration
    from .codex import CodexIntegration
    from .copilot import CopilotIntegration
    from .cursor_agent import CursorAgentIntegration
    from .forge import ForgeIntegration
    from .gemini import GeminiIntegration
    from .generic import GenericIntegration
    from .iflow import IflowIntegration
    from .junie import JunieIntegration
    from .kilocode import KilocodeIntegration
    from .kimi import KimiIntegration
    from .kiro_cli import KiroCliIntegration
    from .opencode import OpencodeIntegration
    from .pi import PiIntegration
    from .qodercli import QodercliIntegration
    from .qwen import QwenIntegration
    from .roo import RooIntegration
    from .shai import ShaiIntegration
    from .tabnine import TabnineIntegration
    from .trae import TraeIntegration
    from .vibe import VibeIntegration
    from .windsurf import WindsurfIntegration

    # -- Registration (alphabetical) --------------------------------------
    _register(AgyIntegration())
    _register(AmpIntegration())
    _register(AuggieIntegration())
    _register(BobIntegration())
    _register(ClaudeIntegration())
    _register(CodebuddyIntegration())
    _register(CodexIntegration())
    _register(CopilotIntegration())
    _register(CursorAgentIntegration())
    _register(ForgeIntegration())
    _register(GeminiIntegration())
    _register(GenericIntegration())
    _register(IflowIntegration())
    _register(JunieIntegration())
    _register(KilocodeIntegration())
    _register(KimiIntegration())
    _register(KiroCliIntegration())
    _register(OpencodeIntegration())
    _register(PiIntegration())
    _register(QodercliIntegration())
    _register(QwenIntegration())
    _register(RooIntegration())
    _register(ShaiIntegration())
    _register(TabnineIntegration())
    _register(TraeIntegration())
    _register(VibeIntegration())
    _register(WindsurfIntegration())


_register_builtins()
