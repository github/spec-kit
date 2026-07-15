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
