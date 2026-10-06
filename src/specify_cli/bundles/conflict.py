"""Conflict detection across the installed-bundle stack."""
from __future__ import annotations

from dataclasses import dataclass, field

from .manifest import BundleManifest
from .records import InstalledBundleRecord
from .versioning import same_version


@dataclass
class ConflictReport:
    integration_clash: str | None = None  # message when a hard clash exists
    version_clashes: list[str] = field(default_factory=list)
    overlaps: list[str] = field(default_factory=list)  # components already provided

    @property
    def has_blocking_conflict(self) -> bool:
        return self.integration_clash is not None or bool(self.version_clashes)


def detect_conflicts(
    manifest: BundleManifest,
    active_integration: str | None,
    installed: list[InstalledBundleRecord],
) -> ConflictReport:
    report = ConflictReport()

    if (
        manifest.integration is not None
        and active_integration
        and manifest.integration.id != active_integration
    ):
        report.integration_clash = (
            f"Bundle targets integration '{manifest.integration.id}' but the "
            f"project's active integration is '{active_integration}'."
        )

    already: dict[tuple[str, str], list[tuple[str, str | None]]] = {}
    for record in installed:
        for component in record.contributed_components:
            already.setdefault((component.kind, component.id), []).append(
                (record.bundle_id, component.version)
            )

    for component in manifest.components:
        for owner, version in already.get((component.kind, component.id), []):
            if owner == manifest.bundle.id:
                continue
            if component.version and (
                not version or not same_version(component.version, version)
            ):
                report.version_clashes.append(
                    f"{component.kind[:-1]} '{component.id}' requires version "
                    f"{component.version}, but bundle '{owner}' already requires "
                    f"version {version or '<unknown>'}. Only one version can be "
                    "installed per ID."
                )
            else:
                report.overlaps.append(
                    f"{component.kind[:-1]} '{component.id}' is already provided by "
                    f"bundle '{owner}'."
                )

    return report
