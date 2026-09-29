"""Implementation of the ``specify preset enable`` command."""

from __future__ import annotations

import typer

from .._console import console
from ._commands import preset_app


@preset_app.command("enable")
def preset_enable(
    preset_id: str = typer.Argument(help="Preset ID to enable"),
):
    """Enable a disabled preset."""
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

    if metadata.get("enabled", True):
        console.print(f"[yellow]Preset '{preset_id}' is already enabled[/yellow]")
        raise typer.Exit(0)

    # Enable the preset
    manager.registry.update(preset_id, {"enabled": True})
    try:
        from ._manifest import PresetManifest
        from ._resolver import PresetResolver

        manifest_path = manager.presets_dir / preset_id / "preset.yml"
        names: list[str] = []
        if manifest_path.is_file():
            PresetManifest(manifest_path)
            names = sorted(
                manager._collect_selector_command_names(PresetResolver(project_root))
            )
        if names:
            manager._reconcile_composed_commands(names)
            manager._reconcile_skills(names)
    except Exception as exc:
        import warnings

        warnings.warn(
            f"Could not reconcile preset commands after enabling {preset_id}: {exc}",
            stacklevel=2,
        )
    manager.reconcile_constitution(
        f"Failed to reconcile constitution after enabling preset {preset_id}"
    )

    console.print(f"[green]✓[/green] Preset '{preset_id}' enabled")
    console.print("\nTemplates from this preset will now be included in resolution.")
    console.print(
        "[dim]Note: Previously registered commands/skills remain active.[/dim]"
    )
