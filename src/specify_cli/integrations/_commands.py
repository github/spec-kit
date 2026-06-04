"""specify integration * commands — app objects and register() entry point."""
from __future__ import annotations

import typer

from .._assets import get_speckit_version  # noqa: F401 — re-exported for monkeypatching in tests

# Re-export helpers used by commands/init.py and tests
from ._helpers import (  # noqa: F401
    _cli_error_detail,
    _cli_phase_label,
    _parse_integration_options,
    _write_integration_json,
)

integration_app = typer.Typer(
    name="integration",
    help="Manage coding agent integrations",
    add_completion=False,
)

integration_catalog_app = typer.Typer(
    name="catalog",
    help="Manage integration catalog sources",
    add_completion=False,
)
integration_app.add_typer(integration_catalog_app, name="catalog")


def register(app: typer.Typer) -> None:
    from . import _install_commands  # noqa: F401 — registers handlers via decorators
    from . import _migrate_commands  # noqa: F401
    from . import _query_commands    # noqa: F401
    app.add_typer(integration_app, name="integration")
