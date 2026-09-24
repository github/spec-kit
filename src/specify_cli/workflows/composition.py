"""Workflow composition — scoped subtree execution helpers.

Implements the workflow composition decisions:

- reserved output names and the composition depth limit,
- registry-backed, installed-and-enabled target resolution,
- strict input binding,
- declared-output evaluation,
- the internal ``ExecutionScope`` data model and persistence helpers.

The engine special-cases ``type: workflow`` and owns the scope tree; custom
steps never see an ``ExecutionScope``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import RunStatus, StepContext
from .expressions import evaluate_expression

if TYPE_CHECKING:
    from .engine import RunState, WorkflowDefinition

#: Engine metadata and run-control keys that cannot be declared as workflow
#: outputs. ``aborted`` controls run-abort behaviour; ``integration``,
#: ``model``, ``options`` and ``input`` are copied into persisted step
#: metadata by the engine; ``workflow``/``status``/``error`` are the stable
#: call metadata.
RESERVED_OUTPUT_NAMES: frozenset[str] = frozenset(
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

#: Maximum number of included-workflow levels. The root workflow is depth 0.
MAX_COMPOSITION_DEPTH = 16

#: Safe single-segment identifier: lowercase letters, digits, and hyphens.
_SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


def _id_pattern() -> re.Pattern[str]:
    """Return the engine's exact workflow-ID pattern (lazy import)."""
    from .engine import _ID_PATTERN

    return _ID_PATTERN


def _reserved_workflow_ids() -> frozenset[str]:
    """Return the reserved installed-workflow directory names (lazy import)."""
    from .overlay.schema import _RESERVED_WORKFLOW_IDS

    return _RESERVED_WORKFLOW_IDS


# -- Target resolution ----------------------------------------------------


def resolve_composed_workflow(
    project_root: Path, workflow_id: str
) -> WorkflowDefinition:
    """Resolve an installed, enabled workflow ID to its composed definition.

    Combines the registry existence/enabled checks that currently live in the
    CLI with overlay resolution and validation. Raises ``ValueError`` (never
    ``typer.Exit``) so a workflow step can surface the failure as a failed
    step result.
    """
    from .catalog import WorkflowRegistry
    from .engine import validate_workflow
    from .overlay import WorkflowResolver

    if not isinstance(workflow_id, str) or not workflow_id:
        msg = "Workflow target must be a non-empty string."
        raise ValueError(msg)

    registry = WorkflowRegistry(project_root)
    metadata = registry.get(workflow_id)
    if metadata is None:
        msg = f"Workflow {workflow_id!r} is not installed."
        raise ValueError(msg)
    if not isinstance(metadata, dict):
        msg = f"Registry entry for workflow {workflow_id!r} is corrupted."
        raise ValueError(msg)
    if not metadata.get("enabled", True):
        msg = f"Workflow {workflow_id!r} is disabled."
        raise ValueError(msg)

    definition = WorkflowResolver(project_root).resolve(workflow_id)
    errors = validate_workflow(definition)
    if errors:
        msg = (
            f"Workflow {workflow_id!r} is invalid: " + " ".join(errors)
        )
        raise ValueError(msg)
    return definition


# -- Definition-time validation ------------------------------------------


def validate_workflow_outputs(definition: WorkflowDefinition) -> list[str]:
    """Validate a workflow's top-level ``outputs`` block."""
    errors: list[str] = []
    outputs = definition.outputs
    if not isinstance(outputs, dict):
        return ["'outputs' must be a mapping (or omitted)."]
    for name, entry in outputs.items():
        if not isinstance(name, str) or not _SAFE_NAME_PATTERN.fullmatch(name):
            errors.append(
                f"Output {name!r} must be a safe identifier (lowercase "
                "letters, digits, and hyphens)."
            )
            continue
        if name in RESERVED_OUTPUT_NAMES:
            errors.append(f"Output {name!r} is a reserved name.")
            continue
        if not isinstance(entry, dict):
            errors.append(f"Output {name!r} must be a mapping.")
            continue
        if set(entry.keys()) != {"value"}:
            errors.append(
                f"Output {name!r} must contain exactly the 'value' field."
            )
    return errors


