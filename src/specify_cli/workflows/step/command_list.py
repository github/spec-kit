"""Command handler for ``specify workflow step list``."""

from __future__ import annotations

from .. import _commands as cli
from . import step_app


@step_app.command("list")
def workflow_step_list():
    """List installed step types (built-in and custom)."""
    from .. import STEP_REGISTRY
    from .catalog import StepRegistry

    project_root = cli._require_specify_project()
    specify_dir = project_root / ".specify"

    # Read installed custom steps from registry only — no dynamic imports
    installed: dict = {}
    if specify_dir.exists():
        registry = StepRegistry(project_root)
        installed = registry.list()

    cli.console.print("\n[bold cyan]Installed Step Types:[/bold cyan]\n")

    built_in = sorted(k for k in STEP_REGISTRY if k not in installed)
    if built_in:
        cli.console.print("  [bold]Built-in:[/bold]")
        for key in built_in:
            cli.console.print(f"    • {key}")
        cli.console.print()

    if installed:
        cli.console.print("  [bold]Custom (installed):[/bold]")
        for key in sorted(installed):
            meta = installed[key] or {}
            name = cli._escape_markup(str(meta.get("name", key)))
            safe_key = cli._escape_markup(str(key))
            version = cli._escape_markup(str(meta.get("version", "?")))
            cli.console.print(f"    • [bold]{name}[/bold] ({safe_key}) v{version}")
        cli.console.print()

    if not built_in and not installed:
        cli.console.print("[yellow]No step types found.[/yellow]")

    if specify_dir.exists():
        cli.console.print(
            "  Install a new step type with: [cyan]specify workflow step add <id>[/cyan]"
        )
