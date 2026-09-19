"""The ``specify integration catalog remove`` command."""
from __future__ import annotations


import typer

from ..._console import console
from . import catalog_app


@catalog_app.command("remove")
def integration_catalog_remove(
    index: int = typer.Argument(..., help="Catalog index to remove (from 'catalog list')"),
):
    """Remove an integration catalog source by 0-based index."""
    from . import IntegrationCatalog, IntegrationCatalogError
    from ... import _require_specify_project

    project_root = _require_specify_project()
    catalog = IntegrationCatalog(project_root)

    try:
        removed_name = catalog.remove_catalog(index)
    except IntegrationCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source '{removed_name}' removed")
