"""Implementation of ``specify extension list``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""
from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from .._installed_list_json import (
    InstalledListJSONCommand,
    emit_json,
    emit_json_error,
    installed_list_item,
)
from .._project import resolve_specify_project_root
from . import _commands


@_commands.extension_app.command("list", cls=InstalledListJSONCommand)
def extension_list(
    available: bool = typer.Option(False, "--available", help="Show available extensions from catalog"),
    all_extensions: bool = typer.Option(False, "--all", help="Show both installed and available"),
    json_output: bool = typer.Option(False, "--json", help="Output installed extensions as JSON"),
):
    """List installed extensions."""
    from . import ExtensionManager, normalize_priority

    if json_output:
        try:
            project_root = resolve_specify_project_root()
            manager = ExtensionManager(project_root)
            installed = manager.list_installed()
            installed = sorted(
                installed,
                key=lambda extension: (
                    normalize_priority(extension.get("priority")),
                    str(extension.get("id", "")),
                ),
            )
            emit_json(
                [installed_list_item(ext, include_hooks=True) for ext in installed]
            )
            return
        except Exception as error:
            emit_json_error(error)

    project_root = _commands._require_specify_project()
    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    if not installed and not (available or all_extensions):
        console.print("[yellow]No extensions installed.[/yellow]")
        console.print("\nInstall an extension with:")
        console.print("  specify extension add <extension-name>")
        return

    if installed:
        console.print("\n[bold cyan]Installed Extensions:[/bold cyan]\n")

        for ext in installed:
            status_icon = "✓" if ext["enabled"] else "✗"
            status_color = "green" if ext["enabled"] else "red"

            console.print(f"  [{status_color}]{status_icon}[/{status_color}] [bold]{_escape_markup(ext['name'])}[/bold] (v{_escape_markup(str(ext['version']))})")
            console.print(f"     [dim]{_escape_markup(ext['id'])}[/dim]")
            console.print(f"     {_escape_markup(ext['description'])}")
            console.print(f"     Commands: {ext['command_count']} | Hooks: {ext['hook_count']} | Priority: {ext['priority']} | Status: {'Enabled' if ext['enabled'] else 'Disabled'}")
            console.print()

    if available or all_extensions:
        console.print("\nInstall an extension:")
        console.print("  [cyan]specify extension add <name>[/cyan]")
