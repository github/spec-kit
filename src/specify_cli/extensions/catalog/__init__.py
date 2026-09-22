"""Registration for the nested ``specify extension catalog`` command group.

Command handlers live in ``command_*.py`` modules and shared catalog helpers
live in ``_helpers.py``.
"""
from __future__ import annotations

import typer


catalog_app = typer.Typer(
    name="catalog",
    help=(
        "Manage extension catalogs.\n\n"
        "Catalogs are either install sources (install_allowed) or discovery-only "
        "search surfaces. The built-in 'community' catalog is discovery-only by "
        "design: it is unvetted, so it is searchable but not installable. To install "
        "something you found there, either use 'specify extension add <name> --from "
        "<url>' after vetting it, or curate your own catalog you control. Never flip a "
        "discovery-only catalog to install_allowed — that is the vetting boundary."
    ),
    add_completion=False,
)


def register(app: typer.Typer) -> None:
    """Attach the catalog command group to the extension Typer app."""
    from . import command_add  # noqa: F401 — registers handler via decorator
    from . import command_list  # noqa: F401 — registers handler via decorator
    from . import command_remove  # noqa: F401 — registers handler via decorator

    app.add_typer(catalog_app, name="catalog")
