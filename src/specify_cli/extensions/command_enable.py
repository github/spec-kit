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
    from . import ExtensionError, ExtensionManager

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)

    # Resolve extension ID from argument (handles ambiguous names)
    installed = manager.list_installed()
    extension_id, display_name = _commands._resolve_installed_extension(
        extension, installed, "enable"
    )

    try:
        enabled = manager.enable(extension_id)
    except (ExtensionError, ValueError, OSError) as exc:
        console.print(f"[red]Error:[/red] {_escape_markup(str(exc))}")
        raise typer.Exit(1) from exc
    if not enabled:
        console.print(f"[yellow]Extension '{_escape_markup(str(display_name))}' is already enabled[/yellow]")
        raise typer.Exit(0)

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
