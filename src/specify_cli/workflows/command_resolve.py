"""Command handler for ``specify workflow resolve``."""

from __future__ import annotations

from . import _commands as cli


@cli.workflow_app.command("resolve")
def workflow_resolve_cmd(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID to resolve"),
):
    """Show layer attribution for a resolved workflow."""
    from .overlay.operations import workflow_resolve

    project_root = cli._require_specify_project()
    if workflow_resolve(project_root, workflow_id) is None:
        raise cli.typer.Exit(1)
