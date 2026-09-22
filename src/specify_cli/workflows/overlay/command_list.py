"""Command handler for ``specify workflow overlay list``."""

from __future__ import annotations

from .. import _commands as cli
from . import overlay_app


@overlay_app.command("list")
def workflow_overlay_list_cmd(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID"),
):
    """List overlays for a workflow."""
    from .operations import workflow_overlay_list

    project_root = cli._require_specify_project()
    if workflow_overlay_list(project_root, workflow_id) is None:
        raise cli.typer.Exit(1)
