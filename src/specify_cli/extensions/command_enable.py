"""Implementation of ``specify extension enable``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""
from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands


@_commands.extension_app.command("enable")
def extension_enable(
    extension: str = typer.Argument(help="Extension ID or name to enable"),
):
    """Enable a disabled extension."""
    from . import ExtensionError, ExtensionManager, HookExecutor

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)
    hook_executor = HookExecutor(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _commands._resolve_installed_extension(
        extension, installed, "enable"
    )

    # Update registry
    metadata = manager.registry.get(extension_id)
    if metadata is None or not isinstance(metadata, dict):
        console.print(
            f"[red]Error:[/red] Extension '{_escape_markup(str(extension_id))}' "
            "not found in registry (corrupted state)"
        )
        raise typer.Exit(1)

    if metadata.get("enabled", True):
        console.print(f"[yellow]Extension '{_escape_markup(str(display_name))}' is already enabled[/yellow]")
        raise typer.Exit(0)

    from .. import load_init_options

    init_options = load_init_options(project_root)
    if not isinstance(init_options, dict):
        init_options = {}
    active_agent = init_options.get("ai")
    if isinstance(active_agent, str) and active_agent:
        try:
            blocked_by_ext, _preset_blocks = manager._hyphenation_collision_blocks(
                active_agent, also_enabled={extension_id}
            )
        except (OSError, ValueError):
            # Generic settings can be missing or unreadable. Registration
            # below already reports that and puts the flag back. A collision
            # check that cannot resolve the agent must not replace that error,
            # and a command-less extension has nothing to collide.
            blocked_by_ext = {}
        blocked_names = blocked_by_ext.get(extension_id, set())
        if blocked_names:
            shown = ", ".join(sorted(blocked_names))
            console.print(
                f"[red]Error:[/red] Cannot enable "
                f"'{_escape_markup(str(display_name))}': "
                f"{_escape_markup(shown)} hyphenate to a prompt another "
                "command already owns. Rename one of those commands, or "
                "remove the other extension, then enable again."
            )
            raise typer.Exit(1)

    manager.registry.update(extension_id, {"enabled": True})
    if init_options.get("ai") == "generic":
        try:
            manifest = manager.get_extension(extension_id)
            if manifest is None:
                raise ExtensionError(f"Cannot read manifest for '{extension_id}'")
            if manifest.commands:
                manager.register_enabled_extensions_for_agent("generic")
                refreshed = manager.registry.get(extension_id) or {}
                from .._init_options import is_ai_skills_enabled

                skills = is_ai_skills_enabled(init_options)
                expected = (
                    {
                        manager._skill_name_for_command(command["name"])
                        for command in manifest.commands
                    }
                    if skills else set(manager._collect_manifest_command_names(manifest))
                )
                owned = set(manager._generic_owned_names(
                    refreshed, list(expected), skills=skills, extension_id=extension_id,
                ))
                missing = expected - owned
                if missing:
                    manager.disable_generic_extension_artifacts(extension_id)
                    raise ExtensionError(
                        "Missing invocation artifacts: " + ", ".join(sorted(missing))
                    )
        except (ExtensionError, OSError, ValueError) as exc:
            manager.registry.update(extension_id, {"enabled": False})
            console.print(
                f"[red]Error:[/red] Could not register generic invocations "
                f"for '{_escape_markup(str(extension_id))}': {_escape_markup(str(exc))}"
            )
            raise typer.Exit(1) from exc

    # Enable hooks in extensions.yml
    config = hook_executor.get_project_config()
    if "hooks" in config:
        for hook_name in config["hooks"]:
            for hook in config["hooks"][hook_name]:
                if hook.get("extension") == extension_id:
                    hook["enabled"] = True
        hook_executor.save_project_config(config)

    console.print(f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' enabled")

    # #1: regenerate native event config so the enabled extension's events
    # are re-emitted in installed integrations.
    _commands._refresh_events_and_warn(project_root)

    # Scaffold config templates on enable
    try:
        deployed, skipped, failed = manager.scaffold_config(extension_id)
    except Exception as exc:
        console.print(
            f"\n[yellow]Warning:[/yellow] Failed to scaffold config for extension "
            f"'{_escape_markup(str(display_name))}'."
        )
        console.print(f"[dim]Details: {_escape_markup(str(exc))}[/dim]")
        deployed, skipped, failed = [], [], []
    config_home = f".specify/extensions/{_escape_markup(str(extension_id))}"
    if deployed:
        console.print("\n[bold cyan]Config scaffolded:[/bold cyan]")
        for cfg in deployed:
            console.print(f"  • {config_home}/{_escape_markup(str(cfg))}")
    if skipped:
        console.print(f"\n[dim]Config files already exist (preserved): {_escape_markup(', '.join(skipped))}[/dim]")
    if failed:
        console.print(
            f"\n[yellow]Warning:[/yellow] Config templates not scaffolded: "
            f"{_escape_markup(', '.join(failed))}. "
            "Verify the extension manifest and template files."
        )
