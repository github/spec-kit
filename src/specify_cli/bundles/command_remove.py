"""Implementation of ``specify bundle remove``."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import _fail, bundle_app
from .project import require_project_root


@bundle_app.command("remove")
def bundle_remove(
    bundle_id: str = typer.Argument(..., help="Installed bundle id to remove"),
) -> None:
    """Uninstall only the components this bundle contributed (no collateral removals)."""
    try:
        project_root = require_project_root()
        from .adapters import DefaultPrimitiveInstaller
        from .installer import remove_bundle

        result = remove_bundle(project_root, bundle_id, DefaultPrimitiveInstaller())
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Removed '{_escape_markup(str(result.bundle_id))}' "
        f"({len(result.uninstalled)} uninstalled, {len(result.skipped)} kept for other bundles)."
    )
