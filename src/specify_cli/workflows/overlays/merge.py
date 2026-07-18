"""Pure-function merge engine for workflow step lists."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .schema import VALID_OPERATIONS, Overlay, OverlayEdit


@dataclass(frozen=True)
class ComposedStep:
    """Attribution tracking for a single composed step."""

    step_id: str
    source: str


@dataclass(frozen=True)
class OverlayLayer:
    """An overlay together with its layer source for attribution."""

    overlay: Overlay
    source: str


# Nested step keys that may contain a list of steps.
_NESTED_LIST_KEYS = ("then", "else", "steps", "default")


def find_step(
    steps: list[dict[str, Any]], step_id: str
) -> tuple[list[dict[str, Any]], int] | None:
    """Recursively locate a step by ID and return its (parent_list, index).

    Searches flat lists and nested lists inside ``then``, ``else``, ``steps``,
    ``default``, and ``cases.*``.  Does *not* descend into ``fan-out`` template
    steps because those are runtime-multiplied stamps, not uniquely-addressable
    nodes.
    """
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        if step.get("id") == step_id:
            return (steps, i)
        for key in _NESTED_LIST_KEYS:
            nested = step.get(key)
            if isinstance(nested, list):
                result = find_step(nested, step_id)
                if result is not None:
                    return result
        cases = step.get("cases")
        if isinstance(cases, dict):
            for case_steps in cases.values():
                if isinstance(case_steps, list):
                    result = find_step(case_steps, step_id)
                    if result is not None:
                        return result
    return None


def _all_base_step_ids(steps: list[dict[str, Any]]) -> set[str]:
    """Collect all step IDs reachable in a step tree (excluding fan-out templates)."""
    ids: set[str] = set()
    for step in steps:
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")
        if isinstance(step_id, str):
            ids.add(step_id)
        for key in _NESTED_LIST_KEYS:
            nested = step.get(key)
            if isinstance(nested, list):
                ids.update(_all_base_step_ids(nested))
        cases = step.get("cases")
        if isinstance(cases, dict):
            for case_steps in cases.values():
                if isinstance(case_steps, list):
                    ids.update(_all_base_step_ids(case_steps))
    return ids


def _descendant_ids(step: dict[str, Any]) -> set[str]:
    """Return all step IDs nested inside *step* (not including *step* itself)."""
    ids: set[str] = set()
    for key in _NESTED_LIST_KEYS:
        nested = step.get(key)
        if isinstance(nested, list):
            ids.update(_all_base_step_ids(nested))
    cases = step.get("cases")
    if isinstance(cases, dict):
        for case_steps in cases.values():
            if isinstance(case_steps, list):
                ids.update(_all_base_step_ids(case_steps))
    return ids


def _check_anchor_conflicts(
    anchor_operations: dict[str, str],
    base_steps: list[dict[str, Any]],
) -> list[str]:
    """Return error messages for anchor pairs where one is an ancestor of the other.

    Only flags conflicts where the ancestor's winning edit is ``replace`` or
    ``remove`` — operations that destroy the subtree and make any descendant
    anchor unresolvable.  Pure insert operations on an ancestor leave it intact,
    so its descendants remain reachable regardless of processing order.

    Callers should raise on any returned errors before mutating the step tree.
    """
    errors: list[str] = []
    for anchor, operation in sorted(anchor_operations.items()):
        if operation in ("insert_after", "insert_before"):
            # Inserts leave the ancestor step intact; descendants are unaffected.
            continue
        location = find_step(base_steps, anchor)
        if location is None:
            continue  # missing anchors are reported by validate_edits
        parent_list, idx = location
        step = parent_list[idx]
        conflicting = set(anchor_operations.keys()) & _descendant_ids(step)
        for child_anchor in sorted(conflicting):
            errors.append(
                f"Anchor conflict: '{anchor}' is an ancestor of '{child_anchor}'. "
                "Targeting both anchors in the same overlay set produces "
                "order-dependent results; restructure edits to avoid nesting."
            )
    return errors


def _init_sources_recursively(
    steps: list[dict[str, Any]], sources: dict[str, str]
) -> None:
    """Initialize attribution sources for all base steps, recursively."""
    for step in steps:
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")
        if isinstance(step_id, str):
            sources[step_id] = "base"
        for key in _NESTED_LIST_KEYS:
            nested = step.get(key)
            if isinstance(nested, list):
                _init_sources_recursively(nested, sources)
        cases = step.get("cases")
        if isinstance(cases, dict):
            for case_steps in cases.values():
                if isinstance(case_steps, list):
                    _init_sources_recursively(case_steps, sources)


def _record_sources_recursively(
    step: dict[str, Any],
    source: str,
    sources: dict[str, str],
) -> None:
    """Record *source* for a step and all its nested child steps.

    Traverses ``then``, ``else``, ``steps``, ``default``, and ``cases.*``
    so that ``workflow resolve`` attributes every step inside a composite
    insert or replacement to the correct overlay layer.
    """
    step_id = step.get("id")
    if isinstance(step_id, str):
        sources[step_id] = source
    for key in _NESTED_LIST_KEYS:
        nested = step.get(key)
        if isinstance(nested, list):
            for child in nested:
                if isinstance(child, dict):
                    _record_sources_recursively(child, source, sources)
    cases = step.get("cases")
    if isinstance(cases, dict):
        for case_steps in cases.values():
            if isinstance(case_steps, list):
                for child in case_steps:
                    if isinstance(child, dict):
                        _record_sources_recursively(child, source, sources)


def _remove_sources_recursively(
    step: dict[str, Any],
    sources: dict[str, str],
) -> None:
    """Remove source entries for a step and all its nested child steps.

    Traverses the same nesting keys as ``_record_sources_recursively``.
    """
    step_id = step.get("id")
    if isinstance(step_id, str) and sources.get(step_id) == "base":
        sources.pop(step_id, None)
    for key in _NESTED_LIST_KEYS:
        nested = step.get(key)
        if isinstance(nested, list):
            for child in nested:
                if isinstance(child, dict):
                    _remove_sources_recursively(child, sources)
    cases = step.get("cases")
    if isinstance(cases, dict):
        for case_steps in cases.values():
            if isinstance(case_steps, list):
                for child in case_steps:
                    if isinstance(child, dict):
                        _remove_sources_recursively(child, sources)



def _build_attribution(
    steps: list[dict[str, Any]],
    sources: dict[str, str],
) -> list[ComposedStep]:
    """Build an ordered attribution list from the composed step tree."""
    result: list[ComposedStep] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")
        if isinstance(step_id, str):
            result.append(ComposedStep(step_id, sources.get(step_id, "unknown")))
        for key in _NESTED_LIST_KEYS:
            nested = step.get(key)
            if isinstance(nested, list):
                result.extend(_build_attribution(nested, sources))
        cases = step.get("cases")
        if isinstance(cases, dict):
            for case_steps in cases.values():
                if isinstance(case_steps, list):
                    result.extend(_build_attribution(case_steps, sources))
    return result


def _traverse_and_apply(
    steps: list[dict[str, Any]],
    edits_by_anchor: dict[str, list[tuple[OverlayLayer, OverlayEdit]]],
    sources: dict[str, str],
) -> list[dict[str, Any]]:
    """Walk the original step tree and apply overlay edits as each step is encountered.

    Edits are always resolved against the *original* structure — this function
    traverses the unmodified list passed in, so a replacement step's new ID can
    never be mistaken for a base anchor.  Nested lists (``then``, ``else``, etc.)
    are recursed into only for steps that survive the edit (not for replaced
    steps).

    *edits* are expected to be in merge order (lowest priority first, highest
    priority last); the winning edit for each anchor is ``edits[-1]``.
    """
    result: list[dict[str, Any]] = []

    for step in steps:
        if not isinstance(step, dict):
            result.append(step)
            continue

        step_id = step.get("id")
        edits = edits_by_anchor.get(step_id, []) if isinstance(step_id, str) else []
        winning_edit = edits[-1][1] if edits else None

        if winning_edit is not None and winning_edit.operation == "remove":
            # Winning edit removes this step; ignore all other edits on this anchor.
            # Do NOT call _remove_sources_recursively here: _build_attribution only
            # traverses the result list, so stale sources entries for removed steps
            # are never read.  Calling it would incorrectly pop the attribution of a
            # *surviving* step that reuses the same ID (e.g. a replacement step
            # introduced by a higher-priority overlay targeting a different anchor).
            continue

        # Insert before (in merge order).
        for layer, edit in edits:
            if edit.operation == "insert_before":
                new_step = copy.deepcopy(edit.step)
                _record_sources_recursively(new_step, layer.source, sources)
                result.append(new_step)

        if winning_edit is not None and winning_edit.operation == "replace":
            winning_layer = edits[-1][0]
            new_step = copy.deepcopy(winning_edit.step)
            _remove_sources_recursively(step, sources)
            _record_sources_recursively(new_step, winning_layer.source, sources)
            result.append(new_step)
        else:
            # No replacement: keep this step and recurse into its nested lists.
            for key in _NESTED_LIST_KEYS:
                nested = step.get(key)
                if isinstance(nested, list):
                    step[key] = _traverse_and_apply(nested, edits_by_anchor, sources)
            cases = step.get("cases")
            if isinstance(cases, dict):
                for case_key, case_steps in cases.items():
                    if isinstance(case_steps, list):
                        cases[case_key] = _traverse_and_apply(case_steps, edits_by_anchor, sources)
            result.append(step)

        # Insert after (highest priority closest to anchor — reversed merge order).
        for layer, edit in reversed(edits):
            if edit.operation == "insert_after":
                new_step = copy.deepcopy(edit.step)
                _record_sources_recursively(new_step, layer.source, sources)
                result.append(new_step)

    return result


def merge_steps(
    base_steps: list[dict[str, Any]],
    overlays: list[OverlayLayer],
) -> tuple[list[dict[str, Any]], list[ComposedStep]]:
    """Apply overlays to base steps in merge order and return composed steps.

    *overlays* is expected to be sorted by merge order (lowest priority first,
    highest priority last).  The returned step list is a deep copy of the base;
    base_steps is never mutated.

    Higher-wins semantics are enforced for edits that target the same base
    anchor: the highest-priority edit (last in *overlays*) decides the fate of
    the anchor.  A lower-priority ``remove`` cannot prevent a higher-priority
    ``replace`` or ``insert_*`` on the same anchor.
    """
    steps = copy.deepcopy(base_steps)
    sources: dict[str, str] = {}
    _init_sources_recursively(steps, sources)

    # Group edits by anchor, preserving merge order.
    edits_by_anchor: dict[str, list[tuple[OverlayLayer, OverlayEdit]]] = {}
    for layer in overlays:
        for edit in layer.overlay.edits:
            edits_by_anchor.setdefault(edit.anchor, []).append((layer, edit))

    # Raise early for non-remove edits that target anchors not present in the base.
    # Overlays always apply to the original tree; they cannot target steps introduced
    # by other overlays.
    base_ids = _all_base_step_ids(base_steps)
    for anchor, anchor_edits in edits_by_anchor.items():
        winning_op = anchor_edits[-1][1].operation
        if winning_op != "remove" and anchor not in base_ids:
            raise ValueError(f"Anchor '{anchor}' not found in workflow steps.")

    # Reject edits that target anchors with a parent/descendant relationship when
    # the ancestor edit replaces or removes its subtree — those produce
    # order-dependent results.  Pure insert edits on an ancestor are safe because
    # the ancestor step (and its descendants) remain intact.
    anchor_winning_ops = {
        anchor: anchor_edits[-1][1].operation
        for anchor, anchor_edits in edits_by_anchor.items()
    }
    anchor_conflicts = _check_anchor_conflicts(anchor_winning_ops, base_steps)
    if anchor_conflicts:
        raise ValueError(
            "Overlay anchor conflict(s) detected:\n  - " + "\n  - ".join(anchor_conflicts)
        )

    # Apply all overlay edits via a single-pass traversal of the original tree.
    # Each edit is resolved against the original step structure, so a replacement
    # step's new ID can never be mistaken for a base anchor in a later edit group.
    result = _traverse_and_apply(steps, edits_by_anchor, sources)

    attribution = _build_attribution(result, sources)
    return result, attribution


def validate_edits(
    edits: list[OverlayEdit],
    base_step_ids: set[str],
) -> list[str]:
    """Validate overlay edits against a set of known base step IDs.

    Returns a list of human-readable error messages.  Does not raise.
    """
    errors: list[str] = []
    for idx, edit in enumerate(edits):
        if edit.operation not in VALID_OPERATIONS:
            errors.append(f"Edit {idx}: invalid operation {edit.operation!r}.")
            continue
        if edit.anchor not in base_step_ids:
            errors.append(
                f"Edit {idx}: anchor '{edit.anchor}' does not match any base step id."
            )
        if edit.operation == "remove":
            if edit.step is not None:
                errors.append(f"Edit {idx}: 'remove' must not include a step.")
            continue
        if not isinstance(edit.step, dict):
            errors.append(f"Edit {idx}: '{edit.operation}' requires a step mapping.")
            continue
        step_id = edit.step.get("id")
        if not isinstance(step_id, str) or not step_id:
            errors.append(f"Edit {idx}: step is missing required 'id'.")
            continue
        if ":" in step_id:
            errors.append(
                f"Edit {idx}: step id {step_id!r} contains ':' which is reserved "
                "for engine-generated nested IDs."
            )
    return errors
