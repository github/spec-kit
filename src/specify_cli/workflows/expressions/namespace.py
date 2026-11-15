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
_INDEXED_SEGMENT = re.compile(r"^([\w-]+)\[(-?\d+)\]$")

_PLAIN_SEGMENT = re.compile(r"^[\w-]+$")


def _resolve_dot_path(obj: Any, path: str) -> Any:
    """Resolve a dotted path like ``steps.specify.output.file`` against *obj*.

    Supports dict key access and list indexing, including the negative form
    Python and Jinja2 both accept (e.g., ``task_list[0]``, ``task_list[-1]``).
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        # Handle list indexing: name[0], name[-1]
        idx_match = _INDEXED_SEGMENT.match(part)
        if idx_match:
            key, idx = idx_match.group(1), int(idx_match.group(2))
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            if isinstance(current, list) and -len(current) <= idx < len(current):
                current = current[idx]
            else:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
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
