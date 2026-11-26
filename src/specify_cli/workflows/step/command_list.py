"""Command handler for ``specify workflow step list``."""

from __future__ import annotations

from .. import _commands as cli
from . import _operation_list as operation
from . import step_app


@step_app.command("list")
def workflow_step_list():
    """List installed step types (built-in and custom)."""
    project_root = cli._require_specify_project()
    specify_dir = project_root / ".specify"
    try:
        result = operation.list_step_types(
            operation.WorkflowStepListRequest(project_root)
        )
    except operation.WorkflowStepListError as exc:
        cli.console.print(f"[red]Error:[/red] {cli._escape_markup(str(exc))}")
        raise cli.typer.Exit(1) from exc

    built_in = [
        item
        for item in result.items
        if isinstance(item, operation.WorkflowStepListEntry) and item.kind == "builtin"
    ]
    installed = [
        item
        for item in result.items
        if isinstance(item, operation.WorkflowStepListEntry) and item.kind == "custom"
    ]
    warnings = [
        item
        for item in result.items
        if isinstance(item, operation.WorkflowStepListWarning)
    ]

    cli.console.print("\n[bold cyan]Installed Step Types:[/bold cyan]\n")

    if built_in:
        cli.console.print("  [bold]Built-in:[/bold]")
        for item in built_in:
            cli.console.print(f"    • {item.id}")
        cli.console.print()

    if installed:
        cli.console.print("  [bold]Custom (installed):[/bold]")
        for item in installed:
            name = cli._escape_markup(item.name)
            safe_key = cli._escape_markup(item.id)
            version = cli._escape_markup(
                item.version if item.version is not None else "?"
            )
            cli.console.print(f"    • [bold]{name}[/bold] ({safe_key}) v{version}")
        cli.console.print()

    for item in warnings:
        cli.console.print(
            f"  [yellow]Warning:[/yellow] {cli._escape_markup(item.message)}\n"
        )

    if not built_in and not installed:
        cli.console.print("[yellow]No step types found.[/yellow]")

    if specify_dir.exists():
        cli.console.print(
            "  Install a new step type with: [cyan]specify workflow step add <id>[/cyan]"
        )
