"""Namespace construction and dot-path resolution for workflow expressions.

Leaf module: no dependencies on the evaluator, the filters, or the
diagnostics. ``_INDEXED_SEGMENT`` is the one definition of an indexed path
segment; both ``_resolve_dot_path`` and the condition diagnostics read it from
here so widening what indexing accepts cannot leave them disagreeing.
"""

from __future__ import annotations

import re
from typing import Any


# The one definition of an indexed path segment. _resolve_dot_path matches
# against it, and the condition gate below reuses it rather than describing the
# same shape a second time, so widening what indexing accepts cannot leave the
# evaluator and the gate disagreeing.
_INDEXED_SEGMENT = re.compile(r"^([\w-]+)((?:\[-?\d+\])+)$")
_INDEX_BRACKET = re.compile(r"\[([^\]]+)\]")

_PLAIN_SEGMENT = re.compile(r"^[\w-]+$")


def _resolve_dot_path(obj: Any, path: str) -> Any:
    """Resolve a dotted path like ``steps.specify.output.file`` against *obj*.

    Supports dict key access and single or chained list indexing, including the
    negative form Python and Jinja2 both accept (e.g., ``task_list[0]``,
    ``task_list[-1]``, ``matrix[0][1]``).

    For chained indexing (two or more bracketed indices on one segment),
    invalid access raises ``IndexError`` for out-of-range list indices and
    ``TypeError`` when the target is not a list, rather than silently
    returning ``None``.
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        # Handle single or chained list indexing: name[0], name[-1], matrix[0][1]
        idx_match = _INDEXED_SEGMENT.match(part)
        if idx_match:
            key = idx_match.group(1)
            if isinstance(current, dict):
                current = current.get(key)
            else:
                current = None
            raw_indices = idx_match.group(2)
            indices = (
                _INDEX_BRACKET.findall(raw_indices)
                if raw_indices.startswith("[")
                else [raw_indices]
            )
            chained = len(indices) > 1
            for raw_idx in indices:
                idx = int(raw_idx)
                if not isinstance(current, list):
                    if chained:
                        raise TypeError(
                            f"cannot index {type(current).__name__} in '{path}': "
                            "chained indexing requires a list"
                        )
                    current = None
                    break
                if -len(current) <= idx < len(current):
                    current = current[idx]
                elif chained:
                    raise IndexError(
                        f"list index {idx} out of range in '{path}' "
                        f"(length {len(current)})"
                    )
                else:
                    current = None
                    break
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            current = None
    return current


def _build_namespace(context: Any) -> dict[str, Any]:
    """Build the variable namespace from a StepContext."""
    ns: dict[str, Any] = {}
    if hasattr(context, "inputs"):
        ns["inputs"] = context.inputs or {}
    if hasattr(context, "steps"):
        ns["steps"] = context.steps or {}
    if hasattr(context, "item"):
        ns["item"] = context.item
    if hasattr(context, "fan_in"):
        ns["fan_in"] = context.fan_in or {}
    # Engine-managed runtime metadata. Always present (even outside a
    # run) so templates referencing it never error: `run_id` falls back
    # to an empty string when no run is active (dry-run, validation,
    # ad-hoc evaluator usage). The value is the same one Spec Kit
    # prints as `Run ID:` at the end of `workflow run` — auto-generated
    # runs use an 8-character uuid4 hex; operator-supplied ids may be
    # any alphanumeric string with hyphens or underscores.
    run_id = getattr(context, "run_id", None) or ""
    workflow_dir = getattr(context, "workflow_dir", None) or ""
    ns["context"] = {"run_id": run_id, "workflow_dir": workflow_dir}
    return ns


# The roots _build_namespace supplies. A reference to anything else resolves to
# None, so a correction built on one turns a truthy condition false.
_NAMESPACE_ROOTS = ("inputs", "steps", "item", "fan_in", "context")


def _is_path_segment(segment: str) -> bool:
    """Whether _resolve_dot_path can walk *segment*: a name, or a name it indexes."""
    return bool(_PLAIN_SEGMENT.match(segment) or _INDEXED_SEGMENT.match(segment))
