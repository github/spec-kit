"""Workflow catalog domain API and nested CLI registration."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import typer

from ..._download_security import MAX_JSON_CATALOG_BYTES as MAX_JSON_CATALOG_BYTES

catalog_app = typer.Typer(
    name="catalog",
    help="Manage workflow catalogs",
    add_completion=False,
)


def register(app: typer.Typer) -> None:
    """Attach the workflow catalog group to the workflow app."""
    from . import command_list  # noqa: F401 -- registers handler
    from . import command_add  # noqa: F401 -- registers handler
    from . import command_remove  # noqa: F401 -- registers handler

    app.add_typer(catalog_app, name="catalog")


_DOMAIN_EXPORTS = {
    "WorkflowCatalog",
    "WorkflowCatalogEntry",
    "WorkflowCatalogError",
    "WorkflowRegistry",
    "WorkflowValidationError",
}
_STEP_COMPATIBILITY_EXPORTS = {
    "StepCatalog",
    "StepCatalogEntry",
    "StepCatalogError",
    "StepRegistry",
    "StepValidationError",
}
_COMPATIBILITY_EXPORTS = {"json", "os", "tempfile"}


def __getattr__(name: str) -> Any:
    """Load catalog domain symbols only when a consumer requests them."""
    if name in _STEP_COMPATIBILITY_EXPORTS:
        step_catalog = import_module("..step.catalog", __name__)
        value = getattr(step_catalog, name)
        globals()[name] = value
        return value
    if name not in _DOMAIN_EXPORTS | _COMPATIBILITY_EXPORTS:
        raise AttributeError(name)
    domain = import_module(f"{__name__}._domain")
    value = getattr(domain, name)
    globals()[name] = value
    return value


__all__ = sorted(_DOMAIN_EXPORTS | _STEP_COMPATIBILITY_EXPORTS)
