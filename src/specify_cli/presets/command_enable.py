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

    # Capture selector matches while the preset is disabled, then enable it and
    # reconcile the newly active resolution stack.
    from ._resolver import PresetResolver

    resolver = PresetResolver(project_root)
    preset_dir = manager.presets_dir / preset_id
    manifest = resolver._get_manifest(preset_dir)
    declarations = [
        item
        for item in (manifest.templates if manifest is not None else [])
        if item.get("type") == "command"
    ]
    names = {
        item["name"]
        for item in manager._expand_command_selectors(
            resolver, preset_dir, declarations
        )
        if isinstance(item.get("name"), str)
    }
    names.update(manager._collect_selector_command_names(resolver))
    manager.registry.update(preset_id, {"enabled": True})
    # Disabled regex declarations have no pre-state expansion. Always collect
    # post-state matches, including historical destinations owned by lower packs.
    names.update(manager._collect_selector_command_names(PresetResolver(project_root)))
    historical_agents, historical_skills_dirs = manager._historical_command_targets(
        names
    )
    from .. import load_init_options

    options = load_init_options(project_root)
    active_agent = options.get("ai") if isinstance(options, dict) else None
    if isinstance(active_agent, str) and active_agent:
        manager.register_enabled_presets_for_agent(active_agent)
    if names:
        try:
            manager._reconcile_composed_commands(
                sorted(names), extra_agents=historical_agents or None
            )
            manager._reconcile_skills(
                sorted(names), extra_skills_dirs=historical_skills_dirs or None
            )
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
