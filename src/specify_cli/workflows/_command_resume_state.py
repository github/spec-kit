"""Resume-private installed-workflow owner state resolution."""

from __future__ import annotations

import os
from pathlib import Path


def _path_has_symlink_component(path: Path) -> bool:
    """Return whether any component of an absolute path is a symlink."""
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def _resolve_run_owner_root(
    installed_registry_root: str | None, project_root: Path
) -> Path:
    """Determine which project's registry gates resuming a run.

    ``installed_registry_root`` is only ever persisted when the run's
    installed workflow genuinely belongs to a *different* project than the
    one whose ``runs/`` directory holds this run's own state (a direct
    external workflow-file invocation) -- see ``workflow_run``. The common
    case (an installed workflow run from its own project) stores ``None``,
    so a later project rename/move is transparently picked up here by
    falling back to the *current* ``project_root`` instead of a stale
    absolute path baked in at run start.

    A persisted cross-project root that no longer exists cannot be safely
    rediscovered and must fail closed instead of consulting the unrelated
    project that happens to store the run state.
    """
    if installed_registry_root:
        candidate = Path(installed_registry_root)
        if (
            candidate.is_absolute()
            and not _path_has_symlink_component(candidate)
            and candidate.is_dir()
        ):
            return candidate
        raise ValueError(
            "Installed workflow owner is unavailable; cannot safely resume"
        )
    return project_root
