"""Implementation of ``specify bundle list``."""

from __future__ import annotations

import json as _json

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import _fail, bundle_app
from .project import require_project_root
from .records import load_records


@bundle_app.command("list")
def bundle_list(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
) -> None:
    """List bundles currently installed in the project with versions."""
    try:
        project_root = require_project_root()
        records = load_records(project_root)
    except BundlerError as exc:
        _fail(str(exc))
        return

    if as_json:
        print(_json.dumps([r.to_dict() for r in records], indent=2))
        return

    if not records:
        console.print("[yellow]No bundles installed.[/yellow]")
        console.print("\nInstall one with: [cyan]specify bundle install <id>[/cyan]")
        return

    console.print("\n[bold cyan]Installed bundles:[/bold cyan]\n")
    for record in records:
        console.print(
            f"  [bold]{_escape_markup(str(record.bundle_id))}[/bold] "
            f"v{_escape_markup(str(record.version))} "
            f"[dim]({len(record.contributed_components)} components, "
            f"installed {_escape_markup(str(record.installed_at))})[/dim]"
        )
