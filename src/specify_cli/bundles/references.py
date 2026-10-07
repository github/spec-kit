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
from .versioning import same_version


def _matches_pin(component: ComponentRef, actual: str | None) -> bool:
    return component.version is None or (
        bool(actual) and same_version(actual, component.version)
    )


def _resolved_locally(root: Path, component: ComponentRef) -> bool:
    kind = component.kind
    try:
        if component.source:
            return False
        from .primitives import _bundled_manifest_version, primitive_manager

        if kind == "presets":
            from .._assets import _locate_bundled_preset

            bundled = _locate_bundled_preset(component.id)
            if bundled is not None and _matches_pin(
                component, _bundled_manifest_version(bundled / "preset.yml", "preset")
            ):
                return True
        if kind == "extensions":
            from .._assets import _locate_bundled_extension

            bundled = _locate_bundled_extension(component.id)
            if bundled is not None and _matches_pin(
                component, _bundled_manifest_version(bundled / "extension.yml", "extension")
            ):
                return True
        if kind == "workflows":
            from .._assets import _locate_bundled_workflow

            bundled = _locate_bundled_workflow(component.id)
            if bundled is not None and _matches_pin(
                component, _bundled_manifest_version(bundled / "workflow.yml", "workflow")
            ):
                return True
        if kind == "steps":
            from ..workflows import BUILTIN_STEP_TYPES

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
            if component.id in BUILTIN_STEP_TYPES and component.version is None:
                return True
        manager = primitive_manager(kind, root, allow_network=False)
        return manager.is_installed(component) and _matches_pin(
            component, manager.installed_version(component)
        )
    except Exception:  # noqa: BLE001 - resolution is best-effort
        return False
    return False


def _catalog_has_release(component: ComponentRef, catalog) -> bool:
    from .component_catalog import select_catalog_release, winning_catalog_entry

    current = winning_catalog_entry(catalog, component)
    if current is None or not current.get("_install_allowed", True):
        return False
    if component.source and current.get("_catalog_name") != component.source:
        return False
    if component.version is None:
        return True
    if component.kind in ("extensions", "presets") and not current.get("version"):
        # These legacy catalogs cannot attest a version; the primitive
        # installer likewise accepts their unversioned current entry.
        return True
    selected = select_catalog_release(component, current)
    return (
        selected is not None
        and selected.get("_catalog_name") == current.get("_catalog_name")
        and selected.get("_install_allowed", True)
        and _matches_pin(component, selected.get("version"))
    )


def _resolved_in_catalog(root: Path, component: ComponentRef) -> bool | str | None:
    """Return the lookup result, a validation error, or None if unreachable."""
    from ..extensions import ExtensionError
    from ..presets import PresetError
    from ..workflows.catalog import StepCatalogError, WorkflowCatalogError
    from . import BundlerError
    from .component_catalog import CatalogUnavailable

    kind = component.kind
    try:
        if kind == "presets":
            from ..presets import PresetCatalog

            catalog = PresetCatalog(root)
            return _catalog_has_release(component, catalog)
        if kind == "extensions":
            from ..extensions import ExtensionCatalog

            catalog = ExtensionCatalog(root)
            return _catalog_has_release(component, catalog)
        if kind == "workflows":
            from ..workflows.catalog import WorkflowCatalog

            catalog = WorkflowCatalog(root)
            return _catalog_has_release(component, catalog)
        if kind == "steps":
            from ..workflows.catalog import StepCatalog

            catalog = StepCatalog(root)
            return _catalog_has_release(component, catalog)
    except (ConnectionError, TimeoutError):
        return None
    except CatalogUnavailable:
        return None
    except (BundlerError, ExtensionError, PresetError, WorkflowCatalogError, StepCatalogError) as exc:
        return f"Catalog lookup failed: {exc}"
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

        if component.kind in ("presets", "extensions") and component.source is None:
            from .._assets import _locate_bundled_extension, _locate_bundled_preset
            from . import BundlerError
            from .primitives import _assert_pinned_version, _bundled_manifest_version

            kind = component.kind[:-1]
            locate = (
                _locate_bundled_preset
                if component.kind == "presets"
                else _locate_bundled_extension
            )
            bundled = locate(component.id)
            if bundled is not None:
                try:
                    _assert_pinned_version(
                        kind.capitalize(),
                        component.id,
                        component.version,
                        _bundled_manifest_version(bundled / f"{kind}.yml", kind),
                    )
                except BundlerError as exc:
                    return str(exc)

        if allow_network:
            in_catalog = _resolved_in_catalog(project_root, component)
            if in_catalog is True:
                return None
            if in_catalog is False:
                return (
                    f"{component.kind[:-1]} '{component.id}' at "
                    f"{component.version or 'current'} is not available "
                    "locally or from the selected install-allowed catalog."
                )
            if isinstance(in_catalog, str):
                return in_catalog
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
