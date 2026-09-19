"""The ``specify integration list`` command."""
from __future__ import annotations


import typer
from rich.table import Table

from .._console import console
from ..integration_state import (
    default_integration_key as _default_integration_key,
    installed_integration_keys as _installed_integration_keys,
)
from ._commands import integration_app
from ._helpers import _read_integration_json


@integration_app.command("list")
def integration_list(
    catalog: bool = typer.Option(False, "--catalog", help="Browse full catalog (built-in + community)"),
):
    """List available integrations and installed status."""
    from . import INTEGRATION_REGISTRY
    from .. import _require_specify_project

    project_root = _require_specify_project()
    current = _read_integration_json(project_root)
    default_key = _default_integration_key(current)
    installed_keys = set(_installed_integration_keys(current))

    if catalog:
        from . import IntegrationCatalog, IntegrationCatalogError

        ic = IntegrationCatalog(project_root)
        try:
            entries = ic.search()
        except IntegrationCatalogError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)

        if not entries:
            console.print("[yellow]No integrations found in catalog.[/yellow]")
            return

        table = Table(title="Integration Catalog")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Source")
        table.add_column("Status")
        table.add_column("Multi-install Safe")

        for entry in sorted(entries, key=lambda e: e["id"]):
            eid = entry["id"]
            cat_name = entry.get("_catalog_name", "")
            install_allowed = entry.get("_install_allowed", True)
            if eid == default_key:
                status = "[green]installed (default)[/green]"
            elif eid in installed_keys:
                status = "[green]installed[/green]"
            elif eid in INTEGRATION_REGISTRY:
                status = "built-in"
            elif install_allowed is False:
                status = "discovery-only"
            else:
                status = ""
            safe = ""
            if eid in INTEGRATION_REGISTRY:
                reg_integ = INTEGRATION_REGISTRY[eid]
                safe = "yes" if getattr(reg_integ, "multi_install_safe", False) else "no"
            table.add_row(
                eid,
                entry.get("name", eid),
                entry.get("version", ""),
                cat_name,
                status,
                safe,
            )
        console.print(table)
        return

    if not INTEGRATION_REGISTRY:
        console.print("[yellow]No integrations available.[/yellow]")
        return

    table = Table(title="Coding Agent Integrations")
    table.add_column("Key", style="cyan")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("CLI Required")
    table.add_column("Multi-install Safe")

    for key in sorted(INTEGRATION_REGISTRY.keys()):
        integration = INTEGRATION_REGISTRY[key]
        cfg = integration.config or {}
        name = cfg.get("name", key)
        requires_cli = cfg.get("requires_cli", False)
        if key == default_key:
            status = "[green]installed (default)[/green]"
        elif key in installed_keys:
            status = "[green]installed[/green]"
        else:
            status = ""
        cli_req = "yes" if requires_cli else "no (IDE)"
        safe = "yes" if getattr(integration, "multi_install_safe", False) else "no"
        table.add_row(key, name, status, cli_req, safe)

    console.print(table)

    if installed_keys:
        console.print(f"\n[dim]Default integration:[/dim] [cyan]{default_key or 'none'}[/cyan]")
        console.print(f"[dim]Installed integrations:[/dim] [cyan]{', '.join(sorted(installed_keys))}[/cyan]")
    else:
        console.print("\n[yellow]No integration currently installed.[/yellow]")
        console.print("Install one with: [cyan]specify integration install <key>[/cyan]")
