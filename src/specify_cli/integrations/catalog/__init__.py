"""Registration for the nested ``specify integration catalog`` command group.

Command handlers live in ``command_*.py`` modules. Catalog domain exports are
retained here for compatibility; their implementation belongs to the parent
``specify_cli.integrations`` package.
"""

from __future__ import annotations

import typer

from .. import (
    IntegrationCatalog,
    IntegrationCatalogEntry,
    IntegrationCatalogError,
    IntegrationDescriptor,
    IntegrationDescriptorError,
    IntegrationValidationError,
    _catalog_shape_error,
)

__all__ = [
    "IntegrationCatalog",
    "IntegrationCatalogEntry",
    "IntegrationCatalogError",
    "IntegrationDescriptor",
    "IntegrationDescriptorError",
    "IntegrationValidationError",
    "_catalog_shape_error",
    "catalog_app",
    "register",
]


catalog_app = typer.Typer(
    name="catalog",
    help="Manage integration catalog sources",
    add_completion=False,
)


def register(app: typer.Typer) -> None:
    """Attach the catalog command group to the integration Typer app."""
    from . import command_list  # noqa: F401 — registers handler via decorator
    from . import command_add  # noqa: F401 — registers handler via decorator
    from . import command_remove  # noqa: F401 — registers handler via decorator

    app.add_typer(catalog_app, name="catalog")
