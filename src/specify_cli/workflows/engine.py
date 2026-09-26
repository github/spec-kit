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
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ..integration_state import (
    default_integration_key,
    try_read_integration_json,
)
from .base import RunStatus, StepContext


# -- Workflow Definition --------------------------------------------------


class WorkflowDefinition:
    """Parsed and validated workflow YAML definition."""

    def __init__(self, data: dict[str, Any], source_path: Path | None = None) -> None:
        self.data = data
        self.source_path = source_path

        workflow = data.get("workflow", {})
        # A present-but-non-mapping ``workflow:`` block (bare ``workflow:`` ->
        # None, or ``workflow: <str/list>``) would crash the following
        # ``workflow.get(...)`` calls with AttributeError, so construction fails
        # before any validation can run. Normalize the local to {} instead: the
        # header fields fall back to their defaults and ``validate_workflow``
        # (which reads those parsed attributes) reports the missing
        # ``workflow.id``/``workflow.name``. ``self.data`` is deliberately left
        # holding the raw value, since it is what gets written back out when a
        # definition is serialized. Mirrors the default_options guard below.
        if not isinstance(workflow, dict):
            workflow = {}
        self.id: str = workflow.get("id", "")
        self.name: str = workflow.get("name", "")
        self.version: str = workflow.get("version", "0.0.0")
        self.author: str = workflow.get("author", "")
        self.description: str = workflow.get("description", "")
        self.schema_version: str = data.get("schema_version", "1.0")

        # Defaults
        # Keep malformed values intact until ``validate_workflow`` can report
        # them. ``None`` remains the supported "no defaults" form for options
        # and retains its existing runtime representation as an empty mapping.
        self.default_integration: Any = workflow.get("integration")
        self.default_model: Any = workflow.get("model")
        raw_default_options = workflow.get("options")
        self.default_options: Any = (
            {} if raw_default_options is None else raw_default_options
        )

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
        self.outputs: Any = data.get("outputs", {})

        # Steps
        self.steps: list[dict[str, Any]] = data.get("steps", [])

    @classmethod
    def from_yaml(cls, path: Path) -> WorkflowDefinition:
        """Load a workflow definition from a YAML file."""
        with open(path, encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                msg = f"Invalid YAML in {path}: {exc}"
                raise ValueError(msg) from exc
        if not isinstance(data, dict):
            msg = f"Workflow YAML must be a mapping, got {type(data).__name__}."
            raise ValueError(msg)
        return cls(data, source_path=path)

    @classmethod
    def from_string(cls, content: str) -> WorkflowDefinition:
        """Load a workflow definition from a YAML string."""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            msg = f"Invalid YAML: {exc}"
            raise ValueError(msg) from exc
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
        "command", "shell", "prompt", "gate", "if", "init", "slot",
        "switch", "while", "do-while", "fan-out", "fan-in", "workflow",
    }


def _dispatch_default_errors(definition: WorkflowDefinition) -> list[str]:
    """Return validation errors for workflow defaults inherited by dispatch steps."""
    errors: list[str] = []

    if (
        definition.default_integration is not None
        and not isinstance(definition.default_integration, str)
    ):
        errors.append(
            "'workflow.integration' must be a string or null, got "
            f"{type(definition.default_integration).__name__} "
            f"({definition.default_integration!r})."
        )

    if (
        definition.default_model is not None
        and not isinstance(definition.default_model, str)
    ):
        errors.append(
            "'workflow.model' must be a string or null, got "
            f"{type(definition.default_model).__name__} "
            f"({definition.default_model!r})."
        )

    if not isinstance(definition.default_options, dict):
        errors.append(
            "'workflow.options' must be a mapping or null, got "
            f"{type(definition.default_options).__name__} "
            f"({definition.default_options!r})."
        )

    return errors


