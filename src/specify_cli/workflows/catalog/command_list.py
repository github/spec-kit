"""Command handler for ``specify workflow catalog list``."""

from __future__ import annotations

from .. import _commands as cli
from . import _operation_list as operation
from . import catalog_app


@catalog_app.command("list")
def workflow_catalog_list():
    """List configured workflow catalog sources."""
    project_root = cli._require_specify_project()

    try:
        result = operation.list_catalog_sources(
            operation.WorkflowCatalogListRequest(project_root)
        )
    except operation.WorkflowCatalogListError as exc:
        # The CLI keeps its established local diagnostics; the shared message is
        # deliberately free of configured values.
        diagnostic = str(exc.__cause__ or exc)
        cli.console.print(f"[red]Error:[/red] {cli._escape_markup(diagnostic)}")
        raise cli.typer.Exit(1) from exc

    cli.console.print("\n[bold cyan]Workflow Catalog Sources:[/bold cyan]\n")
    for i, source in enumerate(result.items):
        install_status = (
            "[green]install allowed[/green]"
            if source.install_allowed
            else "[yellow]discovery only[/yellow]"
        )
        cli.console.print(
            f"  [{i}] [bold]{cli._escape_markup(str(source.name))}[/bold] — {install_status}"
        )
        cli.console.print(f"      {cli._escape_markup(str(source.url))}")
        if source.description:
            cli.console.print(
                f"      [dim]{cli._escape_markup(str(source.description))}[/dim]"
            )
        cli.console.print()
