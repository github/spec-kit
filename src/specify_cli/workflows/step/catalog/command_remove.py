"""Command handler for ``specify workflow step catalog remove``."""

from __future__ import annotations

from ... import _commands as cli
from . import catalog_app


@catalog_app.command("remove")
def workflow_step_catalog_remove(
    index: int = cli.typer.Argument(
        ..., help="Catalog index to remove (from 'step catalog list')"
    ),
):
    """Remove a step catalog source by index."""
    from . import StepCatalog, StepValidationError

    project_root = cli._require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        removed_name = catalog.remove_catalog(index)
    except StepValidationError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    cli.console.print(f"[green]✓[/green] Step catalog source '{removed_name}' removed")
