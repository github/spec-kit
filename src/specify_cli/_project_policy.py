"""Transport-neutral project-boundary policy validation."""

from __future__ import annotations

from pathlib import Path

from ._file_policy import ProjectPolicyError, project_files


class ProjectResolutionError(RuntimeError):
    """A project-root error that callers can render for their own surface."""


def preflight_project_policy(project_root: Path) -> None:
    """Validate at the resolved project boundary without printing or caching."""
    try:
        project_files(project_root)
    except ProjectPolicyError as exc:
        marker = project_root / ".specify"
        if marker.is_symlink():
            raise ProjectResolutionError(
                f"Refusing to use symlinked .specify path: {marker}. {exc}"
            ) from exc
        if marker.exists() and not marker.is_dir():
            raise ProjectResolutionError(
                f"Not a Spec Kit project: .specify path exists but is not a directory: {marker}"
            ) from exc
        raise ProjectResolutionError(str(exc)) from exc
