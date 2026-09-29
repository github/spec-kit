"""Implementation of the ``specify preset disable`` command."""

from __future__ import annotations

import typer

from .._console import console
from ._commands import preset_app


@preset_app.command("disable")
def preset_disable(
    preset_id: str = typer.Argument(help="Preset ID to disable"),
):
    """Disable a preset without removing it."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    manager = PresetManager(project_root)

    # Check if preset is installed
    if not manager.registry.is_installed(preset_id):
        console.print(f"[red]Error:[/red] Preset '{preset_id}' is not installed")
        raise typer.Exit(1)

    # Get current metadata
    metadata = manager.registry.get(preset_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Preset '{preset_id}' not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    if not metadata.get("enabled", True):
        console.print(f"[yellow]Preset '{preset_id}' is already disabled[/yellow]")
        raise typer.Exit(0)

    # Capture concrete names before the mutation as disabling can make selector
    # declarations disappear from the resolver's lower-layer inventory.
    from ._resolver import PresetResolver

    resolver = PresetResolver(project_root)
    affected = manager._collect_selector_command_names(resolver)
    manager.registry.update(preset_id, {"enabled": False})
    affected.update(
        manager._collect_selector_command_names(PresetResolver(project_root))
    )
    names = sorted(affected)
    if names:
        import warnings

        try:
            manager._reconcile_composed_commands(names)
            manager._reconcile_skills(names)
        except Exception as exc:
            warnings.warn(
                f"Could not reconcile preset artifacts after disabling {preset_id}: {exc}",
                stacklevel=2,
            )
    manager.reconcile_constitution(
        f"Failed to reconcile constitution after disabling preset {preset_id}"
    )

    console.print(f"[green]✓[/green] Preset '{preset_id}' disabled")
    console.print("\nTemplates from this preset will be skipped during resolution.")
    console.print(f"To re-enable: specify preset enable {preset_id}")
