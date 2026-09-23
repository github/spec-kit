"""Implementation of ``specify bundle update``."""

from __future__ import annotations

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import _build_stack, _fail, _speckit_version, bundle_app
from .project import active_integration, require_project_root
from .records import load_records
from .sources import _download_manifest


@bundle_app.command("update")
def bundle_update(
    bundle_id: str = typer.Argument(None, help="Bundle id, or omit with --all"),
    all_bundles: bool = typer.Option(
        False, "--all", help="Update every installed bundle"
    ),
    integration: str = typer.Option(None, "--integration", help="Override integration"),
    offline: bool = typer.Option(False, "--offline", help="Do not access the network"),
) -> None:
    """Re-resolve and refresh a bundle's components via each primitive's update path."""
    try:
        project_root = require_project_root()
        records = load_records(project_root)
        if not all_bundles and not bundle_id:
            raise BundlerError("Specify a bundle id or use --all.")
        targets = [r.bundle_id for r in records] if all_bundles else [bundle_id]
        if not targets:
            console.print("[yellow]No installed bundles to update.[/yellow]")
            return

        stack = _build_stack(project_root, offline=offline)
        from .adapters import DefaultPrimitiveInstaller
        from .installer import install_bundle
        from .resolver import resolve_install_plan

        installer = DefaultPrimitiveInstaller(allow_network=not offline)
        for target in targets:
            if not any(r.bundle_id == target for r in records):
                raise BundlerError(f"Bundle '{target}' is not installed.")
            resolved = stack.resolve(target)
            if not resolved.install_allowed:
                raise BundlerError(
                    f"Bundle '{target}' resolves only from a discovery-only source "
                    f"('{resolved.source.id}'); it cannot be updated from there. "
                    "Update requires an install-allowed source (FR-025)."
                )
            manifest = _download_manifest(resolved, offline=offline)
            detected = active_integration(project_root)
            plan = resolve_install_plan(
                manifest,
                speckit_version=_speckit_version(),
                active_integration=detected if detected is not None else integration,
                integration_explicit=bool(integration) and detected is None,
            )
            install_bundle(
                project_root, plan, installer, manifest=manifest, refresh=True
            )
            console.print(
                f"[green]✓[/green] Updated '{_escape_markup(str(target))}' "
                f"to v{_escape_markup(str(plan.version))}."
            )
    except BundlerError as exc:
        _fail(str(exc))
        return
