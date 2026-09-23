"""Command handler for ``specify workflow overlay disable``."""

from __future__ import annotations

from .. import _commands as cli
from . import overlay_app


@overlay_app.command("disable")
def workflow_overlay_disable_cmd(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID the overlay extends"),
    overlay_id: str = cli.typer.Argument(..., help="Overlay ID"),
):
    """Disable a project-local overlay."""
    from .operations import workflow_overlay_disable

    project_root = cli._require_specify_project()
    if not workflow_overlay_disable(project_root, workflow_id, overlay_id):
        raise cli.typer.Exit(1)
