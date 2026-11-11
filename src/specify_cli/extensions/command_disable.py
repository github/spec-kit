"""Implementation of ``specify extension disable``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""
from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands


@_commands.extension_app.command("disable")
def extension_disable(
    extension: str = typer.Argument(help="Extension ID or name to disable"),
):
    """Disable an extension without removing it."""
    from . import ExtensionManager, HookExecutor

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _commands._resolve_installed_extension(
        extension, installed, "disable"
    )

    # Capture script names this extension declares before it's disabled and
    # its own layer drops out of resolution -- a preset wrapping one of these
    # scripts already has that content materialized inline in its generated
    # chain, and disabling the extension alone doesn't re-materialize it.
    ext_manifest_for_scripts = manager.get_extension(extension_id)
    script_names = [
        s["name"]
        for s in getattr(ext_manifest_for_scripts, "scripts", [])
        if s.get("name")
    ]

    # Update registry
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Extension '{_escape_markup(str(extension_id))}' "
            "not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    if not metadata.get("enabled", True):
        console.print(f"[yellow]Extension '{_escape_markup(str(display_name))}' is already disabled[/yellow]")
        raise typer.Exit(0)

    from .. import load_init_options

    if load_init_options(project_root).get("ai") == "generic":
        from . import ExtensionError

        try:
            manager.disable_generic_extension_artifacts(extension_id)
        except (ExtensionError, ValueError, OSError) as exc:
            console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1) from exc
    else:
        manager.registry.update(extension_id, {"enabled": False})

    # Disable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = False
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' disabled")
    console.print("\nCommands will no longer be available. Hooks will not execute.")
    console.print(f"To re-enable: specify extension enable {_escape_markup(str(extension_id))}")

    if script_names:
        from ..presets import PresetManager

        PresetManager(project_root).reconcile_scripts_for_names(
            script_names, "reconcile script chains after disabling extension"
        )

    # #1: regenerate native event config so the disabled extension's events
    # are stripped from installed integrations.
    _commands._refresh_events_and_warn(project_root)
