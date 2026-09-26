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

import hashlib
import math
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

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


def _is_valid_workflow_id(value: Any) -> bool:
    """Return whether *value* meets the engine's workflow-ID contract."""
    from .engine import is_valid_workflow_id

    return is_valid_workflow_id(value)


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
    if definition.id != workflow_id:
        msg = (
            f"Workflow registry entry {workflow_id!r} resolves to a definition "
            f"with ID {definition.id!r}."
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
        else:
            error = _json_value_error(entry["value"], path="'value'")
            if error:
                errors.append(f"Output {name!r}: {error}.")
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
        if not _is_valid_workflow_id(target):
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
        for key, value in input_mapping.items():
            if not isinstance(key, str):
                errors.append(
                    f"Workflow step {step_id!r}: 'input' keys must be strings."
                )
                continue
            error = _json_value_error(value, path=f"'input.{key}'")
            if error:
                errors.append(f"Workflow step {step_id!r}: {error}.")
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
    evaluated: dict[str, Any] = {}
    for name, value in mapping.items():
        if not isinstance(name, str):
            msg = "'input' keys must be strings."
            raise ValueError(msg)
        resolved = evaluate_expression(value, context)
        error = _json_value_error(resolved, path=f"Input {name!r}")
        if error:
            raise ValueError(f"{error}.")
        evaluated[name] = resolved
    return evaluated


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


def _json_value_error(
    value: Any, *, path: str, ancestors: set[int] | None = None
) -> str | None:
    """Return why *value* cannot be persisted as strict JSON, if any.

    Workflow outputs are copied into ``step_results`` and written with
    ``json.dump``. Reject values that would crash persistence or be silently
    changed by JSON object-key coercion; valid JSON values retain their exact
    type across the composition boundary.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return None
    if isinstance(value, float):
        if math.isfinite(value):
            return None
        return f"{path} must be a finite JSON number"
    if isinstance(value, (list, dict)):
        ancestors = ancestors if ancestors is not None else set()
        if id(value) in ancestors:
            return f"{path} contains a circular container"
        ancestors.add(id(value))
        try:
            if isinstance(value, list):
                for index, item in enumerate(value):
                    error = _json_value_error(
                        item, path=f"{path}[{index}]", ancestors=ancestors
                    )
                    if error:
                        return error
                return None
            for key, item in value.items():
                if not isinstance(key, str):
                    return f"{path} has a non-string key of type {type(key).__name__}"
                error = _json_value_error(
                    item, path=f"{path}.{key}", ancestors=ancestors
                )
                if error:
                    return error
            return None
        finally:
            ancestors.remove(id(value))
    return f"{path} is not JSON-safe (got {type(value).__name__})"


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
        value = evaluate_expression(entry["value"], context)
        error = _json_value_error(value, path=f"Output {name!r}")
        if error:
            raise ValueError(f"{error}.")
        result[name] = value
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


# -- Definition snapshots -------------------------------------------------
#
# A composed child's resolved definition is immutable for the life of its
# invocation. Persisting it as a YAML file (instead of embedding the parsed
# mapping in ``state.json``) keeps YAML-native scalars — dates, datetimes, etc.
# — that ``json.dump`` cannot encode. Execution state (status, progress, step
# results) stays in ``state.json`` so the single atomic write that ties a
# completed child to its caller result is preserved.

#: Directory under a run directory holding immutable definition snapshots.
SNAPSHOT_DIRNAME = "snapshots"

#: Snapshot file name: ``<workflow-id>-<digest>.yml``.
_SNAPSHOT_REF_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*\.yml$")


def _invocation_path(scope: ExecutionScope) -> list[str]:
    """Invocation ids from the root scope down to *scope*."""
    parts: list[str] = []
    node: ExecutionScope | None = scope
    while node is not None:
        parts.append(node.scope_id)
        node = node.parent
    return list(reversed(parts))


def _snapshot_ref_for(scope: ExecutionScope) -> str:
    """Deterministic, filesystem-safe snapshot name for *scope*.

    Derived from the invocation path and the target workflow id rather than the
    authored step id, so a step id containing ``/`` or ``:`` can never escape
    the snapshots directory.
    """
    digest = hashlib.sha256(
        "\x00".join(_invocation_path(scope)).encode("utf-8")
    ).hexdigest()[:12]
    return f"{scope.workflow_id}-{digest}.yml"


def _definition_snapshot_path(run_dir: Path, ref: str) -> Path:
    """Resolve a snapshot reference to a path inside *run_dir*/snapshots."""
    if not isinstance(ref, str) or not _SNAPSHOT_REF_PATTERN.fullmatch(ref):
        msg = f"Invalid definition snapshot reference: {ref!r}"
        raise ValueError(msg)
    snapshots_dir = (run_dir / SNAPSHOT_DIRNAME).resolve()
    path = (snapshots_dir / ref).resolve()
    if path.parent != snapshots_dir:
        msg = f"Invalid definition snapshot reference: {ref!r}"
        raise ValueError(msg)
    return path


def _read_definition_snapshot(run_dir: Path, ref: str) -> dict[str, Any]:
    """Load a persisted definition snapshot, failing closed on any problem."""
    path = _definition_snapshot_path(run_dir, ref)
    if not path.is_file():
        msg = f"Invalid run state: definition snapshot {ref!r} is missing"
        raise ValueError(msg)
    with open(path, encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            msg = (
                f"Invalid run state: definition snapshot {ref!r} is not "
                f"valid YAML: {exc}"
            )
            raise ValueError(msg) from exc
    if not isinstance(data, dict):
        msg = f"Invalid run state: definition snapshot {ref!r} must be a mapping"
        raise ValueError(msg)
    return data


def _write_definition_snapshot(
    run_dir: Path, ref: str, data: dict[str, Any]
) -> None:
    """Atomically write a definition snapshot (temp file + ``os.replace``)."""
    path = _definition_snapshot_path(run_dir, ref)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{ref}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_definition_snapshot(
    scope: ExecutionScope, data: dict[str, Any]
) -> str | None:
    """Write *data* as *scope*'s snapshot; return its reference (or ``None``).

    Returns ``None`` for an unpersisted, in-memory scope (no root ``RunState``),
    which keeps ``_serialize``'s embedded-definition fallback in play.
    """
    state = scope.root().root_state
    if state is None:
        return None
    ref = _snapshot_ref_for(scope)
    _write_definition_snapshot(state.runs_dir, ref, data)
    return ref


def _scope_definition_data(record: dict[str, Any], *, run_dir: Path) -> dict[str, Any]:
    """Return a scope record's definition, from a snapshot or the legacy embed."""
    ref = record.get("definition_snapshot")
    if isinstance(ref, str) and ref:
        return _read_definition_snapshot(run_dir, ref)
    embedded = record.get("definition", {})
    return embedded if isinstance(embedded, dict) else {}


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
    #: Persisted snapshot reference for :attr:`definition` (see the section
    #: above). ``None`` means the definition is embedded in ``state.json``
    #: (legacy states, or an in-memory scope with no run directory).
    definition_ref: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    workflow_dir: str | None = None
    step_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    current_step_index: int = 0
    current_step_id: str | None = None
    status: RunStatus = RunStatus.RUNNING
    error: str | None = None
    # A workflow caller stages a terminal child transition here so its caller
    # result can be recorded in the same locked state write.
    pending_terminal_status: RunStatus | None = None
    pending_terminal_error: str | None = None
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
            if self.parent is not None:
                entry = {
                    **entry,
                    "scope_path": _invocation_path(self)[1:],
                    "workflow_id": self.workflow_id,
                }
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
        record: dict[str, Any] = {
            "workflow_id": self.workflow_id,
            "invocation_id": self.scope_id,
            "workflow_dir": self.workflow_dir,
            "inputs": self.inputs,
            "status": self.status.value,
            "error": self.error,
            "current_step_index": self.current_step_index,
            "current_step_id": self.current_step_id,
            "step_results": self.step_results,
            "workflow_scopes": {
                key: child._serialize()
                for key, child in self.workflow_scopes.items()
            },
        }
        if self.definition_ref:
            # Immutable definition lives in a YAML snapshot; state.json keeps
            # only the reference, so YAML-native scalars never hit json.dump.
            record["definition_snapshot"] = self.definition_ref
        else:
            # Legacy/pre-snapshot states, or an in-memory scope with no run
            # directory: keep the embedded definition (already JSON-safe, since
            # it was loaded from state.json or never persisted).
            record["definition"] = (
                self.definition.data if self.definition is not None else {}
            )
        return record

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
        child_scope_id: str | None = None,
    ) -> None:
        """Record a step result and finalize its child in one locked write.

        Used for the workflow-call boundary so a persisted terminal child can
        never lack its caller-step result.
        """
        root = self.root()
        state = root.root_state
        if state is None:
            child = self.workflow_scopes.get(child_scope_id or step_id)
            if child is not None:
                if complete_child:
                    child.status = RunStatus.COMPLETED
                elif child.pending_terminal_status is not None:
                    child.status = child.pending_terminal_status
                    child.error = child.pending_terminal_error
                    child.pending_terminal_status = None
                    child.pending_terminal_error = None
            if context.steps is not self.step_results:
                context.steps[step_id] = data
            self.step_results[step_id] = data
            return
        with state._lock:
            child = self.workflow_scopes.get(child_scope_id or step_id)
            if child is not None:
                if complete_child:
                    child.status = RunStatus.COMPLETED
                elif child.pending_terminal_status is not None:
                    child.status = child.pending_terminal_status
                    child.error = child.pending_terminal_error
                    child.pending_terminal_status = None
                    child.pending_terminal_error = None
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

    definition = WorkflowDefinition(
        _scope_definition_data(record, run_dir=root_state.runs_dir)
    )
    scope = ExecutionScope(
        scope_id=record.get("invocation_id", ""),
        workflow_id=record.get("workflow_id", ""),
        definition=definition,
        definition_ref=record.get("definition_snapshot"),
        inputs=record.get("inputs", {}) or {},
        workflow_dir=record.get("workflow_dir"),
        step_results=record.get("step_results", {}) or {},
        current_step_index=record.get("current_step_index", 0),
        current_step_id=record.get("current_step_id"),
        status=RunStatus(record.get("status", RunStatus.RUNNING.value)),
        error=record.get("error"),
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


def validate_serialized_scopes(
    scopes: Any, *, run_dir: Path | None = None
) -> None:
    """Validate a persisted ``workflow_scopes`` tree.

    Raises ``ValueError`` on any malformed node so ``RunState.load`` can fail
    closed, mirroring its existing validation style. ``run_dir`` locates the
    per-run ``snapshots/`` directory so a scope's definition snapshot can be
    loaded and structurally checked.

    Validation is deliberately *structural*: it checks the shapes the engine
    relies on to slice and deserialize a scope, without consulting the
    process-global step registry. ``RunState.load`` is reached by commands that
    do not call ``load_custom_steps`` (for example ``workflow status``), so a
    full ``validate_workflow`` pass would reject an otherwise valid run whose
    composed child uses a project-installed custom step.
    """
    _validate_scope_tree(scopes, run_dir=run_dir, path="workflow_scopes")


def _validate_scope_tree(
    scopes: Any, *, run_dir: Path | None, path: str
) -> None:
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
        _validate_scope_record(record, run_dir=run_dir, path=f"{path}.{key}")


def _validate_definition_shape(definition: dict[str, Any], *, path: str) -> None:
    """Structural validation of a persisted definition snapshot.

    Only the shapes the engine needs to safely deserialize and resume a scope
    are required: a mapping ``workflow`` header, a list of step mappings each
    carrying a non-empty string ``id``, and mapping ``inputs``/``outputs`` when
    present. Step types are intentionally **not** restricted to the currently
    registered implementations; see ``validate_serialized_scopes``.
    """
    header = definition.get("workflow")
    if header is not None and not isinstance(header, dict):
        msg = f"Invalid run state: '{path}.workflow' must be a JSON object"
        raise ValueError(msg)

    for key in ("inputs", "outputs"):
        value = definition.get(key)
        if value is not None and not isinstance(value, dict):
            msg = f"Invalid run state: '{path}.{key}' must be a JSON object"
            raise ValueError(msg)

    steps = definition.get("steps")
    if not isinstance(steps, list):
        msg = f"Invalid run state: '{path}.steps' must be a list"
        raise ValueError(msg)
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            msg = f"Invalid run state: '{path}.steps[{i}]' must be a JSON object"
            raise ValueError(msg)
        step_id = step.get("id")
        if not isinstance(step_id, str) or not step_id:
            msg = (
                f"Invalid run state: '{path}.steps[{i}].id' must be a "
                "non-empty string"
            )
            raise ValueError(msg)


def _resolve_scope_definition(
    record: dict[str, Any], *, run_dir: Path | None, path: str
) -> dict[str, Any]:
    """Load a scope's definition from its snapshot, or the legacy embed.

    Raises ``ValueError`` if neither is present or the snapshot cannot be read.
    """
    ref = record.get("definition_snapshot")
    if ref is not None:
        if not isinstance(ref, str) or not ref:
            msg = (
                f"Invalid run state: '{path}.definition_snapshot' must be a "
                f"non-empty string, got {ref!r}"
            )
            raise ValueError(msg)
        if run_dir is None:
            msg = (
                f"Invalid run state: '{path}.definition_snapshot' cannot be "
                "resolved without a run directory"
            )
            raise ValueError(msg)
        return _read_definition_snapshot(run_dir, ref)

    definition = record.get("definition")
    if definition is None:
        msg = (
            f"Invalid run state: '{path}' must carry either "
            "'definition_snapshot' or 'definition'"
        )
        raise ValueError(msg)
    if not isinstance(definition, dict):
        msg = f"Invalid run state: '{path}.definition' must be a JSON object"
        raise ValueError(msg)
    return definition


def _validate_scope_record(
    record: dict[str, Any], *, run_dir: Path | None, path: str
) -> None:
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

    # The step a scope rests on. It is *not* required to appear in
    # ``definition.steps``: a scope paused inside a nested control-flow body
    # (``if``/``switch``/loop) rests on a step that only exists in that body,
    # while ``current_step_index`` still points at the enclosing step.
    current_step_id = record.get("current_step_id")
    if current_step_id is not None and (
        not isinstance(current_step_id, str) or not current_step_id
    ):
        msg = (
            f"Invalid run state: '{path}.current_step_id' must be a "
            f"non-empty string or null, got {current_step_id!r}"
        )
        raise ValueError(msg)

    status = record.get("status", RunStatus.RUNNING.value)
    try:
        RunStatus(status)
    except ValueError:
        msg = f"Invalid run state: '{path}.status' is invalid: {status!r}"
        raise ValueError(msg) from None

    error = record.get("error")
    if error is not None and not isinstance(error, str):
        msg = (
            f"Invalid run state: '{path}.error' must be a string or null, "
            f"got {error!r}"
        )
        raise ValueError(msg)

    definition = _resolve_scope_definition(record, run_dir=run_dir, path=path)
    _validate_definition_shape(definition, path=f"{path}.definition")

    # A nested scope resumes by slicing its persisted definition at
    # ``current_step_index``; an index at or beyond the step count would
    # otherwise yield an empty slice and let the scope silently complete
    # without running its remaining steps. Mirrors the root-run bound check in
    # ``WorkflowEngine.resume``, which ``RunState.load`` cannot apply until the
    # definition (and its step count) is known.
    steps = definition["steps"]
    if index >= len(steps):
        msg = (
            f"Invalid run state: '{path}.current_step_index' ({index}) is "
            f"out of range for workflow {workflow_id!r} with "
            f"{len(steps)} step(s)"
        )
        raise ValueError(msg)

    children = record.get("workflow_scopes", {})
    _validate_scope_tree(children, run_dir=run_dir, path=f"{path}.workflow_scopes")


__all__ = [
    "MAX_COMPOSITION_DEPTH",
    "RESERVED_OUTPUT_NAMES",
    "SNAPSHOT_DIRNAME",
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
    "write_definition_snapshot",
]
