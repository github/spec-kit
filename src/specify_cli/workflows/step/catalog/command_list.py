"""Command handler for ``specify workflow step catalog list``."""

from __future__ import annotations

from ... import _commands as cli
from . import catalog_app


@catalog_app.command("list")
def workflow_step_catalog_list():
    """List configured step catalog sources."""
    from . import StepCatalog, StepCatalogError

    project_root = cli._require_specify_project()
    catalog = StepCatalog(project_root)

    try:
        configs = catalog.get_catalog_configs()
    except StepCatalogError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    cli.console.print("\n[bold cyan]Step Catalog Sources:[/bold cyan]\n")
    for i, cfg in enumerate(configs):
        install_status = (
            "[green]install allowed[/green]"
            if cfg["install_allowed"]
            else "[yellow]discovery only[/yellow]"
        )
        cli.console.print(
            f"  [{i}] [bold]{cli._escape_markup(str(cfg['name']))}[/bold] — {install_status}"
        )
        cli.console.print(f"      {cli._escape_markup(str(cfg['url']))}")
        if cfg.get("description"):
            cli.console.print(
                f"      [dim]{cli._escape_markup(str(cfg['description']))}[/dim]"
            )
        cli.console.print()
