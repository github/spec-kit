"""Implementation of ``specify bundle catalog add``."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from ..._console import console
from .. import BundlerError
from .._commands import _fail
from ..project import require_project_root
from . import catalog_app


@catalog_app.command("add")
def catalog_add(
    url: str = typer.Argument(..., help="Catalog URL"),
    policy: str = typer.Option(
        "install-allowed", "--policy", help="install-allowed | discovery-only"
    ),
    priority: int = typer.Option(
        10, "--priority", help="Source priority (lower = higher)"
    ),
    source_id: str = typer.Option(None, "--id", help="Explicit source id"),
) -> None:
    """Register a project-scoped catalog source and persist it."""
    try:
        project_root = require_project_root()
        from ..catalog_config import add_source

        source = add_source(
            project_root, url, policy=policy, priority=priority, source_id=source_id
        )
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Added catalog '{_escape_markup(str(source.id))}' "
        f"(priority {source.priority}, {source.install_policy.value})."
    )
