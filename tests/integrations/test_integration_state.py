"""Tests for integration state normalization helpers."""

import json

from specify_cli.integration_state import (
    INTEGRATION_JSON,
    default_integration_key,
    integration_setting,
    normalize_integration_state,
    write_integration_json,
)


def test_normalize_integration_state_strips_default_key_without_duplicates():
    state = normalize_integration_state(
        {
            "default_integration": " claude ",
            "integration": " claude ",
            "installed_integrations": ["claude"],
        }
    )

    assert state["integration"] == "claude"
    assert state["default_integration"] == "claude"
    assert state["installed_integrations"] == ["claude"]


def test_normalize_integration_state_strips_legacy_key_fallback():
    state = normalize_integration_state(
        {
            "integration": " codex ",
            "installed_integrations": [],
        }
    )

    assert state["integration"] == "codex"
    assert state["default_integration"] == "codex"
    assert state["installed_integrations"] == ["codex"]


def test_normalize_integration_state_preserves_newer_schema():
    state = normalize_integration_state(
        {
            "integration_state_schema": 99,
            "integration": "claude",
            "installed_integrations": ["claude"],
            "future_field": {"keep": True},
        }
    )

    assert state["integration_state_schema"] == 99
    assert state["future_field"] == {"keep": True}


def test_default_integration_key_strips_raw_state_values():
    assert default_integration_key({"default_integration": " claude "}) == "claude"
    assert default_integration_key({"integration": " codex "}) == "codex"


def test_integration_settings_strip_invoke_separator():
    setting = integration_setting(
        {
            "integration_settings": {
                "claude": {
                    "invoke_separator": " - ",
                }
            }
        },
        "claude",
    )

    assert setting["invoke_separator"] == "-"


def test_write_integration_json_strips_integration_key(tmp_path):
    write_integration_json(
        tmp_path,
        version="1.2.3",
        integration_key=" claude ",
        installed_integrations=["claude"],
    )

    state = json.loads((tmp_path / INTEGRATION_JSON).read_text(encoding="utf-8"))
    assert state["integration"] == "claude"
    assert state["default_integration"] == "claude"
    assert state["installed_integrations"] == ["claude"]
