"""Helpers for interpreting persisted init options."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


INIT_OPTIONS_FILE = ".specify/init-options.json"


def save_init_options(project_path: Path, options: dict[str, Any]) -> None:
    """Persist the CLI options used during ``specify init``."""
    dest = project_path / INIT_OPTIONS_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(options, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_init_options(project_path: Path) -> dict[str, Any]:
    """Load persisted init options, returning an empty dict when unavailable."""
    path = project_path / INIT_OPTIONS_FILE
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def is_ai_skills_enabled(opts: Mapping[str, Any] | None) -> bool:
    """Return True only when init options explicitly enable AI skills."""
    return isinstance(opts, Mapping) and opts.get("ai_skills") is True


def is_agent_skills_enabled(project_path: Path, agent_name: str, opts: Mapping[str, Any] | None) -> bool:
    """Return True when *agent_name* should render extension skills.

    Prefers the per-agent ``skills`` flag recorded in
    ``.specify/integration.json`` (``integration_settings[agent_name].parsed_options.skills``),
    which reflects the ``--skills`` option passed to that specific agent's
    install/upgrade/switch. Falls back to the legacy global
    ``init-options.json`` ``ai_skills`` flag only when *agent_name* is the
    active agent recorded there (pre-multi-install behaviour).
    """
    from .integration_state import try_read_integration_json, integration_setting

    state, _error = try_read_integration_json(project_path)
    if state:
        setting = integration_setting(state, agent_name)
        parsed = setting.get("parsed_options")
        if isinstance(parsed, Mapping) and "skills" in parsed:
            return parsed.get("skills") is True

    if isinstance(opts, Mapping) and opts.get("ai") == agent_name:
        return is_ai_skills_enabled(opts)

    return False
