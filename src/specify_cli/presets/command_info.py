"""Implementation of the ``specify preset info`` command."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from ._commands import preset_app


@preset_app.command("info")
def preset_info(
    preset_id: str = typer.Argument(..., help="Preset ID to get info about"),
):
    """Show detailed information about a preset."""
    from .. import _require_specify_project
    from ..extensions import normalize_priority
    from . import PresetCatalog, PresetError, PresetManager

    project_root = _require_specify_project()
    safe_preset_id = _escape_markup(str(preset_id))
    # Check if installed locally first
    manager = PresetManager(project_root)
    local_pack = manager.get_pack(preset_id)

    if local_pack:
        console.print(
            f"\n[bold cyan]Preset: {_escape_markup(str(local_pack.name))}[/bold cyan]\n"
        )
        console.print(f"  ID:          {_escape_markup(str(local_pack.id))}")
        console.print(f"  Version:     {_escape_markup(str(local_pack.version))}")
        console.print(f"  Description: {_escape_markup(str(local_pack.description))}")
        if local_pack.author:
            console.print(f"  Author:      {_escape_markup(str(local_pack.author))}")
        local_tags = local_pack.tags
        if isinstance(local_tags, list) and local_tags:
            tags_str = _escape_markup(", ".join(str(t) for t in local_tags))
            console.print(f"  Tags:        {tags_str}")
        console.print(f"  Templates:   {len(local_pack.templates)}")
        for tmpl in local_pack.templates:
            tmpl_name = _escape_markup(str(tmpl["name"]))
            tmpl_type = _escape_markup(str(tmpl["type"]))
            tmpl_desc = _escape_markup(str(tmpl.get("description", "")))
            console.print(f"    - {tmpl_name} ({tmpl_type}): {tmpl_desc}")
        repo = local_pack.data.get("preset", {}).get("repository")
        if repo:
            console.print(f"  Repository:  {_escape_markup(str(repo))}")
        license_val = local_pack.data.get("preset", {}).get("license")
        if license_val:
            console.print(f"  License:     {_escape_markup(str(license_val))}")
        console.print("\n  [green]Status: installed[/green]")
        # Get priority from registry
        pack_metadata = manager.registry.get(preset_id)
        priority = normalize_priority(
            pack_metadata.get("priority") if isinstance(pack_metadata, dict) else None
        )
        console.print(f"  [dim]Priority:[/dim] {priority}")
        console.print()
        return

    # Fall back to catalog
    catalog = PresetCatalog(project_root)
    try:
        pack_info = catalog.get_pack_info(preset_id)
    except PresetError:
        pack_info = None

    if not pack_info:
        console.print(
            f"[red]Error:[/red] Preset '{preset_id}' not found (not installed and not in catalog)"
        )
        raise typer.Exit(1)

    name = _escape_markup(str(pack_info.get("name", preset_id)))
    console.print(f"\n[bold cyan]Preset: {name}[/bold cyan]\n")
    console.print(f"  ID:          {_escape_markup(str(pack_info['id']))}")
    console.print(
        f"  Version:     {_escape_markup(str(pack_info.get('version', '?')))}"
    )
    console.print(
        f"  Description: {_escape_markup(str(pack_info.get('description', '')))}"
    )
    if pack_info.get("author"):
        console.print(f"  Author:      {_escape_markup(str(pack_info['author']))}")
    catalog_tags = pack_info.get("tags", [])
    if isinstance(catalog_tags, list) and catalog_tags:
        catalog_tags_str = _escape_markup(", ".join(str(t) for t in catalog_tags))
        console.print(f"  Tags:        {catalog_tags_str}")
    if pack_info.get("repository"):
        console.print(f"  Repository:  {_escape_markup(str(pack_info['repository']))}")
    if pack_info.get("license"):
        console.print(f"  License:     {_escape_markup(str(pack_info['license']))}")
    console.print("\n  [yellow]Status: not installed[/yellow]")
    console.print(f"  Install with: [cyan]specify preset add {safe_preset_id}[/cyan]")
    console.print()