def validate_workflow_call_config(config: dict[str, Any]) -> list[str]:
    """Validate a ``type: workflow`` step config (project-independent)."""
    errors: list[str] = []
    step_id = config.get("id", "?")
    target = config.get("workflow")

    if "workflow" not in config:
        errors.append(
            f"Workflow step {step_id!r} is missing 'workflow' field."
        )
    elif not isinstance(target, str):
        errors.append(
            f"Workflow step {step_id!r}: 'workflow' must be a string, got "
            f"{type(target).__name__}."
        )
    elif "{{" not in target:
        # A literal target must be a valid, non-reserved workflow ID.
        if not _id_pattern().fullmatch(target):
            errors.append(
                f"Workflow step {step_id!r}: 'workflow' literal {target!r} "
                "must be lowercase alphanumeric with hyphens."
            )
        elif target in _reserved_workflow_ids():
            errors.append(
                f"Workflow step {step_id!r}: 'workflow' literal {target!r} "
                "is reserved."
            )

    input_mapping = config.get("input")
    if input_mapping is not None and not isinstance(input_mapping, dict):
        errors.append(
            f"Workflow step {step_id!r}: 'input' must be a mapping."
        )
    elif isinstance(input_mapping, dict):
        for key in input_mapping:
            if not isinstance(key, str):
                errors.append(
                    f"Workflow step {step_id!r}: 'input' keys must be strings."
                )
    return errors


# -- Input binding --------------------------------------------------------


def evaluate_input_mapping(
    mapping: Any, context: StepContext
) -> dict[str, Any]:
    """Evaluate a caller's ``input`` mapping once in the caller scope.

    ``mapping`` is the raw ``input`` value from the step config. Omitted or
    explicitly null (``None``) means "no inputs". Any other non-mapping is
    malformed: ``WorkflowEngine.execute`` may be handed an unvalidated
    definition, so fail closed here rather than silently discarding the
    caller's mapping and running the child with defaults. The same shape is
    rejected at definition time by ``validate_workflow_call_config``; the
    callers turn this ``ValueError`` into a failed workflow-step result.
    """
    if mapping is None:
        return {}
    if not isinstance(mapping, dict):
        msg = (
            f"'input' must be a mapping or omitted, got "
            f"{type(mapping).__name__}."
        )
        raise ValueError(msg)
    return {
        name: evaluate_expression(value, context)
        for name, value in mapping.items()
    }


def bind_composed_inputs(
    definition: WorkflowDefinition,
    provided: dict[str, Any],
    *,
    caller_id: str,
    workflow_id: str,
    resolve_default: Any,
) -> dict[str, Any]:
    """Strictly bind caller-supplied values to a target workflow's inputs.

    Unlike the low-level ``_resolve_inputs`` path, an undeclared mapped name is
    rejected rather than silently discarded. ``resolve_default`` is the
    engine's sentinel resolver (``WorkflowEngine._resolve_default``).
    """
    from .engine import WorkflowEngine

    input_defs = definition.inputs if isinstance(definition.inputs, dict) else {}

    for name in provided:
        if name not in input_defs:
            msg = (
                f"Workflow step {caller_id!r} passed undeclared input {name!r} "
                f"to workflow {workflow_id!r}."
            )
            raise ValueError(msg)

    resolved: dict[str, Any] = {}
    for name, input_def in input_defs.items():
        if not isinstance(input_def, dict):
            continue
        if name in provided:
            value = resolve_default(name, provided[name])
        elif "default" in input_def:
            value = resolve_default(name, input_def["default"])
        elif input_def.get("required", False):
            msg = (
                f"Workflow step {caller_id!r} did not provide required input "
                f"{name!r} for workflow {workflow_id!r}."
            )
            raise ValueError(msg)
        else:
            continue

        coerce_input_def = input_def
        if (
            name == "integration"
            and value == "auto"
            and isinstance(input_def.get("enum"), list)
        ):
            coerce_input_def = {
                key: val for key, val in input_def.items() if key != "enum"
            }
        resolved[name] = WorkflowEngine._coerce_input(
            name, value, coerce_input_def
        )
    return resolved


