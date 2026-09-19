"""The ``specify integration search`` command."""
from __future__ import annotations

import os
from typing import Optional

import typer
from rich.markup import escape as _rich_escape

from .._console import console
from ..integration_state import default_integration_key as _default_integration_key
from ._commands import integration_app
from ._helpers import _read_integration_json


@integration_app.command("search")
def integration_search(
    query: Optional[str] = typer.Argument(None, help="Search query (optional)"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    author: Optional[str] = typer.Option(None, "--author", help="Filter by author"),
):
    """Search for integrations in the active catalog stack."""
    from . import INTEGRATION_REGISTRY
    from .catalog import (
        IntegrationCatalog,
        IntegrationCatalogError,
        IntegrationValidationError,
    )
    from .. import _require_specify_project

    project_root = _require_specify_project()
    integration_config = _read_integration_json(project_root)
    installed_key = _default_integration_key(integration_config)
    catalog = IntegrationCatalog(project_root)

    try:
        results = catalog.search(query=query, tag=tag, author=author)
    except IntegrationValidationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        console.print(
            "\nTip: Check the configuration file path shown above for invalid catalog configuration "
            "(for example, .specify/integration-catalogs.yml or ~/.specify/integration-catalogs.yml)."
        )
        raise typer.Exit(1)
    except IntegrationCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        if os.environ.get("SPECKIT_INTEGRATION_CATALOG_URL", "").strip():
            console.print(
                "\nTip: Check the SPECKIT_INTEGRATION_CATALOG_URL environment variable for an invalid "
                "catalog URL, or unset it to use the configured catalog files "
                "(.specify/integration-catalogs.yml or ~/.specify/integration-catalogs.yml)."
            )
        else:
            console.print("\nTip: The catalog may be temporarily unavailable. Try again later.")
        raise typer.Exit(1)

    if not results:
        console.print("\n[yellow]No integrations found matching criteria[/yellow]")
        if query or tag or author:
            console.print("\nTry:")
            console.print("  • Broader search terms")
            console.print("  • Remove filters")
            console.print("  • specify integration search (show all)")
        return

    console.print(f"\n[green]Found {len(results)} integration(s):[/green]\n")
    for integ in sorted(results, key=lambda e: e.get("id", "")):
        iid_value = str(integ.get("id", "?"))
        iid = _rich_escape(iid_value)
        name = _rich_escape(str(integ.get("name", iid_value)))
        version = _rich_escape(str(integ.get("version", "?")))
        console.print(f"[bold]{name}[/bold] ({iid}) v{version}")
        desc = integ.get("description", "")
        if desc:
            console.print(f"  {_rich_escape(str(desc))}")

        author_value = _rich_escape(str(integ.get("author", "Unknown")))
        console.print(f"\n  [dim]Author:[/dim] {author_value}")
        tags = integ.get("tags", [])
        if isinstance(tags, list) and tags:
            safe_tags = _rich_escape(", ".join(str(t) for t in tags))
            console.print(f"  [dim]Tags:[/dim] {safe_tags}")

        cat_name_value = integ.get("_catalog_name", "")
        cat_name = _rich_escape(str(cat_name_value))
        install_allowed = integ.get("_install_allowed", True)
        if cat_name_value:
            if install_allowed:
                console.print(f"  [dim]Catalog:[/dim] {cat_name}")
            else:
                console.print(
                    f"  [dim]Catalog:[/dim] {cat_name} "
                    "[yellow](discovery only — not installable)[/yellow]"
                )

        if iid_value == installed_key:
            console.print("\n  [green]✓ Installed[/green] (currently active)")
        elif iid_value in INTEGRATION_REGISTRY:
            console.print(f"\n  [cyan]Install:[/cyan] specify integration install {iid}")
        elif install_allowed:
            console.print(
                "\n  [yellow]Found in catalog.[/yellow] Only built-in integration IDs "
                "can be installed with 'specify integration install'."
            )
        else:
            console.print(
                f"\n  [yellow]⚠[/yellow]  Not directly installable from '{cat_name}'."
            )
        console.print()
