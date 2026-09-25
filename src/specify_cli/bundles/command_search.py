"""Implementation of ``specify bundle search``."""

from __future__ import annotations

import json as _json
from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import bundle_app, _build_stack, _fail, _trust_badge, _trust_level
from .project import find_project_root


@bundle_app.command("search")
def bundle_search(
    query: str = typer.Argument("", help="Optional text query"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
) -> None:
    """List matching bundles across the active catalog stack."""
    try:
        project_root = find_project_root() or Path.cwd()
        stack = _build_stack(project_root, offline=offline)
        results = stack.search(query)
    except BundlerError as exc:
        _fail(str(exc))
        return

    if as_json:
        payload = [
            {
                "id": r.entry.id,
                "name": r.entry.name,
                "role": r.entry.role,
                "version": r.entry.version,
                "description": r.entry.description,
                "source": r.source.id,
                "install_policy": r.source.install_policy.value,
                "verified": r.entry.verified,
                "trust": _trust_level(r.entry.verified),
            }
            for r in results
        ]
        print(_json.dumps(payload, indent=2))
        return

    if not results:
        console.print("[yellow]No matching bundles found.[/yellow]")
        return

    console.print("\n[bold cyan]Bundles:[/bold cyan]\n")
    for r in results:
        policy = "[dim](discovery-only)[/dim]" if not r.source.install_allowed else ""
        console.print(
            f"  [bold]{_escape_markup(str(r.entry.id))}[/bold] "
            f"v{_escape_markup(str(r.entry.version))} — "
            f"{_escape_markup(str(r.entry.name))} "
            f"[dim]({_escape_markup(str(r.entry.role))})[/dim] "
            f"{_trust_badge(r.entry.verified)} {policy}"
        )
        console.print(f"    {_escape_markup(str(r.entry.description))}")
        console.print(f"    [dim]source: {_escape_markup(str(r.source.id))}[/dim]")
