"""Command handler for ``specify workflow enable``."""

from __future__ import annotations

from . import _commands as cli


@cli.workflow_app.command("enable")
def workflow_enable(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID to enable"),
):
    """Enable a disabled workflow."""
    cli._set_workflow_enabled(workflow_id, True)
