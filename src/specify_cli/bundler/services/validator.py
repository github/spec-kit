"""Validator: structural + reference validation for a bundle manifest.

``specify bundle validate`` reports whether a manifest is well-formed and all
component references are resolvable. Structural checks come from the manifest
model; reference resolution is optional (requires a resolver callback) so the
command can run fully offline against pinned/local references.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .. import BundlerError
from ..lib.versioning import parse_constraint
from ..models.manifest import BundleManifest, ComponentRef

# A reference checker returns None when resolvable, or an error string.
ReferenceChecker = Callable[[ComponentRef], str | None]


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def merge(self, other: "ValidationReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def validate_manifest(
    manifest: BundleManifest,
    reference_checker: ReferenceChecker | None = None,
) -> ValidationReport:
    report = ValidationReport()

    report.errors.extend(manifest.structural_errors())

    if manifest.requires.speckit_version:
        try:
            parse_constraint(manifest.requires.speckit_version)
        except BundlerError as exc:
            report.errors.append(
                f"requires.speckit_version '{manifest.requires.speckit_version}' "
                f"is not a valid constraint: {exc}"
            )

    if reference_checker is not None:
        for component in manifest.components:
            problem = reference_checker(component)
            if problem:
                report.errors.append(
                    f"Unresolved reference {component.label()}: {problem}"
                )

    return report
