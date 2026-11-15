"""Command handler for ``specify workflow list``."""

from __future__ import annotations

from . import _commands as cli
from . import _operation_list as operation


@cli.workflow_app.command("list")
def workflow_list():
    """List installed workflows."""
    project_root = cli._require_specify_project()
    try:
        result = operation.list_workflows(operation.WorkflowListRequest(project_root))
    except operation.WorkflowListError as exc:
        cli.console.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1) from exc

    if not result.items:
        cli.console.print("[yellow]No workflows installed.[/yellow]")
        cli.console.print("\nInstall a workflow with:")
        cli.console.print("  [cyan]specify workflow add <workflow-id>[/cyan]")
        return

    cli.console.print("\n[bold cyan]Installed Workflows:[/bold cyan]\n")
    for item in result.items:
        if isinstance(item, operation.WorkflowListWarning):
            cli.console.print(
                f"  [yellow]Warning:[/yellow] {cli._escape_markup(item.message)}\n"
            )
            continue
        safe_id = cli._escape_markup(item.id)
        marker = "" if item.enabled else " [red]\\[disabled][/red]"
        name = cli._escape_markup(item.name)
        version = cli._escape_markup(item.version)
        cli.console.print(f"  [bold]{name}[/bold] ({safe_id}) v{version}{marker}")
        desc = item.description
        if desc:
            cli.console.print(f"    {cli._escape_markup(str(desc))}")
        cli.console.print()
