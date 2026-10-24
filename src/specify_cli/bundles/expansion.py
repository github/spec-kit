"""Expansion of bundle references into a flat, provenance-aware component plan."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from . import BundlerError
from .conflict import component_differences
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
    # One record per distinct declaring bundle whose copy agrees with
    # ``component``; the route to each is relative to the current bundle.
    declarations: tuple[ComponentOverride, ...]
    overrides: tuple[ComponentOverride, ...] = ()

    @property
    def origin(self) -> tuple[str, ...]:
        """Shortest route to a declaring bundle, for display."""
        return min(
            (declaration.origin for declaration in self.declarations),
            key=lambda origin: (len(origin), origin),
        )


@dataclass(frozen=True)
class _OverrideNotice:
    component: ComponentRef
    declaring: tuple[str, ...]
    replaced: tuple[ComponentOverride, ...]


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
    reference_keys: list[tuple[str, str]] = []
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
                f"({format_chain(chain)}); choose referencing releases that pin "
                "the same version on every route."
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
                reference_keys,
                own_keys,
                conflicts,
                chain,
            )
        for notice in child.notices:
            _append_notice(notices, _prefix_notice(notice, child_prefix))

    # Apply the current bundle's own declarations after all referenced plans.
    own_manifest_keys = [(c.kind, c.id) for c in manifest.components]
    for component in manifest.components:
        key = component.kind, component.id
        existing = candidates.get(key, [])
        entry, notice = _declare_own(component, existing)
        candidates[key] = [entry]
        if notice is not None:
            _append_notice(notices, notice)

    if conflicts:
        raise BundlerError("Bundle component conflicts:\n" + "\n".join(conflicts))

    ordered = [k for k in reference_keys if k not in own_keys] + own_manifest_keys
    entries = tuple(candidates[key][0] for key in _stable_keys(ordered))
    result = _Subplan(
        entries=entries,
        reference_paths=dict(reference_paths),
        longest_path=longest_path,
        notices=tuple(notices),
    )
    state.subplans[manifest.bundle.id] = result
    return result


def _entry_for(
    component: ComponentRef,
    declarations: Iterable[ComponentOverride],
    overrides: Iterable[ComponentOverride] = (),
) -> _Entry:
    """The only way to build an ``_Entry``; applies I3 to both histories.

    This is the single rule for what counts as one declaration: the component
    and the bundle that declared it. The route to it is display-only, so only
    the shortest chain is kept, with ties broken on the chain itself so the
    result does not depend on merge order. Routes to the same declaration
    collapse (otherwise a shared graph grows exponentially), while distinct
    declaring bundles stay separate records. It serves both the declarations
    behind an entry and the override history discarded by a parent.
    """
    return _Entry(
        component,
        _merge_declarations(declarations),
        _merge_declarations(overrides),
    )


def _merge_declarations(
    *groups: Iterable[ComponentOverride],
) -> tuple[ComponentOverride, ...]:
    """Merge declaration records to one per component and declaring bundle."""
    best: dict[tuple[ComponentRef, tuple[str, ...]], ComponentOverride] = {}
    for group in groups:
        for declaration in group:
            key = (declaration.component, declaration.origin[-1:])
            current = best.get(key)
            if current is None or (len(declaration.origin), declaration.origin) < (
                len(current.origin),
                current.origin,
            ):
                best[key] = declaration
    return tuple(best.values())


def _merge_candidate(
    entry: _Entry,
    candidates: dict[tuple[str, str], list[_Entry]],
    reference_keys: list[tuple[str, str]],
    own_keys: set[tuple[str, str]],
    conflicts: list[str],
    declaring_chain: tuple[str, ...],
) -> None:
    key = entry.component.kind, entry.component.id
    existing = candidates.get(key)
    if existing is None:
        candidates[key] = [entry]
        reference_keys.append(key)
        return

    differences = [
        component_differences(previous.component, entry.component)
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

    # A shared dependency can arrive through multiple routes, and distinct
    # bundles can declare the same component. Merge an agreeing copy into the
    # existing candidate, keeping each distinct declaring bundle so a later
    # override can name all of them. Preserve the first component spelling.
    for index, fields in enumerate(differences):
        if not fields:
            previous = existing[index]
            existing[index] = _entry_for(
                previous.component,
                declarations=(*previous.declarations, *entry.declarations),
                overrides=(*previous.overrides, *entry.overrides),
            )
            return

    if key in own_keys:
        existing.append(entry)
        return


def _declare_own(
    component: ComponentRef, existing: list[_Entry]
) -> tuple[_Entry, _OverrideNotice | None]:
    """Entry for a bundle's own declaration over any referenced copies.

    Every declaration of a differing referenced copy is discarded and recorded,
    one per declaring bundle. Agreeing copies are not overrides.
    """
    inherited = tuple(ov for entry in existing for ov in entry.overrides)
    replaced = tuple(
        declaration
        for entry in existing
        if component_differences(entry.component, component)
        for declaration in entry.declarations
    )
    agreeing = tuple(
        declaration
        for entry in existing
        if not component_differences(entry.component, component)
        for declaration in entry.declarations
    )
    entry = _entry_for(
        component,
        declarations=(ComponentOverride(component, ()), *agreeing),
        overrides=(*inherited, *replaced),
    )
    notice = _OverrideNotice(component, (), replaced) if replaced else None
    return entry, notice


def _stable_keys(ordered: list[tuple[str, str]]) -> list[tuple[str, str]]:
    kind_order = {kind: index for index, kind in enumerate(COMPONENT_KINDS)}
    return sorted(ordered, key=lambda key: kind_order.get(key[0], len(kind_order)))


def _prefix_declarations(
    declarations: tuple[ComponentOverride, ...], prefix: tuple[str, ...]
) -> tuple[ComponentOverride, ...]:
    return tuple(
        ComponentOverride(declaration.component, prefix + declaration.origin)
        for declaration in declarations
    )


def _prefix_entry(entry: _Entry, prefix: tuple[str, ...]) -> _Entry:
    return _entry_for(
        entry.component,
        declarations=_prefix_declarations(entry.declarations, prefix),
        overrides=_prefix_declarations(entry.overrides, prefix),
    )


def _prefix_notice(notice: _OverrideNotice, prefix: tuple[str, ...]) -> _OverrideNotice:
    return _OverrideNotice(
        notice.component,
        prefix + notice.declaring,
        _prefix_declarations(notice.replaced, prefix),
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
    fields = component_differences(a.component, b.component)
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
            component_differences(replaced.component, notice.component)
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