# -- Output evaluation ----------------------------------------------------


def evaluate_composed_outputs(
    definition: WorkflowDefinition, scope: ExecutionScope
) -> dict[str, Any]:
    """Evaluate a completed scope's declared outputs in its local context."""
    outputs = definition.outputs
    if not isinstance(outputs, dict):
        return {}
    context = scope.build_context(is_resume=False)
    result: dict[str, Any] = {}
    for name, entry in outputs.items():
        if not isinstance(entry, dict) or "value" not in entry:
            continue
        result[name] = evaluate_expression(entry["value"], context)
    return result


# -- Cycle and depth ------------------------------------------------------


def check_composition_path(active_path: list[str], target: str) -> None:
    """Reject a cyclic or too-deep composition entry.

    Cycle detection runs first so a recursive reference reports a cycle even
    when the depth limit would also apply.
    """
    if target in active_path:
        chain = " -> ".join([*active_path, target])
        msg = f"Workflow composition cycle detected: {chain}."
        raise ValueError(msg)
    if len(active_path) > MAX_COMPOSITION_DEPTH:
        chain = " -> ".join([*active_path, target])
        msg = (
            f"Workflow composition exceeds the maximum depth of "
            f"{MAX_COMPOSITION_DEPTH}: {chain}."
        )
        raise ValueError(msg)


# -- Execution scope ------------------------------------------------------


