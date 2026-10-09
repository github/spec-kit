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

    already_disabled = not metadata.get("enabled", True)
    if already_disabled:
        console.print(f"[yellow]Preset '{preset_id}' is already disabled[/yellow]")
        # A failed best-effort cleanup leaves provenance behind. Repeated disable
        # must retry those artifacts, but an artifact-free preset is a true no-op.
        recorded_artifacts = (
            metadata.get("registered_commands"),
            metadata.get("registered_skills"),
        )
        if not any(
            isinstance(names, list) and any(isinstance(name, str) for name in names)
            for recorded in recorded_artifacts
            for names in (
                recorded.values() if isinstance(recorded, dict) else [recorded]
            )
        ):
            raise typer.Exit(0)

    from ._resolver import PresetResolver

    resolver = PresetResolver(project_root)
    affected = manager._collect_selector_command_names(resolver)
    manifest = resolver._get_manifest(manager.presets_dir / preset_id)
    declarations = [
        item
        for item in (manifest.templates if manifest is not None else [])
        if item.get("type") == "command"
    ]
    names = {
        item["name"]
        for item in manager._expand_command_selectors(
            resolver, manager.presets_dir / preset_id, declarations
        )
        if isinstance(item.get("name"), str)
    }
    names.update(affected)
    original_commands = metadata.get("registered_commands") or {}
    original_skills = metadata.get("registered_skills") or {}
    if names and not already_disabled:
        manager._reconcile_composed_commands(sorted(names))
        manager._reconcile_skills(sorted(names))
    if not all(
        hasattr(manager, name)
        for name in (
            "_collect_selector_command_names",
            "_expand_command_selectors",
            "_skill_names_for_command",
            "_historical_command_targets",
        )
    ):
        manager.registry.update(preset_id, {"enabled": False})
        manager.reconcile_constitution(
            f"Failed to reconcile constitution after disabling preset {preset_id}"
        )
        console.print(f"[green]✓[/green] Preset '{preset_id}' disabled")
        console.print("\nTemplates from this preset will be skipped during resolution.")
        console.print(f"To re-enable: specify preset enable {preset_id}")
        return
    if isinstance(original_commands, dict):
        names.update(
            name
            for values in original_commands.values()
            if isinstance(values, list)
            for name in values
            if isinstance(name, str)
        )
    historical_agents, historical_skills_dirs = manager._historical_command_targets(
        names
    )
    manager.registry.update(preset_id, {"enabled": False})
    try:
        names.update(
            manager._collect_selector_command_names(PresetResolver(project_root))
        )
        if names:
            manager._reconcile_composed_commands(
                sorted(names), extra_agents=historical_agents or None
            )
            manager._reconcile_skills(
                sorted(names), extra_skills_dirs=historical_skills_dirs or None
            )
        concrete_skills = {
            skill_name
            for command_name in names
            for skill_name in manager._skill_names_for_command(command_name)
        }
        commands = original_commands
        if isinstance(commands, dict):
            updated_commands = {
                agent: [name for name in values if name not in names]
                for agent, values in commands.items()
                if isinstance(values, list)
            }
            updated_commands = {
                agent: values for agent, values in updated_commands.items() if values
            }
        else:
            updated_commands = commands
        skills = original_skills
        if isinstance(skills, dict):
            updated_skills = {
                agent: [name for name in values if name not in concrete_skills]
                for agent, values in skills.items()
                if isinstance(values, list)
            }
            updated_skills = {
                agent: values for agent, values in updated_skills.items() if values
            }
        else:
            updated_skills = skills
        manager.registry.update(
            preset_id,
            {
                "registered_commands": updated_commands,
                "registered_skills": updated_skills,
            },
        )
    except Exception as exc:  # noqa: BLE001 - disabling commits before best-effort cleanup
        import warnings

        warnings.warn(
            f"Could not clean preset artifacts after disabling {preset_id}: {exc}. "
            "Tracked artifact provenance was preserved for retry.",
            stacklevel=2,
        )
        console.print(
            f"[yellow]Preset '{preset_id}' disabled; artifact cleanup failed. "
            "Tracked files remain recorded for retry.[/yellow]"
        )
        return
    finally:
        manager.reconcile_constitution(
            f"Failed to reconcile constitution after disabling preset {preset_id}"
        )

    console.print(f"[green]✓[/green] Preset '{preset_id}' disabled")
    console.print("\nTemplates from this preset will be skipped during resolution.")
    console.print(f"To re-enable: specify preset enable {preset_id}")
