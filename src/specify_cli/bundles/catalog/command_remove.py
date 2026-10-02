"""Implementation of ``specify bundle catalog remove``."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from ..._console import console
from .. import BundlerError
from .._commands import _fail
from ..project import require_project_root
from . import catalog_app


@catalog_app.command("remove")
def catalog_remove(
    id_or_url: str = typer.Argument(..., help="Source id or url to remove"),
) -> None:
    """Remove a project-scoped catalog source (built-in defaults can't be deleted)."""
    try:
        project_root = require_project_root()
        from ..catalog_config import remove_source

        removed = remove_source(project_root, id_or_url)
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Removed catalog source '{_escape_markup(str(removed))}'."
    )
