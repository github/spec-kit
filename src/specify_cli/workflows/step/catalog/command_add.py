"""Command handler for ``specify workflow step catalog add``."""

from __future__ import annotations

from ... import _commands as cli
from . import catalog_app


@catalog_app.command("add")
def workflow_step_catalog_add(
    url: str = cli.typer.Argument(..., help="Catalog URL to add"),
    name: str | None = cli.typer.Option(None, "--name", help="Catalog name"),
):
    """Add a step catalog source."""
    from . import StepCatalog, StepValidationError

    project_root = cli._require_specify_project()

    catalog = StepCatalog(project_root)
    try:
        status = catalog.add_catalog(url, name)
    except StepValidationError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    safe_url = cli._escape_markup(url.strip())
    if status == "unchanged":
        cli.console.print(
            f"[green]✓[/green] Step catalog source already configured: {safe_url}"
        )
    else:
        cli.console.print(
            f"[green]✓[/green] Step catalog source added: {safe_url}"
        )
