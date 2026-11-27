"""Typed workflow-call boundary; execution and persistence belong to the engine."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from specify_cli._file_policy import ProjectPolicyError, resolve_nofollow_directory

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


class CallError(ValueError):
    """A treatable violation of the workflow-call boundary."""


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
    if not isinstance(mapping, dict) or any(not isinstance(k, str) for k in mapping):
        errors.append("'input' must be a mapping with string keys")
    else:
        try:
            require_json(mapping)
        except ValueError as exc:
            errors.append(str(exc))
    errors.extend(validate_execution_config(config))
    return errors


def validate_execution_config(config):
    """The execution boundary is opt-in and has no implicit launch defaults."""
    if "execution" not in config:
        return []
    value = config["execution"]
    if not isinstance(value, dict):
        return ["'execution' must be a mapping"]
    mode = value.get("mode")
    if not isinstance(mode, str) or mode not in {"in-process", "subprocess"}:
        return ["'execution.mode' must be literal 'in-process' or 'subprocess'"]
    if mode == "in-process":
        return [] if set(value) == {"mode"} else ["In-process execution accepts only 'mode'"]
    errors = []
    if set(value) - {"mode", "project_root", "timeout"}:
        errors.append("Unknown subprocess execution keys")
    root = value.get("project_root")
    if not isinstance(root, str) or not root.strip() or "\x00" in root:
        errors.append("'execution.project_root' must be a nonempty NUL-free string")
    if "timeout" in value and not valid_timeout(value["timeout"]):
        errors.append("'execution.timeout' must be a finite positive number")
    return errors


def valid_timeout(value):
    try:
        return type(value) in {int, float} and math.isfinite(value) and value > 0
    except OverflowError:
        return False


def checked_root(value, base=None):
    """Freeze an existing directory, refusing symlink/reparse traversal."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise CallError("Execution root must resolve to a nonempty NUL-free string")
    path = Path(value)
    if os.name == "nt" and bool(path.drive) != bool(path.root):
        raise CallError("Execution root must not be drive-relative or root-relative")
    if not path.is_absolute():
        if base is None:
            raise CallError("Stored execution root must be absolute")
        path = Path(base).absolute() / path
    try:
        return str(resolve_nofollow_directory(path))
    except ProjectPolicyError as exc:
        if isinstance(exc.__cause__, OSError):
            # Existing bind/resume callers own their distinct OS-error envelopes.
            raise exc.__cause__
        raise CallError(str(exc)) from exc


def bind_execution(config, context, source_root):
    value = config.get("execution", {"mode": "in-process"})
    if value["mode"] == "in-process":
        return None
    root = evaluate_expression(value["project_root"], context)
    try:
        return {
            "mode": "subprocess",
            "source_root": checked_root(os.fspath(source_root), os.getcwd()),
            "project_root": checked_root(root, context.project_root or os.getcwd()),
            "timeout": value.get("timeout"),
        }
    except OSError as exc:
        raise CallError(f"Cannot use execution root: {exc}") from exc


def check_bound_execution(value, *, paths=False):
    """Validate persisted metadata before it can select a worker or cwd."""
    if (not isinstance(value, dict)
            or set(value) != {"mode", "source_root", "project_root", "timeout"}
            or value["mode"] != "subprocess"
            or (value["timeout"] is not None and not valid_timeout(value["timeout"]))):
        raise CallError("Invalid bound execution metadata")
    for name in ("source_root", "project_root"):
        root = value[name]
        if not isinstance(root, str) or not root.strip() or "\x00" in root or not Path(root).is_absolute():
            raise CallError("Invalid bound execution root")
        if paths:
            try:
                if checked_root(root) != root:
                    raise CallError("Bound execution root changed")
            except OSError as exc:
                raise CallError(f"Cannot use bound execution root: {exc}") from exc


def validate_runtime_call(config: dict[str, Any]) -> None:
    """Raise a call-boundary error for an invalid authored call shape."""
    errors = validate_call(config)
    if errors:
        raise CallError("; ".join(errors))


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

    try:
        if not isinstance(target, str) or not _ID_PATTERN.fullmatch(target):
            raise CallError("Workflow target must be an exact safe workflow ID")
        if target in _RESERVED_WORKFLOW_IDS:
            raise CallError(f"Workflow {target!r} is reserved")
        if target in ancestry:
            raise CallError(
                f"Workflow composition cycle: {' -> '.join((*ancestry, target))}"
            )
        if len(ancestry) > MAX_COMPOSITION_DEPTH:
            raise CallError(
                f"Workflow composition exceeds maximum depth {MAX_COMPOSITION_DEPTH}"
            )
        metadata = WorkflowRegistry(project_root).get(target)
        if not isinstance(metadata, dict):
            raise CallError(f"Workflow {target!r} is not installed")
        if not metadata.get("enabled", True):
            raise CallError(f"Workflow {target!r} is disabled")
        definition = WorkflowResolver(project_root).resolve(target)
        if definition.id != target:
            raise CallError(
                f"Workflow {target!r} resolves to mismatched ID {definition.id!r}"
            )
        errors = validate_workflow(definition)
        if errors:
            raise CallError(f"Invalid workflow {target!r}: {'; '.join(errors)}")
        return definition
    except CallError:
        raise
    except (OSError, ValueError) as exc:
        raise CallError(str(exc)) from exc


def bind_inputs(
    engine,
    definition,
    config: dict[str, Any],
    context: StepContext,
    previous: dict[str, Any] | None = None,
):
    mapping = config.get("input", {})
    if not isinstance(mapping, dict) or any(not isinstance(k, str) for k in mapping):
        raise CallError("'input' must be a mapping with string keys")
    provided = {
        key: evaluate_expression(value, context) for key, value in mapping.items()
    }
    try:
        require_json(provided)
        unknown = provided.keys() - definition.inputs.keys()
        if unknown:
            raise CallError(
                f"Undeclared inputs for workflow {definition.id!r}: {sorted(unknown)}"
            )
        resolved = (
            engine._resolve_inputs(definition, provided)
            if previous is None
            else engine._merge_inputs(definition, previous, provided)
        )
        require_json(resolved)
        return resolved
    except CallError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise CallError(str(exc)) from exc


def evaluate_outputs(definition, context: StepContext) -> dict[str, Any]:
    errors = validate_outputs(definition.outputs)
    if errors:
        raise CallError("; ".join(errors))
    output = {
        name: evaluate_expression(entry["value"], context)
        for name, entry in definition.outputs.items()
    }
    try:
        require_json(output)
        return output
    except (TypeError, ValueError, RecursionError) as exc:
        raise CallError(str(exc)) from exc
