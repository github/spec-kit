"""Registration for the nested ``specify bundle catalog`` command group."""

from __future__ import annotations

import typer

catalog_app = typer.Typer(
    name="catalog",
    help="Manage bundle catalog sources",
    add_completion=False,
)


def register(app: typer.Typer) -> None:
    """Attach the catalog command group to the bundle Typer app."""
    from . import command_list  # noqa: F401 — registers handler via decorator
    from . import command_add  # noqa: F401 — registers handler via decorator
    from . import command_remove  # noqa: F401 — registers handler via decorator

    app.add_typer(catalog_app, name="catalog")