@dataclass
class ExecutionScope:
    """Runtime node in the composed execution tree.

    The root scope wraps a :class:`RunState`; nested scopes hang off it. Every
    scope owns its local inputs, progress, step results, stable binding, and
    nested scopes. Persistence always flows through the root's ``RunState``.
    """

    scope_id: str
    workflow_id: str
    definition: WorkflowDefinition | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    workflow_dir: str | None = None
    step_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    current_step_index: int = 0
    current_step_id: str | None = None
    status: RunStatus = RunStatus.RUNNING
    error: str | None = None
    workflow_scopes: dict[str, ExecutionScope] = field(default_factory=dict)
    parent: ExecutionScope | None = None
    root_state: RunState | None = None
    # Runtime-only resume intent: root --input updates flow through reached,
    # incomplete calls; an ordinary resume retains their persisted bindings.
    rebind_inputs_on_resume: bool = False

    def root(self) -> ExecutionScope:
        """Return the root scope of this tree."""
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    def _lock(self) -> Any:
        state = self.root().root_state
        return state._lock if state is not None else None

    def add_workflow_scope(self, key: str, child: ExecutionScope) -> None:
        """Attach a nested scope under the run lock (concurrent fan-out safe)."""
        lock = self._lock()
        if lock is None:
            self.workflow_scopes[key] = child
            return
        with lock:
            self.workflow_scopes[key] = child

    def record_step_result(self, step_id: str, data: dict[str, Any]) -> None:
        """Record one step result under the run lock."""
        lock = self._lock()
        if lock is None:
            self.step_results[step_id] = data
            return
        with lock:
            self.step_results[step_id] = data

    def set_step_output(self, step_id: str, output: Any) -> None:
        """Replace a recorded step's ``output`` under the run lock."""
        lock = self._lock()
        if lock is None:
            if step_id in self.step_results:
                self.step_results[step_id]["output"] = output
            return
        with lock:
            if step_id in self.step_results:
                self.step_results[step_id]["output"] = output

    def append_log(self, entry: dict[str, Any]) -> None:
        """Delegate logging to the root run state."""
        state = self.root().root_state
        if state is not None:
            state.append_log(entry)

    def build_context(self, *, is_resume: bool = False) -> StepContext:
        """Build a ``StepContext`` scoped to this node."""
        root = self.root()
        state = root.root_state
        definition = self.definition
        return StepContext(
            inputs=self.inputs,
            steps=self.step_results,
            default_integration=(
                definition.default_integration if definition is not None else None
            ),
            default_model=(
                definition.default_model if definition is not None else None
            ),
            default_options=(
                definition.default_options if definition is not None else {}
            ),
            project_root=str(state.project_root) if state is not None else None,
            run_id=state.run_id if state is not None else None,
            is_resume=is_resume,
            workflow_dir=self.workflow_dir,
        )

    def _serialize(self) -> dict[str, Any]:
        """Serialize this node and its descendants into plain JSON data."""
        return {
            "workflow_id": self.workflow_id,
            "invocation_id": self.scope_id,
            "workflow_dir": self.workflow_dir,
            "definition": (
                self.definition.data if self.definition is not None else {}
            ),
            "inputs": self.inputs,
            "status": self.status.value,
            "current_step_index": self.current_step_index,
            "step_results": self.step_results,
            "workflow_scopes": {
                key: child._serialize()
                for key, child in self.workflow_scopes.items()
            },
        }

    def _sync_to_state(self, state: RunState) -> None:
        """Copy the root scope's live fields into *state* (lock held)."""
        state.status = self.status
        state.error = self.error
        state.current_step_id = self.current_step_id
        state.current_step_index = self.current_step_index
        state.step_results = self.step_results
        state.workflow_scopes = {
            key: child._serialize()
            for key, child in self.workflow_scopes.items()
        }

    def persist(self) -> None:
        """Serialize the whole tree into the root state and save once."""
        root = self.root()
        state = root.root_state
        if state is None:
            return
        with state._lock:
            root._sync_to_state(state)
            state._save_locked()

    def record_and_save(
        self,
        context: StepContext,
        step_id: str,
        data: dict[str, Any],
        *,
        complete_child: bool = False,
    ) -> None:
        """Record a step result and complete its child in one locked write.

        Used for the workflow-call boundary so a persisted ``COMPLETED`` child
        can never lack its caller-step result.
        """
        root = self.root()
        state = root.root_state
        if state is None:
            if complete_child and step_id in self.workflow_scopes:
                self.workflow_scopes[step_id].status = RunStatus.COMPLETED
            if context.steps is not self.step_results:
                context.steps[step_id] = data
            self.step_results[step_id] = data
            return
        with state._lock:
            if complete_child and step_id in self.workflow_scopes:
                self.workflow_scopes[step_id].status = RunStatus.COMPLETED
            if context.steps is not self.step_results:
                context.steps[step_id] = data
            self.step_results[step_id] = data
            root._sync_to_state(state)
            state._save_locked()


def deserialize_scope(
    record: dict[str, Any],
    *,
    parent: ExecutionScope | None,
    root_state: RunState,
) -> ExecutionScope:
    """Rebuild a runtime ``ExecutionScope`` from a persisted record."""
    from .engine import WorkflowDefinition

    definition = WorkflowDefinition(record.get("definition", {}))
    scope = ExecutionScope(
        scope_id=record.get("invocation_id", ""),
        workflow_id=record.get("workflow_id", ""),
        definition=definition,
        inputs=record.get("inputs", {}) or {},
        workflow_dir=record.get("workflow_dir"),
        step_results=record.get("step_results", {}) or {},
        current_step_index=record.get("current_step_index", 0),
        status=RunStatus(record.get("status", RunStatus.RUNNING.value)),
        parent=parent,
        root_state=root_state,
    )
    scope.workflow_scopes = {
        key: deserialize_scope(
            child, parent=scope, root_state=root_state
        )
        for key, child in (record.get("workflow_scopes") or {}).items()
    }
    return scope


# -- Persisted-scope validation -------------------------------------------


