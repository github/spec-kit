"""Implementation of ``specify bundle add``."""

from __future__ import annotations

import typer

from ._commands import bundle_app
from .command_install import bundle_install


@bundle_app.command("add")
def bundle_add(
    bundle_id: str = typer.Argument(
        ...,
        help="Bundle id (from the catalog stack) or a local path to a .zip "
        "artifact, bundle directory, or bundle.yml",
    ),
    integration: str = typer.Option(None, "--integration", help="Override integration"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Refresh owned components from this bundle source",
    ),
) -> None:
    """Install a bundle's full component set (alias for install)."""
    bundle_install(
        bundle_id=bundle_id,
        integration=integration,
        offline=offline,
        refresh=refresh,
    )
