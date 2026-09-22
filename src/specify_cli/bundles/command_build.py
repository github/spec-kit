"""Implementation of ``specify bundle build``."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import _fail, bundle_app


@bundle_app.command("build")
def bundle_build(
    path: Path = typer.Option(None, "--path", help="Bundle directory (default: cwd)"),
    output: Path = typer.Option(
        None, "--output", help="Output directory for the artifact"
    ),
) -> None:
    """Produce a single versioned distributable artifact (.zip)."""
    try:
        bundle_dir = (path or Path.cwd()).resolve()
        if bundle_dir.is_file():
            bundle_dir = bundle_dir.parent
        from .packager import build_bundle

        result = build_bundle(bundle_dir, output_dir=output)
    except BundlerError as exc:
        _fail(str(exc))
        return

    console.print(
        f"[green]✓[/green] Built {_escape_markup(result.artifact_path.name)} "
        f"({result.file_count} files) → "
        f"{_escape_markup(str(result.artifact_path))}"
    )
