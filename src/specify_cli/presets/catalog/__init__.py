"""Registration for the nested ``specify preset catalog`` command group.

Command handlers live in ``command_*.py`` modules.
"""

from __future__ import annotations

import typer

catalog_app = typer.Typer(
    name="catalog",
    help="Manage preset catalogs",
    add_completion=False,
)


def register(app: typer.Typer) -> None:
    """Attach the catalog command group to the preset Typer app."""
    # isort: off
    from . import command_list  # noqa: F401 — registers handler via decorator
    from . import command_add  # noqa: F401 — registers handler via decorator
    from . import command_remove  # noqa: F401 — registers handler via decorator
    # isort: on

    app.add_typer(catalog_app, name="catalog")
