"""specify integration helpers — internal utilities shared across command modules."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import typer

from .._agent_config import SCRIPT_TYPE_CHOICES
from .._console import console
from ..integration_runtime import (
    invoke_separator_for_integration as _invoke_separator_for_integration,
    resolve_integration_options as _resolve_integration_options_impl,
    with_integration_setting as _with_integration_setting,
)
from ..integration_state import (
    INTEGRATION_JSON,
    INTEGRATION_STATE_SCHEMA,
    integration_setting as _integration_setting,
    try_read_integration_json as _try_read_integration_json,
    write_integration_json as _write_integration_json_file,
)


def _get_speckit_version() -> str:
    """Return the current Spec Kit version.

    Resolved lazily through ``_commands.get_speckit_version`` so that tests
    that monkeypatch ``specify_cli.integrations._commands.get_speckit_version``
    still affect helpers called from the command handlers.
    """
    from . import _commands  # noqa: PLC0415 — intentional late import to avoid circular + enable patching
    return _commands.get_speckit_version()


# ---------------------------------------------------------------------------
# JSON read / write helpers
# ---------------------------------------------------------------------------

def _read_integration_json(project_root: Path) -> dict[str, Any]:
    """Load ``.specify/integration.json``. Returns normalized state when present.

    Delegates the parse / schema-guard logic to the shared
    :func:`_try_read_integration_json` helper so the CLI and workflow engine
    cannot drift on validation rules. Each error variant is translated into
    the existing loud-fail UX (console message + ``typer.Exit(1)``).
    """
    path = project_root / INTEGRATION_JSON
    state, error = _try_read_integration_json(project_root)
    if error is None:
        return state or {}
    if error.kind == "decode":
        console.print(f"[red]Error:[/red] {path} contains invalid JSON or is not valid UTF-8.")
        console.print(f"Please fix or delete {INTEGRATION_JSON} and retry.")
        console.print(f"[dim]Details:[/dim] {error.detail}")
    elif error.kind == "os":
        console.print(f"[red]Error:[/red] Could not read {path}.")
        console.print(f"Please fix file permissions or delete {INTEGRATION_JSON} and retry.")
        console.print(f"[dim]Details:[/dim] {error.detail}")
    elif error.kind == "not_object":
        console.print(
            f"[red]Error:[/red] {path} must contain a JSON object, got {error.detail}."
        )
        console.print(f"Please fix or delete {INTEGRATION_JSON} and retry.")
    elif error.kind == "schema_too_new":
        console.print(
            f"[red]Error:[/red] {path} uses integration state schema {error.schema}, "
            f"but this CLI only supports schema {INTEGRATION_STATE_SCHEMA}."
        )
        console.print("Please upgrade Spec Kit before modifying integrations.")
    raise typer.Exit(1)


def _write_integration_json(
    project_root: Path,
    integration_key: str | None,
    installed_integrations: list[str] | None = None,
    integration_settings: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Write ``.specify/integration.json`` with legacy-compatible state."""
    _write_integration_json_file(
        project_root,
        version=_get_speckit_version(),
        integration_key=integration_key,
        installed_integrations=installed_integrations,
        settings=integration_settings,
    )


# ---------------------------------------------------------------------------
# init-options.json helpers
# ---------------------------------------------------------------------------

def _refresh_init_options_speckit_version(project_root: Path) -> None:
    """Refresh only the Spec Kit version recorded in init-options.json."""
    from .. import load_init_options, save_init_options
    opts = load_init_options(project_root)
    if not isinstance(opts, dict) or not opts:
        return
    opts["speckit_version"] = _get_speckit_version()
    save_init_options(project_root, opts)


def _clear_init_options_for_integration(project_root: Path, integration_key: str) -> None:
    """Clear active integration keys from init-options.json when they match.

    Also clears ``context_file`` from the agent-context extension config so
    no stale path is left behind when the integration is uninstalled.
    """
    from .. import (
        _AGENT_CTX_EXT_CONFIG,
        _update_agent_context_config_file,
        load_init_options,
        save_init_options,
    )
    opts = load_init_options(project_root)
    has_legacy_context_keys = ("context_file" in opts) or ("context_markers" in opts)
    # Remove legacy fields that older versions may have written.
    opts.pop("context_file", None)
    opts.pop("context_markers", None)

    if opts.get("integration") == integration_key or opts.get("ai") == integration_key:
        opts.pop("integration", None)
        opts.pop("ai", None)
        opts.pop("ai_skills", None)
        save_init_options(project_root, opts)
        # Clear context_file in the extension config if it already exists.
        # Avoid creating the config (and parent dirs) in projects where the
        # agent-context extension was never installed.
        ext_cfg_path = project_root / _AGENT_CTX_EXT_CONFIG
        if ext_cfg_path.exists():
            _update_agent_context_config_file(
                project_root, "", preserve_markers=True, preserve_context_files=False
            )
    elif has_legacy_context_keys:
        save_init_options(project_root, opts)


