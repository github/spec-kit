"""Implementation of ``specify extension enable``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""
from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands


def _present(path) -> bool:
    return path.exists() or path.is_symlink()


def _register_if_absent(manager, extension_id: str, agent: str, metadata: dict) -> None:
    """Register ``extension_id`` for ``agent`` when none of its outputs exist.

    Surviving outputs (customized files, dev symlinks) are never rewritten.
    Every output was absent before registration, so if it leaves any missing
    or raises, the outputs it did write and its registry tracking are undone,
    and a retry starts from the same clean state.
    """
    from . import ExtensionError

    outputs = manager.invocation_outputs(extension_id, agent)
    if not outputs or any(_present(path) for _, path in outputs):
        return
    try:
        manager.register_enabled_extensions_for_agent(agent, extension_ids={extension_id})
        missing = sorted(name for name, path in outputs if not _present(path))
        if missing:
            raise ExtensionError("Missing invocation artifacts: " + ", ".join(missing))
    except Exception:
        for _, path in outputs:
            if path.is_symlink() or path.is_file():
                path.unlink()
            if path.name == "SKILL.md" and path.parent.is_dir() and not any(path.parent.iterdir()):
                path.parent.rmdir()
        manager.registry.update(extension_id, {
            key: metadata[key]
            for key in ("registered_commands", "registered_skills")
            if key in metadata
        })
        raise


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

    manager.registry.update(extension_id, {"enabled": True})

    from .. import load_init_options

    init_options = load_init_options(project_root)
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
    else:
        # `integration use`/`switch` register only enabled extensions for the
        # agent they activate, and `switch` removes a disabled extension's
        # commands from the old one, so an extension disabled at that point has
        # no commands for the now-active agent. Register them only when none
        # of the extension's outputs exist for the active layout, so surviving
        # files, edits and dev symlinks are never rewritten, and roll back if
        # registration leaves any output missing.
        active_ai = init_options.get("ai")
        if isinstance(active_ai, str) and active_ai:
            try:
                _register_if_absent(manager, extension_id, active_ai, metadata)
            except Exception as exc:
                manager.registry.update(extension_id, {"enabled": False})
                console.print(
                    f"[red]Error:[/red] Could not register invocations "
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
