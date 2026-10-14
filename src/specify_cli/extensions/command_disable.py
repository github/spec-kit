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
    from . import ExtensionError, ExtensionManager, HookExecutor

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _commands._resolve_installed_extension(
        extension, installed, "disable"
    )

    try:
        config = hook_executor.load_project_config_for_update()
    except (ValueError, OSError) as exc:
        console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1) from exc

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
        try:
            manager.disable_generic_extension_artifacts(extension_id)
        except (ExtensionError, ValueError, OSError) as exc:
            console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1) from exc
    else:
        manager.registry.update(extension_id, {"enabled": False})

    # Disable hooks in extensions.yml
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = False
        try:
            hook_executor.save_project_config(config)
        except (ValueError, OSError) as exc:
            try:
                manager.registry.update(extension_id, {"enabled": True})
                if load_init_options(project_root).get("ai") == "generic":
                    manager.register_enabled_extensions_for_agent("generic")
                    restored = manager.registry.get(extension_id) or {}
                    if restored.get("enabled") is not True:
                        raise ExtensionError("Rollback did not restore enabled registry state")
                    previous_commands = metadata.get("registered_commands", {})
                    command_names = (
                        previous_commands.get("generic", [])
                        if isinstance(previous_commands, dict) else []
                    )
                    skill_names = metadata.get("registered_skills", [])
                    for names, skills in ((command_names, False), (skill_names, True)):
                        if not isinstance(names, list) or any(
                            not isinstance(name, str) for name in names
                        ):
                            raise ExtensionError("Invalid generic artifact metadata during rollback")
                        restored_commands = restored.get("registered_commands", {})
                        registered = (
                            restored.get("registered_skills", [])
                            if skills else (
                                restored_commands.get("generic", [])
                                if isinstance(restored_commands, dict) else None
                            )
                        )
                        if (
                            not isinstance(registered, list)
                            or any(not isinstance(name, str) for name in registered)
                            or set(names) - set(registered)
                        ):
                            raise ExtensionError("Rollback did not restore generic artifact registry")
                        owned = manager._generic_owned_names(
                            restored, names, skills=skills, extension_id=extension_id
                        )
                        missing = set(names) - set(owned)
                        if missing:
                            raise ExtensionError(
                                "Rollback did not restore generic invocation artifacts: "
                                + ", ".join(sorted(missing))
                            )
            except (ExtensionError, ValueError, OSError) as rollback_exc:
                console.print(
                    f"[red]Error:[/red] {_escape_markup(str(exc))}; "
                    f"rollback failed: {_escape_markup(str(rollback_exc))}"
                )
                raise typer.Exit(1) from exc
            console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
            raise typer.Exit(1) from exc

    console.print(f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' disabled")
    console.print("\nCommands will no longer be available. Hooks will not execute.")
    console.print(f"To re-enable: specify extension enable {_escape_markup(str(extension_id))}")

    # #1: regenerate native event config so the disabled extension's events
    # are stripped from installed integrations.
    _commands._refresh_events_and_warn(project_root)
