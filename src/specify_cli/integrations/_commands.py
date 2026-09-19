"""Shared infrastructure and registration for ``specify integration`` commands.

Command handlers belong in ``command_*.py`` modules. Compatibility exports
required by external CLI consumers remain at this registration boundary.
"""
from __future__ import annotations

import typer

from .._assets import get_speckit_version  # noqa: F401 — re-exported for monkeypatching in tests
from .catalog import catalog_app as integration_catalog_app  # noqa: F401 — compatibility alias

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


def register(app: typer.Typer) -> None:
    """Attach the integration command group to the root Typer app."""
    from .catalog import register as register_catalog

    register_catalog(integration_app)

    # isort: off
    from . import command_install  # noqa: F401 — registers handler via decorator
    from . import command_uninstall  # noqa: F401 — registers handler via decorator
    from . import command_switch  # noqa: F401 — registers handler via decorator
    from . import command_upgrade  # noqa: F401 — registers handler via decorator
    from . import command_list  # noqa: F401 — registers handler via decorator
    from . import command_status  # noqa: F401 — registers handler via decorator
    from . import command_use  # noqa: F401 — registers handler via decorator
    from . import command_search  # noqa: F401 — registers handler via decorator
    from . import command_info  # noqa: F401 — registers handler via decorator
    from . import command_scaffold  # noqa: F401 — registers handler via decorator
    # isort: on

    app.add_typer(integration_app, name="integration")
