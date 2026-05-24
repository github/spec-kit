"""specify integration list/status/use/search/info + catalog list/add/remove command handlers."""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import typer
from rich.markup import escape as _rich_escape
from rich.table import Table

from .._console import console
from ..integration_state import (
    default_integration_key as _default_integration_key,
    installed_integration_keys as _installed_integration_keys,
)
from ._commands import integration_app, integration_catalog_app
from ._helpers import (
    _read_integration_json,
    _register_extensions_for_agent,
    _resolve_integration_options,
    _set_default_integration_or_exit,
)


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
        from .catalog import IntegrationCatalog, IntegrationCatalogError

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


def _print_integration_status_report(report: dict[str, Any]) -> None:
    status = report["status"]
    status_label = {
        "ok": "[green]OK[/green]",
        "warning": "[yellow]WARNING[/yellow]",
        "error": "[red]ERROR[/red]",
    }.get(str(status), str(status).upper())
    installed = report.get("installed_integrations") or []
    installed_display = ", ".join(_rich_escape(str(item)) for item in installed)

    console.print(f"Integration status: {status_label}")
    console.print(
        f"Default integration: {_rich_escape(str(report.get('default_integration') or 'none'))}"
    )
    console.print(f"Installed integrations: {installed_display if installed else 'none'}")
    multi_install_safe = report.get("multi_install_safe")
    if multi_install_safe is None:
        multi_install_safe_display = "unknown"
    else:
        multi_install_safe_display = "yes" if multi_install_safe else "no"
    console.print(f"Multi-install safe: {multi_install_safe_display}")
    console.print(
        f"Shared templates target alignment: "
        f"{_rich_escape(str(report.get('shared_templates_target_alignment') or 'none'))}"
    )
    console.print(f"Modified managed files: {report.get('modified_managed_files', 0)}")
    console.print(f"Missing managed files: {report.get('missing_managed_files', 0)}")
    console.print(f"Invalid manifest paths: {report.get('invalid_manifest_paths', 0)}")
    console.print(f"Unchecked manifests: {report.get('unchecked_manifests', 0)}")

    findings = report.get("findings") or []
    if not findings:
        return

    console.print()
    console.print("[bold]Findings:[/bold]")
    for item in findings:
        severity = item.get("severity", "")
        severity_label = {
            "error": "[red]error[/red]",
            "warning": "[yellow]warning[/yellow]",
        }.get(severity, severity)
        prefix = f"- {severity_label} {_rich_escape(str(item.get('code', '')))}"
        if item.get("integration"):
            prefix += f" ({_rich_escape(str(item['integration']))})"
        console.print(
            f"{prefix}: {_rich_escape(str(item.get('message', '')))}",
            soft_wrap=True,
        )
        if item.get("suggestion"):
            console.print(
                f"  Suggestion: {_rich_escape(str(item['suggestion']))}",
                soft_wrap=True,
            )


@integration_app.command("status")
def integration_status(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable integration status.",
    ),
):
    """Report the current project's integration status without changing files."""
    from .. import _require_specify_project
    from ..integration_status import build_integration_status_report

    project_root = _require_specify_project()
    report = build_integration_status_report(project_root)

    if json_output:
        typer.echo(json.dumps(report, indent=2))
    else:
        _print_integration_status_report(report)

    if report["status"] == "error":
        raise typer.Exit(1)


