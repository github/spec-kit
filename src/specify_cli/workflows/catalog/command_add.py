"""Command handler for ``specify workflow catalog add``."""

from __future__ import annotations

from .. import _commands as cli
from . import catalog_app


@catalog_app.command("add")
def workflow_catalog_add(
    url: str = cli.typer.Argument(..., help="Catalog URL to add"),
    name: str | None = cli.typer.Option(None, "--name", help="Catalog name"),
):
    """Add a workflow catalog source."""
    from . import WorkflowCatalog, WorkflowValidationError

    project_root = cli._require_specify_project()
    catalog = WorkflowCatalog(project_root)
    try:
        status = catalog.add_catalog(url, name)
    except WorkflowValidationError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    safe_url = cli._escape_markup(url.strip())
    if status == "unchanged":
        cli.console.print(
            f"[green]✓[/green] Catalog source already configured: {safe_url}"
        )
    else:
        cli.console.print(f"[green]✓[/green] Catalog source added: {safe_url}")
