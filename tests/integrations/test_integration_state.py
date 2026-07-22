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


def test_with_integration_setting_recomputes_separator_from_retained_options():
    """Updating only script_type must not drop an options-dependent separator.

    Copilot resolves the command-ref separator to '-' when '--skills' options
    are stored and '.' otherwise. A second call that changes only script_type
    (parsed_options=None, raw_options=None) retains the stored parsed_options,
    so invoke_separator must stay '-', not be recomputed from the None argument.
    """
    from specify_cli.integrations import get_integration
    from specify_cli.integration_runtime import with_integration_setting

    copilot = get_integration("copilot")

    settings = with_integration_setting(
        {}, "copilot", copilot, parsed_options={"skills": True}
    )
    assert settings["copilot"]["invoke_separator"] == "-"

    settings2 = with_integration_setting(
        {"integration_settings": settings}, "copilot", copilot, script_type="ps"
    )
    # parsed_options are retained (only script_type changed) ...
    assert settings2["copilot"]["parsed_options"] == {"skills": True}
    assert settings2["copilot"]["script"] == "ps"
    # ... so the separator must reflect them, not the (None) argument.
    assert settings2["copilot"]["invoke_separator"] == "-"