def validate_workflow(definition: WorkflowDefinition) -> list[str]:
    """Validate a workflow definition and return a list of error messages.

    An empty list means the workflow is valid.
    """
    from .composition import validate_outputs

    errors: list[str] = validate_outputs(definition.outputs)

    # -- Schema version ---------------------------------------------------
    # str() so an unquoted ``schema_version: 1.0`` (YAML float) is accepted —
    # rejecting it would print "Unsupported schema_version 1.0. Expected '1.0'."
    if str(definition.schema_version) != "1.0":
        errors.append(
            f"Unsupported schema_version {definition.schema_version!r}. "
            f"Expected '1.0'."
        )

    # -- Top-level fields -------------------------------------------------
    # YAML parses unquoted scalars like ``id: 123`` or ``version: 1.0`` as
    # int/float; check types before regex/string operations so authoring
    # mistakes surface as validation errors instead of tracebacks. Only
    # ``None``/empty-string count as missing so falsey non-strings
    # (``id: 0``, ``name: false``) still get the typed error.
    if definition.id is None or definition.id == "":
        errors.append("Workflow is missing 'workflow.id'.")
    elif not isinstance(definition.id, str):
        errors.append(
            f"'workflow.id' must be a string, got "
            f"{type(definition.id).__name__} ({definition.id!r})."
        )
    elif not _ID_PATTERN.fullmatch(definition.id):
        errors.append(
            f"Workflow ID {definition.id!r} must be lowercase alphanumeric "
            f"with hyphens."
        )

    if definition.name is None or definition.name == "":
        errors.append("Workflow is missing 'workflow.name'.")
    elif not isinstance(definition.name, str):
        errors.append(
            f"'workflow.name' must be a string, got "
            f"{type(definition.name).__name__} ({definition.name!r})."
        )

    if definition.version is None or definition.version == "":
        errors.append("Workflow is missing 'workflow.version'.")
    elif not isinstance(definition.version, str):
        errors.append(
            f"'workflow.version' must be a string, got "
            f"{type(definition.version).__name__} ({definition.version!r}) — "
            f'quote it in YAML (version: "1.0.0").'
        )
    elif not re.fullmatch(r"\d+\.\d+\.\d+", definition.version):
        errors.append(
            f"Workflow version {definition.version!r} is not valid "
            f"semantic versioning (expected X.Y.Z)."
        )

    # Workflow-level dispatch defaults are inherited by command and prompt
    # steps. Validate their shapes before an invalid value reaches dispatch, or
    # (for options) is silently normalized away during construction.
    errors.extend(_dispatch_default_errors(definition))

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

            # ``enum`` must be a list. Checked here — not only via the
            # ``_coerce_input`` call below — because that call is reached only
            # when a ``default`` is present, and the ``integration: auto`` case
            # strips ``enum`` before coercing; a scalar/string ``enum`` on an
            # input with no default (or the auto-integration default) would
            # otherwise slip through here and then crash ``_resolve_inputs`` with
            # a raw ``TypeError`` at run time. ``None`` means "no enum".
            enum_values = input_def.get("enum")
            if enum_values is not None and not isinstance(enum_values, list):
                errors.append(
                    f"Input {input_name!r} has invalid 'enum': must be a list, "
                    f"got {type(enum_values).__name__}."
                )

            # Validate the default eagerly so authoring mistakes (e.g. a
            # default not in the declared enum, or a non-numeric default for
            # a number input) surface at install/validation time instead of
            # at workflow-execution time. ``"auto"`` for the integration
            # input is a runtime-resolved sentinel, so only the
            # enum-membership check is exempted for that exact case — the
            # declared type is still enforced (e.g. ``type: number`` paired
            # with ``default: "auto"`` is still rejected).
            enum_is_valid = enum_values is None or isinstance(enum_values, list)
            if "default" in input_def:
                default_value = input_def["default"]
                is_auto_integration = (
                    input_name == "integration" and default_value == "auto"
                )
                # Strip ``enum`` from the definition handed to ``_coerce_input``
                # when either:
                #   * this is the auto-integration sentinel (enum-membership is
                #     a runtime concern, exempted for ``"auto"``), or
                #   * the ``enum`` is malformed (non-list) and already reported
                #     above — leaving it in would make ``_coerce_input`` re-raise
                #     the same enum-shape error re-framed as an "invalid default"
                #     (a confusing duplicate).
                # Removing *only* ``enum`` (rather than skipping the check
                # entirely) preserves the default's type validation: a
                # ``type: string`` input with ``default: 5, enum: 5`` still
                # reports the wrong-typed default alongside the enum error,
                # instead of hiding it.
                strip_enum = is_auto_integration or not enum_is_valid
                validation_input_def: dict[str, Any] = input_def
                if strip_enum and "enum" in input_def:
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
    # ``input_defs`` maps declared workflow input names to their definitions —
    # used by ``_validate_steps`` to cross-reference gate ``verdict_input``
    # bindings (both that the name exists and that its ``enum`` permits the
    # reset sentinel). ``None`` means the inputs block itself is malformed
    # (already reported above); the cross-check is then disabled so one
    # authoring mistake does not cascade into N spurious "undeclared" errors.
    input_defs: dict[str, Any] | None = (
        dict(definition.inputs) if isinstance(definition.inputs, dict) else None
    )
    _validate_steps(definition.steps, seen_ids, errors, input_defs)

    return errors


