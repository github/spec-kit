"""Implementation of the ``specify preset catalog list`` command."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from ..._console import console
from . import catalog_app


@catalog_app.command("list")
def preset_catalog_list():
    """List all active preset catalogs."""
    from ... import _display_project_path, _require_specify_project
    from .. import PresetCatalog, PresetValidationError

    project_root = _require_specify_project()
    catalog = PresetCatalog(project_root)

    try:
        active_catalogs = catalog.get_active_catalogs()
    except PresetValidationError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    console.print("\n[bold cyan]Active Preset Catalogs:[/bold cyan]\n")
    for entry in active_catalogs:
        install_str = (
            "[green]install allowed[/green]"
            if entry.install_allowed
            else "[yellow]discovery only[/yellow]"
        )
        console.print(
            f"  [bold]{_escape_markup(str(entry.name))}[/bold] (priority {entry.priority})"
        )
        if entry.description:
            console.print(f"     {_escape_markup(str(entry.description))}")
        console.print(f"     URL: {_escape_markup(str(entry.url))}")
        console.print(f"     Install: {install_str}")
        console.print()

    config_path = project_root / ".specify" / "preset-catalogs.yml"
    user_config_path = Path.home() / ".specify" / "preset-catalogs.yml"
    if os.environ.get("SPECKIT_PRESET_CATALOG_URL"):
        console.print(
            "[dim]Catalog configured via SPECKIT_PRESET_CATALOG_URL environment variable.[/dim]"
        )
    else:
        try:
            proj_loaded = (
                config_path.exists()
                and catalog._load_catalog_config(config_path) is not None
            )
        except PresetValidationError:
            proj_loaded = False
        if proj_loaded:
            console.print(
                f"[dim]Config: {_display_project_path(project_root, config_path)}[/dim]"
            )
        else:
            try:
                user_loaded = (
                    user_config_path.exists()
                    and catalog._load_catalog_config(user_config_path) is not None
                )
            except PresetValidationError:
                user_loaded = False
            if user_loaded:
                console.print("[dim]Config: ~/.specify/preset-catalogs.yml[/dim]")
            else:
                console.print("[dim]Using built-in default catalog stack.[/dim]")
                console.print(
                    "[dim]Add .specify/preset-catalogs.yml to customize.[/dim]"
                )
