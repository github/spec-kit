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

from .manifest import ComponentRef


def _resolved_locally(root: Path, component: ComponentRef) -> bool:
    kind = component.kind
    try:
        if kind == "presets":
            from .._assets import _locate_bundled_preset
            from ..presets import PresetManager

            if _locate_bundled_preset(component.id) is not None:
                return True
            return PresetManager(root).get_pack(component.id) is not None
        if kind == "extensions":
            from .._assets import _locate_bundled_extension
            from ..extensions import ExtensionManager

            if _locate_bundled_extension(component.id) is not None:
                return True
            return ExtensionManager(root).registry.is_installed(component.id)
        if kind == "workflows":
            from .._assets import _locate_bundled_workflow
            from ..workflows.catalog import WorkflowRegistry

            if _locate_bundled_workflow(component.id) is not None:
                return True
            return WorkflowRegistry(root).is_installed(component.id)
        if kind == "steps":
            from ..workflows import BUILTIN_STEP_TYPES
            from ..workflows.catalog import StepRegistry

            # Step types ship with Spec Kit as built-ins (shell, gate, if, ...)
            # rather than as an on-disk asset directory, so there is no
            # ``_locate_bundled_step`` to mirror the three lookups above.
            # ``BUILTIN_STEP_TYPES`` is the bundled-with-Spec-Kit check for this
            # kind. Deliberately NOT ``STEP_REGISTRY``: ``load_custom_steps``
            # adds project-installed ids to that process-global mapping and
            # never removes them, so in a long-lived process a community step
            # loaded for one project would be accepted as "bundled" when
            # validating another. Without any bundled check at all, every
            # built-in step type looked unresolved.
            if component.id in BUILTIN_STEP_TYPES:
                return True
            return StepRegistry(root).is_installed(component.id)
    except Exception:  # noqa: BLE001 - resolution is best-effort
        return False
    return False


def _resolved_in_catalog(root: Path, component: ComponentRef) -> dict | bool | None:
    """Return the winning catalog entry, False if absent, or None on failure."""
    kind = component.kind
    try:
        if kind == "presets":
            from ..presets import PresetCatalog

            entry = PresetCatalog(root).get_pack_info(component.id)
        elif kind == "extensions":
            from ..extensions import ExtensionCatalog

            entry = ExtensionCatalog(root).get_extension_info(component.id)
        elif kind == "workflows":
            from ..workflows.catalog import WorkflowCatalog

            entry = WorkflowCatalog(root).get_workflow_info(component.id)
        elif kind == "steps":
            from ..workflows.catalog import StepCatalog

            entry = StepCatalog(root).get_step_info(component.id)
        else:
            return None
    except Exception:  # noqa: BLE001 - catalog may be unreachable/misconfigured
        return None
    return entry if entry is not None else False


def _select_release(component: ComponentRef, entry: dict, version: str):
    kind = component.kind
    if kind == "presets":
        from ..presets._catalog_versions import select_release

        return select_release(entry, version)
    if kind == "extensions":
        from ..extensions._catalog_versions import select_release

        return select_release(entry, version)
    if kind == "workflows":
        from ..workflows.catalog._versions import select_release

        return select_release(entry, version)
    from ..workflows.step.catalog._versions import select_release

    return select_release(entry, component.id, version)


def _missing_pinned_release(component: ComponentRef, entry: dict) -> str | None:
    """Error when the winning catalog entry lacks the release the pin names.

    Mirrors ``bundle install``: an entry advertising no version cannot enforce
    a pin, so only entries that advertise one are checked.
    """
    pinned = component.version
    advertised = entry.get("version")
    if not pinned or advertised is None or not str(advertised).strip():
        return None
    label = f"{component.kind[:-1]} '{component.id}'"
    try:
        selected = _select_release(component, entry, pinned)
    except Exception as exc:  # noqa: BLE001 - malformed release records
        return f"{label} has an invalid catalog entry: {exc}"
    if selected is not None:
        return None
    return (
        f"{label} is pinned to version {pinned}, but its catalog has no release "
        f"for that version (it advertises {str(advertised).strip()})."
    )


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
            if isinstance(in_catalog, dict):
                return _missing_pinned_release(component, in_catalog)
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
