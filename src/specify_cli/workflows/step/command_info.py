"""Command handler for ``specify workflow step info``."""

from __future__ import annotations

from .. import _commands as cli
from . import step_app


def _format_source(installed_meta: dict) -> str:
    """Render a registry entry's provenance as a human-facing source label.

    Local and URL installs deliberately store no path/URL, so only the source
    kind is shown.
    """
    source = installed_meta.get("source")
    if source == "catalog":
        catalog_name = installed_meta.get("catalog_name")
        if catalog_name:
            return f"catalog ({cli._escape_markup(str(catalog_name))})"
        return "catalog"
    if source in ("local", "url"):
        return str(source)
    return ""


@step_app.command("info")
def workflow_step_info(
    step_id: str = cli.typer.Argument(..., help="Step type ID"),
):
    """Show details for a step type."""
    from .. import STEP_REGISTRY
    from .catalog import StepCatalog, StepCatalogError, StepRegistry

    project_root = cli._require_specify_project()
    safe_step_id = cli._escape_markup(str(step_id))

    registry = StepRegistry(project_root)
    installed_meta = registry.get(step_id)

    # Check if it's a built-in
    builtin_step = STEP_REGISTRY.get(step_id)
    is_builtin = builtin_step is not None and not installed_meta

    if is_builtin:
        cli.console.print(
            f"\n[bold cyan]{safe_step_id}[/bold cyan] [dim](built-in)[/dim]"
        )
        cli.console.print(f"  Type key: {safe_step_id}")
        cli.console.print("  [green]Built-in step type[/green]")
        return

    if installed_meta:
        name = cli._escape_markup(str(installed_meta.get("name", step_id)))
        version = cli._escape_markup(str(installed_meta.get("version", "?")))
        cli.console.print(f"\n[bold cyan]{name}[/bold cyan] ({safe_step_id})")
        cli.console.print(f"  Version:     {version}")
        if installed_meta.get("author"):
            cli.console.print(
                f"  Author:      {cli._escape_markup(str(installed_meta['author']))}"
            )
        if installed_meta.get("description"):
            cli.console.print(
                f"  Description: "
                f"{cli._escape_markup(str(installed_meta['description']))}"
            )
        source_label = _format_source(installed_meta)
        if source_label:
            cli.console.print(f"  Source:      {source_label}")
        cli.console.print("  [green]Installed[/green]")
        return

    # Try catalog
    catalog = StepCatalog(project_root)
    try:
        info = catalog.get_step_info(step_id)
    except StepCatalogError:
        info = None

    if info:
        name = cli._escape_markup(str(info.get("name", step_id)))
        version = cli._escape_markup(str(info.get("version", "?")))
        cli.console.print(f"\n[bold cyan]{name}[/bold cyan] ({safe_step_id})")
        cli.console.print(f"  Version:     {version}")
        if info.get("author"):
            cli.console.print(
                f"  Author:      {cli._escape_markup(str(info['author']))}"
            )
        if info.get("description"):
            cli.console.print(
                f"  Description: {cli._escape_markup(str(info['description']))}"
            )
        cli.console.print("  [yellow]Not installed[/yellow]")
        cli.console.print(
            f"\n  Install with: [cyan]specify workflow step add {safe_step_id}[/cyan]"
        )
    else:
        cli.console.print(f"[red]Error:[/red] Step type '{safe_step_id}' not found")
        raise cli.typer.Exit(1)
