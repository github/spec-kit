"""Workflow overlay domain API and nested CLI registration."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import typer

overlay_app = typer.Typer(
    name="overlay",
    help="Manage workflow overlays",
    add_completion=False,
)


def register(app: typer.Typer) -> None:
    """Attach the overlay command group to the workflow app."""
    from . import command_add  # noqa: F401 -- registers handler
    from . import command_set_priority  # noqa: F401 -- registers handler
    from . import command_enable  # noqa: F401 -- registers handler
    from . import command_disable  # noqa: F401 -- registers handler
    from . import command_remove  # noqa: F401 -- registers handler
    from . import command_list  # noqa: F401 -- registers handler

    app.add_typer(overlay_app, name="overlay")


def __getattr__(name: str) -> Any:
    """Load the resolver only when the domain API is requested."""
    if name != "WorkflowResolver":
        raise AttributeError(name)
    resolver = import_module(f"{__name__}.resolver")
    value = resolver.WorkflowResolver
    globals()[name] = value
    return value


__all__ = ["WorkflowResolver"]
