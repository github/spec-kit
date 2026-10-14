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
    from . import ExtensionError, ExtensionManager

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _commands._resolve_installed_extension(
        extension, installed, "disable"
    )

    try:
        disabled = manager.disable(extension_id)
    except (ExtensionError, ValueError, OSError) as exc:
        console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1) from exc
    if not disabled:
        console.print(f"[yellow]Extension '{_escape_markup(str(display_name))}' is already disabled[/yellow]")
        raise typer.Exit(0)

    console.print(f"[green]✓[/green] Extension '{_escape_markup(str(display_name))}' disabled")
    console.print("\nCommands will no longer be available. Hooks will not execute.")
    console.print(f"To re-enable: specify extension enable {_escape_markup(str(extension_id))}")

    # #1: regenerate native event config so the disabled extension's events
    # are stripped from installed integrations.
    _commands._refresh_events_and_warn(project_root)