def _validate_steps(
    steps: list[dict[str, Any]],
    seen_ids: set[str],
    errors: list[str],
    input_defs: dict[str, Any] | None = None,
    inside_fan_out: bool = False,
) -> None:
    """Recursively validate a list of steps.

    ``input_defs`` maps declared workflow input names to their definitions (or
    is ``None`` when the inputs block is malformed). ``inside_fan_out`` is
    threaded through nested control-flow steps so gate verdict bindings can be
    rejected anywhere inside a fan-out template.
    """
    from . import STEP_REGISTRY

    for step_config in steps:
        if not isinstance(step_config, dict):
            errors.append(f"Step must be a mapping, got {type(step_config).__name__}.")
            continue

        step_id = step_config.get("id")
        if step_id is None or step_id == "":
            errors.append("Step is missing 'id' field.")
            continue
        if not isinstance(step_id, str):
            errors.append(
                f"Step ID must be a string, got "
                f"{type(step_id).__name__} ({step_id!r})."
            )
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
        if not isinstance(step_type, str):
            # Registry keys are strings. Checking an unhashable YAML value
            # (for example ``type: [shell]`` or a mapping) against the set
            # below raises a raw TypeError before validation can report the
            # authoring mistake. Guard every non-string shape first, matching
            # the typed validation already applied to workflow and step IDs.
            errors.append(
                f"Step {step_id!r}: 'type' must be a string, got "
                f"{type(step_type).__name__} ({step_type!r})."
            )
            continue
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

        if step_type == "slot" and inside_fan_out:
            errors.append(
                f"Slot step {step_id!r} is not supported inside fan-out "
                "templates because overlays cannot address runtime-multiplied "
                "templates."
            )

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

        # Gate verdict_input: fan-out items cannot bind shared workflow inputs
        # as per-item verdicts. Outside fan-out, the binding must reference a
        # declared workflow input because ``_resolve_inputs`` drops undeclared
        # names at both initial run and resume. Only check a non-empty string;
        # malformed shapes are already reported by ``GateStep.validate()``.
        if step_type == "gate":
            verdict_input = step_config.get("verdict_input")
            if isinstance(verdict_input, str) and verdict_input:
                if inside_fan_out:
                    errors.append(
                        f"Gate step {step_id!r}: 'verdict_input' is not "
                        "supported inside fan-out templates."
                    )
                elif input_defs is not None and verdict_input not in input_defs:
                    errors.append(
                        f"Gate step {step_id!r}: 'verdict_input' references "
                        f"undeclared input {verdict_input!r}."
                    )
                elif input_defs is not None:
                    # ``on_reject: retry`` resets the bound input to "" before
                    # pausing, and every later resume re-resolves the persisted
                    # inputs through ``_coerce_input``. If the input declares an
                    # ``enum`` that omits "", that reset value is instantly
                    # illegal: the run pauses fine, but the next resume that
                    # supplies any input raises "value '' not in allowed
                    # values", and no verdict can be routed through the gate
                    # again. Require the enum to admit the sentinel so the
                    # retry cycle the field advertises is actually reachable.
                    verdict_def = input_defs.get(verdict_input)
                    enum_values = (
                        verdict_def.get("enum")
                        if isinstance(verdict_def, dict)
                        else None
                    )
                    if (
                        step_config.get("on_reject") == "retry"
                        and isinstance(enum_values, list)
                        and "" not in enum_values
                    ):
                        errors.append(
                            f"Gate step {step_id!r}: on_reject='retry' resets "
                            f"verdict input {verdict_input!r} to '' when the "
                            f"gate is rejected, but that input's 'enum' does "
                            f"not allow ''. Add '' to the enum or use "
                            f"on_reject='abort'/'skip'."
                        )

        # Recursively validate nested steps
        for nested_key in ("then", "else", "steps"):
            nested = step_config.get(nested_key)
            if isinstance(nested, list):
                _validate_steps(
                    nested,
                    seen_ids,
                    errors,
                    input_defs,
                    inside_fan_out=inside_fan_out,
                )

        # Validate switch cases
        cases = step_config.get("cases")
        if isinstance(cases, dict):
            for _case_key, case_steps in cases.items():
                if isinstance(case_steps, list):
                    _validate_steps(
                        case_steps,
                        seen_ids,
                        errors,
                        input_defs,
                        inside_fan_out=inside_fan_out,
                    )

        # Validate switch default
        default = step_config.get("default")
        if isinstance(default, list):
            _validate_steps(
                default,
                seen_ids,
                errors,
                input_defs,
                inside_fan_out=inside_fan_out,
            )

        # Validate fan-out nested step (template — not added to seen_ids
        # since the engine generates parentId:templateId:index at runtime)
        fan_step = step_config.get("step")
        if isinstance(fan_step, dict):
            fan_errors: list[str] = []
            _validate_steps(
                [fan_step],
                set(),
                fan_errors,
                input_defs,
                inside_fan_out=True,
            )
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
        if not isinstance(run_id, str) or not cls._RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError(
                f"Invalid run_id {run_id!r}: must be alphanumeric with "
                "hyphens/underscores only (and must start with an "
                "alphanumeric character)."
            )

    @staticmethod
    def _validate_installed_origin(
        installed_workflow_id: str | None,
        installed_registry_root: str | None,
    ) -> None:
        """Validate persisted installed-workflow ownership metadata."""
        if installed_workflow_id is not None:
            if not isinstance(installed_workflow_id, str):
                raise ValueError(
                    "Invalid run state: 'installed_workflow_id' must be a "
                    f"string or null, got {type(installed_workflow_id).__name__}"
                )
            if not _ID_PATTERN.fullmatch(installed_workflow_id):
                raise ValueError(
                    "Invalid run state: 'installed_workflow_id' must be a "
                    "lowercase alphanumeric workflow ID with hyphens"
                )
        if installed_registry_root is not None:
            if not isinstance(installed_registry_root, str):
                raise ValueError(
                    "Invalid run state: 'installed_registry_root' must be a "
                    f"string or null, got {type(installed_registry_root).__name__}"
                )
            if not installed_registry_root or not Path(
                installed_registry_root
            ).is_absolute():
                raise ValueError(
                    "Invalid run state: 'installed_registry_root' must be "
                    "an absolute path or null"
                )
            if installed_workflow_id is None:
                raise ValueError(
                    "Invalid run state: 'installed_registry_root' requires "
                    "'installed_workflow_id'"
                )

    def __init__(
        self,
        run_id: str | None = None,
        workflow_id: str = "",
        project_root: Path | None = None,
        installed_workflow_id: str | None = None,
        installed_registry_root: str | None = None,
        installed_origin_tracked: bool = True,
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
        self._validate_installed_origin(
            installed_workflow_id, installed_registry_root
        )
        self.workflow_id = workflow_id
        self.project_root = project_root or Path(".")
        # Identifies the installed workflow (if any) this run was started
        # from, and the project root that owns its registry — set by
        # execute() when the source was resolved to an installed ID (see
        # workflow_run's ownership mapping). None for a direct/non-installed
        # YAML source. ``installed_origin_tracked`` distinguishes those
        # explicit None values from legacy state files that predate both
        # fields, allowing the CLI to conservatively infer same-project
        # registry ownership before resuming.
        self.installed_workflow_id = installed_workflow_id
        self.installed_registry_root = installed_registry_root
        self.installed_origin_tracked = installed_origin_tracked
        self.status = RunStatus.CREATED
        self.current_step_index = 0
        self.current_step_id: str | None = None
        self.step_results: dict[str, dict[str, Any]] = {}
        self.execution: dict[str, Any] | None = None
        self._checkpoint_failed = False
        # Guards step_results mutation and save() so a concurrent fan-out cannot
        # mutate the dict while save() is serializing it (which would raise
        # "dictionary changed size during iteration").
        self._lock = threading.RLock()
        # Reentrant so an execution transition can update views and call save()
        # under the same lock. Step implementations run outside that lock.
        # Serializes append_log's list append + log.jsonl write so concurrent
        # fan-out workers cannot interleave or corrupt log lines. Kept separate
        # from _lock so frequent logging never contends with state saves; since
        # append_log is never called while _lock is held, the two never nest.
        self._log_lock = threading.Lock()
        self.inputs: dict[str, Any] = {}
        self.workflow_dir: str | None = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.log_entries: list[dict[str, Any]] = []
        self.error: str | None = None

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
            from ._execution import CheckpointError

            if self._checkpoint_failed:
                raise CheckpointError("A previous checkpoint failed; reload the run")
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
            if self._checkpoint_failed:
                from ._execution import CheckpointError

                raise CheckpointError("A previous checkpoint failed; reload the run")
            # Stamp updated_at inside the lock so the timestamp matches the
            # snapshot this thread serializes (concurrent savers don't race it).
            self.updated_at = datetime.now(timezone.utc).isoformat()
            state_data = {
                "run_id": self.run_id,
                "workflow_id": self.workflow_id,
                "installed_workflow_id": self.installed_workflow_id,
                "installed_registry_root": self.installed_registry_root,
                "status": self.status.value,
                "current_step_index": self.current_step_index,
                "current_step_id": self.current_step_id,
                "step_results": self.step_results,
                "workflow_dir": self.workflow_dir,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "error": self.error,
                "inputs": self.inputs,
            }
            if self.execution is not None:
                state_data["execution"] = self.execution
            try:
                self._atomic_write_json(runs_dir / "state.json", state_data)
                self._atomic_write_json(runs_dir / "inputs.json", {"inputs": self.inputs})
            except BaseException as exc:
                from ._execution import CheckpointError

                self._checkpoint_failed = True
                raise CheckpointError(str(exc)) from exc

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

        try:
            with open(state_path, encoding="utf-8") as f:
                state_data = json.load(f)
        except FileNotFoundError:
            msg = f"Run state not found: {state_path}"
            raise FileNotFoundError(msg)
        if not isinstance(state_data, dict):
            raise ValueError("Invalid run state: expected a JSON object")
        missing_fields = [
            field
            for field in ("run_id", "workflow_id", "status")
            if field not in state_data
        ]
        if missing_fields:
            raise ValueError(
                "Invalid run state: missing required field(s): "
                + ", ".join(missing_fields)
            )
        if state_data["run_id"] != run_id:
            raise ValueError(
                f"Invalid run state: stored run_id {state_data['run_id']!r} "
                f"does not match requested run_id {run_id!r}"
            )

        workflow_id = state_data["workflow_id"]
        if not isinstance(workflow_id, str) or not _ID_PATTERN.fullmatch(
            workflow_id
        ):
            raise ValueError(
                "Invalid run state: 'workflow_id' must be a lowercase "
                "alphanumeric workflow ID with hyphens"
            )

        has_installed_workflow_id = "installed_workflow_id" in state_data
        has_installed_registry_root = "installed_registry_root" in state_data
        if has_installed_workflow_id != has_installed_registry_root:
            raise ValueError(
                "Invalid run state: installed workflow origin fields must "
                "either both be present or both be absent"
            )

        installed_workflow_id = state_data.get("installed_workflow_id")
        installed_registry_root = state_data.get("installed_registry_root")

        step_results = state_data.get("step_results", {})
        if not isinstance(step_results, dict):
            raise ValueError(
                "Invalid run state: 'step_results' must be a JSON object"
            )
        for step_id, result in step_results.items():
            if not isinstance(result, dict):
                raise ValueError(
                    "Invalid run state: step_results record "
                    f"{step_id!r} must be a JSON object"
                )

        state = cls(
            run_id=state_data["run_id"],
            workflow_id=workflow_id,
            project_root=project_root,
            installed_workflow_id=installed_workflow_id,
            installed_registry_root=installed_registry_root,
            installed_origin_tracked=has_installed_workflow_id,
        )
        state.status = RunStatus(state_data["status"])

        # Validate the index shape before restoring it. The upper bound cannot
        # be checked until resume() loads the workflow definition and is handled
        # there. Reject bool explicitly because it subclasses int; otherwise a
        # malformed value could fail during slicing or resume from the wrong step.
        current_step_index = state_data.get("current_step_index", 0)
        if (
            isinstance(current_step_index, bool)
            or not isinstance(current_step_index, int)
            or current_step_index < 0
        ):
            raise ValueError(
                "Invalid run state: 'current_step_index' must be a "
                f"non-negative integer, got {current_step_index!r}"
            )
        state.current_step_index = current_step_index
        state.current_step_id = state_data.get("current_step_id")
        state.step_results = step_results
        state.workflow_dir = state_data.get("workflow_dir")
        state.created_at = state_data.get("created_at", "")
        state.updated_at = state_data.get("updated_at", "")
        state.error = state_data.get("error")
        state.execution = state_data.get("execution")
        if "execution" in state_data:
            from ._execution import validate_execution

            validate_execution(state.execution)

        inputs_path = runs_dir / "inputs.json"
        if "inputs" not in state_data and inputs_path.exists():
            with open(inputs_path, encoding="utf-8") as f:
                inputs_data = json.load(f)
            if not isinstance(inputs_data, dict):
                raise ValueError(
                    "Invalid run inputs: expected a JSON object"
                )
            inputs = inputs_data.get("inputs", {})
            if not isinstance(inputs, dict):
                raise ValueError(
                    "Invalid run inputs: 'inputs' must be a JSON object"
                )
            state.inputs = inputs

        if "inputs" in state_data:
            if not isinstance(state_data["inputs"], dict):
                raise ValueError("Invalid run inputs: 'inputs' must be a JSON object")
            state.inputs = state_data["inputs"]

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
        from .overlay import WorkflowResolver

        path = Path(source).expanduser()

        # Try as a direct file path first
        if path.suffix.lower() in (".yml", ".yaml") and path.is_file():
            return WorkflowDefinition.from_yaml(path)

        # Try as an installed workflow ID, resolving any overlays.
        resolver = WorkflowResolver(self.project_root)
        try:
            return resolver.resolve(str(source))
        except FileNotFoundError:
            # Fall back to the direct workflow.yml path so callers still get
            # the original error when the workflow id is not installed.
            pass

        # Legacy direct path check for workflows installed without registry entries.
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
        installed_workflow_id: str | None = None,
        installed_registry_root: Path | None = None,
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
        installed_workflow_id, installed_registry_root:
            When the run was started from an installed workflow (as opposed
            to a direct/non-installed YAML source), identifies it and its
            owning registry root so a later ``resume`` can re-check the
            registry's current disabled state before continuing — see
            ``workflow_resume``.

        Returns
        -------
        The final ``RunState`` after execution completes (or pauses).
        """
        dispatch_default_errors = _dispatch_default_errors(definition)
        if dispatch_default_errors:
            raise ValueError(" ".join(dispatch_default_errors))

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
            installed_workflow_id=installed_workflow_id,
            installed_registry_root=(
                str(installed_registry_root)
                if installed_registry_root is not None
                else None
            ),
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
        workflow_dir = (
            str(definition.source_path.resolve().parent)
            if definition.source_path is not None
            else None
        )
        state.workflow_dir = workflow_dir
        state.status = RunStatus.RUNNING
        state.save()

        context = StepContext(
            inputs=resolved_inputs,
            default_integration=definition.default_integration,
            default_model=definition.default_model,
            default_options=definition.default_options,
            project_root=str(self.project_root),
            run_id=state.run_id,
            workflow_dir=workflow_dir,
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
            if state._checkpoint_failed:
                raise
            state.status = RunStatus.FAILED
            state.error = str(exc)
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
        """Resume a paused/failed run or a tree-backed run interrupted by a crash.

        When ``inputs`` is provided, the values are merged over the run's
        persisted inputs and re-resolved through the same typed validation
        path used by :meth:`execute`, so the resumed step sees updated
        workflow inputs. Keys not supplied keep their persisted values; an
        empty/``None`` ``inputs`` leaves the run's inputs unchanged.
        """
        state = RunState.load(run_id, self.project_root)
        if state.status not in (RunStatus.PAUSED, RunStatus.FAILED) and not (
            state.status == RunStatus.RUNNING and state.execution is not None
        ):
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

        # RunState.load() rejects a non-int/negative current_step_index but
        # can't check the upper bound — the step count isn't known until the
        # workflow definition is loaded, above. An out-of-range positive
        # index (e.g. a hand-edited state.json) would otherwise slice
        # definition.steps[state.current_step_index:] into an empty list
        # below, silently completing the run without executing any step.
        if state.current_step_index >= len(definition.steps):
            msg = (
                "Invalid run state: 'current_step_index' "
                f"({state.current_step_index}) is out of range for "
                f"workflow {state.workflow_id!r} with {len(definition.steps)} "
                "step(s)."
            )
            raise ValueError(msg)

        if state.execution is not None:
            persisted_steps = yaml.safe_load(state.execution["sequence"]["source"])
            offset = state.execution.get("offset", 0)
            if persisted_steps != definition.steps[offset:]:
                raise ValueError("Invalid execution state: root sequence differs from workflow snapshot")

        dispatch_default_errors = _dispatch_default_errors(definition)
        if dispatch_default_errors:
            raise ValueError(" ".join(dispatch_default_errors))

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
            is_resume=True,
            workflow_dir=state.workflow_dir,
        )

        from . import STEP_REGISTRY

        state.error = None
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
                rebind=bool(inputs),
            )
        except KeyboardInterrupt:
            state.status = RunStatus.PAUSED
            state.append_log({"event": "workflow_interrupted"})
            state.save()
            return state
        except Exception as exc:
            if state._checkpoint_failed:
                raise
            state.status = RunStatus.FAILED
            state.error = str(exc)
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
        rebind: bool = False,
    ) -> None:
        """Execute or resume the persisted tree (legacy indices adapt once)."""
        from ._execution import Execution, active_step, sequence
        from copy import deepcopy

        if state.execution is None:
            state.execution = {"version": 1, "sequence": sequence(steps)}
            state.execution["offset"] = max(0, step_offset)
            state.execution["initial"] = deepcopy(context.steps)
        context.steps = deepcopy(state.execution.get("initial", {}))
        state.save()
        tree = state.execution["sequence"]
        executor = Execution(self, state, registry, rebind=rebind)
        outcome, error = executor.run(tree, context, (state.workflow_id,), root=True)
        active = active_step(state.execution)
        if active is not None:
            state.current_step_id = active[0][-1]
        state.status = RunStatus.RUNNING if outcome == "completed" else RunStatus(outcome)
        state.error = error

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
        """Compatibility adapter to the unified fan-out executor."""
        from ._execution import Execution, sequence

        if not items:
            return []
        node = {
            "phase": "children",
            "result": {"output": {"items": items, "step_template": template,
                                   "max_concurrency": max_concurrency}},
            "children": [sequence([template]) for _ in items],
        }
        outcome, error, results = Execution(self, state, registry).fan_out(
            {"id": step_id, "type": "fan-out"}, node, context,
            (state.workflow_id,), (), step_id,
        )
        state.status = RunStatus.RUNNING if outcome == "completed" else RunStatus(outcome)
        state.error = error
        return results

    def _resolve_inputs(
        self,
        definition: WorkflowDefinition,
        provided: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve workflow inputs against definitions and provided values."""
        resolved: dict[str, Any] = {}
        # execute()/resume() accept UNVALIDATED definitions (load_workflow does
        # not validate). A non-mapping ``inputs:`` block (bare ``inputs:`` ->
        # None, or ``inputs: []``) is stored raw, so iterating ``.items()`` here
        # would crash the run with AttributeError. Treat a non-mapping inputs
        # block as "no inputs"; validate_workflow reports the malformed shape
        # via its own isinstance check.
        if not isinstance(definition.inputs, dict):
            return {}
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
            #
            # ``execute()`` accepts unvalidated definitions, so a malformed
            # (non-list) ``enum`` can reach here. Only strip a *list* ``enum``:
            # a scalar/string ``enum`` must stay in the definition so
            # ``_coerce_input`` raises the clean shape ``ValueError`` instead of
            # being silently exempted by the ``auto`` membership skip (which
            # would otherwise let ``enum: 5`` resolve successfully).
            coerce_input_def = input_def
            if (
                name == "integration"
                and value == "auto"
                and isinstance(input_def.get("enum"), list)
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

        # ``enum`` must be a list. A scalar (``enum: 5``, ``enum: true``) makes
        # the ``value not in enum_values`` membership test below raise a raw
        # ``TypeError`` ("argument of type 'int' is not ... iterable"), which
        # escapes ``validate_workflow``'s ``except ValueError`` and breaks its
        # "return errors, never raise" contract — and crashes ``_resolve_inputs``
        # outright at run time. A bare string is just as wrong: ``value in "abc"``
        # is a silent substring/character test, not enum membership. Require a
        # list so both forms fail fast with a clear message. ``None`` means "no
        # enum" and is left alone.
        if enum_values is not None and not isinstance(enum_values, list):
            msg = (
                f"Input {name!r} has invalid 'enum': must be a list, got "
                f"{type(enum_values).__name__}."
            )
            raise ValueError(msg)

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
                try:
                    with open(state_path, encoding="utf-8") as f:
                        state_data = json.load(f)
                except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                    continue
                if not isinstance(state_data, dict) or "run_id" not in state_data:
                    continue
                runs.append(state_data)
        return runs


class WorkflowAbortError(Exception):
    """Raised when a workflow is aborted (e.g., gate rejection)."""
