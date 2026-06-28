"""Resolve bundle component references against real, available components.

Used by ``specify bundle validate`` (FR-005 / SC-007) to confirm that every
declared component points at something installable. Resolution is offline-first:
a reference resolves when the component is bundled with Spec Kit or already
installed in the project; catalog sources are consulted only when network access
is permitted. Offline runs that cannot confirm a reference downgrade to a
warning rather than a false failure, while definitively-unknown references
always error.
"""
from __future__ import annotations

from pathlib import Path

from ..models.manifest import ComponentRef


def _resolved_locally(root: Path, component: ComponentRef) -> bool:
    kind = component.kind
    try:
        if kind == "presets":
            from ..._assets import _locate_bundled_preset
            from ...presets import PresetManager

            if _locate_bundled_preset(component.id) is not None:
                return True
            return PresetManager(root).get_pack(component.id) is not None
        if kind == "extensions":
            from ..._assets import _locate_bundled_extension
            from ...extensions import ExtensionManager

            if _locate_bundled_extension(component.id) is not None:
                return True
            return ExtensionManager(root).registry.is_installed(component.id)
        if kind == "workflows":
            from ..._assets import _locate_bundled_workflow
            from ...workflows.catalog import WorkflowRegistry

            if _locate_bundled_workflow(component.id) is not None:
                return True
            return WorkflowRegistry(root).is_installed(component.id)
        if kind == "steps":
            from ...workflows.catalog import StepRegistry

            return StepRegistry(root).is_installed(component.id)
    except Exception:  # noqa: BLE001 - resolution is best-effort
        return False
    return False


def _resolved_in_catalog(root: Path, component: ComponentRef) -> bool | None:
    """Return True/False if a catalog could be consulted, or None on failure."""
    kind = component.kind
    try:
        if kind == "presets":
            from ...presets import PresetCatalog

            return PresetCatalog(root).get_pack_info(component.id) is not None
        if kind == "extensions":
            from ...extensions import ExtensionCatalog

            return ExtensionCatalog(root).get_extension_info(component.id) is not None
        if kind == "workflows":
            from ...workflows.catalog import WorkflowCatalog

            return WorkflowCatalog(root).get_workflow_info(component.id) is not None
        if kind == "steps":
            from ...workflows.catalog import StepCatalog

            return StepCatalog(root).get_step_info(component.id) is not None
    except Exception:  # noqa: BLE001 - catalog may be unreachable/misconfigured
        return None
    return None


def make_reference_checker(
    project_root: Path,
    *,
    allow_network: bool,
    warnings: list[str],
):
    """Build a ``ReferenceChecker`` for :func:`validate_manifest`.

    Returns an error string for a reference that is definitively unresolvable,
    ``None`` otherwise. Unverifiable references (offline, or an unreachable
    catalog) append a note to *warnings* and pass.
    """

    def check(component: ComponentRef) -> str | None:
        if _resolved_locally(project_root, component):
            return None

        if allow_network:
            in_catalog = _resolved_in_catalog(project_root, component)
            if in_catalog is True:
                return None
            if in_catalog is False:
                return (
                    f"{component.kind[:-1]} '{component.id}' is not bundled, "
                    "installed, or present in any active catalog."
                )
            warnings.append(
                f"Could not verify {component.kind[:-1]} '{component.id}' "
                "(catalog unreachable); reference left unchecked."
            )
            return None

        warnings.append(
            f"Could not verify {component.kind[:-1]} '{component.id}' offline "
            "(not bundled or installed); re-run validate online to check catalogs."
        )
        return None

    return check
