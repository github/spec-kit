"""Spec Kit project detection and active-integration resolution."""
from __future__ import annotations

from pathlib import Path

from .. import BundlerError
from .yamlio import load_json

DEFAULT_INTEGRATION = "copilot"


def find_project_root(start: Path | None = None) -> Path | None:
    """Return the nearest ancestor (incl. *start*) containing a ``.specify/`` dir, or None."""
    current = Path(start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".specify").is_dir():
            return candidate
    return None


def require_project_root(start: Path | None = None) -> Path:
    """Return the Spec Kit project root or raise an actionable error."""
    root = find_project_root(start)
    if root is None:
        raise BundlerError(
            "Not a Spec Kit project (no .specify/ directory). "
            "Run 'specify bundle init' or 'specify init' first."
        )
    return root


def active_integration(project_root: Path) -> str | None:
    """Return the project's active integration id, if recorded.

    Spec Kit records the chosen integration in ``.specify/integration.json``
    during init. Returns None when it cannot be determined (e.g. agnostic).
    """
    marker = Path(project_root) / ".specify" / "integration.json"
    if not marker.exists():
        return None
    try:
        data = load_json(marker)
    except BundlerError:
        return None
    if isinstance(data, dict):
        value = data.get("integration") or data.get("id") or data.get("active")
        if isinstance(value, str) and value:
            return value
    return None
