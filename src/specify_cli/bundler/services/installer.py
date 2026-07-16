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
from ..models.manifest import BundleManifest, ComponentRef
from ..models.records import (
    InstalledBundleRecord,
    components_still_needed,
    find_record,
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
    uninstalled: list[ComponentRef] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.installed or self.refreshed)


def install_bundle(
    project_root: Path,
    plan: InstallPlan,
    installer: PrimitiveInstaller,
    manifest: BundleManifest | None = None,
    refresh: bool = False,
) -> InstallResult:
    """Execute *plan*, recording provenance. Idempotent, with bounded rollback.

    Atomicity is scoped, not global: on failure only the components newly
    installed during *this* call are rolled back, and the provenance record is
    written solely on full success (a failure records nothing). Components that
    were already installed beforehand — including those re-applied when *refresh*
    is True — are never rolled back.

    When *refresh* is True (used by ``specify bundle update``), components that
    are already installed are re-applied through the primitive machinery so they
    are brought up to the plan's pinned versions, rather than skipped. Primitive
    config (e.g. preset priority overrides) is preserved by the underlying
    machinery.

    Version-pin enforcement is install-time only. The primitive ``is_installed``
    checks are id-based (they do not compare versions), so when a component is
    already present and *refresh* is False it is skipped without verifying that
    the on-disk version matches the manifest pin. Pins are therefore only
    guaranteed to be applied when the bundler actually performs an install or a
    refresh; running ``specify bundle update`` re-applies every owned component
    at its pinned version.
    """
    records = load_records(project_root)

    if manifest is not None:
        report = detect_conflicts(manifest, plan.effective_integration, records)
        if report.has_blocking_conflict:
            raise BundlerError(report.integration_clash)

    result = InstallResult(bundle_id=plan.bundle_id)
    existing = find_record(records, plan.bundle_id)
    prior_ours = {
        (c.kind, c.id) for c in existing.contributed_components
    } if existing is not None else set()
    # Components already attributed to a *different* installed bundle: these are
    # legitimately shareable (refcounted on removal), so this bundle may also
    # claim them. A component that is installed on disk but tracked by no bundle
    # was installed independently and must NOT be attributed here — otherwise
    # removing this bundle would uninstall it (collateral removal, FR-022).
    other_tracked = {
        (c.kind, c.id)
        for r in records
        if r.bundle_id != plan.bundle_id
        for c in r.contributed_components
    }

    contributed: list[ComponentRef] = []
    done: list[ComponentRef] = []
    try:
        for component in plan.components:
            key = (component.kind, component.id)
            if installer.is_installed(project_root, component):
                # A component is "ours" only when this bundle (or a sibling
                # bundle) already owns it. Independently-installed components
                # are never attributed and — crucially — never refreshed, so
                # ``bundle update`` cannot make collateral changes to things it
                # does not own (FR-022).
                owned = key in prior_ours or key in other_tracked
                if refresh and owned:
                    _refresh_component(project_root, installer, component)
                    result.refreshed.append(component)
                else:
                    result.skipped.append(component)
                if owned:
                    contributed.append(component)
                continue
            installer.install(project_root, component)
            done.append(component)
            result.installed.append(component)
            contributed.append(component)

        # On update (refresh), uninstall components this bundle used to own
        # that the new version no longer ships. Otherwise they are dropped
        # from the record below (contributed only holds plan.components) yet
        # left on disk — permanently orphaned, since no bundle record can
        # ever remove them. A stale component still owned by another bundle
        # is kept installed and simply de-attributed here (it stays in that
        # bundle's record). Mirrors remove_bundle's refcount logic.
        if refresh and existing is not None:
            planned = {(c.kind, c.id) for c in plan.components}
            still_needed = components_still_needed(
                records, exclude_bundle_id=plan.bundle_id
            )
            for component in existing.contributed_components:
                key = (component.kind, component.id)
                if key in planned:
                    continue
                if key in still_needed:
                    continue
                if installer.is_installed(project_root, component):
                    installer.remove(project_root, component)
                    result.uninstalled.append(component)
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
        components=contributed,
        # Preserve the original install time across refresh/update so
        # ``bundle list`` keeps reporting when the bundle was first installed.
        installed_at=existing.installed_at if existing is not None else None,
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
    remove_attempted = False

    try:
        for component in target.contributed_components:
            key = (component.kind, component.id)
            if key in still_needed:
                result.skipped.append(component)
                continue
            if installer.is_installed(project_root, component):
                remove_attempted = True
                installer.remove(project_root, component)
                result.uninstalled.append(component)
        save_records(project_root, remove_record(records, bundle_id))
    except Exception as exc:  # noqa: BLE001
        if result.uninstalled:
            detail = (
                f"{len(result.uninstalled)} component(s) were already removed "
                "before this failure; the bundle record was left unchanged, "
                "so the project may be partially uninstalled."
            )
        elif remove_attempted:
            detail = (
                "No components were removed, but the failing component may "
                "have made partial changes before raising, so the project "
                "may be partially uninstalled."
            )
        else:
            detail = (
                "No components were removed and no removal was attempted; "
                "the bundle record was left unchanged."
            )
        raise BundlerError(
            f"Failed to remove bundle '{bundle_id}': {exc}. {detail}"
        ) from exc

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
