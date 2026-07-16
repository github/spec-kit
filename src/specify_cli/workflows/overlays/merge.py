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


def apply_edit(
    steps: list[dict[str, Any]],
    edit: OverlayEdit,
    source: str,
) -> tuple[list[dict[str, Any]], ComposedStep | None, str | None]:
    """Apply a single edit to a step list and return the mutated list.

    The returned list is the same list object as *steps* but deep-copied first
    so callers can avoid mutating the base.  Raises ``ValueError`` if the anchor
    is not found.

    Returns:
        ``(steps, composed_step, replaced_or_removed_id)``.  *composed_step* is
        ``None`` for ``remove`` operations; *replaced_or_removed_id* is the
        previous step id for ``replace``/``remove`` operations, otherwise
        ``None``.
    """
    location = find_step(steps, edit.anchor)
    if location is None:
        raise ValueError(f"Anchor '{edit.anchor}' not found in workflow steps.")

    parent_list, index = location
    old_step = parent_list[index]
    old_step_id = old_step.get("id") if isinstance(old_step, dict) else None

    if edit.operation == "insert_after":
        new_step = copy.deepcopy(edit.step)
        parent_list.insert(index + 1, new_step)
        step_id = str(new_step.get("id")) if isinstance(new_step, dict) else ""
        return steps, ComposedStep(step_id, source), None
    if edit.operation == "insert_before":
        new_step = copy.deepcopy(edit.step)
        parent_list.insert(index, new_step)
        step_id = str(new_step.get("id")) if isinstance(new_step, dict) else ""
        return steps, ComposedStep(step_id, source), None
    if edit.operation == "replace":
        new_step = copy.deepcopy(edit.step)
        parent_list[index] = new_step
        step_id = str(new_step.get("id")) if isinstance(new_step, dict) else ""
        return steps, ComposedStep(step_id, source), old_step_id
    if edit.operation == "remove":
        del parent_list[index]
        return steps, None, old_step_id
    raise ValueError(f"Unsupported edit operation: {edit.operation}")


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

    for anchor, edits in edits_by_anchor.items():
        # Highest-priority edit is last because *overlays* is already sorted.
        _, winning_edit = edits[-1]

        if winning_edit.operation == "remove":
            # Anchor is removed; ignore all other edits on this anchor.
            location = find_step(steps, anchor)
            if location is not None:
                parent_list, index = location
                removed_step = parent_list[index]
                removed_id = removed_step.get("id") if isinstance(removed_step, dict) else None
                del parent_list[index]
                if isinstance(removed_id, str):
                    sources.pop(removed_id, None)
            continue

        # For replace/insert_*, the anchor survives. Only the highest-priority
        # replace is applied; lower-priority replaces on the same anchor are
        # skipped. Inserts are applied in merge order.
        if winning_edit.operation == "replace":
            winning_layer, _ = edits[-1]
            steps, composed, replaced_id = apply_edit(steps, winning_edit, winning_layer.source)
            if isinstance(replaced_id, str):
                sources.pop(replaced_id, None)
            if composed is not None:
                sources[composed.step_id] = composed.source

        for layer, edit in edits:
            if edit.operation in ("insert_after", "insert_before"):
                steps, composed, replaced_id = apply_edit(steps, edit, layer.source)
                if replaced_id is not None:
                    sources.pop(replaced_id, None)
                if composed is not None:
                    sources[composed.step_id] = composed.source

    attribution = _build_attribution(steps, sources)
    return steps, attribution


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
