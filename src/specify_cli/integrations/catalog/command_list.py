"""The ``specify integration catalog list`` command."""
from __future__ import annotations

import os

import typer
from rich.markup import escape as _rich_escape

from ..._console import console
from . import catalog_app


@catalog_app.command("list")
def integration_catalog_list():
    """List configured integration catalog sources."""
    from .. import IntegrationCatalog, IntegrationCatalogError
    from ... import _require_specify_project

    project_root = _require_specify_project()
    catalog = IntegrationCatalog(project_root)
    env_override = os.environ.get("SPECKIT_INTEGRATION_CATALOG_URL", "").strip()

    try:
        if env_override:
            project_configs = None
            configs = catalog.get_catalog_configs()
        else:
            project_configs = catalog.get_project_catalog_configs()
            configs = project_configs if project_configs is not None else catalog.get_catalog_configs()
    except IntegrationCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Integration Catalog Sources:[/bold cyan]\n")
    if env_override:
        console.print(
            "  SPECKIT_INTEGRATION_CATALOG_URL is set; it supersedes configured catalog files."
        )
        console.print(
            "  Project/user catalog sources are not active while the env override is set.\n"
        )
        console.print("[bold]Active catalog source from environment (non-removable here):[/bold]\n")
    elif project_configs is None:
        console.print("  No project-level catalog sources configured.\n")
        console.print("[bold]Active catalog sources (non-removable here):[/bold]\n")
    else:
        console.print("[bold]Project catalog sources (removable):[/bold]\n")

    for i, cfg in enumerate(configs):
        install_status = (
            "[green]install allowed[/green]"
            if cfg.get("install_allowed")
            else "[yellow]discovery only[/yellow]"
        )
        raw_name = cfg.get("name")
        display_name = str(raw_name).strip() if raw_name is not None else ""
        if not display_name:
            display_name = f"catalog-{i + 1}"
        safe_name = _rich_escape(display_name)
        if env_override or project_configs is None:
            console.print(f"  - [bold]{safe_name}[/bold] — {install_status}")
        else:
            console.print(f"  [{i}] [bold]{safe_name}[/bold] — {install_status}")
        console.print(f"      {_rich_escape(str(cfg.get('url', '')))}")
        if cfg.get("description"):
            console.print(f"      [dim]{_rich_escape(str(cfg['description']))}[/dim]")
        console.print()
