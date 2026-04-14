"""Workflow engine — loads, validates, and executes workflow YAML definitions.

The engine is the orchestrator that:
- Parses workflow YAML definitions
- Validates step configurations and requirements
- Executes steps sequentially, dispatching to the correct step type
- Manages state persistence for resume capability
- Handles control flow (branching, loops, fan-out/fan-in)
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

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

        # Requirements (declared but not yet enforced at runtime;
        # enforcement is a planned enhancement)
        self.requires: dict[str, Any] = data.get("requires", {})

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

# Valid step types (matching STEP_REGISTRY keys)
def _get_valid_step_types() -> set[str]:
    """Return valid step types from the registry, with a built-in fallback."""
    from . import STEP_REGISTRY
    if STEP_REGISTRY:
        return set(STEP_REGISTRY.keys())
    return {
        "command", "shell", "prompt", "gate", "if",
        "switch", "while", "do-while", "fan-out", "fan-in",
    }


def validate_workflow(definition: WorkflowDefinition) -> list[str]:
    """Validate a workflow definition and return a list of error messages.

    An empty list means the workflow is valid.
    """
    errors: list[str] = []

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

        if step_id.startswith("_fanout_"):
            errors.append(
                f"Step ID {step_id!r} uses reserved prefix '_fanout_'."
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
        # since the engine renames items to _fanout_<step>_<base>_<idx>)
        fan_step = step_config.get("step")
        if isinstance(fan_step, dict):
            fan_errors: list[str] = []
            _validate_steps([fan_step], set(), fan_errors)
            errors.extend(fan_errors)


# -- Run State Persistence ------------------------------------------------


class RunState:
    """Manages workflow run state for persistence and resume."""

    def __init__(
        self,
        run_id: str | None = None,
        workflow_id: str = "",
        project_root: Path | None = None,
    ) -> None:
        self.run_id = run_id or str(uuid.uuid4())[:8]
        self.workflow_id = workflow_id
        self.project_root = project_root or Path(".")
        self.status = RunStatus.CREATED
        self.current_step_index = 0
        self.current_step_id: str | None = None
        self.step_results: dict[str, dict[str, Any]] = {}
        self.inputs: dict[str, Any] = {}
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.log_entries: list[dict[str, Any]] = []

    @property
    def runs_dir(self) -> Path:
        return self.project_root / ".specify" / "workflows" / "runs" / self.run_id

    def save(self) -> None:
        """Persist current state to disk."""
        self.updated_at = datetime.now(timezone.utc).isoformat()
        runs_dir = self.runs_dir
        runs_dir.mkdir(parents=True, exist_ok=True)

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
        with open(runs_dir / "state.json", "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

        inputs_data = {"inputs": self.inputs}
        with open(runs_dir / "inputs.json", "w", encoding="utf-8") as f:
            json.dump(inputs_data, f, indent=2)

    @classmethod
    def load(cls, run_id: str, project_root: Path) -> RunState:
        """Load a run state from disk."""
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
        """Append a log entry to the run log."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.log_entries.append(entry)

        runs_dir = self.runs_dir
        runs_dir.mkdir(parents=True, exist_ok=True)
        with open(runs_dir / "log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


# -- Workflow Engine ------------------------------------------------------


class WorkflowEngine:
    """Orchestrator that loads, validates, and executes workflow definitions."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path(".")
        self.on_step_start: Any = None  # Callable[[str, str], None] | None

    def load_workflow(self, source: str | Path) -> WorkflowDefinition:
        """Load a workflow from an installed ID or a local YAML path.

        Parameters
        ----------
        source:
            Either a workflow ID (looked up in the installed workflows
            directory) or a path to a YAML file.

        Returns
        -------
        A validated ``WorkflowDefinition``.

        Raises
        ------
        FileNotFoundError:
            If the workflow file cannot be found.
        ValueError:
            If the workflow YAML is invalid.
        """
        path = Path(source)

        # Try as a direct file path first
        if path.suffix in (".yml", ".yaml") and path.exists():
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
            Optional run ID (auto-generated if not provided).

        Returns
        -------
        The final ``RunState`` after execution completes (or pauses).
        """
        from . import STEP_REGISTRY

        state = RunState(
            run_id=run_id,
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

    def resume(self, run_id: str) -> RunState:
        """Resume a paused or failed workflow run."""
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
            context.steps[step_id] = step_data
            state.step_results[step_id] = step_data

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
                # Gate abort (output.aborted) maps to ABORTED status
                if result.output.get("aborted"):
                    state.status = RunStatus.ABORTED
                    state.append_log(
                        {
                            "event": "workflow_aborted",
                            "step_id": step_id,
                        }
                    )
                else:
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

            # Fan-out: execute nested step template per item with unique IDs
            if step_type == "fan-out":
                items = result.output.get("items", [])
                template = result.output.get("step_template", {})
                if template and items:
                    fan_out_results = []
                    for item_idx, item_val in enumerate(result.output["items"]):
                        context.item = item_val
                        # Create a per-item copy with an ID in a reserved namespace
                        item_step = dict(template)
                        base_id = item_step.get("id", "item")
                        item_step["id"] = f"_fanout_{step_id}_{base_id}_{item_idx}"
                        self._execute_steps(
                            [item_step], context, state, registry,
                            step_offset=-1,
                        )
                        # Collect per-item result for fan-in
                        item_result = context.steps.get(item_step["id"], {})
                        fan_out_results.append(item_result.get("output", {}))
                        if state.status in (
                            RunStatus.PAUSED,
                            RunStatus.FAILED,
                            RunStatus.ABORTED,
                        ):
                            break
                    context.item = None
                    # Fan-out items are executed sequentially in this engine,
                    # so do not surface max_concurrency in persisted output.
                    fan_out_output = dict(result.output)
                    fan_out_output.pop("max_concurrency", None)
                    fan_out_output["results"] = fan_out_results
                    context.steps[step_id]["output"] = fan_out_output
                    state.step_results[step_id]["output"] = fan_out_output
                    if state.status in (
                        RunStatus.PAUSED,
                        RunStatus.FAILED,
                        RunStatus.ABORTED,
                    ):
                        return
                else:
                    # Empty items or no template — normalize output
                    result.output["results"] = []
                    context.steps[step_id]["output"] = result.output
                    state.step_results[step_id]["output"] = result.output

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
                resolved[name] = self._coerce_input(
                    name, provided[name], input_def
                )
            elif "default" in input_def:
                resolved[name] = input_def["default"]
            elif input_def.get("required", False):
                msg = f"Required input {name!r} not provided."
                raise ValueError(msg)
        return resolved

    @staticmethod
    def _coerce_input(
        name: str, value: Any, input_def: dict[str, Any]
    ) -> Any:
        """Coerce a provided input value to the declared type."""
        input_type = input_def.get("type", "string")
        enum_values = input_def.get("enum")

        if input_type == "number":
            try:
                value = float(value)
                if value == int(value):
                    value = int(value)
            except (ValueError, TypeError):
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
