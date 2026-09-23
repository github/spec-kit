"""Command handler for ``specify workflow disable``."""

from __future__ import annotations

from . import _commands as cli


@cli.workflow_app.command("disable")
def workflow_disable(
    workflow_id: str = cli.typer.Argument(..., help="Workflow ID to disable"),
):
    """Disable a workflow without removing it."""
    cli._set_workflow_enabled(workflow_id, False)
    cli.console.print(
        f"To re-enable: specify workflow enable {cli._escape_markup(workflow_id)}"
    )
