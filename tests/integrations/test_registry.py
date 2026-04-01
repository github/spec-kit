"""Tests for INTEGRATION_REGISTRY — mechanics, completeness, and registrar alignment."""

import pytest

from specify_cli.integrations import (
    INTEGRATION_REGISTRY,
    _register,
    get_integration,
)
from specify_cli.integrations.base import MarkdownIntegration
from .conftest import StubIntegration


# Every integration key that must be registered (Stage 2 + Stage 3 + Stage 4 + Stage 5).
ALL_INTEGRATION_KEYS = [
    "copilot",
    # Stage 3 — standard markdown integrations
    "claude", "qwen", "opencode", "junie", "kilocode", "auggie",
    "roo", "codebuddy", "qodercli", "amp", "shai", "bob", "trae",
    "pi", "iflow", "kiro-cli", "windsurf", "vibe", "cursor-agent",
    # Stage 4 — TOML integrations
    "gemini", "tabnine",
    # Stage 5 — skills, generic & option-driven integrations
    "codex", "kimi", "agy", "generic",
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
    """Every integration key must have a matching AGENT_CONFIGS entry.

    ``generic`` is excluded because it has no fixed directory — its
    output path comes from ``--commands-dir`` at runtime.
    """

    _REGISTRAR_EXEMPT = {"generic"}

    @pytest.mark.parametrize(
        "key",
        [k for k in ALL_INTEGRATION_KEYS if k != "generic"],
    )
    def test_integration_key_in_registrar(self, key):
        from specify_cli.agents import CommandRegistrar
        assert key in CommandRegistrar.AGENT_CONFIGS, (
            f"Integration '{key}' is registered but has no AGENT_CONFIGS entry"
        )

    def test_no_stale_cursor_shorthand(self):
        """The old 'cursor' shorthand must not appear in AGENT_CONFIGS."""
        from specify_cli.agents import CommandRegistrar
        assert "cursor" not in CommandRegistrar.AGENT_CONFIGS
