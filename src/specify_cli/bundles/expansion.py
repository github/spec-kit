"""Expansion of bundle references into a flat, provenance-aware component plan."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from . import BundlerError
from .conflict import component_setting_differences
from .manifest import COMPONENT_KINDS, BundleManifest, BundleRef, ComponentRef
from .versioning import same_version

MAX_REFERENCE_DEPTH = 10
MAX_REFERENCED_BUNDLES = 50


@dataclass(frozen=True)
class LoadedBundle:
    manifest: BundleManifest
    source_id: str
    install_allowed: bool
    verified: bool = False


class BundleLoader(Protocol):
    def load(self, ref: BundleRef, chain: tuple[str, ...]) -> LoadedBundle: ...


@dataclass(frozen=True)
class ResolvedReference:
    id: str
    version: str
    source_id: str
    install_allowed: bool
    via: tuple[str, ...]
    manifest: BundleManifest
    verified: bool = False


class SourceMismatchError(BundlerError):
    """A bundle reference does not match the winning catalog source."""

    def __init__(
        self, ref: BundleRef, actual_source: str, chain: tuple[str, ...]
    ) -> None:
        self.reference = ref
        self.actual_source = actual_source
        self.chain = chain
        super().__init__(
            f"Bundle reference {ref.id} ({format_chain(chain)}) requires source "
            f"'{ref.source}', but the winning catalog is '{actual_source}'."
        )


@dataclass(frozen=True)
class ComponentOverride:
    component: ComponentRef
    origin: tuple[str, ...]


@dataclass(frozen=True)
class ComponentOrigin:
    origin: tuple[str, ...]
    overrides: tuple[ComponentOverride, ...] = ()


@dataclass
class ExpandedManifest:
    root: BundleManifest
    components: list[ComponentRef]
    origins: dict[tuple[str, str], ComponentOrigin]
    references: list[ResolvedReference]
    warnings: list[str]

    @classmethod
    def flat(cls, manifest: BundleManifest) -> "ExpandedManifest":
        return cls(
            root=manifest,
            components=list(manifest.components),
            origins={
                (component.kind, component.id): ComponentOrigin(())
                for component in manifest.components
            },
            references=[],
            warnings=[],
        )

    @property
    def has_references(self) -> bool:
        return bool(self.references)


@dataclass(frozen=True)
class _Entry:
    component: ComponentRef
    origin: tuple[str, ...]
    overrides: tuple[ComponentOverride, ...] = ()


@dataclass(frozen=True)
class _OverrideNotice:
    component: ComponentRef
    declaring: tuple[str, ...]
    replaced: tuple[_Entry, ...]


@dataclass(frozen=True)
class _Subplan:
    entries: tuple[_Entry, ...]
    reference_paths: dict[str, tuple[str, ...]]
    longest_path: tuple[str, ...]
    notices: tuple[_OverrideNotice, ...]


class _ExpansionState:
    def __init__(self, loader: BundleLoader) -> None:
        self.loader = loader
        self.loaded: dict[str, LoadedBundle] = {}
        self.subplans: dict[str, _Subplan] = {}
        self.versions: dict[str, tuple[str, tuple[str, ...]]] = {}
        self.references: list[ResolvedReference] = []
        self._reference_indexes: dict[str, int] = {}
        self.distinct_ids: set[str] = set()

    def register_reference(
        self, ref: BundleRef, loaded: LoadedBundle, chain: tuple[str, ...]
    ) -> None:
        via = chain[1:]
        reference = ResolvedReference(
            id=ref.id,
            version=ref.version or "",
            source_id=loaded.source_id,
            install_allowed=loaded.install_allowed,
            via=via,
            manifest=loaded.manifest,
            verified=loaded.verified,
        )
        index = self._reference_indexes.get(ref.id)
        if index is None:
            self._reference_indexes[ref.id] = len(self.references)
            self.references.append(reference)
        else:
            previous = self.references[index]
            if len(via) < len(previous.via):
                self.references[index] = reference

    def shorten_cached_references(
        self, subplan: _Subplan, chain: tuple[str, ...]
    ) -> None:
        """Apply a newly discovered shorter route to cached reference metadata."""
        for reference_id, path in subplan.reference_paths.items():
            index = self._reference_indexes.get(reference_id)
            if index is None:
                continue
            previous = self.references[index]
            via = chain[1:] + path[:-1]
            if len(via) < len(previous.via):
                self.references[index] = ResolvedReference(
                    id=previous.id,
                    version=previous.version,
                    source_id=previous.source_id,
                    install_allowed=previous.install_allowed,
                    via=via,
                    manifest=previous.manifest,
                    verified=previous.verified,
                )


def format_chain(chain: tuple[str, ...]) -> str:
    return " → ".join(chain)


def expand_manifest(root: BundleManifest, loader: BundleLoader) -> ExpandedManifest:
    """Expand *root* using *loader*, without performing any I/O itself."""
    if not root.bundles:
        return ExpandedManifest.flat(root)

    state = _ExpansionState(loader)
    subplan = _expand(root, (root.bundle.id,), state)
    components = [entry.component for entry in subplan.entries]
    origins = {
        (entry.component.kind, entry.component.id): ComponentOrigin(
            entry.origin, entry.overrides
        )
        for entry in subplan.entries
    }
    warnings = _format_warnings(root, subplan.notices)
    return ExpandedManifest(root, components, origins, state.references, warnings)


def _expand(
    manifest: BundleManifest, chain: tuple[str, ...], state: _ExpansionState
) -> _Subplan:
    """Compute one completed subplan for a bundle (never cache partial results)."""
    cached = state.subplans.get(manifest.bundle.id)
    if cached is not None:
        return cached

    candidates: dict[tuple[str, str], list[_Entry]] = {}
    ordered: list[tuple[str, str]] = []
    reference_paths: dict[str, tuple[str, ...]] = {}
    notices: list[_OverrideNotice] = []
    conflicts: list[str] = []
    longest_path: tuple[str, ...] = ()

    own_keys = {(component.kind, component.id) for component in manifest.components}

    for ref in manifest.bundles:
        if len(chain) > MAX_REFERENCE_DEPTH:
            raise BundlerError(
                f"Bundle reference depth exceeds {MAX_REFERENCE_DEPTH}: "
                f"{format_chain(chain + (ref.id,))}."
            )
        if ref.id in chain:
            raise BundlerError(
                f"Bundle reference cycle: {format_chain(chain + (ref.id,))}"
            )

        old_version = state.versions.get(ref.id)
        if old_version is not None and not same_version(
            old_version[0], ref.version or ""
        ):
            raise BundlerError(
                f"Bundle '{ref.id}' is referenced at versions {old_version[0]} "
                f"({format_chain(old_version[1])}) and {ref.version or '<unpinned>'} "
                f"({format_chain(chain)})."
            )
        if old_version is None:
            state.versions[ref.id] = (ref.version or "", chain)

        if ref.id not in state.distinct_ids:
            if len(state.distinct_ids) >= MAX_REFERENCED_BUNDLES:
                raise BundlerError(
                    f"Bundle reference expansion exceeds the limit of "
                    f"{MAX_REFERENCED_BUNDLES} distinct bundles "
                    f"({format_chain(chain + (ref.id,))})."
                )
            state.distinct_ids.add(ref.id)

        loaded = state.loaded.get(ref.id)
        if loaded is None:
            try:
                loaded = state.loader.load(ref, chain)
            except SourceMismatchError:
                # The loader has already included the reference chain and the
                # winning catalog in this diagnostic. Do not add a second
                # "Cannot resolve ..." wrapper.
                raise
            except BundlerError as exc:
                raise BundlerError(
                    f"Cannot resolve bundle reference "
                    f"{ref.id}@{ref.version or '<unpinned>'} "
                    f"({format_chain(chain)}): {exc}"
                ) from exc
            if loaded.manifest.bundle.id != ref.id:
                raise BundlerError(
                    f"Bundle reference {ref.id} loaded manifest for "
                    f"'{loaded.manifest.bundle.id}'."
                )
            if not same_version(loaded.manifest.bundle.version, ref.version or ""):
                raise BundlerError(
                    f"Bundle reference {ref.id}@{ref.version or '<unpinned>'} "
                    f"loaded manifest version {loaded.manifest.bundle.version}."
                )
            state.loaded[ref.id] = loaded

        if ref.source is not None and ref.source != loaded.source_id:
            raise _source_mismatch(ref, loaded, chain)

        state.register_reference(ref, loaded, chain)
        child = state.subplans.get(ref.id)
        if child is None:
            child = _expand(loaded.manifest, chain + (ref.id,), state)
        # longest_path excludes the child itself. This check is deliberately
        # repeated for cache hits: a shallow first route cannot evade a limit.
        if len(chain) + len(child.longest_path) > MAX_REFERENCE_DEPTH:
            raise BundlerError(
                f"Bundle reference depth exceeds {MAX_REFERENCE_DEPTH}: "
                f"{format_chain(chain + (ref.id,) + child.longest_path)}."
            )
        state.shorten_cached_references(child, chain + (ref.id,))

        child_prefix = (ref.id,)
        if len(child_prefix + child.longest_path) > len(longest_path):
            longest_path = child_prefix + child.longest_path
        _shortest_path(reference_paths, ref.id, child_prefix)
        for descendant, path in child.reference_paths.items():
            _shortest_path(reference_paths, descendant, child_prefix + path)
        for child_entry in child.entries:
            entry = _prefix_entry(child_entry, child_prefix)
            _merge_candidate(
                entry,
                candidates,
                ordered,
                own_keys,
                conflicts,
                chain,
            )
        for notice in child.notices:
            _append_notice(notices, _prefix_notice(notice, child_prefix))

    # Apply the current bundle's own declarations after all referenced plans.
    for component in manifest.components:
        key = component.kind, component.id
        own_entry = _Entry(component, ())
        existing = candidates.get(key, [])
        if not existing:
            candidates[key] = [own_entry]
            ordered.append(key)
            continue

        replaced: list[_Entry] = []
        inherited_overrides: list[ComponentOverride] = []
        for entry in existing:
            inherited_overrides.extend(entry.overrides)
            if _component_differences(entry.component, component):
                replaced.append(entry)
        # Removing and re-adding gives an override the position of the own
        # declaration, rather than the first referenced occurrence.
        ordered.remove(key)
        inherited = _merge_overrides(inherited_overrides)
        candidates[key] = [_Entry(component, (), inherited)]
        ordered.append(key)
        if replaced:
            direct_overrides = tuple(
                ComponentOverride(entry.component, entry.origin) for entry in replaced
            )
            candidates[key] = [
                _Entry(component, (), _merge_overrides(inherited, direct_overrides))
            ]
            _append_notice(
                notices,
                _OverrideNotice(component, (), tuple(replaced)),
            )

    if conflicts:
        raise BundlerError("Bundle component conflicts:\n" + "\n".join(conflicts))

    entries = tuple(candidates[key][0] for key in _stable_keys(ordered))
    result = _Subplan(
        entries=entries,
        reference_paths=dict(reference_paths),
        longest_path=longest_path,
        notices=tuple(notices),
    )
    state.subplans[manifest.bundle.id] = result
    return result


def _merge_candidate(
    entry: _Entry,
    candidates: dict[tuple[str, str], list[_Entry]],
    ordered: list[tuple[str, str]],
    own_keys: set[tuple[str, str]],
    conflicts: list[str],
    declaring_chain: tuple[str, ...],
) -> None:
    key = entry.component.kind, entry.component.id
    existing = candidates.get(key)
    if existing is None:
        candidates[key] = [entry]
        ordered.append(key)
        return

    differences = [
        _component_differences(previous.component, entry.component)
        for previous in existing
    ]
    if any(differences) and key not in own_keys:
        # Compare each newly encountered spelling to the first spelling. This
        # reports every differing field while keeping one diagnostic per pair.
        previous = existing[
            next(index for index, fields in enumerate(differences) if fields)
        ]
        conflicts.append(_format_conflict(previous, entry, declaring_chain))
        return

    # A shared dependency can arrive through multiple routes. Merge an
    # agreeing copy into the existing candidate instead of retaining a
    # duplicate override entry. Preserve the first component spelling and the
    # shorter provenance, while keeping distinct override histories from both
    # routes for `bundle info`.
    for index, fields in enumerate(differences):
        if not fields:
            previous = existing[index]
            overrides = _merge_overrides(previous.overrides, entry.overrides)
            origin = (
                entry.origin
                if len(entry.origin) < len(previous.origin)
                else previous.origin
            )
            existing[index] = _Entry(previous.component, origin, overrides)
            return

    if key in own_keys:
        existing.append(entry)
        return


def _merge_overrides(
    *histories: tuple[ComponentOverride, ...] | list[ComponentOverride],
) -> tuple[ComponentOverride, ...]:
    """Merge override histories to one record per discarded declaration.

    The declaration is identified by the discarded component and the bundle
    that declared it; the route to it is display-only, so only the shortest
    chain is kept. Without this, every route through a shared graph would add
    its own copy and the history would grow exponentially.
    """
    best: dict[tuple[ComponentRef, str], ComponentOverride] = {}
    for history in histories:
        for override in history:
            key = (override.component, override.origin[-1])
            current = best.get(key)
            if current is None or (len(override.origin), override.origin) < (
                len(current.origin),
                current.origin,
            ):
                best[key] = override
    return tuple(best.values())


def _stable_keys(ordered: list[tuple[str, str]]) -> list[tuple[str, str]]:
    kind_order = {kind: index for index, kind in enumerate(COMPONENT_KINDS)}
    return sorted(ordered, key=lambda key: kind_order.get(key[0], len(kind_order)))


def _prefix_entry(entry: _Entry, prefix: tuple[str, ...]) -> _Entry:
    return _Entry(
        entry.component,
        prefix + entry.origin,
        tuple(
            ComponentOverride(override.component, prefix + override.origin)
            for override in entry.overrides
        ),
    )


def _prefix_notice(notice: _OverrideNotice, prefix: tuple[str, ...]) -> _OverrideNotice:
    return _OverrideNotice(
        notice.component,
        prefix + notice.declaring,
        tuple(
            _Entry(entry.component, prefix + entry.origin, entry.overrides)
            for entry in notice.replaced
        ),
    )


def _notice_key(notice: _OverrideNotice) -> tuple[str | None, str, str]:
    return (
        notice.declaring[-1] if notice.declaring else None,
        notice.component.kind,
        notice.component.id,
    )


def _append_notice(notices: list[_OverrideNotice], notice: _OverrideNotice) -> None:
    key = _notice_key(notice)
    for index, previous in enumerate(notices):
        if _notice_key(previous) == key:
            if len(notice.declaring) < len(previous.declaring):
                notices[index] = notice
            return
    notices.append(notice)


def _shortest_path(
    paths: dict[str, tuple[str, ...]], key: str, path: tuple[str, ...]
) -> None:
    old = paths.get(key)
    if old is None or len(path) < len(old):
        paths[key] = path


def _component_differences(a: ComponentRef, b: ComponentRef) -> list[str]:
    different: list[str] = []
    if a.version is None or b.version is None:
        if a.version != b.version:
            different.append("version")
    elif not same_version(a.version, b.version):
        different.append("version")
    different.extend(component_setting_differences(a, b))
    return different


def _source_mismatch(
    ref: BundleRef, loaded: LoadedBundle, chain: tuple[str, ...]
) -> SourceMismatchError:
    return SourceMismatchError(ref, loaded.source_id, chain)


def _display_value(field: str, value: object) -> str:
    if value is None:
        return "<unpinned>" if field == "version" else "<unset>"
    return str(value)


def _field_text(component: ComponentRef, field: str) -> str:
    return f"{field} {_display_value(field, getattr(component, field))}"


def _component_name(component: ComponentRef) -> str:
    return f"{component.kind[:-1]} '{component.id}'"


def _format_conflict(
    a: _Entry, b: _Entry, declaring_chain: tuple[str, ...]
) -> str:
    fields = _component_differences(a.component, b.component)
    left = "; ".join(_field_text(a.component, field) for field in fields)
    right = "; ".join(_field_text(b.component, field) for field in fields)
    left_chain = format_chain(declaring_chain + a.origin)
    right_chain = format_chain(declaring_chain + b.origin)
    return (
        f"{_component_name(a.component)}: {left} ({left_chain}) vs {right} "
        f"({right_chain}); declare '{a.component.id}' in "
        f"'{declaring_chain[-1]}' to choose."
    )


def _format_warnings(
    root: BundleManifest, notices: tuple[_OverrideNotice, ...]
) -> list[str]:
    warnings: list[str] = []
    for notice in notices:
        own_chain = format_chain((root.bundle.id,) + notice.declaring)
        fields_by_entry: list[str] = []
        differences_by_entry = [
            _component_differences(replaced.component, notice.component)
            for replaced in notice.replaced
        ]
        for replaced, fields in zip(notice.replaced, differences_by_entry):
            old_chain = format_chain((root.bundle.id,) + replaced.origin)
            fields_by_entry.append(
                " and ".join(
                    f"{field} "
                    f"{_display_value(field, getattr(replaced.component, field))} "
                    f"from {old_chain}"
                    for field in fields
                )
            )
        fields = list(
            dict.fromkeys(
                field
                for differences in differences_by_entry
                for field in differences
            )
        )
        own_fields = " and ".join(
            f"{field} {_display_value(field, getattr(notice.component, field))}"
            for field in fields
        )
        warnings.append(
            f"{_component_name(notice.component)} {own_fields} ({own_chain}) "
            f"overrides {' and '.join(fields_by_entry)}."
        )
    return warnings


def discovery_only_messages(expanded: ExpandedManifest) -> list[str]:
    """Return install-policy errors for references from discovery-only sources."""
    messages: list[str] = []
    for reference in expanded.references:
        if reference.install_allowed:
            continue
        chain = (expanded.root.bundle.id,) + reference.via + (reference.id,)
        messages.append(
            f"Bundle '{reference.id}' ({format_chain(chain)}) resolves only from "
            f"discovery-only source '{reference.source_id}'; it cannot be "
            "installed from there."
        )
    return messages


def require_installable(expanded: ExpandedManifest) -> None:
    messages = discovery_only_messages(expanded)
    if messages:
        raise BundlerError(messages[0])
