"""CLI adapter for ``specify integration uninstall``."""

from __future__ import annotations

import typer
from rich.markup import escape

from .._console import console
from .._utils import _display_project_path
from ._commands import integration_app
from ._operation_uninstall import (
    IntegrationUninstallError,
    IntegrationUninstallRequest,
    uninstall_integration,
)


@integration_app.command("uninstall")
def integration_uninstall(
    key: str = typer.Argument(None, help="Integration key to uninstall (default: current integration)"),
    force: bool = typer.Option(False, "--force", help="Remove files even if modified"),
):
    """Uninstall an integration, safely preserving modified files."""
    from .. import _require_specify_project

    root = _require_specify_project()
    try:
        result = uninstall_integration(IntegrationUninstallRequest(root, key, force))
    except IntegrationUninstallError as exc:
        console.print(f"[red]Error:[/red] {escape(exc.message)}")
        raise typer.Exit(1) from exc
    if result.key is None:
        console.print("[yellow]No integration is currently installed.[/yellow]")
        return
    for warning in result.warnings:
        console.print(f"[yellow]Warning:[/yellow] {escape(warning)}")
    if result.missing_manifest:
        console.print(f"[yellow]No manifest found for integration '{escape(result.key)}'. Nothing to uninstall.[/yellow]")
    console.print(f"\n[green]✓[/green] Integration '{escape(result.name)}' uninstalled")
    if result.removed:
        console.print(f"  Removed {len(result.removed)} file(s)")
    if result.skipped:
        console.print(f"\n[yellow]⚠[/yellow]  {len(result.skipped)} modified file(s) were preserved:")
        for path in result.skipped:
            console.print(f"    {_display_project_path(root, path)}")
