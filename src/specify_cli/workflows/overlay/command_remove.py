"""Command handler for ``specify workflow overlay remove``."""

from __future__ import annotations

from .. import _commands as cli
from . import overlay_app


@overlay_app.command("remove")
def workflow_overlay_remove_cmd(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID the overlay extends"),
    overlay_id: str = cli.typer.Argument(..., help="Overlay ID"),
):
    """Remove a project-local overlay."""
    from .operations import workflow_overlay_remove

    project_root = cli._require_specify_project()
    if not workflow_overlay_remove(project_root, workflow_id, overlay_id):
        raise cli.typer.Exit(1)
