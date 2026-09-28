"""Implementation of the ``specify preset set-priority`` command."""

from __future__ import annotations

import typer

from .._console import console
from . import _commands
from ._commands import preset_app


@preset_app.command("set-priority")
def preset_set_priority(
    preset_id: str = typer.Argument(help="Preset ID"),
    priority: int = typer.Argument(help="New priority (lower = higher precedence)"),
):
    """Set the resolution priority of an installed preset."""
    from .. import _require_specify_project
    from . import PresetManager

    project_root = _require_specify_project()
    _commands._validate_priority(priority)

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

    from ..extensions import normalize_priority

    raw_priority = metadata.get("priority")
    # Only skip if the stored value is already a valid int equal to requested priority
    # This ensures corrupted values (e.g., "high") get repaired even when setting to default (10)
    # A bool is an int in Python (isinstance(True, int) is True), so exclude it explicitly —
    # mirroring normalize_priority's bool guard — otherwise a corrupted True/False priority
    # equals 1/0 here and is never repaired.
    if (
        isinstance(raw_priority, int)
        and not isinstance(raw_priority, bool)
        and raw_priority == priority
    ):
        console.print(
            f"[yellow]Preset '{preset_id}' already has priority {priority}[/yellow]"
        )
        raise typer.Exit(0)

    old_priority = normalize_priority(raw_priority)

    from ._resolver import PresetResolver
    from ._selectors import is_regex_selector

    resolver = PresetResolver(project_root)
    affected_commands: set[str] = set()
    for pack_id, _pack_metadata in manager.registry.list_by_priority():
        manifest = resolver._get_manifest(manager.presets_dir / pack_id)
        if manifest is None:
            continue
        expanded = manager._expand_command_selectors(
            resolver,
            manager.presets_dir / pack_id,
            [item for item in manifest.templates if item.get("type") == "command"],
        )
        affected_commands.update(
            item["name"]
            for item in expanded
            if isinstance(item.get("name"), str) and not is_regex_selector(item["name"])
        )

    manager.registry.update(preset_id, {"priority": priority})
    names = sorted(affected_commands)
    if names:
        manager._reconcile_composed_commands(names)
        manager._reconcile_skills(names)
    manager.reconcile_constitution(
        f"Failed to reconcile constitution after changing priority for preset {preset_id}"
    )

    console.print(
        f"[green]✓[/green] Preset '{preset_id}' priority changed: {old_priority} → {priority}"
    )
    console.print(
        "\n[dim]Lower priority = higher precedence in template resolution[/dim]"
    )
