"""Tests for capability vocabulary validation.

Covers:
- T014: validate_capabilities against known/unknown keys
- T020: parametrized validation of integration capability declarations
"""

import logging

import pytest

from specify_cli.integrations._capability_vocabulary import (
    STANDARD_CAPABILITIES,
    validate_capabilities,
)


# ---------------------------------------------------------------------------
# T014: validate_capabilities unit tests
# ---------------------------------------------------------------------------

class TestValidateCapabilities:
    """Tests for vocabulary validation."""

    def test_known_capability_passes(self):
        caps = {
            "interactive_prompts": {
                "tool": "AskUserQuestion",
                "structured": True,
            },
        }
        warnings = validate_capabilities(caps)
        assert warnings == []

    def test_all_standard_capabilities_pass(self):
        caps = {name: {"tool": "dummy"} for name in STANDARD_CAPABILITIES}
        warnings = validate_capabilities(caps)
        assert warnings == []

    def test_unknown_capability_produces_warning(self, caplog):
        caps = {
            "teleportation": {"tool": "beam_me_up"},
        }
        with caplog.at_level(logging.WARNING):
            warnings = validate_capabilities(caps)
        assert len(warnings) == 1
        assert "teleportation" in warnings[0]
        assert "not in the standard vocabulary" in warnings[0]

    def test_empty_capabilities_no_warnings(self):
        warnings = validate_capabilities({})
        assert warnings == []

    def test_mixed_known_and_unknown(self, caplog):
        caps = {
            "interactive_prompts": {"tool": "ask"},
            "custom_thing": {"tool": "custom"},
        }
        with caplog.at_level(logging.WARNING):
            warnings = validate_capabilities(caps)
        assert len(warnings) == 1
        assert "custom_thing" in warnings[0]

    def test_custom_vocabulary(self):
        from specify_cli.integrations._capability_vocabulary import CapabilitySpec
        custom_vocab = {
            "my_cap": CapabilitySpec(description="test"),
        }
        caps = {"my_cap": {"tool": "x"}}
        warnings = validate_capabilities(caps, vocabulary=custom_vocab)
        assert warnings == []

    def test_standard_vocabulary_has_five_entries(self):
        assert len(STANDARD_CAPABILITIES) == 5
        expected = {
            "interactive_prompts",
            "subagents",
            "process_enforcement",
            "context_clearing",
            "script_discovery",
        }
        assert set(STANDARD_CAPABILITIES.keys()) == expected


# ---------------------------------------------------------------------------
# T020: parametrized integration capability validation
# ---------------------------------------------------------------------------

def _integration_capabilities():
    """Yield (key, integration) for integrations that declare capabilities."""
    from specify_cli.integrations import INTEGRATION_REGISTRY
    for key, integration in INTEGRATION_REGISTRY.items():
        yield pytest.param(key, integration, id=key)


@pytest.mark.parametrize("key,integration", list(_integration_capabilities()))
def test_integration_capabilities_pass_vocabulary_validation(key, integration):
    """Every integration's capabilities must validate against the standard vocabulary."""
    warnings = validate_capabilities(integration.capabilities)
    assert warnings == [], (
        f"Integration '{key}' declares unknown capabilities: {warnings}"
    )