def _remove_integration_json(project_root: Path) -> None:
    """Remove ``.specify/integration.json`` if it exists."""
    path = project_root / INTEGRATION_JSON
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Error sentinels
# ---------------------------------------------------------------------------

_MANIFEST_READ_ERRORS = (ValueError, FileNotFoundError, OSError, UnicodeDecodeError)


class _SharedTemplateRefreshError(RuntimeError):
    """Raised when default integration metadata should not be persisted."""


# ---------------------------------------------------------------------------
# Script type resolution
# ---------------------------------------------------------------------------

def _normalize_script_type(script_type: str, source: str) -> str:
    """Normalize and validate a script type from CLI/config sources."""
    normalized = script_type.strip().lower()
    if normalized in SCRIPT_TYPE_CHOICES:
        return normalized
    console.print(
        f"[red]Error:[/red] Invalid script type {script_type!r} from {source}. "
        f"Expected one of: {', '.join(sorted(SCRIPT_TYPE_CHOICES.keys()))}."
    )
    raise typer.Exit(1)


def _resolve_script_type(project_root: Path, script_type: str | None) -> str:
    """Resolve the script type from the CLI flag or init-options.json."""
    from .. import load_init_options
    if script_type:
        return _normalize_script_type(script_type, "--script")
    opts = load_init_options(project_root)
    saved = opts.get("script")
    if isinstance(saved, str) and saved.strip():
        return _normalize_script_type(saved, ".specify/init-options.json")
    return "ps" if os.name == "nt" else "sh"


def _resolve_integration_script_type(
    project_root: Path,
    state: dict[str, Any],
    key: str,
    script_type: str | None = None,
) -> str:
    """Resolve script type for an integration, preferring stored settings."""
    if script_type:
        return _normalize_script_type(script_type, "--script")

    stored = _integration_setting(state, key).get("script")
    if isinstance(stored, str) and stored.strip():
        return _normalize_script_type(stored, f"{INTEGRATION_JSON} integration_settings.{key}.script")

    return _resolve_script_type(project_root, None)


# ---------------------------------------------------------------------------
# Integration options
# ---------------------------------------------------------------------------

def _parse_integration_options(integration: Any, raw_options: str) -> dict[str, Any] | None:
    """Parse --integration-options string into a dict matching the integration's declared options.

    Returns ``None`` when no options are provided.
    """
    import shlex
    parsed: dict[str, Any] = {}
    tokens = shlex.split(raw_options)
    declared_options = list(integration.options())
    declared = {opt.name.lstrip("-"): opt for opt in declared_options}
    allowed = ", ".join(sorted(opt.name for opt in declared_options))
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token.startswith("-"):
            console.print(f"[red]Error:[/red] Unexpected integration option value '{token}'.")
            if allowed:
                console.print(f"Allowed options: {allowed}")
            raise typer.Exit(1)
        name = token.lstrip("-")
        value: str | None = None
        # Handle --name=value syntax
        if "=" in name:
            name, value = name.split("=", 1)
        opt = declared.get(name)
        if not opt:
            console.print(f"[red]Error:[/red] Unknown integration option '{token}'.")
            if allowed:
                console.print(f"Allowed options: {allowed}")
            raise typer.Exit(1)
        key = name.replace("-", "_")
        if opt.is_flag:
            if value is not None:
                console.print(f"[red]Error:[/red] Option '{opt.name}' is a flag and does not accept a value.")
                raise typer.Exit(1)
            parsed[key] = True
            i += 1
        elif value is not None:
            parsed[key] = value
            i += 1
        elif i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
            parsed[key] = tokens[i + 1]
            i += 2
        else:
            console.print(f"[red]Error:[/red] Option '{opt.name}' requires a value.")
            raise typer.Exit(1)
    return parsed or None


