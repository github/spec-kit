"""Implementation of the ``specify preset catalog remove`` command."""

from __future__ import annotations

import typer
import yaml
from rich.markup import escape as _escape_markup

from ..._console import console
from . import catalog_app


@catalog_app.command("remove")
def preset_catalog_remove(
    name: str = typer.Argument(help="Catalog name to remove"),
):
    """Remove a catalog from .specify/preset-catalogs.yml."""
    from ... import _require_specify_project

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    config_path = specify_dir / "preset-catalogs.yml"
    if not config_path.exists():
        console.print(
            "[red]Error:[/red] No preset catalog config found. Nothing to remove."
        )
        raise typer.Exit(1)

    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 - preserve CLI error boundary
        console.print(f"[red]Error:[/red] Failed to read preset catalog config: {e}")
        raise typer.Exit(1)
    if config is None:
        config = {}
    elif not isinstance(config, dict):
        console.print("[red]Error:[/red] Invalid catalog config: expected a mapping.")
        raise typer.Exit(1)

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print(
            "[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list."
        )
        raise typer.Exit(1)
    # Rendering only — the raw name drives the comparison below.
    safe_name = _escape_markup(str(name))

    original_count = len(catalogs)
    catalogs = [c for c in catalogs if isinstance(c, dict) and c.get("name") != name]

    if len(catalogs) == original_count:
        console.print(f"[red]Error:[/red] Catalog '{safe_name}' not found.")
        raise typer.Exit(1)

    config["catalogs"] = catalogs
    config_path.write_text(
        yaml.safe_dump(
            config, default_flow_style=False, sort_keys=False, allow_unicode=True
        ),
        encoding="utf-8",
    )

    console.print(f"[green]✓[/green] Removed catalog '{safe_name}'")
    if not catalogs:
        console.print(
            "\n[dim]No catalogs remain in config. Built-in defaults will be used.[/dim]"
        )
