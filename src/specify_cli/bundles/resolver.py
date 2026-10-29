"""Resolver: expand a bundle manifest into a concrete, ordered install plan.

The plan the resolver produces is the single source of truth shared by
``info`` (preview) and ``install`` (execution) so the two never diverge
(SC-002 transparency). Resolution also enforces the SpecKit version gate
(FR-016) and the integration-compatibility check (FR-019).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import BundlerError
from .versioning import satisfies
from .expansion import ExpandedManifest, ResolvedReference, format_chain
from .manifest import BundleManifest, ComponentRef


@dataclass
class InstallPlan:
    bundle_id: str
    version: str
    role: str
    effective_integration: str | None
    components: list[ComponentRef] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    references: list[ResolvedReference] = field(default_factory=list)

    @property
    def component_count(self) -> int:
        return len(self.components)

    def grouped(self) -> dict[str, list[ComponentRef]]:
        groups: dict[str, list[ComponentRef]] = {
            "extensions": [],
            "presets": [],
            "steps": [],
            "workflows": [],
        }
        for component in self.components:
            groups.setdefault(component.kind, []).append(component)
        return groups


def resolve_install_plan(
    source: ExpandedManifest | BundleManifest,
    *,
    speckit_version: str,
    active_integration: str | None,
    integration_explicit: bool = False,
    enforce_version: bool = True,
) -> InstallPlan:
    """Expand *source* into an :class:`InstallPlan`, enforcing gates.

    Raises :class:`BundlerError` when a hard gate fails (version gate,
    integration clash). Soft issues are collected in ``plan.warnings``.

    *integration_explicit* signals that ``active_integration`` came from an
    explicit ``--integration`` override rather than project auto-detection. When
    a bundle pins an integration but the project's active integration cannot be
    determined (``active_integration is None``) and the caller did not supply an
    explicit override, resolution fails instead of silently adopting the
    bundle's required integration (FR-019 guard).
    """
    if isinstance(source, BundleManifest):
        if source.bundles:
            raise BundlerError(
                "Cannot resolve a bundle manifest with references before expansion."
            )
        expanded = ExpandedManifest.flat(source)
    else:
        expanded = source

    manifest = expanded.root
    structural = manifest.structural_errors()
    if structural:
        raise BundlerError(
            "Cannot resolve an invalid manifest:\n  - " + "\n  - ".join(structural)
        )

    # FR-016: SpecKit version gate — refuse incompatible installs.
    if enforce_version and manifest.requires.speckit_version:
        if not satisfies(speckit_version, manifest.requires.speckit_version):
            raise BundlerError(
                f"Bundle '{manifest.bundle.id}' requires Spec Kit "
                f"{manifest.requires.speckit_version}, but this project uses "
                f"{speckit_version}. Update Spec Kit or choose a compatible bundle."
            )

    # FR-019: integration-compatibility — a bundle that pins a different
    # integration than the project's active one halts (no silent change).
    #
    # A blank integration arrives as ``""``, not ``None`` — which is not a usable
    # integration id but satisfied NEITHER guard below (the first is a truthiness
    # test, the second an ``is None`` test), so a pinned bundle was silently
    # adopted: precisely the outcome this guard exists to prevent. Treat blank as
    # indeterminate, and strip first like the writer
    # (``integration_state.clean_integration_key``) so a padded value is not
    # reported as clashing with itself.
    if active_integration is not None:
        active_integration = active_integration.strip() or None
    effective_integration = active_integration
    if manifest.integration is not None:
        required = manifest.integration.id
        if active_integration and required != active_integration:
            raise BundlerError(
                f"Bundle '{manifest.bundle.id}' targets integration '{required}', "
                f"but this project's active integration is '{active_integration}'. "
                "Installing it would conflict; aborting with no changes."
            )
        if active_integration is None and not integration_explicit:
            raise BundlerError(
                f"Bundle '{manifest.bundle.id}' targets integration '{required}', "
                "but this project's active integration could not be determined "
                "(missing or unreadable .specify/integration.json). Re-run with "
                "'--integration' to confirm the target, or repair the project "
                "before installing."
            )
        effective_integration = required

    warnings: list[str] = []
    if expanded.references:
        tools: list[str] = []
        mcp: list[str] = []
        requirements_to_merge = [
            manifest.requires,
            *(reference.manifest.requires for reference in expanded.references),
        ]
        for requirements in requirements_to_merge:
            for tool in requirements.tools:
                if tool not in tools:
                    tools.append(tool)
            for server in requirements.mcp:
                if server not in mcp:
                    mcp.append(server)
    else:
        # A flat bundle is deliberately byte-compatible with the pre-reference
        # resolver: duplicate declarations remain visible in warning output.
        tools = list(manifest.requires.tools)
        mcp = list(manifest.requires.mcp)
    if tools:
        warnings.append("Requires external tools: " + ", ".join(tools))
    if mcp:
        warnings.append("Requires MCP servers: " + ", ".join(mcp))

    for reference in expanded.references:
        reference_manifest = reference.manifest
        chain = (manifest.bundle.id,) + reference.via + (reference.id,)
        if enforce_version and reference_manifest.requires.speckit_version:
            if not satisfies(
                speckit_version, reference_manifest.requires.speckit_version
            ):
                raise BundlerError(
                    f"Bundle '{reference.id}' ({format_chain(chain)}) requires "
                    f"Spec Kit {reference_manifest.requires.speckit_version}, "
                    f"but this project uses {speckit_version}. Update Spec Kit or "
                    "choose a compatible bundle."
                )

        if reference_manifest.integration is not None:
            required = reference_manifest.integration.id
            if effective_integration is None:
                warnings.append(
                    f"Bundle '{reference.id}' ({format_chain(chain)}) targets "
                    f"integration '{required}'; the project's integration could "
                    "not be determined."
                )
            elif required != effective_integration:
                warnings.append(
                    f"Bundle '{reference.id}' ({format_chain(chain)}) targets "
                    f"'{required}'; this install uses '{effective_integration}'."
                )

    warnings.extend(expanded.warnings)

    return InstallPlan(
        bundle_id=manifest.bundle.id,
        version=manifest.bundle.version,
        role=manifest.bundle.role,
        effective_integration=effective_integration,
        components=list(expanded.components),
        warnings=warnings,
        references=list(expanded.references),
    )


def load_manifest_from_dir(bundle_dir: Path) -> BundleManifest:
    """Load ``bundle.yml`` from a bundle directory."""
    manifest_path = Path(bundle_dir) / "bundle.yml"
    if not manifest_path.exists():
        raise BundlerError(f"No bundle.yml found in '{bundle_dir}'.")
    return BundleManifest.from_file(manifest_path)
