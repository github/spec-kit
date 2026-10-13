"""Implementation of ``specify bundle init``."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import (
    _default_script_type,
    _fail,
    _resolve_init_integration,
    _run_init,
    bundle_app,
)
from .command_install import bundle_install
from .project import require_project_root


@bundle_app.command("init")
def bundle_init(
    bundle: str = typer.Argument(None, help="Optional bundle to install after init"),
    integration: str = typer.Option(None, "--integration", help="Integration override"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
) -> None:
    """Ensure the project is initialized (idempotent), then optionally install a bundle."""
    from .project import find_project_root

    try:
        project_root = find_project_root()
        if project_root is None:
            init_integration = _resolve_init_integration(integration, None)
            console.print(
                f"[cyan]Initializing a Spec Kit project with integration "
                f"'{_escape_markup(str(init_integration))}'…[/cyan]"
            )
            _run_init(
                init_integration, script_type=_default_script_type(), offline=offline
            )
            project_root = require_project_root()
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Spec Kit project ready at "
        f"{_escape_markup(str(project_root))}."
    )
    if bundle:
        bundle_install(bundle, integration=integration, offline=offline)
