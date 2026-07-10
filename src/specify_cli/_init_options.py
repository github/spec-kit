"""Helpers for interpreting persisted init options."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Union


INIT_OPTIONS_FILE = ".specify/init-options.json"


class _MissingInitOptionsFile:
    """Sentinel: init-options.json does not exist at all (legacy layout)."""

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return "MISSING_INIT_OPTIONS_FILE"


MISSING_INIT_OPTIONS_FILE = _MissingInitOptionsFile()


def save_init_options(project_path: Path, options: dict[str, Any]) -> None:
    """Persist the CLI options used during ``specify init``."""
    dest = project_path / INIT_OPTIONS_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(options, indent=2, sort_keys=True, ensure_ascii=False),
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


def resolve_active_agent_for_registration(
    project_path: Path,
) -> Union[str, None, _MissingInitOptionsFile]:
    """Resolve the active integration key for active-only registration (#2948).

    ``load_init_options`` collapses "no file", "unreadable/malformed file",
    and "valid file with no recorded active agent" into the same ``{}``
    result, which previously made corrupted-but-present init-options behave
    like a legacy pre-init-options project and fall back to registering
    every detected agent. This helper distinguishes those cases explicitly:

    - Returns :data:`MISSING_INIT_OPTIONS_FILE` when init-options.json does
      not exist at all (pre-init-options layout or direct library use).
      Callers should fall back to detection-based registration for all
      agents, matching the original pre-#2948 behavior for such projects.
    - Returns ``None`` when init-options.json exists but could not provide a
      valid non-empty string active agent (malformed/unreadable JSON,
      non-object payload, or a non-string/empty ``ai`` value). Callers must
      fail closed (register nothing) rather than treat this like "no file"
      or pass a non-string key into agent-config lookups.
    - Returns the active agent key (a non-empty string) otherwise.
    """
    path = project_path / INIT_OPTIONS_FILE
    # A dangling symlink's target doesn't exist, so Path.exists() (which
    # follows symlinks) returns False even though the path itself is
    # present as a broken/corrupted entry. Treat any symlink as "present"
    # so a dangling one fails closed via the invalid-file branch below
    # instead of being mistaken for "no file at all" (legacy fallback).
    if not path.is_symlink() and not path.exists():
        return MISSING_INIT_OPTIONS_FILE

    active_agent = load_init_options(project_path).get("ai")
    if isinstance(active_agent, str) and active_agent:
        return active_agent
    return None
