"""Conflict detection across the installed-bundle stack."""
from __future__ import annotations

from dataclasses import dataclass, field

from .manifest import BundleManifest, ComponentRef
from .primitives import DEFAULT_PRIORITY
from .records import InstalledBundleRecord
from .versioning import same_version


@dataclass
class ConflictReport:
    integration_clash: str | None = None  # message when a hard clash exists
    version_clashes: list[str] = field(default_factory=list)
    overlaps: list[str] = field(default_factory=list)  # components already required

    @property
    def has_blocking_conflict(self) -> bool:
        return self.integration_clash is not None or bool(self.version_clashes)


def effective_setting(
    kind: str, field: str, value, *, extension_priority: bool = True
):
    """Return *value* as it affects install for a component of *kind*.

    ``priority`` applies to presets and, when *extension_priority* is true,
    extensions, where an omitted value installs as ``DEFAULT_PRIORITY``.
    ``strategy`` applies to presets only. Settings that do not apply return
    ``None``; ``source`` always applies.
    """
    if field == "priority":
        if kind == "extensions" and extension_priority:
            return DEFAULT_PRIORITY if value is None else value
        return value if kind == "presets" else None
    if field == "strategy":
        return value if kind == "presets" else None
    return value


def component_setting_differences(
    a: ComponentRef, b: ComponentRef, *, extension_priority: bool = True
) -> list[str]:
    """Return install-affecting setting fields that differ between two refs.

    Compares ``source``, ``priority`` and ``strategy`` through
    :func:`effective_setting`. Versions are intentionally not compared.
    """
    return [
        field
        for field in ("source", "priority", "strategy")
        if effective_setting(
            a.kind, field, getattr(a, field), extension_priority=extension_priority
        )
        != effective_setting(
            b.kind, field, getattr(b, field), extension_priority=extension_priority
        )
    ]


def detect_conflicts(
    manifest: BundleManifest,
    active_integration: str | None,
    installed: list[InstalledBundleRecord],
    components: list[ComponentRef] | None = None,
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
        for component in record.required_components:
            already.setdefault((component.kind, component.id), []).append(
                (record.bundle_id, component.version)
            )

    selected_components = manifest.components if components is None else components
    for component in selected_components:
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
                    f"{component.kind[:-1]} '{component.id}' is already required by "
                    f"bundle '{owner}'."
                )

    return report
