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

    # Update priority
    manager.registry.update(preset_id, {"priority": priority})

    # A priority change can change the winning command or skill layer just as
    # install and removal do, so rematerialize artifacts provided by this
    # preset from the full priority stack.
    try:
        from ._manifest import PresetManifest

        manifest = PresetManifest(manager.presets_dir / preset_id / "preset.yml")
        command_names = [
            template["name"]
            for template in manifest.templates
            if template.get("type") == "command"
        ]
        if command_names:
            manager._reconcile_composed_commands(command_names)
            manager._reconcile_skills(command_names)
    except Exception as exc:  # noqa: BLE001 - lifecycle reconciliation is best-effort
        import warnings

        warnings.warn(
            f"Post-priority reconciliation failed for {preset_id}: {exc}. "
            "Agent command files may not reflect the current priority stack.",
            stacklevel=2,
        )

    manager.reconcile_constitution(
        f"Failed to reconcile constitution after changing priority for preset {preset_id}"
    )

    console.print(
        f"[green]✓[/green] Preset '{preset_id}' priority changed: {old_priority} → {priority}"
    )
    console.print(
        "\n[dim]Lower priority = higher precedence in template resolution[/dim]"
    )
