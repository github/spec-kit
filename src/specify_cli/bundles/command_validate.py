"""Implementation of ``specify bundle validate``."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import _fail, bundle_app


@bundle_app.command("validate")
def bundle_validate(
    path: Path = typer.Option(
        None, "--path", help="Bundle directory or bundle.yml (default: cwd)"
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Do not access catalogs; verify references against bundled/installed only",
    ),
) -> None:
    """Report whether the manifest is well-formed and references resolve."""
    try:
        manifest_path = _resolve_manifest_path(path)
        from .project import find_project_root
        from .manifest import BundleManifest
        from .references import make_reference_checker
        from .validator import validate_manifest

        manifest = BundleManifest.from_file(manifest_path)
        ref_root = find_project_root(manifest_path.parent) or Path.cwd()
        ref_warnings: list[str] = []
        checker = make_reference_checker(
            ref_root, allow_network=not offline, warnings=ref_warnings
        )
        report = validate_manifest(manifest, reference_checker=checker)
        report.warnings.extend(ref_warnings)
    except BundlerError as exc:
        _fail(str(exc))
        return

    for warning in report.warnings:
        console.print(f"[yellow]![/yellow] {_escape_markup(str(warning))}")
    if not report.ok:
        console.print("[red]Manifest is invalid:[/red]")
        for error in report.errors:
            console.print(f"  [red]-[/red] {_escape_markup(str(error))}")
        raise typer.Exit(code=1)
    console.print(
        f"[green]✓[/green] {_escape_markup(str(manifest.bundle.id))} "
        "is well-formed and valid."
    )


def _resolve_manifest_path(path: Path | None) -> Path:
    target = (path or Path.cwd()).resolve()
    if target.is_dir():
        target = target / "bundle.yml"
    if not target.exists():
        raise BundlerError(f"No bundle.yml found at '{target}'.")
    return target
