"""Workflow overlay schema — dataclasses and validation for overlay manifests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from ...extensions import normalize_priority

# Safe single-segment identifiers: no path separators, no traversal, no dots.
_SAFE_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_RESERVED_OVERLAY_WORKFLOW_IDS: frozenset[str] = frozenset({"overlays"})
_RESERVED_WORKFLOW_IDS: frozenset[str] = frozenset({"overlays", "runs", "steps"})

VALID_OPERATIONS = frozenset({"insert_after", "insert_before", "replace", "remove"})

# Map shorthand keys to operation names.
_SHORTHAND_OPERATION_KEYS: frozenset[str] = VALID_OPERATIONS


@dataclass(frozen=True)
class OverlayEdit:
    """A single edit operation on a workflow step list."""

    operation: Literal["insert_after", "insert_before", "replace", "remove"]
    anchor: str
    step: dict[str, Any] | None = None


@dataclass
class Overlay:
    """A declared overlay (one YAML file)."""

    id: str
    extends: str
    edits: list[OverlayEdit]
    priority: int = 10
    enabled: bool = True


def _validate_safe_id(
    value: str,
    field_name: str,
    allow_reserved: bool = False,
    reserved_ids: frozenset[str] = _RESERVED_OVERLAY_WORKFLOW_IDS,
) -> str | None:
    """Return an error message if *value* is not a safe path segment ID."""
    if not isinstance(value, str) or not value:
        return f"Overlay '{field_name}' is required and must be a non-empty string."
    if not _SAFE_ID_PATTERN.fullmatch(value):
        return (
            f"Overlay '{field_name}' {value!r} contains invalid characters; "
            "only lowercase letters, digits, and hyphens are allowed."
        )
    if not allow_reserved and value in reserved_ids:
        return f"Overlay '{field_name}' {value!r} is reserved."
    return None


def _parse_edit(edit_raw: dict[str, Any], idx: int) -> tuple[OverlayEdit | None, str | None]:
    """Parse a single edit dict into an OverlayEdit or an error string."""
    shorthand_keys = [key for key in _SHORTHAND_OPERATION_KEYS if key in edit_raw]
    has_operation = "operation" in edit_raw

    operation: str | None = None
    anchor: Any = None

    if shorthand_keys and has_operation:
        return None, (
            f"Edit at index {idx} mixes shorthand operation key "
            f"({shorthand_keys[0]!r}) with explicit 'operation' field."
        )

    if len(shorthand_keys) > 1:
        return None, (
            f"Edit at index {idx} has multiple operation keys: "
            f"{', '.join(repr(k) for k in shorthand_keys)}."
        )

    if shorthand_keys:
        operation = shorthand_keys[0]
        anchor = edit_raw[operation]
    elif has_operation:
        operation = edit_raw.get("operation")
        anchor = edit_raw.get("anchor")
    else:
        return None, f"Edit at index {idx} has no operation; expected one of {sorted(VALID_OPERATIONS)}."

    if operation not in VALID_OPERATIONS:
        return None, f"Edit at index {idx} has invalid operation {operation!r}."

    if not isinstance(anchor, str) or not anchor:
        return None, f"Edit at index {idx} has invalid 'anchor'."

    step = edit_raw.get("step")
    if operation == "remove":
        if step is not None:
            return None, f"Edit at index {idx} ('remove') must not include 'step'."
        return OverlayEdit(operation=operation, anchor=anchor), None

    if not isinstance(step, dict):
        return None, f"Edit at index {idx} ('{operation}') requires 'step' mapping."
    step_id = step.get("id")
    if not isinstance(step_id, str) or not step_id:
        return None, f"Edit at index {idx} step is missing required 'id'."
    if ":" in step_id:
        return None, (
            f"Edit at index {idx} step id {step_id!r} contains ':' "
            "which is reserved for engine-generated nested IDs."
        )
    return OverlayEdit(operation=operation, anchor=anchor, step=step), None


def validate_overlay_yaml(data: dict[str, Any]) -> tuple[Overlay | None, list[str]]:
    """Validate an overlay manifest dict and return (Overlay, errors).

    Errors are returned as a list of strings; validation never raises.
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        return None, ["Overlay manifest must be a mapping."]

    overlay_id = data.get("id")
    if err := _validate_safe_id(overlay_id, "id"):
        errors.append(err)
        overlay_id = ""

    extends = data.get("extends")
    if err := _validate_safe_id(
        extends,
        "extends",
        reserved_ids=_RESERVED_WORKFLOW_IDS,
    ):
        errors.append(err)
        extends = ""

    priority = normalize_priority(data.get("priority", 10))

    edits_raw = data.get("edits")
    edits: list[OverlayEdit] = []
    if not isinstance(edits_raw, list):
        errors.append("Overlay 'edits' is required and must be a list.")
    elif not edits_raw:
        errors.append("Overlay 'edits' must be a non-empty list.")
    else:
        for idx, edit_raw in enumerate(edits_raw):
            if not isinstance(edit_raw, dict):
                errors.append(f"Edit at index {idx} must be a mapping.")
                continue
            edit, err = _parse_edit(edit_raw, idx)
            if err:
                errors.append(err)
                continue
            if edit is not None:
                edits.append(edit)

    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        errors.append("Overlay 'enabled' must be a boolean.")
        enabled = bool(enabled)

    if errors:
        return None, errors

    return (
        Overlay(
            id=overlay_id,
            extends=extends,
            priority=priority,
            edits=edits,
            enabled=enabled,
        ),
        [],
    )
