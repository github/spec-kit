"""Implementation of the ``specify preset catalog add`` command."""

from __future__ import annotations

import typer
import yaml
from rich.markup import escape as _escape_markup

from ..._console import console
from . import catalog_app


@catalog_app.command("add")
def preset_catalog_add(
    url: str = typer.Argument(help="Catalog URL (must use HTTPS)"),
    name: str = typer.Option(..., "--name", help="Catalog name"),
    priority: int = typer.Option(
        10, "--priority", help="Priority (lower = higher priority)"
    ),
    install_allowed: bool = typer.Option(
        False,
        "--install-allowed/--no-install-allowed",
        help="Allow presets from this catalog to be installed",
    ),
    description: str = typer.Option(
        "", "--description", help="Description of the catalog"
    ),
):
    """Add a catalog to .specify/preset-catalogs.yml."""
    from ... import _display_project_path, _require_specify_project
    from .. import PresetCatalog, PresetValidationError

    project_root = _require_specify_project()
    specify_dir = project_root / ".specify"

    # Validate URL
    tmp_catalog = PresetCatalog(project_root)
    try:
        tmp_catalog._validate_catalog_url(url)
    except PresetValidationError as e:
        console.print(f"[red]Error:[/red] {_escape_markup(str(e))}")
        raise typer.Exit(1)

    config_path = specify_dir / "preset-catalogs.yml"

    # Load existing config
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 - preserve CLI error boundary
            config_label = _display_project_path(project_root, config_path)
            console.print(
                f"[red]Error:[/red] Failed to read {_escape_markup(str(config_label))}: {_escape_markup(str(e))}"
            )
            raise typer.Exit(1)
        if config is None:
            config = {}
        elif not isinstance(config, dict):
            console.print(
                "[red]Error:[/red] Invalid catalog config: expected a mapping."
            )
            raise typer.Exit(1)
    else:
        config = {}

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        console.print(
            "[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list."
        )
        raise typer.Exit(1)

    # Only rendering is escaped — the raw values are what get persisted and
    # compared below, so a name containing markup still round-trips exactly.
    safe_name = _escape_markup(str(name))
    safe_url = _escape_markup(str(url))

    entry = {
        "name": name,
        "url": url,
        "priority": priority,
        "install_allowed": install_allowed,
        "description": description,
    }

    # Check for duplicate name
    for existing in catalogs:
        if isinstance(existing, dict) and existing.get("name") == name:
            if all(
                existing.get(field) == entry[field]
                for field in (
                    "url",
                    "priority",
                    "install_allowed",
                    "description",
                )
            ):
                return
            console.print(
                f"[yellow]Warning:[/yellow] A catalog named '{safe_name}' already exists."
            )
            console.print(
                "Use 'specify preset catalog remove' first, or choose a different name."
            )
            raise typer.Exit(1)

    catalogs.append(entry)

    config["catalogs"] = catalogs
    config_path.write_text(
        yaml.safe_dump(
            config, default_flow_style=False, sort_keys=False, allow_unicode=True
        ),
        encoding="utf-8",
    )

    install_label = "install allowed" if install_allowed else "discovery only"
    console.print(
        f"\n[green]✓[/green] Added catalog '[bold]{safe_name}[/bold]' ({install_label})"
    )
    console.print(f"  URL: {safe_url}")
    console.print(f"  Priority: {priority}")
    config_label = _escape_markup(str(_display_project_path(project_root, config_path)))
    console.print(f"\nConfig saved to {config_label}")
