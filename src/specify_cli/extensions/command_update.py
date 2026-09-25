"""Implementation of ``specify extension update``.

Registered by ``_commands.register()``; private update phases live in adjacent
``_command_update_*`` modules.
"""
from __future__ import annotations

import typer

from . import _commands
from ._command_update_artifacts import (
    _archive_extension_directory as _archive_extension_directory,
)
from ._command_update_discovery import (
    _bundled_update_source as _bundled_update_source,
)
from ._command_update_transaction import run_update_command


@_commands.extension_app.command("update")
def extension_update(
    extension: str = typer.Argument(None, help="Extension ID or name to update (or all)"),
):
    """Update extension(s) to latest version."""
    return run_update_command(extension)
