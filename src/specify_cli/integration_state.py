"""State helpers for installed AI agent integrations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


INTEGRATION_JSON = ".specify/integration.json"
INTEGRATION_STATE_SCHEMA = 1
SPECIFY_DIR = ".specify"


class IntegrationStateError(Exception):
    """Raised when integration.json is invalid or unreadable."""


class IntegrationStateSchemaError(IntegrationStateError):
    """Raised when integration.json uses an unsupported schema version."""


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


def read_integration_state(project_root: Path) -> dict[str, Any] | None:
    """Read and normalize ``.specify/integration.json``.

    Returns None if the file does not exist.

    Raises
    ------
    IntegrationStateSchemaError
        If the file declares a schema version newer than this CLI supports.
    IntegrationStateError
        If the file cannot be read, parsed, or is not a JSON object.
    """

    path = project_root / INTEGRATION_JSON
    if not path.is_file():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise IntegrationStateError(f"Could not read {path}") from exc
    except json.JSONDecodeError as exc:
        raise IntegrationStateError(f"{path} contains invalid JSON") from exc

    if not isinstance(data, dict):
        raise IntegrationStateError(
            f"{path} must contain a JSON object, got {type(data).__name__}."
        )

    schema = data.get("integration_state_schema")
    if (
        isinstance(schema, int)
        and not isinstance(schema, bool)
        and schema > INTEGRATION_STATE_SCHEMA
    ):
        raise IntegrationStateSchemaError(
            f"{path} uses integration state schema {schema}, "
            f"but this CLI only supports schema {INTEGRATION_STATE_SCHEMA}."
        )

    return normalize_integration_state(data)


def resolve_project_integration(project_root: Path) -> str:
    """Return the active integration key for a project.

    Fallback chain:
    - ``.specify/integration.json`` (normalized, schema-guarded)
    - ``.specify/init-options.json`` (legacy keys: ``integration`` then ``ai``)
    - ``"copilot"`` (hard-coded default)

    Notes
    -----
    If ``integration.json`` exists but is unreadable/invalid or declares a future
    schema version, this function raises an exception instead of silently falling
    back. That keeps the engine and CLI consistent.
    """

    state = read_integration_state(project_root)  # raises on invalid files
    if state is not None:
        key = default_integration_key(state)
        if key and key != "auto":
            return key

    init_opts_path = project_root / f"{SPECIFY_DIR}/init-options.json"
    integration = _read_legacy_init_options(init_opts_path, "integration", "ai")
    if integration is not None:
        return integration

    return "copilot"


def _read_legacy_init_options(path: Path, *keys: str) -> str | None:
    """Read a string value from a legacy init-options.json file."""

    if not path.is_file():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned and cleaned != "auto":
                return cleaned

    return None
