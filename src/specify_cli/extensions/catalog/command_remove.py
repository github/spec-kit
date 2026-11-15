"""Implementation of ``specify extension catalog remove``.

Registered by ``catalog.register()``; shared catalog helpers live in
``catalog._helpers``.
"""
from __future__ import annotations

import os

import typer
from rich.markup import escape as _escape_markup

from .. import _commands
from . import catalog_app
from ._helpers import load_catalog_command_config


@catalog_app.command("remove")
def catalog_remove(
    name: str = typer.Argument(help="Catalog name to remove"),
):
    """Remove a catalog from .specify/extension-catalogs.yml."""
    project_root = _commands._require_specify_project()
    specify_dir = project_root / ".specify"

    config_path = specify_dir / "extension-catalogs.yml"
    if not config_path.exists():
        _commands.console.print(
            "[red]Error:[/red] No catalog config found. Nothing to remove."
        )
        raise typer.Exit(1)

    config = load_catalog_command_config(project_root, config_path)

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        _commands.console.print(
            "[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list."
        )
        raise typer.Exit(1)
    for index, entry in enumerate(catalogs):
        if not isinstance(entry, dict):
            _commands.console.print(
                f"[red]Error:[/red] Invalid catalog entry at index {index}: "
                f"expected a mapping, got {type(entry).__name__}"
            )
            raise typer.Exit(1)
    safe_name = _escape_markup(name)
    original_count = len(catalogs)
    catalogs = [
        catalog
        for catalog in catalogs
        if catalog.get("name") != name
    ]

    if len(catalogs) == original_count:
        _commands.console.print(f"[red]Error:[/red] Catalog '{safe_name}' not found.")
        raise typer.Exit(1)

    if catalogs:
        config["catalogs"] = catalogs
        config_path.write_text(
            _commands.yaml.safe_dump(
                config,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
    else:
        # The catalog loader rejects an existing config with no entries, so
        # delete the file instead of writing ``catalogs: []``.
        try:
            config_path.unlink(missing_ok=True)
        except OSError as error:
            config_label = _escape_markup(
                str(_commands._display_project_path(project_root, config_path))
            )
            _commands.console.print(
                f"[red]Error:[/red] Failed to delete {config_label}: "
                f"{_escape_markup(str(error))}"
            )
            raise typer.Exit(1)

    _commands.console.print(f"[green]✓[/green] Removed catalog '{safe_name}'")
    if not catalogs:
        if os.environ.get("SPECKIT_CATALOG_URL"):
            fallback = "the SPECKIT_CATALOG_URL environment variable still takes precedence"
        else:
            fallback = "user configuration or built-in defaults will be used"
        _commands.console.print(
            f"\n[dim]Project catalog override removed; {fallback}.[/dim]"
        )
