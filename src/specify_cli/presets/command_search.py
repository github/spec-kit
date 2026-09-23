"""Implementation of the ``specify preset search`` command."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from ._commands import preset_app


@preset_app.command("search")
def preset_search(
    query: str = typer.Argument(None, help="Search query"),
    tag: str = typer.Option(None, "--tag", help="Filter by tag"),
    author: str = typer.Option(None, "--author", help="Filter by author"),
):
    """Search for presets in the catalog."""
    from .. import _require_specify_project
    from . import PresetCatalog, PresetError

    project_root = _require_specify_project()
    catalog = PresetCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag, author=author)
    except PresetError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    if not results:
        console.print("[yellow]No presets found matching your criteria.[/yellow]")
        return

    console.print(f"\n[bold cyan]Presets ({len(results)} found):[/bold cyan]\n")
    for pack in results:
        name = _escape_markup(str(pack.get("name", pack["id"])))
        pack_id = _escape_markup(str(pack["id"]))
        version = _escape_markup(str(pack.get("version", "?")))
        console.print(f"  [bold]{name}[/bold] ({pack_id}) v{version}")
        console.print(f"    {_escape_markup(str(pack.get('description', '')))}")
        tags = pack.get("tags", [])
        if isinstance(tags, list) and tags:
            tags_str = _escape_markup(", ".join(str(t) for t in tags))
            console.print(f"    [dim]Tags: {tags_str}[/dim]")
        console.print()
