"""Installer: apply an :class:`InstallPlan` via existing primitive machinery.

The actual component installation (extensions, presets, steps, workflows) is
delegated to a :class:`PrimitiveInstaller` so the bundler never re-implements
primitive logic (Principle I) and integration tests can inject a deterministic,
offline fake (Principle II/IV). The real adapter dispatches in-process to the
existing extension/preset/step/workflow machinery.

Installation is idempotent and stops on first failure with no partial record
write (FR-018, SC partial-failure-stop).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .. import BundlerError
from ..models.manifest import ComponentRef
from ..models.records import (
    InstalledBundleRecord,
    components_still_needed,
    load_records,
    remove_record,
    save_records,
    upsert_record,
)
from .conflict import detect_conflicts
from .resolver import InstallPlan


class PrimitiveInstaller(Protocol):
    """Adapter over the existing Spec Kit primitive install/remove machinery."""

    def is_installed(self, project_root: Path, component: ComponentRef) -> bool: ...

    def install(self, project_root: Path, component: ComponentRef) -> None: ...

    def remove(self, project_root: Path, component: ComponentRef) -> None: ...


@dataclass
class InstallResult:
    bundle_id: str
    installed: list[ComponentRef] = field(default_factory=list)
    skipped: list[ComponentRef] = field(default_factory=list)
    refreshed: list[ComponentRef] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.installed or self.refreshed)


def install_bundle(
    project_root: Path,
    plan: InstallPlan,
    installer: PrimitiveInstaller,
    manifest=None,
    refresh: bool = False,
) -> InstallResult:
    """Execute *plan*, recording provenance. Idempotent and atomic on failure.

    When *refresh* is True (used by ``specify bundle update``), components that
    are already installed are re-applied through the primitive machinery so they
    are brought up to the plan's pinned versions, rather than skipped. Primitive
    config (e.g. preset priority overrides) is preserved by the underlying
    machinery. Pre-existing components are never rolled back on failure.
    """
    records = load_records(project_root)

    if manifest is not None:
        report = detect_conflicts(manifest, plan.effective_integration, records)
        if report.has_blocking_conflict:
            raise BundlerError(report.integration_clash)

    result = InstallResult(bundle_id=plan.bundle_id)
    done: list[ComponentRef] = []
    try:
        for component in plan.components:
            if installer.is_installed(project_root, component):
                if refresh:
                    _refresh_component(project_root, installer, component)
                    result.refreshed.append(component)
                else:
                    result.skipped.append(component)
                continue
            installer.install(project_root, component)
            done.append(component)
            result.installed.append(component)
    except BundlerError:
        _rollback(project_root, installer, done)
        raise
    except Exception as exc:  # noqa: BLE001
        _rollback(project_root, installer, done)
        raise BundlerError(
            f"Failed to install bundle '{plan.bundle_id}': {exc}. "
            "No changes were recorded."
        ) from exc

    record = InstalledBundleRecord.create(
        bundle_id=plan.bundle_id,
        version=plan.version,
        components=list(plan.components),
    )
    save_records(project_root, upsert_record(records, record))
    return result


def remove_bundle(
    project_root: Path,
    bundle_id: str,
    installer: PrimitiveInstaller,
) -> InstallResult:
    """Remove a bundle, uninstalling only components no other bundle still needs."""
    records = load_records(project_root)
    target = next((r for r in records if r.bundle_id == bundle_id), None)
    if target is None:
        raise BundlerError(f"Bundle '{bundle_id}' is not installed.")

    still_needed = components_still_needed(records, exclude_bundle_id=bundle_id)
    result = InstallResult(bundle_id=bundle_id)

    for component in target.contributed_components:
        key = (component.kind, component.id)
        if key in still_needed:
            result.skipped.append(component)
            continue
        if installer.is_installed(project_root, component):
            installer.remove(project_root, component)
        result.installed.append(component)

    save_records(project_root, remove_record(records, bundle_id))
    return result


def _refresh_component(
    project_root: Path,
    installer: PrimitiveInstaller,
    component: ComponentRef,
) -> None:
    """Re-apply an already-installed component to bring it up to its pinned version.

    Prefers a primitive-provided ``refresh`` hook when available; otherwise falls
    back to a re-install through the existing idempotent install path.
    """
    op = getattr(installer, "refresh", None)
    if callable(op):
        op(project_root, component)
    else:
        installer.install(project_root, component)


def _rollback(
    project_root: Path,
    installer: PrimitiveInstaller,
    done: list[ComponentRef],
) -> None:
    for component in reversed(done):
        try:
            installer.remove(project_root, component)
        except Exception:  # noqa: BLE001 - best-effort rollback
            continue
