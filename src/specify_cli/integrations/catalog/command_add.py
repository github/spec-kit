"""The ``specify integration catalog add`` command."""
from __future__ import annotations

from typing import Optional

import typer
from rich.markup import escape as _rich_escape

from ..._console import console
from . import catalog_app


@catalog_app.command("add")
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
    from .. import IntegrationCatalog, IntegrationCatalogError
    from ... import _require_specify_project

    project_root = _require_specify_project()
    catalog = IntegrationCatalog(project_root)

    # Normalize once here so the success message reflects what was actually
    # stored. ``IntegrationCatalog.add_catalog`` strips again defensively.
    normalized_url = url.strip()

    try:
        status = catalog.add_catalog(normalized_url, name)
    except IntegrationCatalogError as exc:
        # Covers both URL validation (base class) and config-file validation
        # (IntegrationValidationError subclass).
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    safe_url = _rich_escape(normalized_url)
    if status == "unchanged":
        console.print(
            f"[green]✓[/green] Catalog source already configured: {safe_url}"
        )
    else:
        console.print(f"[green]✓[/green] Catalog source added: {safe_url}")
