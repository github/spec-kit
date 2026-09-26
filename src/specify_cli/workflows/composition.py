"""Typed workflow-call boundary; execution and persistence belong to the engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import StepContext
from .expressions import evaluate_expression

RESERVED_OUTPUT_NAMES = frozenset(
    {
        "workflow",
        "status",
        "error",
        "aborted",
        "integration",
        "model",
        "options",
        "input",
    }
)
MAX_COMPOSITION_DEPTH = 16


def require_json(value: Any) -> None:
    """Reject lossy/non-JSON values, including cycles, before checkpointing."""
    try:
        encoded = json.dumps(value, allow_nan=False)
        if json.loads(encoded) != value:
            raise ValueError("JSON encoding changes the value")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError(f"Value is not JSON-safe: {exc}") from exc


def validate_call(config: dict[str, Any]) -> list[str]:
    from .engine import _ID_PATTERN
    from .overlay.schema import _RESERVED_WORKFLOW_IDS

    errors = []
    target = config.get("workflow")
    if not isinstance(target, str):
        errors.append("'workflow' must be a string")
    elif "{{" not in target and (
        not _ID_PATTERN.fullmatch(target) or target in _RESERVED_WORKFLOW_IDS
    ):
        errors.append("'workflow' must be an exact, safe, non-reserved workflow ID")
    mapping = config.get("input", {})
    if mapping is not None:
        if not isinstance(mapping, dict) or any(
            not isinstance(k, str) for k in mapping
        ):
            errors.append("'input' must be a mapping with string keys")
        else:
            try:
                require_json(mapping)
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def validate_outputs(outputs: Any) -> list[str]:
    from .engine import _ID_PATTERN

    if not isinstance(outputs, dict):
        return ["'outputs' must be a mapping"]
    errors = []
    for name, entry in outputs.items():
        if not isinstance(name, str) or not _ID_PATTERN.fullmatch(name):
            errors.append(f"Output {name!r} must be a safe identifier")
        elif name in RESERVED_OUTPUT_NAMES:
            errors.append(f"Output {name!r} is reserved")
        if not isinstance(entry, dict) or set(entry) != {"value"}:
            errors.append(f"Output {name!r} must contain exactly 'value'")
        else:
            try:
                require_json(entry["value"])
            except ValueError as exc:
                errors.append(f"Output {name!r}: {exc}")
    return errors


def resolve_target(project_root: Path, target: Any, ancestry: tuple[str, ...]):
    from .catalog import WorkflowRegistry
    from .engine import _ID_PATTERN, validate_workflow
    from .overlay import WorkflowResolver
    from .overlay.schema import _RESERVED_WORKFLOW_IDS

    if not isinstance(target, str) or not _ID_PATTERN.fullmatch(target):
        raise ValueError("Workflow target must be an exact safe workflow ID")
    if target in _RESERVED_WORKFLOW_IDS:
        raise ValueError(f"Workflow {target!r} is reserved")
    if target in ancestry:
        raise ValueError(
            f"Workflow composition cycle: {' -> '.join((*ancestry, target))}"
        )
    if len(ancestry) > MAX_COMPOSITION_DEPTH:
        raise ValueError(
            f"Workflow composition exceeds maximum depth {MAX_COMPOSITION_DEPTH}"
        )
    metadata = WorkflowRegistry(project_root).get(target)
    if not isinstance(metadata, dict):
        raise ValueError(f"Workflow {target!r} is not installed")
    if not metadata.get("enabled", True):
        raise ValueError(f"Workflow {target!r} is disabled")
    definition = WorkflowResolver(project_root).resolve(target)
    if definition.id != target:
        raise ValueError(
            f"Workflow {target!r} resolves to mismatched ID {definition.id!r}"
        )
    errors = validate_workflow(definition)
    if errors:
        raise ValueError(f"Invalid workflow {target!r}: {'; '.join(errors)}")
    return definition


def bind_inputs(engine, definition, config: dict[str, Any], context: StepContext):
    mapping = config.get("input")
    if mapping is None:
        mapping = {}
    if not isinstance(mapping, dict) or any(not isinstance(k, str) for k in mapping):
        raise ValueError("'input' must be a mapping with string keys")
    provided = {
        key: evaluate_expression(value, context) for key, value in mapping.items()
    }
    require_json(provided)
    unknown = provided.keys() - definition.inputs.keys()
    if unknown:
        raise ValueError(
            f"Undeclared inputs for workflow {definition.id!r}: {sorted(unknown)}"
        )
    resolved = engine._resolve_inputs(definition, provided)
    require_json(resolved)
    return resolved


def evaluate_outputs(definition, context: StepContext) -> dict[str, Any]:
    errors = validate_outputs(definition.outputs)
    if errors:
        raise ValueError("; ".join(errors))
    output = {
        name: evaluate_expression(entry["value"], context)
        for name, entry in definition.outputs.items()
    }
    require_json(output)
    return output
