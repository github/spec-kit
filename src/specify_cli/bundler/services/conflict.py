"""Conflict detection across the installed-bundle stack.

The single cross-bundle conflict point is the active integration (FR-019).
Component-level overlaps (same preset id at different priorities, etc.) are
resolved by the existing primitive machinery's own precedence rules, so the
bundler only needs to guard the integration invariant and surface informational
overlaps.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..models.manifest import BundleManifest
from ..models.records import InstalledBundleRecord


@dataclass
class ConflictReport:
    integration_clash: str | None = None  # message when a hard clash exists
    overlaps: list[str] = field(default_factory=list)  # components already provided

    @property
    def has_blocking_conflict(self) -> bool:
        return self.integration_clash is not None


def detect_conflicts(
    manifest: BundleManifest,
    active_integration: str | None,
    installed: list[InstalledBundleRecord],
) -> ConflictReport:
    report = ConflictReport()

    if manifest.integration is not None and active_integration:
        if manifest.integration.id != active_integration:
            report.integration_clash = (
                f"Bundle targets integration '{manifest.integration.id}' but the "
                f"project's active integration is '{active_integration}'."
            )

    already: dict[tuple[str, str], str] = {}
    for record in installed:
        for component in record.contributed_components:
            already[(component.kind, component.id)] = record.bundle_id

    for component in manifest.components:
        owner = already.get((component.kind, component.id))
        if owner and owner != manifest.bundle.id:
            report.overlaps.append(
                f"{component.kind[:-1]} '{component.id}' is already provided by "
                f"bundle '{owner}'."
            )

    return report