def _resolve_integration_options(
    integration: Any,
    state: dict[str, Any],
    key: str,
    raw_options: str | None,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve raw and parsed options for an integration operation."""
    return _resolve_integration_options_impl(
        integration,
        state,
        key,
        raw_options,
        parse_options=_parse_integration_options,
    )


def _update_init_options_for_integration(
    project_root: Path,
    integration: Any,
    script_type: str | None = None,
) -> None:
    """Update init-options.json and the agent-context extension config to
    reflect *integration* as the active one.

    ``context_file``, ``context_files``, and ``context_markers`` are stored in the agent-context
    extension config (``.specify/extensions/agent-context/agent-context-config.yml``),
    not in ``init-options.json``.  Existing user-customised markers are
    always preserved when the config already exists. Existing ``context_files``
    lists are also preserved so projects can keep multi-agent context anchors
    during integration switches. Invalid marker values are
    silently ignored at runtime by ``_resolve_context_markers()`` which falls
    back to the class-level defaults.
    """
    from .. import (
        _AGENT_CTX_EXT_CONFIG,
        _update_agent_context_config_file,
        load_init_options,
        save_init_options,
    )
    from .base import SkillsIntegration
    opts = load_init_options(project_root)
    opts["integration"] = integration.key
    opts["ai"] = integration.key
    # Remove legacy fields if they were written by an older version.
    opts.pop("context_file", None)
    opts.pop("context_markers", None)
    opts["speckit_version"] = _get_speckit_version()
    if script_type:
        opts["script"] = script_type
    if isinstance(integration, SkillsIntegration) or getattr(integration, "_skills_mode", False):
        opts["ai_skills"] = True
    else:
        opts.pop("ai_skills", None)

    # Update the agent-context extension config BEFORE init-options.json
    # so a failure here doesn't leave init-options partially updated.
    ext_cfg_path = project_root / _AGENT_CTX_EXT_CONFIG
    if ext_cfg_path.exists():
        _update_agent_context_config_file(
            project_root,
            integration.context_file,
            preserve_markers=True,
        )
    elif integration.context_file:
        # Extension config doesn't exist yet (extension not installed).
        # Write defaults so scripts have something to read.
        _update_agent_context_config_file(
            project_root,
            integration.context_file,
            preserve_markers=False,
        )

    save_init_options(project_root, opts)


# ---------------------------------------------------------------------------
# Default integration persistence
# ---------------------------------------------------------------------------

def _set_default_integration(
    project_root: Path,
    state: dict[str, Any],
    key: str,
    integration: Any,
    installed_keys: list[str],
    *,
    script_type: str | None = None,
    raw_options: str | None = None,
    parsed_options: dict[str, Any] | None = None,
    refresh_templates: bool = True,
    refresh_templates_force: bool = False,
    refresh_hint: str | None = None,
) -> None:
    """Persist *key* as default and align active runtime metadata."""
    from .. import _install_shared_infra
    resolved_script = _resolve_integration_script_type(project_root, state, key, script_type)
    settings = _with_integration_setting(
        state,
        key,
        integration,
        script_type=resolved_script,
        raw_options=raw_options,
        parsed_options=parsed_options,
    )

    if refresh_templates:
        try:
            _install_shared_infra(
                project_root,
                resolved_script,
                invoke_separator=_invoke_separator_for_integration(
                    integration, {"integration_settings": settings}, key, parsed_options
                ),
                force=refresh_templates_force,
                refresh_managed=True,
                refresh_hint=refresh_hint,
            )
        except (ValueError, OSError) as exc:
            raise _SharedTemplateRefreshError(
                f"Failed to refresh shared infrastructure for '{key}': {exc}"
            ) from exc

    _write_integration_json(project_root, key, installed_keys, settings)
    _update_init_options_for_integration(project_root, integration, script_type=resolved_script)


def _set_default_integration_or_exit(*args: Any, **kwargs: Any) -> None:
    try:
        _set_default_integration(*args, **kwargs)
    except _SharedTemplateRefreshError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# CLI formatting helpers (re-exported from _commands.py)
# ---------------------------------------------------------------------------

def _cli_error_detail(exc: BaseException) -> str:
    """Return a compact one-line exception detail for CLI output."""
    return str(exc).replace("\n", " ").strip() or exc.__class__.__name__


def _cli_phase_label(phase: str, target_kind: str, target: str | None = None) -> str:
    """Format a stable operation label for user-visible diagnostics."""
    label = f"{phase} {target_kind}".strip()
    if target:
        label = f"{label} '{target}'"
    return label
