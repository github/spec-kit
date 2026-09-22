"""Implementation of ``specify extension catalog add``.

Registered by ``catalog.register()``; shared catalog helpers live in
``catalog._helpers``.
"""
from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .. import _commands
from . import catalog_app
from ._helpers import load_catalog_command_config


@catalog_app.command("add")
def catalog_add(
    url: str = typer.Argument(help="Catalog URL (must use HTTPS)"),
    name: str = typer.Option(..., "--name", help="Catalog name"),
    priority: int = typer.Option(10, "--priority", help="Priority (lower = higher priority)"),
    install_allowed: bool = typer.Option(
        False, "--install-allowed/--no-install-allowed",
        help=(
            "Mark this catalog as a trusted install source. Only enable this for a "
            "catalog you own and vet; leave it off (the default) for discovery-only "
            "search surfaces. Never enable it for an unvetted public catalog."
        ),
    ),
    description: str = typer.Option("", "--description", help="Description of the catalog"),
):
    """Add a catalog to .specify/extension-catalogs.yml."""
    from .. import ExtensionCatalog, ValidationError

    project_root = _commands._require_specify_project()
    specify_dir = project_root / ".specify"

    # Validate URL
    tmp_catalog = ExtensionCatalog(project_root)
    try:
        tmp_catalog._validate_catalog_url(url)
    except ValidationError as error:
        _commands.console.print(f"[red]Error:[/red] {_escape_markup(str(error))}")
        raise typer.Exit(1)

    config_path = specify_dir / "extension-catalogs.yml"

    # Load existing config
    if config_path.exists():
        config = load_catalog_command_config(project_root, config_path)
    else:
        config = {}

    catalogs = config.get("catalogs", [])
    if not isinstance(catalogs, list):
        _commands.console.print(
            "[red]Error:[/red] Invalid catalog config: 'catalogs' must be a list."
        )
        raise typer.Exit(1)

    safe_name = _escape_markup(name)
    safe_url = _escape_markup(url)

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
            if existing == entry:
                return
            _commands.console.print(
                f"[yellow]Warning:[/yellow] A catalog named '{safe_name}' already exists."
            )
            _commands.console.print(
                "Use 'specify extension catalog remove' first, or choose a different name."
            )
            raise typer.Exit(1)

    catalogs.append(entry)

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

    install_label = "install allowed" if install_allowed else "discovery only"
    _commands.console.print(
        f"\n[green]✓[/green] Added catalog '[bold]{safe_name}[/bold]' ({install_label})"
    )
    _commands.console.print(f"  URL: {safe_url}")
    _commands.console.print(f"  Priority: {priority}")
    config_label = _escape_markup(
        str(_commands._display_project_path(project_root, config_path))
    )
    _commands.console.print(f"\nConfig saved to {config_label}")
