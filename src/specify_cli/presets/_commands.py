"""Typer command group and shared CLI infrastructure for ``specify preset``."""

from __future__ import annotations

import typer

from .._console import console
from .._download_security import read_response_limited as _read_response_limited

read_response_limited = _read_response_limited

preset_app = typer.Typer(
    name="preset",
    help="Manage spec-kit presets",
    add_completion=False,
)

# Lowest priority a user may request. Lower numbers win resolution, so the
# stack is anchored at 1 rather than 0 to leave no unreachable slot above the
# highest-precedence preset.
MINIMUM_PRESET_PRIORITY = 1


def _render_powershell_argv(argv: list[str]) -> str:
    """Render argv as a copy-pastable PowerShell command."""

    def quote_arg(arg: str) -> str:
        return "'" + arg.replace("'", "''") + "'"

    return "& " + " ".join(quote_arg(arg) for arg in argv)


def _validate_priority(priority: int) -> None:
    """Reject a non-positive priority before destructive work begins."""
    if priority < MINIMUM_PRESET_PRIORITY:
        console.print(
            "[red]Error:[/red] Priority must be a positive integer "
            f"({MINIMUM_PRESET_PRIORITY} or higher)"
        )
        raise typer.Exit(1)


def _warn_unmet_extension_dependencies(manager, manifest) -> None:
    """Preserve the legacy helper import path for external consumers."""
    from .command_add import _warn_unmet_extension_dependencies as implementation

    implementation(manager, manifest)


def preset_add(*args, **kwargs):
    """Preserve the legacy add-handler import path for external consumers."""
    from .command_add import preset_add as implementation

    return implementation(*args, **kwargs)


def preset_remove(*args, **kwargs):
    """Preserve the legacy remove-handler import path for external consumers."""
    from .command_remove import preset_remove as implementation

    return implementation(*args, **kwargs)


def preset_update(*args, **kwargs):
    """Preserve the legacy update-handler import path for external consumers."""
    from .command_update import preset_update as implementation

    return implementation(*args, **kwargs)


def register(app: typer.Typer) -> None:
    """Register preset commands on the parent application."""
    # Imports are intentionally ordered to preserve command help output.
    from . import command_list as _command_list
    from . import command_add as _command_add
    from . import command_remove as _command_remove
    from . import command_update as _command_update
    from . import command_search as _command_search
    from . import command_resolve as _command_resolve
    from . import command_info as _command_info
    from . import command_set_priority as _command_set_priority
    from . import command_enable as _command_enable
    from . import command_disable as _command_disable
    from .catalog import register as register_catalog

    _ = (
        _command_list,
        _command_add,
        _command_remove,
        _command_update,
        _command_search,
        _command_resolve,
        _command_info,
        _command_set_priority,
        _command_enable,
        _command_disable,
    )
    register_catalog(preset_app)
    app.add_typer(preset_app, name="preset")
