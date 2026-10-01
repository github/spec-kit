"""Command handler for ``specify workflow step search``."""

from __future__ import annotations

from .. import _commands as cli
from . import step_app


@step_app.command("search")
def workflow_step_search(
    query: str | None = cli.typer.Argument(None, help="Search query"),
):
    """Search the step type catalog."""
    from .catalog import StepCatalog, StepCatalogError

    project_root = cli._require_specify_project()

    catalog = StepCatalog(project_root)

    try:
        results = catalog.search(query=query)
    except StepCatalogError as exc:
        cli.console.print(f"[red]Error:[/red] {exc}")
        raise cli.typer.Exit(1)

    if not results:
        if query:
            cli.console.print(
                f"[yellow]No step types found matching '{query}'.[/yellow]"
            )
        else:
            cli.console.print("[yellow]No step types found in catalog.[/yellow]")
        return

    cli.console.print(f"\n[bold cyan]Step Types ({len(results)}):[/bold cyan]\n")
    for step in results:
        install_note = (
            "" if step.get("_install_allowed", True) else " [dim](discovery only)[/dim]"
        )
        name = cli._escape_markup(str(step.get("name", step.get("id", "?"))))
        step_id = cli._escape_markup(str(step.get("id", "?")))
        version = cli._escape_markup(str(step.get("version", "?")))
        cli.console.print(f"  [bold]{name}[/bold] ({step_id}) v{version}{install_note}")
        desc = step.get("description", "")
        if desc:
            cli.console.print(f"    {cli._escape_markup(str(desc))}")
        cli.console.print()
