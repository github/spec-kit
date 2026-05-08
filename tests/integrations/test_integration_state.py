"""Tests for integration state helpers."""

import json

import pytest

from specify_cli.integration_state import (
    INTEGRATION_JSON,
    INTEGRATION_STATE_SCHEMA,
    IntegrationStateError,
    IntegrationStateSchemaError,
    default_integration_key,
    integration_setting,
    normalize_integration_state,
    read_integration_state,
    resolve_project_integration,
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


class TestReadIntegrationState:
    """Tests for read_integration_state()."""

    def test_returns_none_when_file_missing(self, tmp_path):
        assert read_integration_state(tmp_path) is None

    def test_returns_normalized_state(self, tmp_path):
        data = {"integration": "claude", "version": "0.8.0"}
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

        result = read_integration_state(tmp_path)

        assert result is not None
        assert result["integration"] == "claude"
        assert result["default_integration"] == "claude"

    def test_raises_schema_error_on_future_schema(self, tmp_path):
        data = {"integration_state_schema": 999}
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

        with pytest.raises(IntegrationStateSchemaError):
            read_integration_state(tmp_path)

    def test_raises_on_invalid_json(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            "not valid json", encoding="utf-8"
        )

        with pytest.raises(IntegrationStateError):
            read_integration_state(tmp_path)

    def test_raises_on_non_dict(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps(["a", "list"]), encoding="utf-8"
        )

        with pytest.raises(IntegrationStateError):
            read_integration_state(tmp_path)

    def test_accepts_current_schema(self, tmp_path):
        data = {"integration_state_schema": INTEGRATION_STATE_SCHEMA}
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

        result = read_integration_state(tmp_path)

        assert result is not None

    def test_uses_installed_integrations_fallback(self, tmp_path):
        data = {"installed_integrations": ["gemini", "claude"]}
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps(data), encoding="utf-8"
        )

        result = read_integration_state(tmp_path)

        assert result is not None
        assert result["default_integration"] == "gemini"


class TestResolveProjectIntegration:
    """Tests for resolve_project_integration()."""

    def test_from_integration_json(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps({"integration": "opencode"}), encoding="utf-8"
        )

        assert resolve_project_integration(tmp_path) == "opencode"

    def test_fallback_to_init_options(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "init-options.json").write_text(
            json.dumps({"integration": "claude"}), encoding="utf-8"
        )

        assert resolve_project_integration(tmp_path) == "claude"

    def test_fallback_to_init_options_ai_key(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "opencode"}), encoding="utf-8"
        )

        assert resolve_project_integration(tmp_path) == "opencode"

    def test_fallback_to_copilot(self, tmp_path):
        assert resolve_project_integration(tmp_path) == "copilot"

    def test_integration_json_takes_priority(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps({"integration": "gemini"}), encoding="utf-8"
        )
        (tmp_path / ".specify" / "init-options.json").write_text(
            json.dumps({"integration": "claude"}), encoding="utf-8"
        )

        assert resolve_project_integration(tmp_path) == "gemini"

    def test_raises_on_invalid_integration_json(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            "not valid json", encoding="utf-8"
        )

        with pytest.raises(IntegrationStateError):
            resolve_project_integration(tmp_path)

    def test_uses_default_integration_field(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps(
                {"default_integration": "gemini", "integration_state_schema": 1}
            ),
            encoding="utf-8",
        )

        assert resolve_project_integration(tmp_path) == "gemini"

    def test_raises_on_future_schema(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps({"integration_state_schema": 999}), encoding="utf-8"
        )

        with pytest.raises(IntegrationStateSchemaError):
            resolve_project_integration(tmp_path)

    def test_whitespace_only_value_falls_through(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "integration.json").write_text(
            json.dumps({"integration": "   "}), encoding="utf-8"
        )

        assert resolve_project_integration(tmp_path) == "copilot"

    def test_auto_value_falls_through(self, tmp_path):
        (tmp_path / ".specify").mkdir()
        (tmp_path / ".specify" / "init-options.json").write_text(
            json.dumps({"integration": "auto"}), encoding="utf-8"
        )

        assert resolve_project_integration(tmp_path) == "copilot"
