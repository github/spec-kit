"""Registration for the nested ``specify workflow step`` command group."""

from __future__ import annotations

import typer

step_app = typer.Typer(
    name="step",
    help="Manage workflow step types",
    add_completion=False,
)


def register(app: typer.Typer) -> None:
    """Attach the step command group to the workflow app."""
    from .catalog import register as register_catalog

    register_catalog(step_app)

    # isort: off
    from . import command_list  # noqa: F401 -- registers handler
    from . import command_add  # noqa: F401 -- registers handler
    from . import command_remove  # noqa: F401 -- registers handler
    from . import command_search  # noqa: F401 -- registers handler
    from . import command_info  # noqa: F401 -- registers handler
    # isort: on

    app.add_typer(step_app, name="step")
