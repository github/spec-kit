"""Transport-neutral validation of existing workflow storage boundaries."""

from pathlib import Path


class WorkflowStorageError(ValueError):
    """A workflow storage directory is symlinked or has the wrong type."""


def validate_workflow_storage(project_root: Path) -> None:
    """Check storage without creating directories or following child symlinks."""
    for suffix in (
        ".specify",
        ".specify/workflows",
        ".specify/workflows/runs",
        ".specify/workflows/overlays",
    ):
        path = project_root / suffix
        if path.is_symlink():
            raise WorkflowStorageError(f"Refusing to use symlinked {suffix} path")
        if path.exists() and not path.is_dir():
            raise WorkflowStorageError(f"{suffix} path exists but is not a directory")
