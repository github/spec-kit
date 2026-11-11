"""Implementation of the ``specify preset disable`` command."""

from __future__ import annotations

import warnings

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

    # Disable the preset
    manager.registry.update(preset_id, {"enabled": False})
    manager.reconcile_constitution(
        f"Failed to reconcile constitution after disabling preset {preset_id}"
    )
    # reconcile_scripts_for_preset() only warns on failure (consistent with
    # reconcile_constitution() above), since one bad script name shouldn't
    # block the registry change it's reporting on. But unlike a stale
    # constitution, a stale *script* chain is still executable, so silently
    # reporting "disabled" success while the old generated script keeps
    # running would leave recorded and executable state disagreeing. Capture
    # whether reconciliation actually failed and report it as a command
    # failure -- the registry change itself stands (the preset genuinely is
    # disabled), but the user needs to know the script side didn't converge.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        manager.reconcile_scripts_for_preset(
            preset_id,
            f"Failed to reconcile scripts after disabling preset {preset_id}",
        )
    script_reconcile_failures = [str(w.message) for w in caught]

    console.print(f"[green]✓[/green] Preset '{preset_id}' disabled")
    console.print("\nTemplates from this preset will be skipped during resolution.")
    console.print(
        "[dim]Note: Previously registered commands/skills remain active until preset removal.[/dim]"
    )
    console.print(f"To re-enable: specify preset enable {preset_id}")

    if script_reconcile_failures:
        for failure in script_reconcile_failures:
            console.print(f"[red]Error:[/red] {failure}")
        console.print(
            "[red]Preset is disabled, but its generated script(s) could not be "
            "reconciled and may still be active. Inspect "
            ".specify/scripts/bash/ before relying on this preset being fully "
            "inactive.[/red]"
        )
        raise typer.Exit(1)
