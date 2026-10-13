"""Command handler for ``specify workflow overlay set-priority``."""

from __future__ import annotations

from .. import _commands as cli
from . import overlay_app


@overlay_app.command("set-priority")
def workflow_overlay_set_priority_cmd(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID the overlay extends"),
    overlay_id: str = cli.typer.Argument(..., help="Overlay ID"),
    priority: int = cli.typer.Argument(
        ..., help="New priority (lower = higher precedence)"
    ),
):
    """Set the priority of a project-local overlay."""
    from .operations import workflow_overlay_set_priority

    project_root = cli._require_specify_project()
    if not workflow_overlay_set_priority(
        project_root, workflow_id, overlay_id, priority
    ):
        raise cli.typer.Exit(1)
