"""Implementation of ``specify extension search``.

Registered by ``_commands.register()``; shared command infrastructure lives in
``_commands.py``.
"""
from __future__ import annotations

from typing import Optional

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import _commands


@_commands.extension_app.command("search")
def extension_search(
    query: str = typer.Argument(None, help="Search query (optional)"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    author: Optional[str] = typer.Option(None, "--author", help="Filter by author"),
    verified: bool = typer.Option(False, "--verified", help="Show only verified extensions"),
):
    """Search for available extensions in catalog."""
    from . import ExtensionCatalog, ExtensionError

    project_root = _commands._require_specify_project()
    catalog = ExtensionCatalog(project_root)

    try:
        console.print("🔍 Searching extension catalog...")
        results = catalog.search(query=query, tag=tag, author=author, verified_only=verified)

        if not results:
            console.print("\n[yellow]No extensions found matching criteria[/yellow]")
            if query or tag or author or verified:
                console.print("\nTry:")
                console.print("  • Broader search terms")
                console.print("  • Remove filters")
                console.print("  • specify extension search (show all)")
            raise typer.Exit(0)

        console.print(f"\n[green]Found {len(results)} extension(s):[/green]\n")

        for ext in results:
            # Extension header
            verified_badge = " [green]✓ Verified[/green]" if ext.get("verified") else ""
            console.print(f"[bold]{_escape_markup(str(ext['name']))}[/bold] (v{_escape_markup(str(ext['version']))}){verified_badge}")
            console.print(f"  {_escape_markup(str(ext['description']))}")

            # Metadata
            console.print(f"\n  [dim]Author:[/dim] {_escape_markup(str(ext.get('author', 'Unknown')))}")
            ext_tags = ext.get('tags', [])
            if isinstance(ext_tags, list) and ext_tags:
                tags_str = ", ".join(str(t) for t in ext_tags)
                console.print(f"  [dim]Tags:[/dim] {_escape_markup(tags_str)}")

            # Source catalog
            catalog_name = _escape_markup(str(ext.get("_catalog_name", "")))
            install_allowed = ext.get("_install_allowed", True)
            if catalog_name:
                if install_allowed:
                    console.print(f"  [dim]Catalog:[/dim] {catalog_name}")
                else:
                    console.print(f"  [dim]Catalog:[/dim] {catalog_name} [yellow](discovery only — not installable)[/yellow]")

            # Stats
            stats = []
            downloads = ext.get('downloads')
            if downloads is not None:
                # Catalog fields are untrusted; a non-numeric ``downloads``
                # (e.g. the JSON string "1500") would crash the ``:,`` format
                # with "Cannot specify ',' with 's'". Only group-format numbers,
                # and escape the fallback: the joined stats are rendered as Rich
                # markup, so a value like "[/red]foo" would raise MarkupError
                # (matching how every other catalog field here is escaped).
                stats.append(
                    f"Downloads: {downloads:,}"
                    if isinstance(downloads, (int, float))
                    else f"Downloads: {_escape_markup(str(downloads))}"
                )
            stars = ext.get('stars')
            if stars is not None:
                # Same untrusted-value/Rich-markup hazard as `downloads` above,
                # in the same joined string.
                stats.append(f"Stars: {_escape_markup(str(stars))}")
            if stats:
                console.print(f"  [dim]{' | '.join(stats)}[/dim]")

            # Links
            if ext.get('repository'):
                console.print(f"  [dim]Repository:[/dim] {_escape_markup(str(ext['repository']))}")

            # Install command (show warning if not installable)
            cmd_id = _commands._command_safe_id(ext['id'])
            if install_allowed:
                console.print(f"\n  [cyan]Install:[/cyan] specify extension add {cmd_id}")
            else:
                console.print(f"\n  [yellow]⚠[/yellow]  Not directly installable from '{catalog_name}' (discovery-only).")
                console.print(
                    f"  Once vetted, install it directly: specify extension add {cmd_id} --from <archive-url>"
                )
                console.print(
                    "  Don't flip a discovery-only catalog to install_allowed — that's the vetting boundary."
                )
            console.print()

    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {_escape_markup(str(e))}")
        console.print("\nTip: The catalog may be temporarily unavailable. Try again later.")
        raise typer.Exit(1)
