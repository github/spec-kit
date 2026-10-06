"""Implementation of the ``specify preset remove`` command."""

from __future__ import annotations

import typer

from .._console import console
from ._commands import preset_app


@preset_app.command("remove")
def preset_remove(
    preset_id: str = typer.Argument(..., help="Preset ID to remove"),
):
    """Remove an installed preset."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    manager = PresetManager(project_root)

    if not manager.registry.is_installed(preset_id):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' is not installed")
        raise typer.Exit(1)

    if manager.remove(preset_id):
        console.print(f"[green]✓[/green] Preset '{preset_id}' removed successfully")
    else:
        console.print(f"[red]Error:[/red] Failed to remove preset '{preset_id}'")
        raise typer.Exit(1)
