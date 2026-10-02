"""Implementation of ``specify bundle install``."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.markup import escape as _escape_markup

from .._console import console
from . import BundlerError
from ._commands import (
    _build_stack,
    _bundle_overlaps,
    _default_script_type,
    _fail,
    _resolve_init_integration,
    _run_init,
    _speckit_version,
    bundle_app,
)
from .project import active_integration, require_project_root
from .sources import (
    _download_manifest,
    _local_manifest_source,
    _validate_manifest_structure,
)


@bundle_app.command("install")
def bundle_install(
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
    """Install a bundle's full component set through each primitive's machinery.

    ``bundle_id`` may be a catalog bundle id, or a local path to a built
    artifact (``.zip``), a bundle directory, or a ``bundle.yml`` file. Local
    sources install directly without consulting the catalog stack. Use
    ``--refresh`` to update owned components from a newer local source.
    """
    try:
        from .project import find_project_root
        from .adapters import DefaultPrimitiveInstaller
        from .installer import install_bundle
        from .resolver import resolve_install_plan

        project_root = find_project_root()

        local_manifest = _local_manifest_source(bundle_id)
        if local_manifest is not None:
            manifest = local_manifest
            _validate_manifest_structure(
                manifest,
                source=f"Local bundle source {bundle_id!r}",
            )
        else:
            stack = _build_stack(project_root or Path.cwd(), offline=offline)
            resolved = stack.resolve(bundle_id)

            if not resolved.install_allowed:
                raise BundlerError(
                    f"Bundle '{bundle_id}' resolves only from a discovery-only source "
                    f"('{resolved.source.id}'); it cannot be installed from there."
                )
            manifest = _download_manifest(resolved, offline=offline)

        if project_root is None:
            init_integration = _resolve_init_integration(integration, manifest)
            # Resolve all hard compatibility gates before ``specify init``.
            # Otherwise an incompatible but structurally valid bundle would
            # initialize a project and only then fail its version/integration
            # checks, leaving state behind after a failed install.
            resolve_install_plan(
                manifest,
                speckit_version=_speckit_version(),
                active_integration=init_integration,
                integration_explicit=True,
            )
            console.print(
                f"[cyan]No Spec Kit project here; initializing with integration "
                f"'{_escape_markup(str(init_integration))}'…[/cyan]"
            )
            _run_init(
                init_integration, script_type=_default_script_type(), offline=offline
            )
            project_root = require_project_root()

        for overlap in _bundle_overlaps(project_root, manifest, offline=offline):
            console.print(f"[yellow]![/yellow] {_escape_markup(str(overlap))}")

        # For an already-initialized project, the project's recorded active
        # integration is authoritative — an explicit --integration must not be
        # able to bypass the FR-019 integration-clash guard. The override only
        # selects the integration at init time (handled above) or confirms the
        # target when the active integration cannot be determined.
        detected = active_integration(project_root)
        plan = resolve_install_plan(
            manifest,
            speckit_version=_speckit_version(),
            active_integration=detected if detected is not None else integration,
            integration_explicit=bool(integration) and detected is None,
        )
        for warning in plan.warnings:
            console.print(f"[yellow]![/yellow] {_escape_markup(str(warning))}")

        result = install_bundle(
            project_root,
            plan,
            DefaultPrimitiveInstaller(allow_network=not offline),
            manifest=manifest,
            refresh=refresh,
        )
    except BundlerError as exc:
        _fail(str(exc))
        return

    refresh_summary = (
        f", {len(result.refreshed)} refreshed, {len(result.uninstalled)} removed"
        if refresh
        else ""
    )
    console.print(
        f"[green]✓[/green] Installed '{_escape_markup(str(result.bundle_id))}' "
        f"({len(result.installed)} added, {len(result.skipped)} already present"
        f"{refresh_summary})."
    )
