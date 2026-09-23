"""Implementation of ``specify extension catalog list``.

Registered by ``catalog.register()``; shared catalog helpers live in
``catalog._helpers``.
"""
from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .. import _commands
from . import catalog_app


@catalog_app.command("list")
def catalog_list():
    """List all active extension catalogs."""
    from .. import ExtensionCatalog, ValidationError

    project_root = _commands._require_specify_project()
    catalog = ExtensionCatalog(project_root)

    try:
        active_catalogs = catalog.get_active_catalogs()
    except ValidationError as error:
        _commands.console.print(f"[red]Error:[/red] {_escape_markup(str(error))}")
        raise typer.Exit(1)

    _commands.console.print("\n[bold cyan]Active Extension Catalogs:[/bold cyan]\n")
    for entry in active_catalogs:
        install_str = (
            "[green]install allowed[/green]"
            if entry.install_allowed
            else "[yellow]discovery only[/yellow]"
        )
        _commands.console.print(
            f"  [bold]{_escape_markup(entry.name)}[/bold] "
            f"(priority {entry.priority})"
        )
        if entry.description:
            _commands.console.print(f"     {_escape_markup(entry.description)}")
        _commands.console.print(f"     URL: {_escape_markup(str(entry.url))}")
        _commands.console.print(f"     Install: {install_str}")
        _commands.console.print()

    if any(not entry.install_allowed for entry in active_catalogs):
        _commands.console.print(
            "[dim]Discovery-only catalogs are searchable but not installable by design "
            "(unvetted sources). To install something you found in one, vet it and run "
            "'specify extension add <name> --from <url>', or add it to a catalog you "
            "control. Don't flip a discovery-only catalog to install_allowed.[/dim]\n"
        )

    config_path = project_root / ".specify" / "extension-catalogs.yml"
    user_config_path = Path.home() / ".specify" / "extension-catalogs.yml"
    if os.environ.get("SPECKIT_CATALOG_URL"):
        _commands.console.print(
            "[dim]Catalog configured via SPECKIT_CATALOG_URL environment variable.[/dim]"
        )
    else:
        try:
            proj_loaded = (
                config_path.exists()
                and catalog._load_catalog_config(config_path) is not None
            )
        except ValidationError:
            proj_loaded = False
        if proj_loaded:
            config_label = _escape_markup(
                str(_commands._display_project_path(project_root, config_path))
            )
            _commands.console.print(f"[dim]Config: {config_label}[/dim]")
        else:
            try:
                user_loaded = (
                    user_config_path.exists()
                    and catalog._load_catalog_config(user_config_path) is not None
                )
            except ValidationError:
                user_loaded = False
            if user_loaded:
                _commands.console.print(
                    "[dim]Config: ~/.specify/extension-catalogs.yml[/dim]"
                )
            else:
                _commands.console.print(
                    "[dim]Using built-in default catalog stack.[/dim]"
                )
                _commands.console.print(
                    "[dim]Add .specify/extension-catalogs.yml to customize.[/dim]"
                )
