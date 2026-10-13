"""Command handler for ``specify workflow list``."""

from __future__ import annotations

from . import _commands as cli


@cli.workflow_app.command("list")
def workflow_list():
    """List installed workflows."""
    project_root = cli._require_specify_project()
    registry = cli._open_workflow_registry(project_root)
    installed = registry.list()

    if not installed:
        cli.console.print("[yellow]No workflows installed.[/yellow]")
        cli.console.print("\nInstall a workflow with:")
        cli.console.print("  [cyan]specify workflow add <workflow-id>[/cyan]")
        return

    cli.console.print("\n[bold cyan]Installed Workflows:[/bold cyan]\n")
    for wf_id, wf_data in installed.items():
        safe_id = cli._escape_markup(wf_id)
        if not isinstance(wf_data, dict):
            cli.console.print(
                f"  [yellow]Warning:[/yellow] Skipping corrupted registry entry '{safe_id}'.\n"
            )
            continue
        marker = "" if wf_data.get("enabled", True) else " [red]\\[disabled][/red]"
        name = cli._escape_markup(str(wf_data.get("name", wf_id)))
        version = cli._escape_markup(str(wf_data.get("version", "?")))
        cli.console.print(f"  [bold]{name}[/bold] ({safe_id}) v{version}{marker}")
        desc = wf_data.get("description", "")
        if desc:
            cli.console.print(f"    {cli._escape_markup(str(desc))}")
        cli.console.print()
