"""Workflow engine — loads, validates, and executes workflow YAML definitions.

The engine is the orchestrator that:
- Parses workflow YAML definitions
- Validates step configurations and requirements
- Executes steps sequentially, dispatching to the correct step type
- Manages state persistence for resume capability
- Handles control flow (branching, loops, fan-out/fan-in)
"""

from __future__ import annotations

import dataclasses
import json
import os
import re
import tempfile
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ..integration_state import (
    default_integration_key,
    try_read_integration_json,
)
from .base import RunStatus, StepContext, StepResult, StepStatus


# -- Workflow Definition --------------------------------------------------


class WorkflowDefinition:
    """Parsed and validated workflow YAML definition."""

    def __init__(self, data: dict[str, Any], source_path: Path | None = None) -> None:
        self.data = data
        self.source_path = source_path

        workflow = data.get("workflow", {})
        self.id: str = workflow.get("id", "")
        self.name: str = workflow.get("name", "")
        self.version: str = workflow.get("version", "0.0.0")
        self.author: str = workflow.get("author", "")
        self.description: str = workflow.get("description", "")
        self.schema_version: str = data.get("schema_version", "1.0")

        # Defaults
        self.default_integration: str | None = workflow.get("integration")
        self.default_model: str | None = workflow.get("model")
        self.default_options: dict[str, Any] = workflow.get("options") or {}
        if not isinstance(self.default_options, dict):
            self.default_options = {}

        # Advisory pre-conditions (spec-kit version / integrations a workflow
        # expects). Validated by ``validate_workflow`` (recognized keys only;
        # see ``_RECOGNIZED_REQUIRES_KEYS``) but NOT enforced at run time — they
        # are not a security boundary. In particular there is no
        # ``requires.permissions`` capability gate: shell steps always run with
        # the user's privileges.
        #
        # Holds the raw parsed value, so before ``validate_workflow`` runs it may
        # be a non-mapping (``None`` for a bare ``requires:``, a list for
        # ``requires: []``, etc.); typed ``Any`` rather than ``dict[str, Any]``
        # to avoid implying it is always a mapping at this point.
        self.requires: Any = data.get("requires", {})

        # Inputs
        self.inputs: dict[str, Any] = data.get("inputs", {})

        # Steps
        self.steps: list[dict[str, Any]] = data.get("steps", [])

    @classmethod
    def from_yaml(cls, path: Path) -> WorkflowDefinition:
        """Load a workflow definition from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            msg = f"Workflow YAML must be a mapping, got {type(data).__name__}."
            raise ValueError(msg)
        return cls(data, source_path=path)

    @classmethod
    def from_string(cls, content: str) -> WorkflowDefinition:
        """Load a workflow definition from a YAML string."""
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            msg = f"Workflow YAML must be a mapping, got {type(data).__name__}."
            raise ValueError(msg)
        return cls(data)


# -- Workflow Validation --------------------------------------------------

# ID format: lowercase alphanumeric with hyphens
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")

# Keys accepted under a workflow's ``requires`` block: the advisory
# pre-conditions documented for workflows (``speckit_version`` and
# ``integrations``). This is the *workflow* schema only — the bundle manifest's
# ``requires`` (see ``bundler/models/manifest.py``) is a separate schema that
# also carries ``tools``/``mcp``; those are not workflow ``requires`` keys.
# Any other key — notably ``permissions`` — is rejected by ``validate_workflow``
# so it is never mistaken for an enforced runtime control.
_RECOGNIZED_REQUIRES_KEYS = frozenset({"speckit_version", "integrations"})

# Valid step types (matching STEP_REGISTRY keys)
def _get_valid_step_types() -> set[str]:
    """Return valid step types from the registry, with a built-in fallback."""
    from . import STEP_REGISTRY
    if STEP_REGISTRY:
        return set(STEP_REGISTRY.keys())
    return {
        "command", "shell", "prompt", "gate", "if", "init",
        "switch", "while", "do-while", "fan-out", "fan-in",
    }


def validate_workflow(definition: WorkflowDefinition) -> list[str]:
    """Validate a workflow definition and return a list of error messages.

    An empty list means the workflow is valid.
    """
    errors: list[str] = []

    # -- Schema version ---------------------------------------------------
    if definition.schema_version not in ("1.0", "1"):
        errors.append(
            f"Unsupported schema_version {definition.schema_version!r}. "
            f"Expected '1.0'."
        )

    # -- Top-level fields -------------------------------------------------
    if not definition.id:
        errors.append("Workflow is missing 'workflow.id'.")
    elif not _ID_PATTERN.match(definition.id):
        errors.append(
            f"Workflow ID {definition.id!r} must be lowercase alphanumeric "
            f"with hyphens."
        )

    if not definition.name:
        errors.append("Workflow is missing 'workflow.name'.")

    if not definition.version:
        errors.append("Workflow is missing 'workflow.version'.")
    elif not re.match(r"^\d+\.\d+\.\d+$", definition.version):
        errors.append(
            f"Workflow version {definition.version!r} is not valid "
            f"semantic versioning (expected X.Y.Z)."
        )

    # -- Inputs -----------------------------------------------------------
    if not isinstance(definition.inputs, dict):
        errors.append("'inputs' must be a mapping (or omitted).")
    else:
        for input_name, input_def in definition.inputs.items():
            if not isinstance(input_def, dict):
                errors.append(f"Input {input_name!r} must be a mapping.")
                continue
            input_type = input_def.get("type")
            if input_type and input_type not in ("string", "number", "boolean"):
                errors.append(
                    f"Input {input_name!r} has invalid type {input_type!r}. "
                    f"Must be 'string', 'number', or 'boolean'."
                )

            # Validate the default eagerly so authoring mistakes (e.g. a
            # default not in the declared enum, or a non-numeric default for
            # a number input) surface at install/validation time instead of
            # at workflow-execution time. ``"auto"`` for the integration
            # input is a runtime-resolved sentinel, so only the
            # enum-membership check is exempted for that exact case — the
            # declared type is still enforced (e.g. ``type: number`` paired
            # with ``default: "auto"`` is still rejected).
            if "default" in input_def:
                default_value = input_def["default"]
                is_auto_integration = (
                    input_name == "integration" and default_value == "auto"
                )
                validation_input_def: dict[str, Any] = input_def
                if is_auto_integration and "enum" in input_def:
                    validation_input_def = {
                        key: value
                        for key, value in input_def.items()
                        if key != "enum"
                    }
                try:
                    WorkflowEngine._coerce_input(
                        input_name, default_value, validation_input_def
                    )
                except ValueError as exc:
                    errors.append(
                        f"Input {input_name!r} has invalid default: {exc}"
                    )

    # -- Requires ---------------------------------------------------------
    # ``requires`` declares advisory pre-conditions (the spec-kit version and
    # integrations a workflow expects). Only a fixed set of keys is recognized;
    # reject anything else so authoring typos surface here instead of being
    # silently ignored at runtime. In particular ``requires.permissions`` is
    # rejected explicitly: it reads like a runtime capability gate, but no such
    # gate exists — a ``shell`` step always runs with the user's privileges, so
    # declaring it would give a false sense of sandboxing.
    #
    # Mirror ``inputs`` validation: an omitted block defaults to ``{}`` and is
    # valid, but any present-but-non-mapping value — ``requires:`` (YAML null),
    # ``requires: []`` or ``requires: ''`` — is an authoring error and must
    # surface here rather than be silently ignored at runtime.
    if not isinstance(definition.requires, dict):
        errors.append("'requires' must be a mapping (or omitted).")
    else:
        for key in definition.requires:
            if key == "permissions":
                errors.append(
                    "'requires.permissions' is not a recognized or "
                    "enforced capability gate — shell steps always run "
                    "with the user's privileges. Remove it and gate "
                    "sensitive steps with a 'gate' step instead."
                )
            elif key not in _RECOGNIZED_REQUIRES_KEYS:
                errors.append(
                    f"Unknown 'requires' key {key!r}. Recognized keys: "
                    f"{', '.join(sorted(_RECOGNIZED_REQUIRES_KEYS))}."
                )

    # -- Steps ------------------------------------------------------------
    if not isinstance(definition.steps, list):
        errors.append("'steps' must be a list.")
        return errors
    if not definition.steps:
        errors.append("Workflow has no steps defined.")

    seen_ids: set[str] = set()
    _validate_steps(definition.steps, seen_ids, errors)

    return errors


def _validate_steps(
    steps: list[dict[str, Any]],
    seen_ids: set[str],
    errors: list[str],
) -> None:
    """Recursively validate a list of steps."""
    from . import STEP_REGISTRY

    for step_config in steps:
        if not isinstance(step_config, dict):
            errors.append(f"Step must be a mapping, got {type(step_config).__name__}.")
            continue

        step_id = step_config.get("id")
        if not step_id:
            errors.append("Step is missing 'id' field.")
            continue

        if ":" in step_id:
            errors.append(
                f"Step ID {step_id!r} contains ':' which is reserved "
                f"for engine-generated nested IDs (parentId:childId)."
            )

        if step_id in seen_ids:
            errors.append(f"Duplicate step ID {step_id!r}.")
        seen_ids.add(step_id)

        # Determine step type
        step_type = step_config.get("type", "command")
        if step_type not in _get_valid_step_types():
            errors.append(
                f"Step {step_id!r} has invalid type {step_type!r}."
            )
            continue

        # Delegate to step-specific validation
        step_impl = STEP_REGISTRY.get(step_type)
        if step_impl:
            step_errors = step_impl.validate(step_config)
            errors.extend(step_errors)

        # Validate optional `continue_on_error` field. The engine honours
        # this on any step that returns StepStatus.FAILED so the pipeline can route
        # around the failure via a downstream `if` or `switch` (or a
        # `gate` that surfaces the failure to the operator via message
        # interpolation). The field must be a literal boolean —
        # coercion from truthy strings is deliberately not supported so
        # authoring mistakes surface at validation time rather than
        # silently changing run semantics.
        if "continue_on_error" in step_config:
            coe = step_config["continue_on_error"]
            if not isinstance(coe, bool):
                errors.append(
                    f"Step {step_id!r}: 'continue_on_error' must be a "
                    f"boolean, got {type(coe).__name__}."
                )

        # Fan-in: every wait_for id must reference a step declared at or before
        # this point. An id not yet seen is either a typo (unknown step) or a
        # forward reference (the target runs after this fan-in, so its results
        # cannot exist yet) — both are wiring errors that previously surfaced as
        # a silent empty result + COMPLETED. A step that is declared but only
        # conditionally executed (e.g. inside an if/switch branch) is still
        # "seen" here, so a legitimately-empty result at runtime stays valid.
        if step_type == "fan-in":
            wait_for = step_config.get("wait_for")
            if isinstance(wait_for, list):
                for wid in wait_for:
                    if not isinstance(wid, str):
                        # A non-string entry (e.g. YAML `wait_for: [123]`) can
                        # never match a real step id, so the join is silently
                        # empty at runtime — surface it as a wiring error.
                        errors.append(
                            f"Fan-in step {step_id!r}: 'wait_for' entries must "
                            f"be step-id strings, got {type(wid).__name__} "
                            f"({wid!r})."
                        )
                    elif wid == step_id:
                        # The fan-in's own id is already in seen_ids by now, so
                        # a self-reference would pass the membership check below
                        # while still producing an empty join at runtime.
                        errors.append(
                            f"Fan-in step {step_id!r}: 'wait_for' references "
                            f"itself; a fan-in cannot wait for its own results."
                        )
                    elif wid not in seen_ids:
                        errors.append(
                            f"Fan-in step {step_id!r}: 'wait_for' references "
                            f"unknown or not-yet-declared step id {wid!r}."
                        )

        # Recursively validate nested steps
        for nested_key in ("then", "else", "steps"):
            nested = step_config.get(nested_key)
            if isinstance(nested, list):
                _validate_steps(nested, seen_ids, errors)

        # Validate switch cases
        cases = step_config.get("cases")
        if isinstance(cases, dict):
            for _case_key, case_steps in cases.items():
                if isinstance(case_steps, list):
                    _validate_steps(case_steps, seen_ids, errors)

        # Validate switch default
        default = step_config.get("default")
        if isinstance(default, list):
            _validate_steps(default, seen_ids, errors)

        # Validate fan-out nested step (template — not added to seen_ids
        # since the engine generates parentId:templateId:index at runtime)
        fan_step = step_config.get("step")
        if isinstance(fan_step, dict):
            fan_errors: list[str] = []
            _validate_steps([fan_step], set(), fan_errors)
            errors.extend(fan_errors)


# -- Run State Persistence ------------------------------------------------


class RunState:
    """Manages workflow run state for persistence and resume."""

    # ``run_id`` is interpolated into a filesystem path (``runs/<run_id>``)
    # by both ``save()`` and ``load()``. Constrain it to a charset that
    # cannot contain path separators (``/`` ``\``), parent-directory
    # segments (``..``), or NULs — anything that could escape the
    # ``.specify/workflows/runs/`` directory or be mis-interpreted by the
    # filesystem. The first-character anchor blocks IDs that start with
    # ``-`` (which would be mistaken for a CLI flag in error messages
    # and shell completions).
    _RUN_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")

    @classmethod
    def _validate_run_id(cls, run_id: str) -> None:
        """Raise ``ValueError`` if ``run_id`` is not a safe path component.

        This is the single source of truth for what counts as a valid
        ``run_id``. ``__init__`` calls it to reject malformed IDs at
        construction time; ``load`` calls it *before* interpolating the
        ID into a path so a malicious value cannot probe or read files
        outside ``.specify/workflows/runs/<run_id>/``.
        """
        if not isinstance(run_id, str) or not cls._RUN_ID_PATTERN.match(run_id):
            raise ValueError(
                f"Invalid run_id {run_id!r}: must be alphanumeric with "
                "hyphens/underscores only (and must start with an "
                "alphanumeric character)."
            )

    def __init__(
        self,
        run_id: str | None = None,
        workflow_id: str = "",
        project_root: Path | None = None,
    ) -> None:
        # ``run_id is None`` (omitted) → auto-generate. An explicit empty
        # string is *not* the same as "omitted" and must be validated like
        # any other caller-provided value — otherwise ``__init__("")``
        # would silently substitute a UUID while ``load("")`` rejects, and
        # the two entry points would diverge on the empty-string vector.
        if run_id is None:
            self.run_id = str(uuid.uuid4())[:8]
        else:
            self.run_id = run_id
        self._validate_run_id(self.run_id)
        self.workflow_id = workflow_id
        self.project_root = project_root or Path(".")
        self.status = RunStatus.CREATED
        self.current_step_index = 0
        self.current_step_id: str | None = None
        self.step_results: dict[str, dict[str, Any]] = {}
        # Guards step_results mutation and save() so a concurrent fan-out cannot
        # mutate the dict while save() is serializing it (which would raise
        # "dictionary changed size during iteration").
        self._lock = threading.Lock()
        # Serializes append_log's list append + log.jsonl write so concurrent
        # fan-out workers cannot interleave or corrupt log lines. Kept separate
        # from _lock so frequent logging never contends with state saves; since
        # append_log is never called while _lock is held, the two never nest.
        self._log_lock = threading.Lock()
        self.inputs: dict[str, Any] = {}
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.log_entries: list[dict[str, Any]] = []

    @property
    def runs_dir(self) -> Path:
        return self.project_root / ".specify" / "workflows" / "runs" / self.run_id

    def record_step_result(self, step_id: str, data: dict[str, Any]) -> None:
        """Record one step's result under the run lock.

        Routing the mutation through the lock keeps it from racing a concurrent
        ``save()`` that is iterating ``step_results`` (e.g. during a concurrent
        fan-out). For a sequential run this is an uncontended lock.
        """
        with self._lock:
            self.step_results[step_id] = data

    def set_step_output(self, step_id: str, output: Any) -> None:
        """Replace an already-recorded step's ``output`` under the run lock.

        Fan-out updates its parent step's output after the items have run;
        routing that nested mutation through the lock keeps it from racing a
        ``save()`` serializing ``step_results`` — the same invariant
        ``record_step_result`` provides for the top-level assignment.
        """
        with self._lock:
            if step_id in self.step_results:
                self.step_results[step_id]["output"] = output

    def save(self) -> None:
        """Persist current state to disk.

        Held under the run lock and written atomically (temp file + ``os.replace``)
        so a concurrent fan-out can neither mutate ``step_results`` mid-serialization
        nor leave a reader observing a half-written file. Racing writers only
        contend to be last; they never corrupt.
        """
        runs_dir = self.runs_dir
        runs_dir.mkdir(parents=True, exist_ok=True)

        with self._lock:
            # Stamp updated_at inside the lock so the timestamp matches the
            # snapshot this thread serializes (concurrent savers don't race it).
            self.updated_at = datetime.now(timezone.utc).isoformat()
            state_data = {
                "run_id": self.run_id,
                "workflow_id": self.workflow_id,
                "status": self.status.value,
                "current_step_index": self.current_step_index,
                "current_step_id": self.current_step_id,
                "step_results": self.step_results,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
            self._atomic_write_json(runs_dir / "state.json", state_data)
            self._atomic_write_json(runs_dir / "inputs.json", {"inputs": self.inputs})

    @staticmethod
    def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
        """Write *data* as indented JSON to *path* atomically (temp + ``os.replace``)."""
        fd, tmp = tempfile.mkstemp(
            dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    @classmethod
    def load(cls, run_id: str, project_root: Path) -> RunState:
        """Load a run state from disk.

        Validates ``run_id`` against ``_RUN_ID_PATTERN`` *before* building
        the lookup path. Without this guard, a caller passing a value like
        ``../escape`` (e.g. via ``specify workflow resume`` CLI argument)
        would interpolate path-traversal segments into
        ``runs_dir`` below, letting ``state_path.exists()`` probe arbitrary
        paths and ``json.load`` read attacker-planted JSON from outside
        the project's ``runs/`` directory. ``__init__`` already runs this
        check on the stored ``state_data["run_id"]``, but that fires
        *after* the file lookup — too late to prevent the disclosure.
        Mirrors the precedent in ``agents._ensure_within_directory``.
        """
        cls._validate_run_id(run_id)
        runs_dir = project_root / ".specify" / "workflows" / "runs" / run_id
        state_path = runs_dir / "state.json"
        if not state_path.exists():
            msg = f"Run state not found: {state_path}"
            raise FileNotFoundError(msg)

        with open(state_path, encoding="utf-8") as f:
            state_data = json.load(f)

        state = cls(
            run_id=state_data["run_id"],
            workflow_id=state_data["workflow_id"],
            project_root=project_root,
        )
        state.status = RunStatus(state_data["status"])
        state.current_step_index = state_data.get("current_step_index", 0)
        state.current_step_id = state_data.get("current_step_id")
        state.step_results = state_data.get("step_results", {})
        state.created_at = state_data.get("created_at", "")
        state.updated_at = state_data.get("updated_at", "")

        inputs_path = runs_dir / "inputs.json"
        if inputs_path.exists():
            with open(inputs_path, encoding="utf-8") as f:
                inputs_data = json.load(f)
            state.inputs = inputs_data.get("inputs", {})

        return state

    def append_log(self, entry: dict[str, Any]) -> None:
        """Append a log entry to the run log.

        Held under ``_log_lock`` so concurrent fan-out workers serialize their
        list append and ``log.jsonl`` write rather than interleaving lines.
        """
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        runs_dir = self.runs_dir
        runs_dir.mkdir(parents=True, exist_ok=True)
        with self._log_lock:
            self.log_entries.append(entry)
            with open(runs_dir / "log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")


# -- Workflow Engine ------------------------------------------------------


class WorkflowEngine:
    """Orchestrator that loads, validates, and executes workflow definitions."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path(".")
        self.on_step_start: Any = None  # Callable[[str, str], None] | None
        # Serializes on_step_start so a concurrent fan-out can't interleave the
        # callback's output (the CLI sets it to a console.print lambda). Uncontended
        # for sequential runs.
        self._callback_lock = threading.Lock()

    def load_workflow(self, source: str | Path) -> WorkflowDefinition:
        """Load a workflow from an installed ID or a local YAML path.

        Parameters
        ----------
        source:
            Either a workflow ID (looked up in the installed workflows
            directory) or a path to a YAML file.

        Returns
        -------
        A parsed ``WorkflowDefinition`` (not yet validated; call
        ``validate_workflow()`` or ``engine.validate()`` separately).

        Raises
        ------
        FileNotFoundError:
            If the workflow file cannot be found.
        ValueError:
            If the workflow YAML is invalid.
        """
        path = Path(source).expanduser()

        # Try as a direct file path first
        if path.suffix.lower() in (".yml", ".yaml") and path.is_file():
            return WorkflowDefinition.from_yaml(path)

        # Try as an installed workflow ID
        installed_path = (
            self.project_root
            / ".specify"
            / "workflows"
            / str(source)
            / "workflow.yml"
        )
        if installed_path.exists():
            return WorkflowDefinition.from_yaml(installed_path)

        msg = f"Workflow not found: {source}"
        raise FileNotFoundError(msg)

    def validate(self, definition: WorkflowDefinition) -> list[str]:
        """Validate a workflow definition."""
        return validate_workflow(definition)

    def execute(
        self,
        definition: WorkflowDefinition,
        inputs: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> RunState:
        """Execute a workflow definition.

        Parameters
        ----------
        definition:
            The validated workflow definition.
        inputs:
            User-provided input values.
        run_id:
            Optional run ID (uses SPECKIT_WORKFLOW_RUN_ID when set, otherwise auto-generated).

        Returns
        -------
        The final ``RunState`` after execution completes (or pauses).
        """
        from . import STEP_REGISTRY

        effective_run_id = run_id
        if effective_run_id is None:
            env_run_id = os.environ.get("SPECKIT_WORKFLOW_RUN_ID", "").strip()
            if env_run_id:
                effective_run_id = env_run_id

        state = RunState(
            run_id=effective_run_id,
            workflow_id=definition.id,
            project_root=self.project_root,
        )

        # Persist a copy of the workflow definition so resume can
        # reload it even if the original source is no longer available
        # (e.g. a local YAML path that was moved or deleted).
        run_dir = self.project_root / ".specify" / "workflows" / "runs" / state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        workflow_copy = run_dir / "workflow.yml"
        import yaml
        with open(workflow_copy, "w", encoding="utf-8") as f:
            yaml.safe_dump(definition.data, f, sort_keys=False)

        # Resolve inputs
        resolved_inputs = self._resolve_inputs(definition, inputs or {})
        state.inputs = resolved_inputs
        state.status = RunStatus.RUNNING
        state.save()

        context = StepContext(
            inputs=resolved_inputs,
            default_integration=definition.default_integration,
            default_model=definition.default_model,
            default_options=definition.default_options,
            project_root=str(self.project_root),
            run_id=state.run_id,
        )

        # Execute steps
        try:
            self._execute_steps(definition.steps, context, state, STEP_REGISTRY)
        except KeyboardInterrupt:
            state.status = RunStatus.PAUSED
            state.append_log({"event": "workflow_interrupted"})
            state.save()
            return state
        except Exception as exc:
            state.status = RunStatus.FAILED
            state.append_log({"event": "workflow_failed", "error": str(exc)})
            state.save()
            raise

        if state.status == RunStatus.RUNNING:
            state.status = RunStatus.COMPLETED
        state.append_log({"event": "workflow_finished", "status": state.status.value})
        state.save()
        return state

    def resume(
        self,
        run_id: str,
        inputs: dict[str, Any] | None = None,
    ) -> RunState:
        """Resume a paused or failed workflow run.

        When ``inputs`` is provided, the values are merged over the run's
        persisted inputs and re-resolved through the same typed validation
        path used by :meth:`execute`, so the resumed step sees updated
        workflow inputs. Keys not supplied keep their persisted values; an
        empty/``None`` ``inputs`` leaves the run's inputs unchanged.
        """
        state = RunState.load(run_id, self.project_root)
        if state.status not in (RunStatus.PAUSED, RunStatus.FAILED):
            msg = f"Cannot resume run {run_id!r} with status {state.status.value!r}."
            raise ValueError(msg)

        # Load the workflow definition — try the persisted copy in the
        # run directory first so resume works even if the original
        # source (e.g. a local YAML path) is no longer available.
        run_dir = self.project_root / ".specify" / "workflows" / "runs" / run_id
        run_copy = run_dir / "workflow.yml"
        if run_copy.exists():
            definition = WorkflowDefinition.from_yaml(run_copy)
        else:
            definition = self.load_workflow(state.workflow_id)

        # Merge any newly-supplied inputs over the persisted ones and
        # re-validate through the same typing path as the initial run.
        if inputs:
            merged = {**state.inputs, **inputs}
            state.inputs = self._resolve_inputs(definition, merged)

        # Restore context
        context = StepContext(
            inputs=state.inputs,
            steps=state.step_results,
            default_integration=definition.default_integration,
            default_model=definition.default_model,
            default_options=definition.default_options,
            project_root=str(self.project_root),
            run_id=state.run_id,
        )

        from . import STEP_REGISTRY

        state.status = RunStatus.RUNNING
        state.save()

        # Resume from the current step — re-execute it so gates
        # can prompt interactively again.
        remaining_steps = definition.steps[state.current_step_index :]
        step_offset = state.current_step_index

        try:
            self._execute_steps(
                remaining_steps, context, state, STEP_REGISTRY,
                step_offset=step_offset,
            )
        except KeyboardInterrupt:
            state.status = RunStatus.PAUSED
            state.append_log({"event": "workflow_interrupted"})
            state.save()
            return state
        except Exception as exc:
            state.status = RunStatus.FAILED
            state.append_log({"event": "resume_failed", "error": str(exc)})
            state.save()
            raise

        if state.status == RunStatus.RUNNING:
            state.status = RunStatus.COMPLETED
        state.append_log({"event": "workflow_finished", "status": state.status.value})
        state.save()
        return state

    @staticmethod
    def _record_result(
        context: StepContext, state: RunState, step_id: str, data: dict[str, Any]
    ) -> None:
        """Record a step result into both the live context and persistent state.

        ``record_step_result`` writes ``state.step_results`` under the run lock.
        On a resume run ``context.steps`` *is* that same dict, so that locked
        write is the only one needed; mirror into ``context.steps`` separately
        only when it is a distinct object (a fresh run), to avoid an unlocked
        mutation of the shared dict that could race a concurrent ``save()``.
        """
        if context.steps is not state.step_results:
            context.steps[step_id] = data
        state.record_step_result(step_id, data)

    def _execute_steps(
        self,
        steps: list[dict[str, Any]],
        context: StepContext,
        state: RunState,
        registry: dict[str, Any],
        *,
        step_offset: int = 0,
    ) -> None:
        """Execute a list of steps sequentially."""
        for i, step_config in enumerate(steps):
            step_id = step_config.get("id", f"step-{i}")
            step_type = step_config.get("type", "command")

            state.current_step_id = step_id
            if step_offset >= 0:
                state.current_step_index = step_offset + i
            state.save()

            state.append_log(
                {"event": "step_started", "step_id": step_id, "type": step_type}
            )

            # Log progress — use the engine's on_step_start callback if set,
            # otherwise stay silent (library-safe default).
            label = step_config.get("command", "") or step_type
            if self.on_step_start is not None:
                with self._callback_lock:
                    self.on_step_start(step_id, label)

            step_impl = registry.get(step_type)
            if not step_impl:
                state.status = RunStatus.FAILED
                state.append_log(
                    {
                        "event": "step_failed",
                        "step_id": step_id,
                        "error": f"Unknown step type: {step_type!r}",
                    }
                )
                state.save()
                return

            result: StepResult = step_impl.execute(step_config, context)

            # Record step results — prefer resolved values from step output
            step_data = {
                "type": step_type,
                "integration": result.output.get("integration")
                or step_config.get("integration")
                or context.default_integration,
                "model": result.output.get("model")
                or step_config.get("model")
                or context.default_model,
                "options": result.output.get("options")
                or step_config.get("options", {}),
                "input": result.output.get("input")
                or step_config.get("input", {}),
                "output": result.output,
                "status": result.status.value,
            }
            self._record_result(context, state, step_id, step_data)

            state.append_log(
                {
                    "event": "step_completed",
                    "step_id": step_id,
                    "status": result.status.value,
                }
            )

            # Handle gate pauses
            if result.status == StepStatus.PAUSED:
                state.status = RunStatus.PAUSED
                state.save()
                return

            # Handle failures
            if result.status == StepStatus.FAILED:
                # Gate abort (output.aborted) maps to ABORTED status.
                # Aborts are deliberate operator decisions, so
                # `continue_on_error` does NOT override them — that flag
                # is for transient/expected step failures only.
                if result.output.get("aborted"):
                    state.status = RunStatus.ABORTED
                    state.append_log(
                        {
                            "event": "workflow_aborted",
                            "step_id": step_id,
                        }
                    )
                    state.save()
                    return

                # `continue_on_error: true` lets the pipeline route
                # around the failure instead of halting. The step
                # result (including exit_code, stderr, status) is
                # still recorded so a downstream `if` or `switch`
                # can branch on it (or a `gate` can surface it to the
                # operator via message interpolation). Log a single,
                # unambiguous event per failure resolution — either
                # the run continued past it, or it halted.
                #
                # Use identity comparison (`is True`) rather than
                # truthiness so that only a literal boolean enables
                # the behaviour, even if validation was skipped.
                # Validation rejects non-bool values at parse time,
                # but `WorkflowEngine.execute()` does not auto-validate
                # (see `WorkflowEngine.load_workflow`, whose docstring
                # explicitly notes "not yet validated; call
                # `validate_workflow()` or `engine.validate()`
                # separately"), so a caller passing an unvalidated
                # definition could otherwise see truthy non-bool
                # values like the string `"true"` silently change
                # run semantics.
                if step_config.get("continue_on_error") is True:
                    state.append_log(
                        {
                            "event": "step_continue_on_error",
                            "step_id": step_id,
                            "error": result.error,
                        }
                    )
                    state.save()
                    continue

                state.status = RunStatus.FAILED
                state.append_log(
                    {
                        "event": "step_failed",
                        "step_id": step_id,
                        "error": result.error,
                    }
                )
                state.save()
                return

            # Execute nested steps (from control flow)
            # NOTE: Nested steps run with step_offset=-1 so they don't
            # update current_step_index.  If a nested step pauses,
            # resume will re-run the parent step and its nested body.
            # A step-path stack for exact nested resume is a future
            # enhancement.
            if result.next_steps:
                self._execute_steps(
                    result.next_steps, context, state, registry,
                    step_offset=-1,
                )
                if state.status in (
                    RunStatus.PAUSED,
                    RunStatus.FAILED,
                    RunStatus.ABORTED,
                ):
                    return

                # Loop iteration: while/do-while re-evaluate after body
                if step_type in ("while", "do-while"):
                    from .expressions import evaluate_condition

                    max_iters = step_config.get("max_iterations")
                    if not isinstance(max_iters, int) or max_iters < 1:
                        max_iters = 10
                    condition = step_config.get("condition", False)
                    for _loop_iter in range(max_iters - 1):
                        if not evaluate_condition(condition, context):
                            break
                        # Namespace nested step IDs per iteration
                        # so logs and state keys are unique.
                        # Execute one step at a time and alias each
                        # result back to the unprefixed key so that
                        # later steps in the same body and the loop
                        # condition see the latest values.
                        for ns_idx, ns in enumerate(result.next_steps):
                            ns_copy = dict(ns)
                            orig = ns_copy.get("id")
                            base_id = orig or f"step-{ns_idx}"
                            ns_copy["id"] = f"{step_id}:{base_id}:{_loop_iter + 1}"
                            self._execute_steps(
                                [ns_copy], context, state, registry,
                                step_offset=-1,
                            )
                            if state.status in (
                                RunStatus.PAUSED,
                                RunStatus.FAILED,
                                RunStatus.ABORTED,
                            ):
                                return
                            if orig and ns_copy["id"] in context.steps:
                                self._record_result(
                                    context, state, orig,
                                    context.steps[ns_copy["id"]],
                                )

            # Fan-out: execute the nested step template once per item. Honors
            # max_concurrency — <=1 runs sequentially (default, historical
            # behavior); >1 runs up to that many items concurrently. Either way
            # results are assembled in item order under the
            # parentId:templateId:index id grammar.
            if step_type == "fan-out":
                items = result.output.get("items", [])
                template = result.output.get("step_template", {})
                if template and items:
                    fan_out_results = self._run_fan_out(
                        items, template, step_id, context, state, registry,
                        result.output.get("max_concurrency", 1),
                    )
                    context.item = None
                    # Preserve original output and add collected results
                    fan_out_output = dict(result.output)
                    fan_out_output["results"] = fan_out_results
                    # set_step_output updates the recorded dict under the run lock;
                    # context.steps[step_id] is that same object, so it reflects the
                    # change too — no separate (unlocked) context mutation needed.
                    state.set_step_output(step_id, fan_out_output)
                    if state.status in (
                        RunStatus.PAUSED,
                        RunStatus.FAILED,
                        RunStatus.ABORTED,
                    ):
                        return
                else:
                    # Empty items or no template — normalize output
                    result.output["results"] = []
                    state.set_step_output(step_id, result.output)

    def _run_fan_out(
        self,
        items: list[Any],
        template: dict[str, Any],
        step_id: str,
        context: StepContext,
        state: RunState,
        registry: dict[str, Any],
        max_concurrency: Any,
    ) -> list[Any]:
        """Run a fan-out template once per item; return per-item outputs in item order.

        ``max_concurrency`` <= 1 (the default) runs items sequentially, identical
        to the historical fan-out behavior. ``max_concurrency`` > 1 runs items on a
        bounded thread pool using a sliding submission window of that size: at most
        that many items are ever in flight, and no new item is launched once the run
        has reached a halting status, so a halt cannot keep starting queued work.

        Results are always returned in item order (never completion order). On a
        halt (PAUSED/FAILED/ABORTED) the returned prefix is the items up to and
        including the first item *in item order* whose own execution halted the run
        — identical to the sequential path. Later items that have not yet started
        are cancelled; any already running are allowed to finish but their outputs
        are ignored. Halt is attributed per item from that item's recorded result
        (not the shared run status, which a concurrently-running later item may have
        already flipped), so the prefix never drops the actual halting item.

        ``max_concurrency`` is coerced with ``int()``; a value that cannot be
        coerced (``None``, a non-numeric string, …) or that coerces to <= 1 runs
        sequentially, while a numeric string like ``"4"`` or a float like ``4.0``
        is honored.
        """
        if not items:
            return []

        halting = (RunStatus.PAUSED, RunStatus.FAILED, RunStatus.ABORTED)
        try:
            workers = max(1, int(max_concurrency))
        except (TypeError, ValueError):
            workers = 1
        # Never spin up more workers than there is work — bounds a user-controlled
        # max_concurrency from over-allocating threads.
        workers = min(workers, len(items))

        base_id = template.get("id", "item")

        def item_id(idx: int) -> str:
            # Per-item ID grammar: parentId:templateId:index.
            return f"{step_id}:{base_id}:{idx}"

        def run_item(idx: int, item_ctx: StepContext) -> Any:
            item_step = dict(template)
            item_step["id"] = item_id(idx)
            self._execute_steps(
                [item_step], item_ctx, state, registry, step_offset=-1,
            )
            # Read back through the context that was actually executed against,
            # not the outer closure — clearer and robust if StepContext copying
            # ever stops sharing the steps dict by reference.
            return item_ctx.steps.get(item_step["id"], {}).get("output", {})

        # Sequential path — identical to the historical behavior.
        if workers <= 1:
            results: list[Any] = []
            for item_idx, item_val in enumerate(items):
                context.item = item_val
                results.append(run_item(item_idx, context))
                if state.status in halting:
                    break
            return results

        # Concurrent path — bounded sliding window; results assembled in item order.
        n = len(items)
        slots: list[Any] = [None] * n

        def run_isolated(idx: int) -> Any:
            # Each item runs against its own context copy so context.item is not
            # clobbered across threads; the shared steps dict is written only on the
            # disjoint parentId:templateId:index key (GIL-safe on distinct keys).
            return run_item(idx, dataclasses.replace(context, item=items[idx]))

        def item_halt_status(idx: int) -> RunStatus | None:
            # If THIS item's own execution halted the run, return the resulting run
            # status; else None. Decided from the item's own recorded result, not
            # the shared run status, so a later item's concurrent halt is never
            # misattributed here. Mirrors the sequential mapping: PAUSED -> PAUSED;
            # FAILED -> ABORTED when aborted, else FAILED, unless continue_on_error
            # routes around it.
            rec = context.steps.get(item_id(idx))
            if rec is None:
                # Ran but recorded nothing — only when the item failed before
                # record_step_result (e.g. an unknown step type returns early).
                # Every item runs the same template, so the shared run status is
                # this item's own outcome; attribute the halt to it.
                return state.status if state.status in halting else None
            status = rec.get("status")
            if status == StepStatus.PAUSED.value:
                return RunStatus.PAUSED
            if status == StepStatus.FAILED.value:
                out = rec.get("output") or {}
                if out.get("aborted"):
                    return RunStatus.ABORTED
                if template.get("continue_on_error") is not True:
                    return RunStatus.FAILED
            return None

        # (halting item index, its run status) once a halt is attributed.
        halt: tuple[int, RunStatus] | None = None
        collected = 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures: dict[int, Future] = {}
            next_submit = 0
            for idx in range(n):
                # Refill the window: keep <= workers in flight, and stop launching
                # new items once the run is halting so a halt cannot keep starting
                # queued work. Already-submitted futures are still collected in
                # item order below.
                while (
                    next_submit < n
                    and len(futures) < workers
                    and state.status not in halting
                ):
                    futures[next_submit] = pool.submit(run_isolated, next_submit)
                    next_submit += 1

                fut = futures.pop(idx, None)
                if fut is None:
                    # Safety net: the window submits indices in order and the loop
                    # breaks at the first halting item, so every collected index has
                    # an in-flight future. Stop cleanly rather than raise if a future
                    # change ever breaks that invariant.
                    break
                try:
                    slots[idx] = fut.result()
                except Exception:
                    # A genuine exception escaping a step (not a normal step
                    # FAILED, which sets state.status) must not be masked: cancel
                    # outstanding work and re-raise — with a bare ``raise`` so the
                    # original traceback is preserved — so the engine marks the run
                    # failed instead of reporting a vacuous completion. The pool's
                    # __exit__ still joins any already-running workers.
                    for other in futures.values():
                        other.cancel()
                    raise
                collected = idx + 1
                halt_status = item_halt_status(idx)
                if halt_status is not None:
                    # First halting item in item order: include it (slots[idx] is
                    # already set), record its status, and cancel everything pending.
                    halt = (idx, halt_status)
                    for other in futures.values():
                        other.cancel()
                    break

        if halt is not None:
            halted_at, halted_status = halt
            # A later in-flight item may have overwritten state.status before the
            # pool joined; restore the halting item's own outcome so the final run
            # status matches the sequential semantics.
            state.status = halted_status
            return slots[: halted_at + 1]
        return slots[:collected]

    def _resolve_inputs(
        self,
        definition: WorkflowDefinition,
        provided: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve workflow inputs against definitions and provided values."""
        resolved: dict[str, Any] = {}
        for name, input_def in definition.inputs.items():
            if not isinstance(input_def, dict):
                continue
            if name in provided:
                # Resolve sentinels for explicitly-provided values too: a
                # caller passing ``{"integration": "auto"}`` (which the
                # workflow prompt advertises as a valid value) must be
                # treated identically to omitting the input and letting the
                # default flow through, so dispatch never sees the literal
                # sentinel.
                value = self._resolve_default(name, provided[name])
            elif "default" in input_def:
                value = self._resolve_default(name, input_def["default"])
            elif input_def.get("required", False):
                msg = f"Required input {name!r} not provided."
                raise ValueError(msg)
            else:
                continue

            # When the ``integration`` default could not be resolved against
            # project state and falls back to the literal ``"auto"``
            # sentinel, strip ``enum`` from the input definition before
            # coercion so a workflow that lists specific integrations in
            # ``enum`` does not crash at runtime on the sentinel value.
            # NOTE: only enum-membership is skipped; ``_coerce_input``
            # still enforces the declared ``type`` against the filtered
            # definition (``string`` rejects non-strings, ``number`` rejects
            # bools and uncoercible values, ``boolean`` rejects non-bools),
            # so ill-typed values still fail fast here.
            coerce_input_def = input_def
            if (
                name == "integration"
                and value == "auto"
                and "enum" in input_def
            ):
                coerce_input_def = {
                    key: val
                    for key, val in input_def.items()
                    if key != "enum"
                }
            resolved[name] = self._coerce_input(name, value, coerce_input_def)
        return resolved

    def _resolve_default(self, name: str, default: Any) -> Any:
        """Resolve special default sentinels against project state.

        For the ``integration`` input, ``"auto"`` resolves to the integration
        recorded in ``.specify/integration.json`` so workflows dispatch to the
        AI the project was actually initialized with, instead of a hardcoded
        value baked into the workflow YAML.
        """
        if name == "integration" and default == "auto":
            resolved = self._load_project_integration()
            if resolved is not None:
                return resolved
        return default

    def _load_project_integration(self) -> str | None:
        """Read the default integration key from ``.specify/integration.json``.

        Delegates parsing and schema validation to
        :func:`try_read_integration_json` — the same low-level helper used by
        the CLI — so the engine cannot drift from CLI behavior on the parse
        path. Returns ``None`` when the file is missing, malformed, or
        written by a newer CLI; callers fall back to the literal default.
        """
        state, error = try_read_integration_json(self.project_root)
        if state is None or error is not None:
            return None
        return default_integration_key(state)

    @staticmethod
    def _coerce_input(
        name: str, value: Any, input_def: dict[str, Any]
    ) -> Any:
        """Coerce a provided input value to the declared type."""
        input_type = input_def.get("type", "string")
        enum_values = input_def.get("enum")

        if input_type == "number":
            # Reject bools explicitly: ``bool`` is a subclass of ``int`` so
            # ``float(True)`` succeeds and would silently coerce a YAML
            # authoring mistake like ``type: number`` + ``default: true``
            # into ``1``. Fail fast instead.
            if isinstance(value, bool):
                msg = f"Input {name!r} expected a number, got {value!r}."
                raise ValueError(msg)
            try:
                value = float(value)
                if value == int(value):
                    value = int(value)
            except (ValueError, TypeError, OverflowError):
                # OverflowError: `int(value)` raises it for an infinite float
                # (e.g. a `default: .inf` authoring mistake), which would
                # otherwise escape validate_workflow's `except ValueError` and
                # break its "return errors, never raise" contract. Surface it as
                # the same clean "expected a number" error as NaN does.
                msg = f"Input {name!r} expected a number, got {value!r}."
                raise ValueError(msg) from None
        elif input_type == "boolean":
            if isinstance(value, str):
                if value.lower() in ("true", "1", "yes"):
                    value = True
                elif value.lower() in ("false", "0", "no"):
                    value = False
                else:
                    msg = f"Input {name!r} expected a boolean, got {value!r}."
                    raise ValueError(msg)
            elif not isinstance(value, bool):
                msg = f"Input {name!r} expected a boolean, got {value!r}."
                raise ValueError(msg)
        elif input_type == "string":
            # Without this, ``type: string`` accepts any Python value
            # (numbers, lists, dicts) because nothing else rejects it —
            # YAML ``default: 5`` would slip through. Require an actual
            # string so authoring mistakes fail at resolve time.
            if not isinstance(value, str):
                msg = f"Input {name!r} expected a string, got {value!r}."
                raise ValueError(msg)

        if enum_values is not None and value not in enum_values:
            msg = (
                f"Input {name!r} value {value!r} not in allowed "
                f"values: {enum_values}."
            )
            raise ValueError(msg)

        return value

    def list_runs(self) -> list[dict[str, Any]]:
        """List all workflow runs in the project."""
        runs_dir = self.project_root / ".specify" / "workflows" / "runs"
        if not runs_dir.exists():
            return []

        runs: list[dict[str, Any]] = []
        for run_dir in sorted(runs_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            state_path = run_dir / "state.json"
            if state_path.exists():
                with open(state_path, encoding="utf-8") as f:
                    state_data = json.load(f)
                runs.append(state_data)
        return runs


class WorkflowAbortError(Exception):
    """Raised when a workflow is aborted (e.g., gate rejection)."""