def validate_serialized_scopes(scopes: Any) -> None:
    """Validate a persisted ``workflow_scopes`` tree.

    Raises ``ValueError`` on any malformed node so ``RunState.load`` can fail
    closed, mirroring its existing validation style.
    """
    from .engine import validate_workflow

    _validate_scope_tree(scopes, validate_workflow, path="workflow_scopes")


def _validate_scope_tree(scopes: Any, validate_workflow: Any, *, path: str) -> None:
    if not isinstance(scopes, dict):
        msg = f"Invalid run state: '{path}' must be a JSON object"
        raise ValueError(msg)
    for key, record in scopes.items():
        if not isinstance(key, str):
            msg = f"Invalid run state: '{path}' keys must be strings"
            raise ValueError(msg)
        if not isinstance(record, dict):
            msg = (
                f"Invalid run state: '{path}.{key}' must be a JSON object"
            )
            raise ValueError(msg)
        _validate_scope_record(record, validate_workflow, path=f"{path}.{key}")


def _validate_scope_record(
    record: dict[str, Any], validate_workflow: Any, *, path: str
) -> None:
    from .engine import WorkflowDefinition

    workflow_id = record.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id:
        msg = f"Invalid run state: '{path}.workflow_id' must be a non-empty string"
        raise ValueError(msg)

    inputs = record.get("inputs", {})
    if not isinstance(inputs, dict):
        msg = f"Invalid run state: '{path}.inputs' must be a JSON object"
        raise ValueError(msg)

    step_results = record.get("step_results", {})
    if not isinstance(step_results, dict):
        msg = f"Invalid run state: '{path}.step_results' must be a JSON object"
        raise ValueError(msg)
    for step_id, result in step_results.items():
        if not isinstance(result, dict):
            msg = (
                f"Invalid run state: '{path}.step_results.{step_id}' must be "
                "a JSON object"
            )
            raise ValueError(msg)

    index = record.get("current_step_index", 0)
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        msg = (
            f"Invalid run state: '{path}.current_step_index' must be a "
            f"non-negative integer, got {index!r}"
        )
        raise ValueError(msg)

    status = record.get("status", RunStatus.RUNNING.value)
    try:
        RunStatus(status)
    except ValueError:
        msg = f"Invalid run state: '{path}.status' is invalid: {status!r}"
        raise ValueError(msg) from None

    definition = record.get("definition", {})
    if not isinstance(definition, dict):
        msg = f"Invalid run state: '{path}.definition' must be a JSON object"
        raise ValueError(msg)
    parsed_definition = WorkflowDefinition(definition)
    errors = validate_workflow(parsed_definition)
    if errors:
        msg = (
            f"Invalid run state: '{path}.definition' is invalid: "
            + " ".join(errors)
        )
        raise ValueError(msg)

    # A nested scope resumes by slicing its persisted definition at
    # ``current_step_index``; an index at or beyond the step count would
    # otherwise yield an empty slice and let the scope silently complete
    # without running its remaining steps. Mirrors the root-run bound check in
    # ``WorkflowEngine.resume``, which ``RunState.load`` cannot apply until the
    # definition (and its step count) is known.
    if index >= len(parsed_definition.steps):
        msg = (
            f"Invalid run state: '{path}.current_step_index' ({index}) is "
            f"out of range for workflow {workflow_id!r} with "
            f"{len(parsed_definition.steps)} step(s)"
        )
        raise ValueError(msg)

    children = record.get("workflow_scopes", {})
    _validate_scope_tree(children, validate_workflow, path=f"{path}.workflow_scopes")


__all__ = [
    "MAX_COMPOSITION_DEPTH",
    "RESERVED_OUTPUT_NAMES",
    "ExecutionScope",
    "bind_composed_inputs",
    "check_composition_path",
    "deserialize_scope",
    "evaluate_composed_outputs",
    "evaluate_input_mapping",
    "resolve_composed_workflow",
    "validate_serialized_scopes",
    "validate_workflow_call_config",
    "validate_workflow_outputs",
]
