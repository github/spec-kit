"""Runtime helpers for integration commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .integration_state import integration_setting, integration_settings


ParseOptions = Callable[[Any, str], dict[str, Any] | None]


def resolve_integration_options(
    integration: Any,
    state: dict[str, Any],
    key: str,
    raw_options: str | None,
    *,
    parse_options: ParseOptions,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve raw and parsed options for an integration operation."""
    if raw_options is not None:
        return raw_options, parse_options(integration, raw_options)

    setting = integration_setting(state, key)
    stored_raw = setting.get("raw_options")
    if not isinstance(stored_raw, str):
        stored_raw = None

    stored_parsed = setting.get("parsed_options")
    if isinstance(stored_parsed, dict):
        return stored_raw, stored_parsed or None

    if stored_raw:
        return stored_raw, parse_options(integration, stored_raw)

    return None, None


def with_integration_setting(
    state: dict[str, Any],
    key: str,
    integration: Any,
    *,
    script_type: str | None = None,
    raw_options: str | None = None,
    parsed_options: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return integration settings with *key* updated."""
    settings = integration_settings(state)
    current = dict(settings.get(key, {}))

    if script_type:
        current["script"] = script_type
    if raw_options is not None:
        current["raw_options"] = raw_options
    elif "raw_options" in current and not current.get("raw_options"):
        current.pop("raw_options", None)

    if parsed_options is not None:
        current["parsed_options"] = parsed_options
    elif raw_options is not None:
        current.pop("parsed_options", None)

    current["invoke_separator"] = integration.effective_invoke_separator(parsed_options)
    settings[key] = current
    return settings


def invoke_separator_for_integration(
    integration: Any,
    state: dict[str, Any],
    key: str,
    parsed_options: dict[str, Any] | None = None,
) -> str:
    """Resolve the invocation separator for stored/default integration state."""
    if parsed_options is not None:
        return integration.effective_invoke_separator(parsed_options)

    setting = integration_setting(state, key)
    stored_separator = setting.get("invoke_separator")
    if isinstance(stored_separator, str) and stored_separator:
        return stored_separator

    stored_parsed = setting.get("parsed_options")
    if isinstance(stored_parsed, dict):
        return integration.effective_invoke_separator(stored_parsed)

    return integration.effective_invoke_separator(None)
