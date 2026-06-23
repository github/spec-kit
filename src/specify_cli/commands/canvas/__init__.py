"""``specify canvas`` command group — install bundled canvas extensions.

v1 supports a single first-party canvas (``speckit-board``) and is intentionally
lightweight: no registry, no manifest abstraction. Adding more canvases later
should extend ``_CANVASES`` and (if needed) split into a richer module.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import typer

from ..._console import console
from ..._assets import _repo_root

canvas_app = typer.Typer(
    name="canvas",
    help="Install and manage Spec Kit canvas extensions for Copilot CLI",
    add_completion=False,
)


_CANVASES: dict[str, dict[str, str]] = {
    "speckit-board": {
        "source_subpath": "extensions/speckit-board",
        "description": (
            "Spec-Driven Development dashboard: portfolio view of all features, "
            "pipeline stages, and one-click slash-command actions."
        ),
    },
}


def _extensions_root() -> Path:
    """Return the Copilot CLI user-scope extensions directory."""
    home = os.environ.get("COPILOT_HOME") or str(Path.home() / ".copilot")
    return Path(home) / "extensions"


def _source_dir(name: str) -> Path:
    spec = _CANVASES[name]
    return _repo_root() / spec["source_subpath"]


def _fail(message: str) -> None:
    console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(code=1)


@canvas_app.command("list")
def canvas_list() -> None:
    """List canvases available to install."""
    console.print("[bold]Available canvases:[/bold]")
    for name, spec in _CANVASES.items():
        installed = (_extensions_root() / name).exists()
        marker = "[green]✓ installed[/green]" if installed else "[dim]not installed[/dim]"
        console.print(f"  • [cyan]{name}[/cyan]  {marker}")
        console.print(f"      {spec['description']}")


@canvas_app.command("install")
def canvas_install(
    name: str = typer.Argument(
        "speckit-board",
        help="Canvas to install (default: speckit-board).",
    ),
    dev: bool = typer.Option(
        False,
        "--dev",
        help="Install via symlink from the repo source (for active development).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite an existing installation.",
    ),
) -> None:
    """Install a canvas extension into ~/.copilot/extensions/."""
    if name not in _CANVASES:
        _fail(f"Unknown canvas '{name}'. Run 'specify canvas list' to see options.")

    src = _source_dir(name)
    if not src.is_dir():
        _fail(
            f"Source not found at {src}. This command must be run from a checkout of the spec-kit repo."
        )

    dest_root = _extensions_root()
    dest = dest_root / name
    dest_root.mkdir(parents=True, exist_ok=True)

    if dest.exists() or dest.is_symlink():
        if not force:
            _fail(
                f"{dest} already exists. Re-run with --force to overwrite, "
                f"or run 'specify canvas uninstall {name}' first."
            )
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)

    if dev:
        dest.symlink_to(src.resolve(), target_is_directory=True)
        console.print(f"[green]✓[/green] Symlinked [cyan]{name}[/cyan] → {src}")
    else:
        shutil.copytree(src, dest)
        console.print(f"[green]✓[/green] Installed [cyan]{name}[/cyan] → {dest}")

    console.print()
    console.print(
        "[dim]Restart Copilot CLI (or run an extensions_reload from the agent) to activate.[/dim]"
    )
    console.print(
        f"[dim]Open with: ask the agent to 'open the {name} canvas'.[/dim]"
    )


@canvas_app.command("uninstall")
def canvas_uninstall(
    name: str = typer.Argument(
        "speckit-board",
        help="Canvas to uninstall (default: speckit-board).",
    ),
) -> None:
    """Remove a canvas extension from ~/.copilot/extensions/."""
    if name not in _CANVASES:
        _fail(f"Unknown canvas '{name}'.")

    dest = _extensions_root() / name
    if not dest.exists() and not dest.is_symlink():
        console.print(f"[yellow]Not installed:[/yellow] {dest}")
        return

    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    else:
        shutil.rmtree(dest)
    console.print(f"[green]✓[/green] Removed [cyan]{name}[/cyan] from {dest.parent}")


def register(app: typer.Typer) -> None:
    """Attach the canvas command group to the root Typer app."""
    app.add_typer(canvas_app, name="canvas")
