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
        from ._selectors import is_regex_selector

        manifest_path = manager.presets_dir / preset_id / "preset.yml"
        if manifest_path.is_file():
            manifest = PresetManifest(manifest_path)
            expanded = manager._expand_command_selectors(
                PresetResolver(project_root),
                manager.presets_dir / preset_id,
                [item for item in manifest.templates if item.get("type") == "command"],
            )
            names = sorted(
                {
                    item["name"]
                    for item in expanded
                    if isinstance(item.get("name"), str)
                    and not is_regex_selector(item["name"])
                }
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
