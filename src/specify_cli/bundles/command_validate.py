"""Implementation of ``specify bundle validate``."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import _expand_manifest, _fail, bundle_app
from .expansion import discovery_only_messages
# Kept at module scope as the command's download monkeypatch point for tests.
from .sources import _download_manifest
from .validator import ValidationReport


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
        from .manifest import BundleManifest

        manifest = BundleManifest.from_file(manifest_path)
        report = _validate(manifest, manifest_path, offline=offline)
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


def _validate(manifest, manifest_path: Path, *, offline: bool) -> ValidationReport:
    """Run structural, expansion, and component checks in stable phases."""
    from .project import find_project_root
    from .references import make_reference_checker
    from .validator import validate_manifest

    ref_root = find_project_root(manifest_path.parent) or Path.cwd()
    ref_warnings: list[str] = []
    checker = make_reference_checker(
        ref_root, allow_network=not offline, warnings=ref_warnings
    )

    # A flat manifest retains the historical single validation call and output.
    if not manifest.bundles:
        report = validate_manifest(manifest, reference_checker=checker)
        report.warnings.extend(ref_warnings)
        return report

    # Structural errors on a reference-bearing manifest must not resolve or
    # download anything. The structural phase intentionally performs no
    # reference checks.
    structural = validate_manifest(manifest)
    if structural.errors:
        return structural

    if offline:
        report = validate_manifest(manifest, reference_checker=checker)
        report.warnings.extend(ref_warnings)
        report.warnings.extend(_offline_reference_warnings(manifest))
        return report

    try:
        expanded = _expand_manifest(
            ref_root,
            manifest,
            offline=False,
            download=_download_manifest,
        )
    except BundlerError as exc:
        # Structural checks already passed, so ``checked`` holds only the
        # reference checker's own-component errors; the expansion error leads.
        checked = validate_manifest(manifest, reference_checker=checker)
        checked.errors.insert(0, str(exc))
        checked.warnings.extend(ref_warnings)
        return checked

    report = validate_manifest(
        manifest,
        reference_checker=checker,
        components=expanded.components,
        origins={key: origin.origin for key, origin in expanded.origins.items()},
    )
    report.errors.extend(discovery_only_messages(expanded))
    report.warnings.extend(ref_warnings)
    report.warnings.extend(expanded.warnings)
    return report


def _offline_reference_warnings(manifest) -> list[str]:
    return [
        f"Offline: bundle reference '{reference.id}@{reference.version}' "
        f"({manifest.bundle.id} → {reference.id}) was not expanded."
        for reference in manifest.bundles
    ]


def _resolve_manifest_path(path: Path | None) -> Path:
    target = (path or Path.cwd()).resolve()
    if target.is_dir():
        target = target / "bundle.yml"
    if not target.exists():
        raise BundlerError(f"No bundle.yml found at '{target}'.")
    return target
