"""The ``specify integration info`` command."""
from __future__ import annotations

import os
from typing import Optional

import typer
from rich.markup import escape as _rich_escape

from .._console import console
from ..integration_state import default_integration_key as _default_integration_key
from ._commands import integration_app
from ._helpers import _read_integration_json


@integration_app.command("info")
def integration_info(
    integration_id: str = typer.Argument(..., help="Integration ID"),
):
    """Show catalog details for a single integration."""
    from . import INTEGRATION_REGISTRY
    from .catalog import (
        IntegrationCatalog,
        IntegrationCatalogError,
        IntegrationValidationError,
    )
    from .. import _require_specify_project

    project_root = _require_specify_project()
    catalog = IntegrationCatalog(project_root)
    installed_key = _default_integration_key(_read_integration_json(project_root))
    safe_integration_id = _rich_escape(str(integration_id))

    try:
        info = catalog.get_integration_info(integration_id)
    except IntegrationCatalogError as exc:
        info = None
        # Keep the live exception so the fallback branch below can give
        # different guidance for local-config vs. network failures.
        catalog_error: Optional[IntegrationCatalogError] = exc
    else:
        catalog_error = None

    if info:
        name = _rich_escape(str(info.get("name", integration_id)))
        version = _rich_escape(str(info.get("version", "?")))
        console.print(
            f"\n[bold cyan]{name}[/bold cyan] ({safe_integration_id}) v{version}"
        )
        if info.get("description"):
            console.print(f"  {_rich_escape(str(info['description']))}")
        console.print()

        author_value = _rich_escape(str(info.get("author", "Unknown")))
        console.print(f"  [dim]Author:[/dim] {author_value}")
        if info.get("license"):
            console.print(
                f"  [dim]License:[/dim] {_rich_escape(str(info['license']))}"
            )

        tags = info.get("tags", [])
        if isinstance(tags, list) and tags:
            safe_tags = _rich_escape(", ".join(str(t) for t in tags))
            console.print(f"  [dim]Tags:[/dim] {safe_tags}")

        cat_name_value = info.get("_catalog_name", "")
        cat_name = _rich_escape(str(cat_name_value))
        install_allowed = info.get("_install_allowed", True)
        if cat_name_value:
            install_note = "" if install_allowed else " [yellow](discovery only)[/yellow]"
            console.print(f"  [dim]Source catalog:[/dim] {cat_name}{install_note}")

        if info.get("repository"):
            console.print(
                f"  [dim]Repository:[/dim] {_rich_escape(str(info['repository']))}"
            )

        if integration_id == installed_key:
            console.print("\n  [green]✓ Installed[/green] (currently active)")
        elif integration_id in INTEGRATION_REGISTRY:
            console.print("\n  [dim]Built-in integration (not currently active)[/dim]")
        return

    if integration_id in INTEGRATION_REGISTRY:
        integration = INTEGRATION_REGISTRY[integration_id]
        cfg = integration.config or {}
        name = cfg.get("name", integration_id)
        console.print(f"\n[bold cyan]{name}[/bold cyan] ({integration_id})")
        console.print("  [dim]Built-in integration (not listed in catalog)[/dim]")
        if integration_id == installed_key:
            console.print("\n  [green]✓ Installed[/green] (currently active)")
        if catalog_error:
            console.print(f"\n[yellow]Catalog unavailable:[/yellow] {catalog_error}")
        return

    if catalog_error:
        console.print(f"[red]Error:[/red] Could not query integration catalog: {catalog_error}")
        if isinstance(catalog_error, IntegrationValidationError):
            console.print(
                "\nCheck the configuration file path shown above "
                "(.specify/integration-catalogs.yml or ~/.specify/integration-catalogs.yml), "
                "or use a built-in integration ID directly."
            )
        elif os.environ.get("SPECKIT_INTEGRATION_CATALOG_URL", "").strip():
            console.print(
                "\nCheck whether SPECKIT_INTEGRATION_CATALOG_URL is set correctly and reachable, "
                "or unset it to use the configured catalog files, or use a built-in integration ID directly."
            )
        else:
            console.print("\nTry again when online, or use a built-in integration ID directly.")
    else:
        console.print(f"[red]Error:[/red] Integration '{safe_integration_id}' not found")
        console.print("\nTry: specify integration search")
    raise typer.Exit(1)
