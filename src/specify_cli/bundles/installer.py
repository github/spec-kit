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

from . import BundlerError
from .conflict import detect_conflicts
from .manifest import BundleManifest, ComponentRef
from .records import (
    InstalledBundleRecord,
    components_still_needed,
    find_record,
    load_records,
    remove_record,
    save_records,
    transfer_contributions,
    upsert_record,
)
from .resolver import InstallPlan
from .versioning import same_version


class PrimitiveInstaller(Protocol):
    """Adapter over the existing Spec Kit primitive install/remove machinery."""

    def is_installed(self, project_root: Path, component: ComponentRef) -> bool: ...

    def installed_version(
        self, project_root: Path, component: ComponentRef
    ) -> str | None: ...

    def validate_source(self, project_root: Path, component: ComponentRef) -> None: ...

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
        # `uninstalled` is a mutating outcome too: a `bundle update` whose new
        # manifest drops components (removing them via the refresh path) with no
        # new install/refresh must still report changed=True, not a no-op.
        return bool(self.installed or self.refreshed or self.uninstalled)


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

    Already-installed components must match their pins before they can be
    skipped. A refresh may repair drift in components owned exclusively by
    this bundle, but cannot change a version required by another bundle or an
    independently installed component. Changes to owned component metadata
    still require refresh. Other bundles' source and preset settings cannot be
    changed by sharing or refreshing a component.
    """
    records = load_records(project_root)

    if manifest is not None:
        report = detect_conflicts(manifest, plan.effective_integration, records)
        if report.has_blocking_conflict:
            raise BundlerError(
                "; ".join(
                    [*([report.integration_clash] if report.integration_clash else []),
                     *report.version_clashes]
                )
            )

    result = InstallResult(bundle_id=plan.bundle_id)
    existing = find_record(records, plan.bundle_id)
    if (
        existing is not None
        and not refresh
        and (
            existing.version != plan.version
            or not set(existing.contributed_components).issubset(plan.components)
        )
    ):
        raise BundlerError(
            f"Bundle '{plan.bundle_id}' is already installed at version "
            f"{existing.version}, but the requested manifest changes the bundle "
            "version or changes/removes owned components. "
            "Use 'specify bundle update <id>' for a catalog bundle, or "
            "'specify bundle install <path> --refresh' for a local source, "
            "to refresh owned components before advancing the installed record."
        )

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
    other_pins: dict[tuple[str, str], set[str]] = {}
    other_requirements: dict[tuple[str, str], list[tuple[str, ComponentRef]]] = {}
    for record in records:
        if record.bundle_id == plan.bundle_id:
            continue
        for component in record.required_components:
            key = component.kind, component.id
            other_requirements.setdefault(key, []).append((record.bundle_id, component))
            if component.version:
                other_pins.setdefault(key, set()).add(component.version)
    contributed: list[ComponentRef] = []
    done: list[ComponentRef] = []
    try:
        _check_installed_pins(
            project_root, plan, installer, prior_ours, other_tracked,
            other_pins, other_requirements, refresh=refresh,
        )
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
    except Exception as exc:
        _rollback(project_root, installer, done)
        raise BundlerError(
            f"Failed to install bundle '{plan.bundle_id}': {exc}. "
            "No changes were recorded."
        ) from exc

    record = InstalledBundleRecord.create(
        bundle_id=plan.bundle_id,
        version=plan.version,
        components=contributed,
        required_components=plan.components,
        # Preserve the original install time across refresh/update so
        # ``bundle list`` keeps reporting when the bundle was first installed.
        installed_at=existing.installed_at if existing is not None else None,
    )
    updated = upsert_record(records, record)
    if refresh and existing is not None:
        planned = {(c.kind, c.id) for c in plan.components}
        updated = transfer_contributions(
            updated,
            [
                component for component in existing.contributed_components
                if (component.kind, component.id) not in planned
            ],
        )
    save_records(project_root, updated)
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
        remaining = transfer_contributions(
            remove_record(records, bundle_id), target.contributed_components
        )
        save_records(project_root, remaining)
    except Exception as exc:
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


def _check_installed_pins(
    project_root: Path,
    plan: InstallPlan,
    installer: PrimitiveInstaller,
    prior_ours: set[tuple[str, str]],
    other_tracked: set[tuple[str, str]],
    other_pins: dict[tuple[str, str], set[str]],
    other_requirements: dict[tuple[str, str], list[tuple[str, ComponentRef]]],
    *,
    refresh: bool,
) -> None:
    """Check installed pins and other bundles' requirements before mutation."""
    mismatches = []
    for component in plan.components:
        key = component.kind, component.id
        for bundle_id, required in other_requirements.get(key, []):
            different = []
            if component.source != required.source:
                different.append("source")
            if component.kind == "presets":
                if component.priority != required.priority:
                    different.append("priority")
                if component.strategy != required.strategy:
                    different.append("strategy")
            if different:
                raise BundlerError(
                    f"Cannot install or refresh shared {component.kind[:-1]} "
                    f"'{component.id}': bundle '{bundle_id}' requires different "
                    f"{', '.join(different)}. Shared components must agree on "
                    "install-affecting requirements."
                )
        if component.source:
            installer.validate_source(project_root, component)
        if refresh and not component.version and key in other_tracked:
            raise BundlerError(
                f"Cannot refresh unpinned shared {component.kind[:-1]} "
                f"'{component.id}': another bundle may require its installed "
                "version. Pin this component before refreshing."
            )
        if not component.version:
            pins = other_pins.get(key)
            if pins:
                installed = installer.is_installed(project_root, component)
                actual = (
                    installer.installed_version(project_root, component)
                    if installed else None
                )
                if (
                    (refresh and key in prior_ours)
                    or not actual
                    or any(not same_version(actual, pin) for pin in pins)
                ):
                    raise BundlerError(
                        f"Cannot install or refresh unpinned {component.kind[:-1]} "
                        f"'{component.id}': another bundle requires version "
                        f"{', '.join(sorted(pins))}. Pin this component to a "
                        "compatible version before installing or refreshing."
                    )
            continue
        if not installer.is_installed(project_root, component):
            continue
        actual = installer.installed_version(project_root, component)
        if actual and same_version(actual, component.version):
            continue
        if refresh and key in prior_ours and key not in other_tracked:
            continue
        pinned = f"{component.kind[:-1]} '{component.id}' to {component.version}"
        if not actual:
            mismatches.append(f"{pinned}, but its installed version is unknown")
        else:
            mismatches.append(f"{pinned}, but {actual} is installed")
    if mismatches:
        raise BundlerError(
            f"Bundle '{plan.bundle_id}' pins {'; '.join(mismatches)}. Only one "
            "version can be installed per ID; independently installed and "
            "other bundles' components cannot be replaced by this bundle."
        )


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
        except Exception:  # noqa: BLE001, S112 - rollback cannot mask the original failure
            continue
