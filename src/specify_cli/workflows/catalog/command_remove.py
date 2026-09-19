"""Command handler for ``specify workflow catalog remove``."""

from __future__ import annotations

from .. import _commands as cli
from . import catalog_app


@catalog_app.command("remove")
def workflow_catalog_remove(
    index: int = cli.typer.Argument(
        ..., help="Catalog index to remove (from 'catalog list')"
    ),
):
    """Remove a workflow catalog source by index."""
    from . import WorkflowCatalog, WorkflowValidationError

    project_root = cli._require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except WorkflowValidationError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    cli.console.print(f"[green]✓[/green] Catalog source '{removed_name}' removed")
