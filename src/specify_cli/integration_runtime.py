"""Runtime helpers for integration commands."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from ._invocation_style import get_invocation_prefix
from .integration_state import integration_setting, integration_settings

ParseOptions = Callable[[Any, str], dict[str, Any] | None]
_registration_options: ContextVar[tuple[Path, dict[str, Any]] | None] = ContextVar(
    "integration_registration_options", default=None,
)
file_write_validator: ContextVar[Callable[[Path, bytes], bool] | None] = ContextVar(
    "integration_file_write_validator", default=None,
)


def should_write_file(path: Path, content: bytes) -> bool:
    """Let lifecycle composition validate final bytes before replacing content."""
    validator = file_write_validator.get()
    return validator(path, content) if validator is not None else True


@contextmanager
def registration_options(project_root: Path, options: dict[str, Any]) -> Iterator[None]:
    """Scope contribution rendering without persisting a different default."""
    token = _registration_options.set((project_root.resolve(), dict(options)))
    try:
        yield
    finally:
        _registration_options.reset(token)


def current_registration_options(project_root: Path) -> dict[str, Any] | None:
    context = _registration_options.get()
    if context is not None and context[0] == project_root.resolve():
        return dict(context[1])
    return None


def parse_integration_options(integration: Any, raw_options: str) -> dict[str, Any] | None:
    """Parse saved integration options without CLI output or process exits."""
    import shlex

    tokens = shlex.split(raw_options)
    declared = {option.name.lstrip("-"): option for option in integration.options()}
    parsed: dict[str, Any] = {}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        name, separator, value = token.lstrip("-").partition("=")
        option = declared.get(name) if token.startswith("-") else None
        if option is None:
            raise ValueError(f"Unknown integration option {token!r}")
        if option.is_flag:
            if separator:
                raise ValueError(f"Option {option.name!r} is a flag and does not accept a value")
            parsed[name.replace("-", "_")] = True
        else:
            if not separator:
                index += 1
                if index == len(tokens) or tokens[index].startswith("-"):
                    raise ValueError(f"Option {option.name!r} requires a value")
                value = tokens[index]
            parsed[name.replace("-", "_")] = value
        index += 1
    return parsed or None


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
    project_root: Any = None,
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

    # Recompute the separator from the options actually STORED on ``current``
    # after the update, not the raw ``parsed_options`` argument. When only
    # ``script_type`` changes (``parsed_options`` and ``raw_options`` both
    # None), the previously-stored ``parsed_options`` are retained above, so
    # deriving the separator from the argument (None) would drop an
    # options-dependent separator (e.g. Copilot ``--commands`` -> ".") back to
    # the default "-".
    current["invoke_separator"] = integration.effective_invoke_separator(
        current.get("parsed_options"), project_root
    )
    settings[key] = current
    return settings


def invoke_separator_for_integration(
    integration: Any,
    state: dict[str, Any],
    key: str,
    parsed_options: dict[str, Any] | None = None,
    project_root: Any = None,
) -> str:
    """Resolve the invocation separator for stored/default integration state."""
    if parsed_options is not None:
        return integration.effective_invoke_separator(parsed_options, project_root)

    setting = integration_setting(state, key)
    stored_separator = setting.get("invoke_separator")
    if isinstance(stored_separator, str) and stored_separator:
        return stored_separator

    stored_parsed = setting.get("parsed_options")
    if isinstance(stored_parsed, dict):
        return integration.effective_invoke_separator(stored_parsed, project_root)

    return integration.effective_invoke_separator(None, project_root)


def invoke_prefix_for_integration(
    integration: Any,
    key: str,
    parsed_options: dict[str, Any] | None = None,
    project_root: Any = None,
) -> str:
    """Resolve the native invocation prefix for an integration's output mode."""
    skills_mode = integration.is_skills_mode(parsed_options, project_root)
    return get_invocation_prefix(key, skills_mode)
