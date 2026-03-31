"""Tests for INTEGRATION_REGISTRY — mechanics, completeness, and registrar alignment."""

import pytest

from specify_cli.integrations import (
    INTEGRATION_REGISTRY,
    _register,
    get_integration,
)
from specify_cli.integrations.base import MarkdownIntegration
from .conftest import StubIntegration


# Every integration key that must be registered (Stage 2 + Stage 3).
ALL_INTEGRATION_KEYS = [
    "copilot",
    # Stage 3 — standard markdown integrations
    "claude", "qwen", "opencode", "junie", "kilocode", "auggie",
    "roo", "codebuddy", "qodercli", "amp", "shai", "bob", "trae",
    "pi", "iflow", "kiro-cli", "windsurf", "vibe", "cursor-agent",
]


class TestRegistry:
    def test_registry_is_dict(self):
        assert isinstance(INTEGRATION_REGISTRY, dict)

    def test_register_and_get(self):
        stub = StubIntegration()
        _register(stub)
        try:
            assert get_integration("stub") is stub
        finally:
            INTEGRATION_REGISTRY.pop("stub", None)

    def test_get_missing_returns_none(self):
        assert get_integration("nonexistent-xyz") is None

    def test_register_empty_key_raises(self):
        class EmptyKey(MarkdownIntegration):
            key = ""
        with pytest.raises(ValueError, match="empty key"):
            _register(EmptyKey())

    def test_register_duplicate_raises(self):
        stub = StubIntegration()
        _register(stub)
        try:
            with pytest.raises(KeyError, match="already registered"):
                _register(StubIntegration())
        finally:
            INTEGRATION_REGISTRY.pop("stub", None)


class TestRegistryCompleteness:
    """Every expected integration must be registered."""

    @pytest.mark.parametrize("key", ALL_INTEGRATION_KEYS)
    def test_key_registered(self, key):
        assert key in INTEGRATION_REGISTRY, f"{key} missing from registry"


class TestRegistrarKeyAlignment:
    """AGENT_CONFIGS keys must match integration keys (no mismatches)."""

    def test_cursor_agent_key_in_registrar(self):
        from specify_cli.agents import CommandRegistrar
        assert "cursor-agent" in CommandRegistrar.AGENT_CONFIGS
        assert "cursor" not in CommandRegistrar.AGENT_CONFIGS

    def test_vibe_key_in_registrar(self):
        from specify_cli.agents import CommandRegistrar
        assert "vibe" in CommandRegistrar.AGENT_CONFIGS
        assert CommandRegistrar.AGENT_CONFIGS["vibe"]["dir"] == ".vibe/prompts"