@integration_app.command("use")
def integration_use(
    key: str = typer.Argument(help="Installed integration key to make the default"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing shared infrastructure files, including customizations, while changing the default"),
):
    """Set the default integration without uninstalling other integrations."""
    from . import get_integration
    from .. import _require_specify_project

    project_root = _require_specify_project()
    current = _read_integration_json(project_root)
    installed_keys = _installed_integration_keys(current)
    if key not in installed_keys:
        console.print(f"[red]Error:[/red] Integration '{key}' is not installed.")
        if installed_keys:
            console.print(f"[yellow]Installed integrations:[/yellow] {', '.join(installed_keys)}")
        else:
            console.print("Install one with: [cyan]specify integration install <key>[/cyan]")
        raise typer.Exit(1)

    integration = get_integration(key)
    if integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{key}'")
        raise typer.Exit(1)

    raw_options, parsed_options = _resolve_integration_options(integration, current, key, None)
    _set_default_integration_or_exit(
        project_root,
        current,
        key,
        integration,
        installed_keys,
        raw_options=raw_options,
        parsed_options=parsed_options,
        refresh_templates_force=force,
        refresh_hint=(
            "To overwrite customizations, re-run with "
            f"[cyan]specify integration use {key} --force[/cyan]."
        ),
    )
    _register_extensions_for_agent(
        project_root,
        key,
        continuing="The integration was selected, but installed extensions may need re-registration.",
    )
    console.print(f"[green]✓[/green] Default integration set to [bold]{key}[/bold].")


# ===== Integration catalog discovery commands =====
#
# These commands mirror the workflow catalog CLI shape:
#   - `search` / `info` for discovery over the active catalog stack
#   - `catalog list/add/remove` for managing catalog sources
#
# They deliberately do NOT add `integration add/remove/enable/disable/
# set-priority`: integrations are single-active (install / uninstall / switch),
# not additive like extensions and presets.
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
        iid = integ.get("id", "?")
        name = integ.get("name", iid)
        version = integ.get("version", "?")
        console.print(f"[bold]{name}[/bold] ({iid}) v{version}")
        desc = integ.get("description", "")
        if desc:
            console.print(f"  {desc}")

        console.print(f"\n  [dim]Author:[/dim] {integ.get('author', 'Unknown')}")
        tags = integ.get("tags", [])
        if isinstance(tags, list) and tags:
            console.print(f"  [dim]Tags:[/dim] {', '.join(str(t) for t in tags)}")

        cat_name = integ.get("_catalog_name", "")
        install_allowed = integ.get("_install_allowed", True)
        if cat_name:
            if install_allowed:
                console.print(f"  [dim]Catalog:[/dim] {cat_name}")
            else:
                console.print(
                    f"  [dim]Catalog:[/dim] {cat_name} "
                    "[yellow](discovery only — not installable)[/yellow]"
                )

        if iid == installed_key:
            console.print("\n  [green]✓ Installed[/green] (currently active)")
        elif iid in INTEGRATION_REGISTRY:
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
        name = info.get("name", integration_id)
        version = info.get("version", "?")
        console.print(f"\n[bold cyan]{name}[/bold cyan] ({integration_id}) v{version}")
        if info.get("description"):
            console.print(f"  {info['description']}")
        console.print()

        console.print(f"  [dim]Author:[/dim] {info.get('author', 'Unknown')}")
        if info.get("license"):
            console.print(f"  [dim]License:[/dim] {info['license']}")

        tags = info.get("tags", [])
        if isinstance(tags, list) and tags:
            console.print(f"  [dim]Tags:[/dim] {', '.join(str(t) for t in tags)}")

        cat_name = info.get("_catalog_name", "")
        install_allowed = info.get("_install_allowed", True)
        if cat_name:
            install_note = "" if install_allowed else " [yellow](discovery only)[/yellow]"
            console.print(f"  [dim]Source catalog:[/dim] {cat_name}{install_note}")

        if info.get("repository"):
            console.print(f"  [dim]Repository:[/dim] {info['repository']}")

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
        console.print(f"[red]Error:[/red] Integration '{integration_id}' not found")
        console.print("\nTry: specify integration search")
    raise typer.Exit(1)


@integration_catalog_app.command("list")
def integration_catalog_list():
    """List configured integration catalog sources."""
    from .catalog import IntegrationCatalog, IntegrationCatalogError
    from .. import _require_specify_project

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
        if env_override or project_configs is None:
            console.print(f"  - [bold]{display_name}[/bold] — {install_status}")
        else:
            console.print(f"  [{i}] [bold]{display_name}[/bold] — {install_status}")
        console.print(f"      {cfg.get('url', '')}")
        if cfg.get("description"):
            console.print(f"      [dim]{cfg['description']}[/dim]")
        console.print()


@integration_catalog_app.command("add")
def integration_catalog_add(
    url: str = typer.Argument(
        ...,
        help=(
            "Catalog URL to add (HTTPS required, except http://localhost, "
            "http://127.0.0.1, or http://[::1] for local testing)"
        ),
    ),
    name: Optional[str] = typer.Option(None, "--name", help="Catalog name"),
):
    """Add an integration catalog source to the project config."""
    from .catalog import IntegrationCatalog, IntegrationCatalogError
    from .. import _require_specify_project

    project_root = _require_specify_project()
    catalog = IntegrationCatalog(project_root)

    # Normalize once here so the success message reflects what was actually
    # stored. ``IntegrationCatalog.add_catalog`` strips again defensively.
    normalized_url = url.strip()

    try:
        catalog.add_catalog(normalized_url, name)
    except IntegrationCatalogError as exc:
        # Covers both URL validation (base class) and config-file validation
        # (IntegrationValidationError subclass).
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source added: {normalized_url}")


@integration_catalog_app.command("remove")
def integration_catalog_remove(
    index: int = typer.Argument(..., help="Catalog index to remove (from 'catalog list')"),
):
    """Remove an integration catalog source by 0-based index."""
    from .catalog import IntegrationCatalog, IntegrationCatalogError
    from .. import _require_specify_project

    project_root = _require_specify_project()
    catalog = IntegrationCatalog(project_root)

    try:
        removed_name = catalog.remove_catalog(index)
    except IntegrationCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Catalog source '{removed_name}' removed")
