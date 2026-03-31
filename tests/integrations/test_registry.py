"""Tests for INTEGRATION_REGISTRY."""

import pytest

from specify_cli.integrations import (
    INTEGRATION_REGISTRY,
    _register,
    get_integration,
)
from specify_cli.integrations.base import MarkdownIntegration
from .conftest import StubIntegration


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

    def test_copilot_registered(self):
        assert "copilot" in INTEGRATION_REGISTRY
