"""Implementation of the ``specify preset list`` command."""

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
from ._commands import preset_app


@preset_app.command("list", cls=InstalledListJSONCommand)
def preset_list(
    json_output: bool = typer.Option(
        False, "--json", help="Output installed presets as JSON"
    ),
):
    """List installed presets."""
    from .. import _require_specify_project
    from . import PresetManager

    if json_output:
        try:
            project_root = resolve_specify_project_root()
            manager = PresetManager(project_root)
            installed = manager.list_installed()
            installed = sorted(
                installed,
                key=lambda pack: (pack.get("priority", 10), str(pack.get("id", ""))),
            )
            emit_json(
                [installed_list_item(pack, include_hooks=False) for pack in installed]
            )
            return
        except Exception as error:  # noqa: BLE001 - emit the JSON error contract
            emit_json_error(error)

    project_root = _require_specify_project()
    manager = PresetManager(project_root)
    installed = manager.list_installed()

    if not installed:
        console.print("[yellow]No presets installed.[/yellow]")
        console.print("\nInstall a preset with:")
        console.print("  [cyan]specify preset add <pack-name>[/cyan]")
        return

    # Sort by actual resolution precedence: lower priority number wins, ties
    # broken by preset id (matching PresetRegistry.list_by_priority()). This
    # keeps the printed order aligned with how presets are composed/resolved.
    installed = sorted(
        installed,
        key=lambda pack: (pack.get("priority", 10), str(pack.get("id", ""))),
    )

    console.print(
        "\n[bold cyan]Installed Presets[/bold cyan] [dim](in resolution order — highest precedence first)[/dim]\n"
    )
    for pack in installed:
        status = (
            "[green]enabled[/green]"
            if pack.get("enabled", True)
            else "[red]disabled[/red]"
        )
        pri = pack.get("priority", 10)
        name = _escape_markup(str(pack["name"]))
        pack_id = _escape_markup(str(pack["id"]))
        version = _escape_markup(str(pack["version"]))
        console.print(
            f"  [bold]{name}[/bold] ({pack_id}) v{version} — {status} — priority {pri}"
        )
        console.print(f"    {_escape_markup(str(pack['description']))}")
        tags = pack.get("tags", [])
        if isinstance(tags, list) and tags:
            tags_str = _escape_markup(", ".join(str(t) for t in tags))
            console.print(f"    [dim]Tags: {tags_str}[/dim]")
        console.print(f"    [dim]Templates: {pack['template_count']}[/dim]")
        console.print()

    console.print(
        "[dim]Lower priority number = higher precedence. Ties are broken by preset id (alphabetical).[/dim]"
    )
