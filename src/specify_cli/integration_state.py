"""State helpers for installed AI agent integrations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


INTEGRATION_JSON = ".specify/integration.json"
INTEGRATION_STATE_SCHEMA = 1


@dataclass(frozen=True)
class IntegrationReadError:
    """Structured failure from :func:`try_read_integration_json`.

    Callers map ``kind`` to whatever surface they need (loud CLI error,
    silent fallback, etc.) without re-implementing the parse/validation logic.
    """

    kind: str  # "decode", "os", "not_object", "schema_too_new"
    detail: str = ""
    schema: int | None = None


def try_read_integration_json(
    project_root: Path,
) -> tuple[dict[str, Any] | None, IntegrationReadError | None]:
    """Parse ``.specify/integration.json`` without raising.

    Returns ``(normalized_state, None)`` on success, ``(None, None)`` when the
    file does not exist, or ``(None, error)`` for any parse / validation
    failure. This is the single low-level reader; both the CLI's loud
    ``_read_integration_json`` and the workflow engine's silent
    ``_load_project_integration`` consume it so the schema guard and parse
    logic cannot drift between them.
    """
    path = project_root / INTEGRATION_JSON
    if not path.is_file():
        return None, None
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return None, IntegrationReadError(kind="decode", detail=str(exc))
    except OSError as exc:
        return None, IntegrationReadError(kind="os", detail=str(exc))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, IntegrationReadError(kind="decode", detail=str(exc))
    if not isinstance(data, dict):
        return None, IntegrationReadError(kind="not_object", detail=type(data).__name__)
    schema = data.get("integration_state_schema")
    if (
        isinstance(schema, int)
        and not isinstance(schema, bool)
        and schema > INTEGRATION_STATE_SCHEMA
    ):
        return None, IntegrationReadError(kind="schema_too_new", schema=schema)
    return normalize_integration_state(data), None


def clean_integration_key(key: Any) -> str | None:
    """Return a stripped integration key, or None for empty/non-string values."""
    if not isinstance(key, str) or not key.strip():
        return None
    return key.strip()


def dedupe_integration_keys(keys: list[Any]) -> list[str]:
    """Return a de-duplicated list of non-empty integration keys."""
    seen: set[str] = set()
    deduped: list[str] = []
    for key in keys:
        clean = clean_integration_key(key)
        if clean is None:
            continue
        if clean in seen:
            continue
        seen.add(clean)
        deduped.append(clean)
    return deduped


def normalize_integration_settings(settings: Any) -> dict[str, dict[str, Any]]:
    """Return JSON-safe per-integration runtime settings."""
    if not isinstance(settings, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for key, value in settings.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(value, dict):
            continue

        clean: dict[str, Any] = {}
        script = value.get("script")
        if isinstance(script, str) and script.strip():
            clean["script"] = script.strip()

        raw_options = value.get("raw_options")
        if isinstance(raw_options, str):
            clean["raw_options"] = raw_options

        parsed_options = value.get("parsed_options")
        if isinstance(parsed_options, dict):
            clean["parsed_options"] = parsed_options

        invoke_separator = value.get("invoke_separator")
        if isinstance(invoke_separator, str) and invoke_separator.strip():
            clean["invoke_separator"] = invoke_separator.strip()

        if clean:
            normalized[key.strip()] = clean

    return normalized


def _normalized_integration_state_schema(value: Any) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > INTEGRATION_STATE_SCHEMA:
        return value
    return INTEGRATION_STATE_SCHEMA


def normalize_integration_state(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy and multi-install integration metadata."""
    legacy_key = clean_integration_key(data.get("integration"))
    default_key = clean_integration_key(data.get("default_integration")) or legacy_key

    installed = data.get("installed_integrations")
    installed_keys = dedupe_integration_keys(installed if isinstance(installed, list) else [])
    if not default_key and installed_keys:
        default_key = installed_keys[0]
    if default_key and default_key not in installed_keys:
        installed_keys.insert(0, default_key)

    settings = normalize_integration_settings(data.get("integration_settings"))

    normalized = dict(data)
    normalized["integration_state_schema"] = _normalized_integration_state_schema(
        data.get("integration_state_schema")
    )
    if default_key:
        normalized["integration"] = default_key
        normalized["default_integration"] = default_key
    else:
        normalized.pop("integration", None)
        normalized.pop("default_integration", None)
    normalized["installed_integrations"] = installed_keys
    normalized["integration_settings"] = {
        key: settings[key] for key in installed_keys if key in settings
    }
    return normalized


def default_integration_key(state: dict[str, Any]) -> str | None:
    """Return the default integration key from normalized state."""
    key = state.get("default_integration") or state.get("integration")
    return clean_integration_key(key)


def installed_integration_keys(state: dict[str, Any]) -> list[str]:
    """Return installed integration keys from normalized state."""
    return dedupe_integration_keys(state.get("installed_integrations", []))


def integration_settings(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return normalized per-integration settings from state."""
    return normalize_integration_settings(state.get("integration_settings"))


def integration_setting(state: dict[str, Any], key: str) -> dict[str, Any]:
    """Return stored runtime settings for *key*."""
    return dict(integration_settings(state).get(key, {}))


def write_integration_json(
    project_root: Path,
    *,
    version: str,
    integration_key: str | None,
    installed_integrations: list[str] | None = None,
    settings: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Write ``.specify/integration.json`` with legacy-compatible state."""
    dest = project_root / INTEGRATION_JSON
    dest.parent.mkdir(parents=True, exist_ok=True)

    integration_key = clean_integration_key(integration_key)
    installed = dedupe_integration_keys(installed_integrations or [])
    if integration_key and integration_key not in installed:
        installed.insert(0, integration_key)
    if not integration_key and installed:
        integration_key = installed[0]

    normalized_settings = normalize_integration_settings(settings or {})
    normalized_settings = {
        key: normalized_settings[key] for key in installed if key in normalized_settings
    }

    data: dict[str, Any] = {
        "version": version,
        "integration_state_schema": INTEGRATION_STATE_SCHEMA,
        "installed_integrations": installed,
        "integration_settings": normalized_settings,
    }
    if integration_key:
        data["integration"] = integration_key
        data["default_integration"] = integration_key

    dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
