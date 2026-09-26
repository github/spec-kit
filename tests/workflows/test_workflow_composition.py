"""Tests for workflow composition (the built-in ``type: workflow`` step).

Covers the composition helpers, engine scoped execution, strict input binding,
persistence/resume, and CLI reporting.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Event, Thread

import pytest
import yaml

from specify_cli.workflows.base import RunStatus, StepContext, StepStatus
from specify_cli.workflows.composition import (
    MAX_COMPOSITION_DEPTH,
    RESERVED_OUTPUT_NAMES,
    bind_composed_inputs,
    check_composition_path,
    evaluate_input_mapping,
    resolve_composed_workflow,
    validate_workflow_call_config,
)
from specify_cli.workflows.engine import (
    RunState,
    WorkflowDefinition,
    WorkflowEngine,
    validate_workflow,
)

# -- Helpers --------------------------------------------------------------


def _workflow(
    workflow_id: str,
    steps: list[dict],
    *,
    inputs: dict | None = None,
    outputs: dict | None = None,
    name: str | None = None,
) -> dict:
    data: dict = {
        "schema_version": "1.0",
        "workflow": {
            "id": workflow_id,
            "name": name or workflow_id.title(),
            "version": "1.0.0",
        },
        "steps": steps,
    }
    if inputs is not None:
        data["inputs"] = inputs
    if outputs is not None:
        data["outputs"] = outputs
    return data


def _install(project_root: Path, workflow_id: str, data: dict, *, enabled: bool = True) -> Path:
    from specify_cli.workflows.catalog import WorkflowRegistry

    workflow_dir = project_root / ".specify" / "workflows" / workflow_id
    workflow_dir.mkdir(parents=True, exist_ok=True)
    path = workflow_dir / "workflow.yml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    WorkflowRegistry(project_root).add(
        workflow_id,
        {
            "name": data["workflow"]["name"],
            "version": "1.0.0",
            "enabled": enabled,
        },
    )
    return path


def _definition(project_root: Path, workflow_id: str) -> WorkflowDefinition:
    return WorkflowDefinition.from_yaml(
        project_root / ".specify" / "workflows" / workflow_id / "workflow.yml"
    )


def _run(project_root: Path, workflow_id: str, inputs: dict | None = None) -> RunState:
    engine = WorkflowEngine(project_root)
    return engine.execute(_definition(project_root, workflow_id), inputs or {})


def _shell(step_id: str, run: str, **extra) -> dict:
    return {"id": step_id, "type": "shell", "run": run, **extra}


# -- Composition helper unit tests ---------------------------------------


class TestWorkflowOutputsValidation:
    def _errors(self, outputs) -> list[str]:
        definition = WorkflowDefinition(
            _workflow("w", [_shell("s", "echo")], outputs=outputs)
        )
        return validate_workflow(definition)

    def test_safe_output_names_accepted(self):
        errors = self._errors({"result": {"value": "{{ steps.s.output.stdout }}"}})
        assert errors == []

    @pytest.mark.parametrize("name", sorted(RESERVED_OUTPUT_NAMES))
    def test_reserved_output_names_rejected(self, name):
        errors = self._errors({name: {"value": "x"}})
        assert any("reserved" in e for e in errors), errors

    def test_non_mapping_outputs_rejected(self):
        errors = self._errors([{"value": "x"}])
        assert any("'outputs' must be a mapping" in e for e in errors)

    def test_entry_missing_value_rejected(self):
        errors = self._errors({"result": {"expr": "x"}})
        assert any("exactly the 'value' field" in e for e in errors)

    def test_entry_extra_keys_rejected(self):
        errors = self._errors({"result": {"value": "x", "extra": 1}})
        assert any("exactly the 'value' field" in e for e in errors)

    def test_bad_output_name_rejected(self):
        errors = self._errors({"Bad Name": {"value": "x"}})
        assert any("safe identifier" in e for e in errors)

    def test_non_mapping_entry_rejected(self):
        errors = self._errors({"result": "x"})
        assert any("must be a mapping" in e for e in errors)

    def test_non_json_safe_value_rejected(self):
        # An unquoted YAML date is a valid scalar but not a string expression;
        # accepting it would later crash json.dump on the declared output.
        from datetime import date

        errors = self._errors({"when": {"value": date(2026, 1, 1)}})
        assert any("not JSON-safe" in e for e in errors)

    @pytest.mark.parametrize(
        "value",
        [True, 42, 3.14, None, ["a", 1], {"ok": True, "items": [1, 2]}],
    )
    def test_json_safe_literal_values_accepted(self, value):
        assert self._errors({"result": {"value": value}}) == []

    def test_nested_non_json_safe_value_rejected(self):
        from datetime import date

        errors = self._errors(
            {"result": {"value": {"when": [date(2026, 1, 1)]}}}
        )
        assert any("not JSON-safe" in e for e in errors)

    def test_non_string_object_key_rejected(self):
        errors = self._errors({"result": {"value": {1: "numeric"}}})
        assert any("non-string key" in e for e in errors)

    @pytest.mark.parametrize("factory", [list, dict])
    def test_circular_container_rejected(self, factory):
        value = factory()
        if isinstance(value, list):
            value.append(value)
        else:
            value["self"] = value

        errors = self._errors({"result": {"value": value}})

        assert any("circular container" in error for error in errors)

    def test_shared_acyclic_container_accepted(self):
        shared = ["value"]
        assert self._errors({"result": {"value": {"one": shared, "two": shared}}}) == []


class TestComposedOutputPersistence:
    def test_non_json_safe_evaluated_output_fails_workflow_step(self, project_dir):
        """Output persistence errors become a failed workflow-step result.

        The aggregate boundary catches output evaluation failures so the caller
        can still use normal ``continue_on_error`` handling instead of crashing
        later in ``json.dump``. ``WorkflowEngine.execute`` accepts unvalidated
        definitions, so retain the runtime guard in addition to validation.
        """
        from datetime import date

        from specify_cli.workflows.composition import ExecutionScope

        definition = WorkflowDefinition(
            _workflow(
                "child",
                [_shell("s", "true")],
                outputs={"when": {"value": date(2026, 1, 1)}},
            )
        )
        scope = ExecutionScope(
            scope_id="call",
            workflow_id="child",
            definition=definition,
        )
        result = WorkflowEngine(project_dir)._aggregate_workflow_result(
            scope, definition, "call"
        )

        assert result.status == StepStatus.FAILED
        assert scope.status == RunStatus.FAILED
        assert "not JSON-safe" in (result.error or "")


class TestWorkflowCallConfigValidation:
    def test_literal_valid(self):
        assert validate_workflow_call_config({"id": "s", "workflow": "bugfix"}) == []

    def test_missing_workflow(self):
        errors = validate_workflow_call_config({"id": "s"})
        assert any("missing 'workflow'" in e for e in errors)

    def test_non_string_workflow(self):
        errors = validate_workflow_call_config({"id": "s", "workflow": 5})
        assert any("must be a string" in e for e in errors)

    def test_invalid_literal_id(self):
        errors = validate_workflow_call_config({"id": "s", "workflow": "Bad_ID"})
        assert any("lowercase alphanumeric" in e for e in errors)

    def test_reserved_literal_id(self):
        errors = validate_workflow_call_config({"id": "s", "workflow": "runs"})
        assert any("reserved" in e for e in errors)

    def test_expression_target_allowed(self):
        errors = validate_workflow_call_config(
            {"id": "s", "workflow": "{{ steps.pick.output.stdout }}"}
        )
        assert errors == []

    def test_non_mapping_input_rejected(self):
        errors = validate_workflow_call_config(
            {"id": "s", "workflow": "bugfix", "input": ["x"]}
        )
        assert any("'input' must be a mapping" in e for e in errors)

    def test_non_json_safe_input_value_rejected(self):
        from datetime import date

        errors = validate_workflow_call_config(
            {
                "id": "s",
                "workflow": "bugfix",
                "input": {"when": date(2026, 1, 1)},
            }
        )
        assert any("not JSON-safe" in e for e in errors)


class TestEvaluateInputMapping:
    def test_omitted_returns_empty(self):
        assert evaluate_input_mapping({}, StepContext()) == {}

    def test_explicit_null_returns_empty(self):
        assert evaluate_input_mapping(None, StepContext()) == {}

    @pytest.mark.parametrize("mapping", [["x"], "who", 5, True])
    def test_non_mapping_rejected(self, mapping):
        # An unvalidated definition can reach the engine; a malformed ``input``
        # must fail rather than silently run the child with defaults.
        with pytest.raises(ValueError, match="must be a mapping or omitted"):
            evaluate_input_mapping(mapping, StepContext())

    def test_values_evaluated_in_caller_scope(self):
        context = StepContext(inputs={"who": "world"})
        assert evaluate_input_mapping(
            {"name": "{{ inputs.who }}", "literal": "x"}, context
        ) == {"name": "world", "literal": "x"}

    def test_non_json_safe_value_rejected(self):
        from datetime import date

        with pytest.raises(ValueError, match="not JSON-safe"):
            evaluate_input_mapping({"when": date(2026, 1, 1)}, StepContext())

    def test_non_string_key_rejected(self):
        with pytest.raises(ValueError, match="keys must be strings"):
            evaluate_input_mapping({1: "x"}, StepContext())


class TestCheckCompositionPath:
    def test_cycle_reported_before_depth(self):
        path = [f"w{i}" for i in range(MAX_COMPOSITION_DEPTH + 5)] + ["target"]
        with pytest.raises(ValueError, match="cycle"):
            check_composition_path(path, "target")

    def test_depth_16_allowed(self):
        path = [f"w{i}" for i in range(MAX_COMPOSITION_DEPTH)]
        check_composition_path(path, "new")

    def test_depth_17_rejected(self):
        path = [f"w{i}" for i in range(MAX_COMPOSITION_DEPTH + 1)]
        with pytest.raises(ValueError, match="maximum depth"):
            check_composition_path(path, "new")

    def test_diamond_allowed(self):
        # A -> B -> D and A -> C -> D: D is not in the A->B path.
        check_composition_path(["a", "b"], "d")
        check_composition_path(["a", "c"], "d")


class TestStrictInputBinding:
    def _bind(self, definition, provided, resolve_default=lambda n, v: v):
        return bind_composed_inputs(
            definition,
            provided,
            caller_id="call",
            workflow_id=definition.id,
            resolve_default=resolve_default,
        )

    def _def(self, inputs):
        return WorkflowDefinition(_workflow("child", [_shell("s", "echo")], inputs=inputs))

    def test_undeclared_input_rejected(self):
        definition = self._def({"who": {"type": "string"}})
        with pytest.raises(ValueError, match="undeclared input"):
            self._bind(definition, {"typo": "x"})

    def test_defaults_applied(self):
        definition = self._def({"who": {"type": "string", "default": "world"}})
        assert self._bind(definition, {}) == {"who": "world"}

    def test_required_missing_rejected(self):
        definition = self._def({"who": {"type": "string", "required": True}})
        with pytest.raises(ValueError, match="required input"):
            self._bind(definition, {})

    def test_enum_enforced(self):
        definition = self._def(
            {"mode": {"type": "string", "enum": ["a", "b"], "default": "a"}}
        )
        assert self._bind(definition, {"mode": "b"}) == {"mode": "b"}
        with pytest.raises(ValueError, match="not in allowed values"):
            self._bind(definition, {"mode": "c"})

    def test_integration_auto_sentinel(self):
        definition = self._def(
            {"integration": {"type": "string", "default": "auto", "enum": ["claude"]}}
        )

        def resolve_default(name, value):
            return "claude" if name == "integration" and value == "auto" else value

        assert self._bind(definition, {}, resolve_default) == {"integration": "claude"}


# -- Engine composition tests --------------------------------------------


class TestLiteralAndRuntimeTargets:
    def test_literal_target(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [{"id": "call", "type": "workflow", "workflow": "child"}],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["call"]["output"]["workflow"] == "child"

    def test_runtime_selected_target(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    _shell("pick", "printf child"),
                    {
                        "id": "call",
                        "type": "workflow",
                        "workflow": "{{ steps.pick.output.stdout }}",
                    },
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["call"]["output"]["workflow"] == "child"

    def test_runtime_target_from_echo_requires_exact_id(self, project_dir):
        """A dynamic target is not normalized before installed-ID matching."""
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    _shell("pick", "echo child"),
                    {
                        "id": "call",
                        "type": "workflow",
                        "workflow": "{{ steps.pick.output.stdout }}",
                        "continue_on_error": True,
                    },
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        result = state.step_results["call"]
        assert result["status"] == "failed"
        assert result["output"]["workflow"] == "child\n"
        assert "not a valid workflow ID" in result["error"]

    def test_long_valid_target_uses_bounded_snapshot_name(self, project_dir):
        # This ID fits an installed-workflow directory component, but adding the
        # old readable ``-<digest>.yml`` suffix exceeded the common 255-byte cap.
        long_id = "a" * 239
        _install(
            project_dir,
            long_id,
            _workflow(long_id, [_shell("x", "echo hi")]),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "call",
                        "type": "workflow",
                        "workflow": long_id,
                    },
                ],
            ),
        )

        state = _run(project_dir, "parent")

        result = state.step_results["call"]
        assert state.status == RunStatus.COMPLETED
        assert result["status"] == "completed"
        assert result["output"]["workflow"] == long_id
        reference = state.workflow_scopes["call"]["definition_snapshot"]
        assert len(reference.encode("ascii")) == 68
        assert (state.runs_dir / "snapshots" / reference).is_file()

    def test_registry_key_must_match_resolved_definition_id(self, project_dir):
        _install(project_dir, "child", _workflow("other", [_shell("x", "echo hi")]))

        with pytest.raises(ValueError, match="registry entry 'child'.*ID 'other'"):
            resolve_composed_workflow(project_dir, "child")


class TestScopeIsolation:
    def _parent_and_child(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    _shell("child-local", "echo {{ inputs.declared }}"),
                    _shell("peek-input", "echo {{ inputs.shared | default('MISSING') }}"),
                    _shell(
                        "peek-step",
                        "echo {{ steps.caller-step.output.stdout | default('NOPE') }}",
                    ),
                ],
                inputs={"declared": {"type": "string", "default": "d"}},
                outputs={"echoed": {"value": "{{ steps.child-local.output.stdout }}"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    _shell("caller-step", "echo caller-value"),
                    {
                        "id": "call",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"declared": "{{ inputs.shared }}"},
                    },
                    _shell(
                        "consume",
                        "echo {{ steps.call.output.echoed | default('MISSING') }}",
                    ),
                ],
                inputs={"shared": {"type": "string", "default": "secret"}},
            ),
        )

    def test_child_cannot_see_caller_locals(self, project_dir):
        self._parent_and_child(project_dir)
        state = _run(project_dir, "parent")
        child = state.workflow_scopes["call"]
        assert child["step_results"]["peek-input"]["output"]["stdout"].strip() == "MISSING"
        assert child["step_results"]["peek-step"]["output"]["stdout"].strip() == "NOPE"

    def test_caller_cannot_see_child_locals(self, project_dir):
        self._parent_and_child(project_dir)
        state = _run(project_dir, "parent")
        assert "child-local" not in state.step_results
        call_output = state.step_results["call"]["output"]
        assert call_output["echoed"].strip() == "secret"
        # Only declared outputs + stable metadata cross the boundary.
        assert set(call_output) == {"workflow", "status", "echoed"}

    def test_caller_can_consume_child_output_downstream(self, project_dir):
        """The caller context must publish a completed child's output *before*
        the next step runs, so a downstream expression can consume it."""
        self._parent_and_child(project_dir)
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["consume"]["output"]["stdout"].strip() == "secret"


class TestScopeLogging:
    def test_nested_events_include_their_scope_path(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("build", "echo child")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    _shell("build", "echo parent"),
                    {"id": "call", "type": "workflow", "workflow": "child"},
                ],
            ),
        )

        state = _run(project_dir, "parent")
        entries = [
            json.loads(line)
            for line in (state.runs_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        started = [
            entry
            for entry in entries
            if entry["event"] == "step_started" and entry["step_id"] == "build"
        ]

        assert len(started) == 2
        root_entry = next(entry for entry in started if "scope_path" not in entry)
        child_entry = next(entry for entry in started if entry.get("scope_path") == ["call"])
        assert root_entry["step_id"] == child_entry["step_id"] == "build"
        assert child_entry["workflow_id"] == "child"


class TestPublicOutputShapes:
    def test_completed_shape(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        out = _run(project_dir, "parent").step_results["c"]["output"]
        assert out["status"] == "completed"
        assert out["workflow"] == "child"

    def test_failed_shape(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "exit 3")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "continue_on_error": True,
                    }
                ],
            ),
        )
        result = _run(project_dir, "parent").step_results["c"]
        assert result["status"] == "failed"
        assert result["output"]["status"] == "failed"
        assert result["output"]["workflow"] == "child"

    def test_paused_shape(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [{"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"]}],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.PAUSED
        assert state.step_results["c"]["output"]["status"] == "paused"

    def test_aborted_shape(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "g",
                        "type": "gate",
                        "message": "ok?",
                        "options": ["approve", "reject"],
                        "on_reject": "abort",
                    }
                ],
                inputs={"verdict": {"type": "string", "default": ""}},
            ),
        )
        # Abort requires a reject choice; route it through a verdict input.
        _install(
            project_dir,
            "child2",
            _workflow(
                "child2",
                [
                    {
                        "id": "g",
                        "type": "gate",
                        "message": "ok?",
                        "options": ["approve", "reject"],
                        "on_reject": "abort",
                        "verdict_input": "verdict",
                    }
                ],
                inputs={
                    "verdict": {
                        "type": "string",
                        "default": "",
                        "enum": ["approve", "reject", ""],
                    }
                },
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child2",
                        "input": {"verdict": "{{ inputs.verdict }}"},
                    }
                ],
                inputs={"verdict": {"type": "string", "default": "reject"}},
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.ABORTED
        result = state.step_results["c"]
        assert result["status"] == "failed"
        assert result["output"]["status"] == "aborted"
        assert result["output"].get("aborted") is True


class TestContinueOnError:
    def test_child_expression_failure_uses_call_boundary_on_execute(self, project_dir):
        """Expression errors inside a child obey the caller's recovery policy."""
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    _shell("source", "printf not-json"),
                    {
                        "id": "parse",
                        "type": "if",
                        "condition": "{{ steps.source.output.stdout | from_json }}",
                        "then": [_shell("after-parse", "echo unreachable")],
                    },
                ],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "continue_on_error": True,
                    },
                    _shell("after", "echo recovered"),
                ],
            ),
        )

        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["c"]["status"] == "failed"
        assert state.workflow_scopes["c"]["status"] == "failed"
        assert "from_json: invalid JSON" in state.step_results["c"]["error"]
        assert state.step_results["after"]["output"]["stdout"].strip() == "recovered"

    def test_child_expression_failure_uses_call_boundary_on_resume(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "gate",
                        "type": "gate",
                        "message": "continue?",
                        "options": ["approve", "reject"],
                        "verdict_input": "verdict",
                    },
                    _shell("source", "printf not-json"),
                    {
                        "id": "parse",
                        "type": "if",
                        "condition": "{{ steps.source.output.stdout | from_json }}",
                        "then": [_shell("after-parse", "echo unreachable")],
                    },
                ],
                inputs={
                    "verdict": {
                        "type": "string",
                        "default": "",
                        "enum": ["", "approve", "reject"],
                    }
                },
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"verdict": "{{ inputs.verdict }}"},
                        "continue_on_error": True,
                    },
                    _shell("after", "echo recovered"),
                ],
                inputs={"verdict": {"type": "string", "default": ""}},
            ),
        )

        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED

        resumed = engine.resume(state.run_id, {"verdict": "approve"})
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.step_results["c"]["status"] == "failed"
        assert resumed.workflow_scopes["c"]["status"] == "failed"
        assert "from_json: invalid JSON" in resumed.step_results["c"]["error"]
        assert resumed.step_results["after"]["output"]["stdout"].strip() == "recovered"

    @pytest.mark.parametrize("continue_on_error", [False, True])
    def test_output_evaluation_failure_uses_call_boundary(
        self, project_dir, continue_on_error
    ):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("x", "printf not-json")],
                outputs={"parsed": {"value": "{{ steps.x.output.stdout | from_json }}"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c", "type": "workflow", "workflow": "child",
                        "continue_on_error": continue_on_error,
                    },
                    _shell("after", "echo continued"),
                ],
            ),
        )

        state = _run(project_dir, "parent")
        result = state.step_results["c"]
        assert result["status"] == "failed"
        assert result["output"] == {"workflow": "child", "status": "failed"}
        assert "failed to evaluate outputs" in result["error"]
        assert "from_json: invalid JSON" in result["error"]
        assert state.workflow_scopes["c"]["status"] == "failed"
        assert state.workflow_scopes["c"]["step_results"]["x"]["status"] == "completed"
        if continue_on_error:
            assert state.status == RunStatus.COMPLETED
            assert state.step_results["after"]["output"]["stdout"].strip() == "continued"
        else:
            assert state.status == RunStatus.FAILED
            assert state.error == result["error"]
            assert "after" not in state.step_results

    def test_call_boundary_continue(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "exit 3")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "continue_on_error": True,
                    },
                    _shell("after", "echo continued"),
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["c"]["status"] == "failed"
        assert state.step_results["after"]["output"]["stdout"].strip() == "continued"

    def test_included_step_continue(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    _shell("bad", "exit 3", continue_on_error=True),
                    _shell("ok", "echo child-ok"),
                ],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert state.workflow_scopes["c"]["step_results"]["ok"]["status"] == "completed"

    def test_abort_not_overridden_by_continue_on_error(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "g",
                        "type": "gate",
                        "message": "ok?",
                        "options": ["approve", "reject"],
                        "on_reject": "abort",
                        "verdict_input": "verdict",
                    }
                ],
                inputs={
                    "verdict": {
                        "type": "string",
                        "default": "",
                        "enum": ["approve", "reject", ""],
                    }
                },
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "continue_on_error": True,
                        "input": {"verdict": "{{ inputs.verdict }}"},
                    }
                ],
                inputs={"verdict": {"type": "string", "default": "reject"}},
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.ABORTED

    def test_pause_not_bypassed_by_continue_on_error(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [{"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"]}],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "continue_on_error": True,
                    }
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.PAUSED


class TestRuntimeResolutionFailures:
    def test_unknown_target(self, project_dir):
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "does-not-exist",
                        "continue_on_error": True,
                    }
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["c"]["status"] == "failed"
        assert state.step_results["c"]["output"]["status"] == "failed"
        assert "not installed" in state.step_results["c"]["error"]

    def test_disabled_target(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo")]), enabled=False)
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "continue_on_error": True,
                    }
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.step_results["c"]["status"] == "failed"
        assert "disabled" in state.step_results["c"]["error"]

    def test_unknown_input(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow("child", [_shell("x", "echo")], inputs={"known": {"type": "string"}}),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"typo": "x"},
                        "continue_on_error": True,
                    }
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.step_results["c"]["status"] == "failed"
        assert "undeclared input" in state.step_results["c"]["error"]

    def test_non_string_expression_target(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    _shell("pick", "echo 5"),
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "{{ steps.pick.output.exit_code }}",
                        "continue_on_error": True,
                    },
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.step_results["c"]["status"] == "failed"
        assert "expected a string" in state.step_results["c"]["error"]

    def test_dynamic_target_failure_reports_resolved_id(self, project_dir):
        """A post-resolution failure reports the resolved id, not the template."""
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    _shell("pick", "printf missing-wf"),
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "{{ steps.pick.output.stdout }}",
                        "continue_on_error": True,
                    },
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.step_results["c"]["status"] == "failed"
        assert state.step_results["c"]["output"]["workflow"] == "missing-wf"
        assert "not installed" in state.step_results["c"]["error"]

    def test_malformed_input_mapping_fails_step(self, project_dir):
        """A non-mapping ``input`` must fail, not run the child on defaults.

        ``_run`` executes an unvalidated definition (as a direct engine caller
        may), so the helper itself has to reject the malformed mapping.
        """
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("x", "echo {{ inputs.who }}")],
                inputs={"who": {"type": "string", "default": "default-who"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": ["not-a-mapping"],
                        "continue_on_error": True,
                    }
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["c"]["status"] == "failed"
        assert "must be a mapping or omitted" in state.step_results["c"]["error"]
        # The guard fires before a child scope is created, so the child never
        # runs on silently-discarded inputs.
        assert "c" not in state.workflow_scopes

    def test_non_json_safe_input_mapping_persists_clean_failure(self, project_dir):
        """Unsafe authored inputs must not crash recording the failure result.

        ``_run`` intentionally bypasses definition validation, covering direct
        engine callers that hand a YAML-native scalar to a workflow step.
        """
        from datetime import date

        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("x", "echo {{ inputs.who }}")],
                inputs={"who": {"type": "string", "default": "world"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"who": date(2026, 1, 1)},
                        "continue_on_error": True,
                    }
                ],
            ),
        )
        state = _run(project_dir, "parent")
        result = state.step_results["c"]
        assert state.status == RunStatus.COMPLETED
        assert result["status"] == "failed"
        assert "not JSON-safe" in result["error"]
        assert result["input"] == {}
        assert "c" not in state.workflow_scopes

        loaded = RunState.load(state.run_id, project_dir)
        assert loaded.step_results["c"]["input"] == {}

    def test_non_json_safe_dynamic_target_persists_clean_failure(
        self, project_dir, monkeypatch
    ):
        """Invalid target diagnostics must not make the failed call unsaveable."""
        from datetime import date

        monkeypatch.setattr(
            "specify_cli.workflows.step.workflow.evaluate_expression",
            lambda *_: date(2026, 1, 1),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "{{ inputs.target }}",
                        "continue_on_error": True,
                    }
                ],
            ),
        )

        state = _run(project_dir, "parent")
        result = state.step_results["c"]

        assert state.status == RunStatus.COMPLETED
        assert result["status"] == "failed"
        assert result["output"]["workflow"] == "<date>"
        assert "expected a string" in result["error"]
        assert RunState.load(state.run_id, project_dir).step_results["c"] == result


class TestRecursionAndDepth:
    def test_cycle_rejected(self, project_dir):
        _install(
            project_dir,
            "a",
            _workflow("a", [{"id": "b", "type": "workflow", "workflow": "b"}]),
        )
        _install(
            project_dir,
            "b",
            _workflow("b", [{"id": "a", "type": "workflow", "workflow": "a"}]),
        )
        state = _run(project_dir, "a")
        assert state.status == RunStatus.FAILED
        assert "cycle" in (state.error or "").lower()

    def test_diamond_allowed(self, project_dir):
        _install(project_dir, "d", _workflow("d", [_shell("x", "echo d")]))
        _install(
            project_dir, "b", _workflow("b", [{"id": "d", "type": "workflow", "workflow": "d"}])
        )
        _install(
            project_dir, "c", _workflow("c", [{"id": "d", "type": "workflow", "workflow": "d"}])
        )
        _install(
            project_dir,
            "a",
            _workflow(
                "a",
                [
                    {"id": "b", "type": "workflow", "workflow": "b"},
                    {"id": "c", "type": "workflow", "workflow": "c"},
                ],
            ),
        )
        state = _run(project_dir, "a")
        assert state.status == RunStatus.COMPLETED
        assert "d" in state.workflow_scopes["b"]["workflow_scopes"]
        assert "d" in state.workflow_scopes["c"]["workflow_scopes"]

    def _chain(self, project_dir, length: int) -> None:
        for i in range(length):
            if i == length - 1:
                steps = [_shell("x", "echo end")]
            else:
                steps = [{"id": "next", "type": "workflow", "workflow": f"w{i + 1}"}]
            _install(project_dir, f"w{i}", _workflow(f"w{i}", steps))

    def test_depth_16_allowed(self, project_dir):
        # w0 (depth 0) ... w16 (depth 16): 16 included levels.
        self._chain(project_dir, MAX_COMPOSITION_DEPTH + 1)
        state = _run(project_dir, "w0")
        assert state.status == RunStatus.COMPLETED

    def test_depth_17_rejected(self, project_dir):
        self._chain(project_dir, MAX_COMPOSITION_DEPTH + 2)
        state = _run(project_dir, "w0")
        assert state.status == RunStatus.FAILED
        assert "maximum depth" in (state.error or "")


class TestPersistence:
    def test_state_json_contains_scope_tree(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        state = _run(project_dir, "parent")
        state_path = state.runs_dir / "state.json"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        assert "workflow_scopes" in data
        scope = data["workflow_scopes"]["c"]
        assert scope["workflow_id"] == "child"
        # The resolved definition lives in an immutable YAML snapshot, not in
        # the JSON state, so YAML-native scalars never reach json.dump.
        assert "definition" not in scope
        ref = scope["definition_snapshot"]
        snapshot = yaml.safe_load(
            (state.runs_dir / "snapshots" / ref).read_text(encoding="utf-8")
        )
        assert snapshot["workflow"]["id"] == "child"

    def test_load_defaults_when_absent(self, project_dir):
        state = RunState(run_id="r", workflow_id="w", project_root=project_dir)
        state.status = RunStatus.PAUSED
        state.save()
        path = state.runs_dir / "state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("workflow_scopes", None)
        path.write_text(json.dumps(data), encoding="utf-8")
        loaded = RunState.load("r", project_dir)
        assert loaded.workflow_scopes == {}

    def test_backward_compatible_pre_feature_state(self, project_dir):
        state = RunState(run_id="old", workflow_id="w", project_root=project_dir)
        state.status = RunStatus.PAUSED
        state.save()
        path = state.runs_dir / "state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("workflow_scopes", None)
        path.write_text(json.dumps(data), encoding="utf-8")
        loaded = RunState.load("old", project_dir)
        assert loaded.workflow_scopes == {}

    def test_load_rejects_out_of_range_nested_step_index(self, project_dir):
        """A nested scope's index must stay within its persisted step count.

        A malformed index would otherwise slice the child's remaining steps to
        an empty list and let the scope silently complete on resume.
        """
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        state = _run(project_dir, "parent")
        path = state.runs_dir / "state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        scope = data["workflow_scopes"]["c"]
        snapshot = yaml.safe_load(
            (state.runs_dir / "snapshots" / scope["definition_snapshot"]).read_text(
                encoding="utf-8"
            )
        )
        scope["current_step_index"] = len(snapshot["steps"]) + 1
        path.write_text(json.dumps(data), encoding="utf-8")

        with pytest.raises(ValueError, match="out of range"):
            RunState.load(state.run_id, project_dir)

    def test_yaml_native_scalar_in_composed_definition_persists(self, project_dir):
        """A YAML-native date must not break composed-scope persistence.

        PyYAML parses an unquoted ``2026-01-01`` to ``datetime.date``, which
        ``json.dump`` cannot encode. The resolved definition is kept in a YAML
        snapshot; the gate's persisted step output is coerced to text.
        """
        from datetime import date

        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [{"id": "review", "type": "gate", "message": date(2026, 1, 1)}],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.PAUSED
        scope = state.workflow_scopes["c"]
        snapshot = yaml.safe_load(
            (state.runs_dir / "snapshots" / scope["definition_snapshot"]).read_text(
                encoding="utf-8"
            )
        )
        assert isinstance(snapshot["steps"][0]["message"], date)
        assert scope["step_results"]["review"]["output"]["message"] == "2026-01-01"

    def test_completion_handoff_is_atomic(self, project_dir, monkeypatch):
        """Every persisted snapshot with a COMPLETED child also has its caller result."""
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )

        snapshots: list[dict] = []
        real = RunState._atomic_write_json

        def spy(path, data):
            if str(path).endswith("state.json"):
                snapshots.append(json.loads(json.dumps(data)))
            return real(path, data)

        monkeypatch.setattr(RunState, "_atomic_write_json", staticmethod(spy))
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert snapshots
        for snap in snapshots:
            for key, scope in (snap.get("workflow_scopes") or {}).items():
                if scope.get("status") == "completed":
                    assert key in snap["step_results"], snap

    def test_concurrent_fan_out_cannot_save_unpaired_completion(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows.composition import ExecutionScope

        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [{
                    "id": "spread", "type": "fan-out", "items": ["a", "b"],
                    "max_concurrency": 2,
                    "step": {"id": "call", "type": "workflow", "workflow": "child"},
                }],
            ),
        )

        first_waiting = Event()
        sibling_saved = Event()
        snapshots = []
        real_record_and_save = ExecutionScope.record_and_save

        def coordinated_handoff(self, context, step_id, data, **kwargs):
            if step_id == "spread:call:0":
                first_waiting.set()
                assert sibling_saved.wait(5), "sibling never saved during handoff"
            elif step_id == "spread:call:1":
                assert first_waiting.wait(5), "first item never reached handoff"
                # Emulate the sibling worker's ordinary progress save while
                # item 0 has finished its subtree but has not recorded its result.
                self.persist()
                snapshots.append(json.loads((self.root().root_state.runs_dir / "state.json").read_text()))
                sibling_saved.set()
            return real_record_and_save(self, context, step_id, data, **kwargs)

        monkeypatch.setattr(ExecutionScope, "record_and_save", coordinated_handoff)
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert len(snapshots) == 1
        snapshot = snapshots[0]
        assert snapshot["workflow_scopes"]["spread:call:0"]["status"] == "running"
        assert "spread:call:0" not in snapshot["step_results"]
        assert all(
            child["status"] != "completed" or key in snapshot["step_results"]
            for key, child in snapshot["workflow_scopes"].items()
        )


class TestSerializedScopeValidation:
    def _save_state_with_scope(self, project_dir, definition):
        state = RunState(run_id="r", workflow_id="w", project_root=project_dir)
        state.status = RunStatus.PAUSED
        state.workflow_scopes = {
            "c": {
                "workflow_id": "child",
                "invocation_id": "c",
                "definition": definition,
                "inputs": {},
                "status": "paused",
                "current_step_index": 0,
                "step_results": {},
                "workflow_scopes": {},
            }
        }
        state.save()
        return state

    def test_load_allows_well_formed_unregistered_step_type(self, project_dir):
        """Schema validation must not depend on the live step registry.

        A composed child may use a project custom step that is not loaded in
        this process (``workflow status`` never calls ``load_custom_steps``).
        """
        self._save_state_with_scope(
            project_dir,
            _workflow("child", [{"id": "s", "type": "not-registered"}]),
        )
        loaded = RunState.load("r", project_dir)
        assert loaded.workflow_scopes["c"]["workflow_id"] == "child"

    def test_load_rejects_non_list_steps(self, project_dir):
        definition = _workflow("child", [])
        definition["steps"] = {"id": "s"}
        self._save_state_with_scope(project_dir, definition)
        with pytest.raises(ValueError, match=r"\.steps' must be a list"):
            RunState.load("r", project_dir)

    def test_load_rejects_step_without_id(self, project_dir):
        self._save_state_with_scope(
            project_dir, _workflow("child", [{"type": "shell", "run": "true"}])
        )
        with pytest.raises(ValueError, match="non-empty string"):
            RunState.load("r", project_dir)

    def _save_state_with_snapshot_ref(self, project_dir, ref):
        state = RunState(run_id="r", workflow_id="w", project_root=project_dir)
        state.status = RunStatus.PAUSED
        state.workflow_scopes = {
            "c": {
                "workflow_id": "child",
                "invocation_id": "c",
                "definition_snapshot": ref,
                "inputs": {},
                "status": "paused",
                "current_step_index": 0,
                "step_results": {},
                "workflow_scopes": {},
            }
        }
        state.save()
        return state

    def test_snapshot_definition_loads(self, project_dir):
        snap_dir = (
            project_dir / ".specify" / "workflows" / "runs" / "r" / "snapshots"
        )
        snap_dir.mkdir(parents=True, exist_ok=True)
        (snap_dir / "child-abc123.yml").write_text(
            yaml.safe_dump(
                _workflow("child", [{"id": "s", "type": "shell", "run": "true"}])
            ),
            encoding="utf-8",
        )
        self._save_state_with_snapshot_ref(project_dir, "child-abc123.yml")
        loaded = RunState.load("r", project_dir)
        assert (
            loaded.workflow_scopes["c"]["definition_snapshot"]
            == "child-abc123.yml"
        )

    def test_load_rejects_missing_snapshot(self, project_dir):
        self._save_state_with_snapshot_ref(project_dir, "child-deadbeef.yml")
        with pytest.raises(ValueError, match="missing"):
            RunState.load("r", project_dir)

    def test_load_rejects_unsafe_snapshot_ref(self, project_dir):
        self._save_state_with_snapshot_ref(project_dir, "../escape.yml")
        with pytest.raises(
            ValueError, match="Invalid definition snapshot reference"
        ):
            RunState.load("r", project_dir)

    def test_custom_step_scope_loads_without_registration(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows import STEP_REGISTRY
        from specify_cli.workflows.base import StepBase, StepResult

        class _Custom(StepBase):
            type_key = "temp-custom-step"

            def execute(self, config, context):
                return StepResult(output={"ok": True})

        monkeypatch.setitem(STEP_REGISTRY, "temp-custom-step", _Custom())
        _install(
            project_dir,
            "child",
            _workflow("child", [{"id": "s", "type": "temp-custom-step"}]),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED

        # Simulate a fresh process that did not load project custom steps:
        # `workflow status` must still be able to load the persisted run.
        monkeypatch.delitem(STEP_REGISTRY, "temp-custom-step")
        loaded = RunState.load(state.run_id, project_dir)
        assert loaded.workflow_scopes["c"]["workflow_id"] == "child"


class TestResume:
    def _paused_child(self, project_dir, child_steps, *, child_inputs=None, outputs=None):
        _install(
            project_dir,
            "child",
            _workflow("child", child_steps, inputs=child_inputs, outputs=outputs),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"verdict": "{{ inputs.verdict }}"},
                    }
                ],
                inputs={"verdict": {"type": "string", "default": ""}},
            ),
        )

    def test_pause_resumes_from_scope_index(self, project_dir):
        self._paused_child(
            project_dir,
            [
                {"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"],
                 "verdict_input": "verdict"},
                _shell("after", "echo after"),
            ],
            child_inputs={
                "verdict": {
                    "type": "string",
                    "default": "",
                    "enum": ["approve", ""],
                }
            },
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED

        resumed = engine.resume(state.run_id, {"verdict": "approve"})
        assert resumed.status == RunStatus.COMPLETED
        child = resumed.workflow_scopes["c"]
        assert child["step_results"]["after"]["status"] == "completed"

    def test_failed_call_retries_on_resume(self, project_dir, monkeypatch):
        from specify_cli.workflows import STEP_REGISTRY
        from specify_cli.workflows.base import StepBase, StepResult

        calls = 0

        class _FailOnce(StepBase):
            type_key = "fail-once"

            def execute(self, config, context):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return StepResult(status=StepStatus.FAILED, error="first attempt")
                return StepResult(status=StepStatus.COMPLETED)

        monkeypatch.setitem(STEP_REGISTRY, "fail-once", _FailOnce())
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [{"id": "x", "type": "fail-once"}],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [{"id": "c", "type": "workflow", "workflow": "child"}],
            ),
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.FAILED
        assert state.workflow_scopes["c"]["status"] == "failed"

        resumed = engine.resume(state.run_id)
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.workflow_scopes["c"]["status"] == "completed"
        assert calls == 2

    def test_failed_output_evaluation_retries_on_resume(self, project_dir):
        marker = project_dir / "valid-json"
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    _shell("prepare", "echo prepared"),
                    _shell("x", f"test -f {marker} && printf '{{\"ok\": true}}' || printf bad"),
                ],
                outputs={"parsed": {"value": "{{ steps.x.output.stdout | from_json }}"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        calls = []
        engine = WorkflowEngine(project_dir)
        engine.on_step_start = lambda step_id, label: calls.append(step_id)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.FAILED
        assert state.workflow_scopes["c"]["status"] == "failed"
        assert calls == ["c", "prepare", "x"]

        # Repeated output failures must keep the completed prefix intact.
        assert engine.resume(state.run_id).status == RunStatus.FAILED
        assert calls == ["c", "prepare", "x", "c", "x"]

        marker.touch()
        resumed = engine.resume(state.run_id)
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.step_results["c"]["output"]["parsed"] == {"ok": True}
        assert calls == ["c", "prepare", "x", "c", "x", "c", "x"]

    def test_resume_uses_definition_snapshot(self, project_dir):
        self._paused_child(
            project_dir,
            [
                {"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"],
                 "verdict_input": "verdict"},
                _shell("x", "echo v1"),
            ],
            child_inputs={
                "verdict": {
                    "type": "string",
                    "default": "",
                    "enum": ["approve", ""],
                }
            },
            outputs={"v": {"value": "{{ steps.x.output.stdout }}"}},
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED

        # Edit the installed child: new invocations see v2, the bound scope does not.
        edited = _workflow(
            "child",
            [
                {"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"],
                 "verdict_input": "verdict"},
                _shell("x", "echo v2"),
            ],
            inputs={"verdict": {"type": "string", "default": "", "enum": ["approve", ""]}},
            outputs={"v": {"value": "{{ steps.x.output.stdout }}"}},
        )
        _install(project_dir, "child", edited)

        resumed = engine.resume(state.run_id, {"verdict": "approve"})
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.step_results["c"]["output"]["v"].strip() == "v1"

    def test_resume_does_not_resolve_bound_target(self, project_dir, monkeypatch):
        from specify_cli.workflows.catalog import WorkflowRegistry
        from specify_cli.workflows.step.workflow import WorkflowStep

        self._paused_child(
            project_dir,
            [
                {
                    "id": "g", "type": "gate", "message": "ok?",
                    "options": ["approve", "reject"], "verdict_input": "verdict",
                }
            ],
            child_inputs={"verdict": {"type": "string", "default": ""}},
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED

        registry = WorkflowRegistry(project_dir)
        registry.add("child", {**registry.get("child"), "enabled": False})

        def unexpected_resolution(self, config, context):
            pytest.fail("a bound workflow target was resolved again")

        monkeypatch.setattr(WorkflowStep, "execute", unexpected_resolution)
        resumed = engine.resume(state.run_id, {"verdict": "approve"})
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.workflow_scopes["c"]["status"] == "completed"

    def test_resume_input_update_forwards_through_mapping(self, project_dir):
        self._paused_child(
            project_dir,
            [
                {"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"],
                 "on_reject": "abort", "verdict_input": "verdict"},
            ],
            child_inputs={
                "verdict": {
                    "type": "string",
                    "default": "",
                    "enum": ["approve", "reject", ""],
                }
            },
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED

        resumed = engine.resume(state.run_id, {"verdict": "approve"})
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.workflow_scopes["c"]["inputs"]["verdict"] == "approve"

    def test_rebind_failure_marks_paused_child_failed(self, project_dir):
        """A rejected resumed binding cannot leave a bypassed child paused."""
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [{"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"]}],
                inputs={
                    "mode": {
                        "type": "string",
                        "default": "",
                        "enum": ["approve", ""],
                    }
                },
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"mode": "{{ inputs.mode }}"},
                        "continue_on_error": True,
                    },
                    _shell("after", "echo continued"),
                ],
                inputs={"mode": {"type": "string", "default": ""}},
            ),
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED
        assert state.workflow_scopes["c"]["status"] == "paused"

        resumed = engine.resume(state.run_id, {"mode": "invalid"})
        child = resumed.workflow_scopes["c"]
        caller = resumed.step_results["c"]
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.step_results["after"]["output"]["stdout"].strip() == "continued"
        assert caller["status"] == "failed"
        assert child["status"] == "failed"
        assert child["error"] == caller["error"]

        loaded = RunState.load(resumed.run_id, project_dir)
        assert loaded.workflow_scopes["c"]["status"] == "failed"
        assert loaded.workflow_scopes["c"]["error"] == caller["error"]

    def test_concurrent_save_cannot_persist_unpaired_rebind_failure(
        self, project_dir, monkeypatch
    ):
        """A failed rebinding is committed with its caller result atomically."""
        from specify_cli.workflows.composition import ExecutionScope

        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "g",
                        "type": "gate",
                        "message": "ok?",
                        "options": ["approve", "reject"],
                    }
                ],
                inputs={
                    "mode": {
                        "type": "string",
                        "default": "",
                        "enum": ["approve", ""],
                    }
                },
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"mode": "{{ inputs.mode }}"},
                        "continue_on_error": True,
                    }
                ],
                inputs={"mode": {"type": "string", "default": ""}},
            ),
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED

        snapshots: list[dict] = []
        real_commit = ExecutionScope.commit_cursor_result

        def coordinated_handoff(self, context, step_id, data, **kwargs):
            if step_id == "c":
                worker = Thread(target=self.persist)
                worker.start()
                worker.join(timeout=5)
                assert not worker.is_alive(), "concurrent save did not complete"
                snapshots.append(
                    json.loads(
                        (self.root().root_state.runs_dir / "state.json").read_text(
                            encoding="utf-8"
                        )
                    )
                )
            return real_commit(self, context, step_id, data, **kwargs)

        monkeypatch.setattr(ExecutionScope, "commit_cursor_result", coordinated_handoff)
        resumed = engine.resume(state.run_id, {"mode": "invalid"})

        assert resumed.status == RunStatus.COMPLETED
        assert len(snapshots) == 1
        snapshot = snapshots[0]
        assert snapshot["workflow_scopes"]["c"]["status"] == "paused"
        assert snapshot["step_results"]["c"]["status"] == "paused"
        assert resumed.workflow_scopes["c"]["status"] == "failed"
        assert resumed.step_results["c"]["status"] == "failed"

    def test_resume_without_input_updates_keeps_binding(self, project_dir):
        self._paused_child(
            project_dir,
            [
                {"id": "g", "type": "gate", "message": "ok?", "options": ["approve", "reject"],
                 "verdict_input": "verdict"},
            ],
            child_inputs={
                "verdict": {
                    "type": "string",
                    "default": "approve",
                    "enum": ["approve", ""],
                }
            },
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED
        before = state.workflow_scopes["c"]["inputs"]["verdict"]

        # No explicit --input: the gate still sees the persisted default.
        resumed = engine.resume(state.run_id)
        assert resumed.workflow_scopes["c"]["inputs"]["verdict"] == before

    def test_retry_gate_keeps_reset_child_input_without_root_update(self, project_dir):
        self._paused_child(
            project_dir,
            [{
                "id": "g", "type": "gate", "message": "ok?",
                "options": ["approve", "reject"], "on_reject": "retry",
                "verdict_input": "verdict",
            }],
            child_inputs={"verdict": {
                "type": "string", "default": "", "enum": ["", "approve", "reject"],
            }},
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {"verdict": "reject"})
        assert state.status == RunStatus.PAUSED
        assert state.inputs["verdict"] == "reject"
        assert state.workflow_scopes["c"]["inputs"]["verdict"] == ""
        assert state.workflow_scopes["c"]["step_results"]["g"]["output"]["choice"] == "reject"

        resumed = engine.resume(state.run_id)
        assert resumed.status == RunStatus.PAUSED
        assert resumed.workflow_scopes["c"]["inputs"]["verdict"] == ""
        assert resumed.workflow_scopes["c"]["step_results"]["g"]["output"]["choice"] is None

        approved = engine.resume(state.run_id, {"verdict": "approve"})
        assert approved.status == RunStatus.COMPLETED
        assert approved.workflow_scopes["c"]["inputs"]["verdict"] == "approve"

    def test_root_input_update_propagates_through_nested_calls(self, project_dir):
        gate = {
            "id": "g", "type": "gate", "message": "ok?",
            "options": ["approve", "reject"], "verdict_input": "verdict",
        }
        inputs = {"verdict": {"type": "string", "default": ""}}
        _install(project_dir, "leaf", _workflow("leaf", [gate], inputs=inputs))
        _install(project_dir, "middle", _workflow(
            "middle", [{
                "id": "leaf-call", "type": "workflow", "workflow": "leaf",
                "input": {"verdict": "{{ inputs.verdict }}"},
            }], inputs=inputs,
        ))
        _install(project_dir, "parent", _workflow(
            "parent", [{
                "id": "middle-call", "type": "workflow", "workflow": "middle",
                "input": {"verdict": "{{ inputs.verdict }}"},
            }], inputs=inputs,
        ))
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED

        resumed = engine.resume(state.run_id, {"verdict": "approve"})
        assert resumed.status == RunStatus.COMPLETED
        middle = resumed.workflow_scopes["middle-call"]
        assert middle["inputs"]["verdict"] == "approve"
        leaf = middle["workflow_scopes"]["leaf-call"]
        assert leaf["inputs"]["verdict"] == "approve"
        assert leaf["step_results"]["g"]["output"]["choice"] == "approve"


class TestRepeatedCalls:
    def test_same_named_calls_in_separate_branches_keep_distinct_scopes(
        self, project_dir
    ):
        _install(project_dir, "child", _workflow(
            "child", [_shell("capture", "echo {{ inputs.value }}")],
            inputs={"value": {"type": "string", "required": True}},
        ))
        parent = _workflow("parent", [
            {"id": branch, "type": "if", "condition": True, "then": [
                {"id": "call", "type": "workflow", "workflow": "child",
                 "input": {"value": branch}},
            ]}
            for branch in ("first", "second")
        ])
        state = WorkflowEngine(project_dir).execute(WorkflowDefinition(parent))
        assert state.status == RunStatus.COMPLETED
        assert set(state.workflow_scopes) == {"first:call", "second:call"}
        assert {
            key: record["step_results"]["capture"]["output"]["stdout"].strip()
            for key, record in state.workflow_scopes.items()
        } == {"first:call": "first", "second:call": "second"}
        assert set(RunState.load(state.run_id, project_dir).workflow_scopes) == {
            "first:call", "second:call"
        }

    def test_later_nested_call_reuses_its_own_scope_on_resume(self, project_dir):
        from specify_cli.workflows import STEP_REGISTRY
        from specify_cli.workflows.base import StepBase, StepResult

        calls = []

        class Count(StepBase):
            type_key = "count"

            def execute(self, config, context):
                calls.append(context.inputs["value"])
                if context.inputs["value"] == "second" and not context.inputs["approved"]:
                    return StepResult(status=StepStatus.PAUSED)
                return StepResult(status=StepStatus.COMPLETED)

        old = STEP_REGISTRY.get("count")
        STEP_REGISTRY["count"] = Count()
        try:
            _install(project_dir, "child", _workflow(
                "child", [{"id": "count", "type": "count"}],
                inputs={
                    "value": {"type": "string", "required": True},
                    "approved": {"type": "boolean", "default": False},
                },
            ))
            parent = _workflow("parent", [
                {"id": branch, "type": "if", "condition": True, "then": [
                    {"id": "call", "type": "workflow", "workflow": "child",
                     "input": {"value": branch, "approved": "{{ inputs.approved }}"}},
                ]}
                for branch in ("first", "second")
            ], inputs={"approved": {"type": "boolean", "default": False}})
            engine = WorkflowEngine(project_dir)
            state = engine.execute(WorkflowDefinition(parent))
            assert state.status == RunStatus.PAUSED
            assert set(state.workflow_scopes) == {"first:call", "second:call"}
            assert engine.resume(state.run_id, {"approved": True}).status == RunStatus.COMPLETED
            assert calls == ["first", "second", "second"]
        finally:
            if old is None:
                STEP_REGISTRY.pop("count", None)
            else:
                STEP_REGISTRY["count"] = old

    def test_handled_child_failure_commits_caller_progress(self, project_dir, monkeypatch):
        from specify_cli.workflows import STEP_REGISTRY
        from specify_cli.workflows.base import StepBase, StepResult
        from specify_cli.workflows.composition import ExecutionScope

        calls = []

        class Fail(StepBase):
            type_key = "fail-once"

            def execute(self, config, context):
                calls.append("child")
                return StepResult(status=StepStatus.FAILED, error="expected failure")

        monkeypatch.setitem(STEP_REGISTRY, "fail-once", Fail())
        _install(project_dir, "child", _workflow(
            "child", [{"id": "fail", "type": "fail-once"}]
        ))
        parent = WorkflowDefinition(_workflow("parent", [
            {"id": "call", "type": "workflow", "workflow": "child",
             "continue_on_error": True},
            _shell("after", "echo done"),
        ]))
        original = ExecutionScope.append_log
        raised = False

        def fail_completion_log(self, entry):
            nonlocal raised
            if entry.get("event") == "step_completed" and entry.get("step_id") == "call" and not raised:
                raised = True
                raise RuntimeError("log failed")
            return original(self, entry)

        monkeypatch.setattr(ExecutionScope, "append_log", fail_completion_log)
        engine = WorkflowEngine(project_dir)
        with pytest.raises(RuntimeError, match="log failed"):
            engine.execute(parent, run_id="handled-failure-run")
        loaded = RunState.load("handled-failure-run", project_dir)
        assert loaded.continuation["sequence"]["next_index"] == 1
        assert loaded.step_results["call"]["status"] == "failed"
        assert loaded.workflow_scopes["call"]["status"] == "failed"
        assert engine.resume(loaded.run_id).status == RunStatus.COMPLETED
        assert calls == ["child"]

    def test_long_child_expansion_keeps_scope_index_loadable(self, project_dir, monkeypatch):
        from specify_cli.workflows import STEP_REGISTRY
        from specify_cli.workflows.base import StepBase, StepResult

        calls = []

        class Count(StepBase):
            type_key = "count"

            def execute(self, config, context):
                calls.append(config["id"])
                return StepResult(
                    status=StepStatus.PAUSED
                    if config["id"] == "review" and not context.inputs["approved"]
                    else StepStatus.COMPLETED
                )

        monkeypatch.setitem(STEP_REGISTRY, "count", Count())
        _install(project_dir, "child", _workflow(
            "child", [{"id": "branch", "type": "if", "condition": True,
                       "then": [{"id": name, "type": "count"}
                                for name in ("one", "two", "three", "review", "after")]}],
            inputs={"approved": {"type": "boolean", "default": False}},
        ))
        parent = WorkflowDefinition(_workflow(
            "parent", [{"id": "call", "type": "workflow", "workflow": "child",
                        "input": {"approved": "{{ inputs.approved }}"}}],
            inputs={"approved": {"type": "boolean", "default": False}},
        ))
        engine = WorkflowEngine(project_dir)
        paused = engine.execute(parent)
        assert paused.status == RunStatus.PAUSED
        child = RunState.load(paused.run_id, project_dir).workflow_scopes["call"]
        assert child["current_step_index"] == 0
        assert child["current_step_id"] == "review"
        assert engine.resume(paused.run_id, {"approved": True}).status == RunStatus.COMPLETED
        assert calls == ["one", "two", "three", "review", "review", "after"]

    def test_child_handoff_write_failure_retries_without_replaying_child(
        self, project_dir, monkeypatch
    ):
        from specify_cli.workflows import STEP_REGISTRY
        from specify_cli.workflows.base import StepBase, StepResult

        calls = []

        class Count(StepBase):
            type_key = "count"

            def execute(self, config, context):
                calls.append(config["id"])
                return StepResult(status=StepStatus.COMPLETED)

        monkeypatch.setitem(STEP_REGISTRY, "count", Count())
        _install(project_dir, "child", _workflow(
            "child", [{"id": "count", "type": "count"}]
        ))
        parent = WorkflowDefinition(_workflow(
            "parent", [{"id": "call", "type": "workflow", "workflow": "child"}]
        ))
        real_write = RunState._atomic_write_json
        failed = False

        def fail_handoff(path, data):
            nonlocal failed
            if (path.name == "state.json" and not failed
                    and data["step_results"].get("call", {}).get("status") == "completed"):
                failed = True
                raise OSError("handoff write failed")
            return real_write(path, data)

        monkeypatch.setattr(RunState, "_atomic_write_json", staticmethod(fail_handoff))
        engine = WorkflowEngine(project_dir)
        with pytest.raises(OSError, match="handoff write failed"):
            engine.execute(parent, run_id="handoff-fault-run")
        saved = RunState.load("handoff-fault-run", project_dir)
        assert saved.workflow_scopes["call"]["status"] == "running"
        assert "call" not in saved.step_results
        assert engine.resume(saved.run_id).status == RunStatus.COMPLETED
        assert calls == ["count"]

    def test_nested_if_workflow_calls_have_distinct_loop_invocations(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("capture", "echo {{ inputs.value }}")],
                inputs={"value": {"type": "string", "required": True}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "loop",
                        "type": "while",
                        "condition": "{{ true }}",
                        "max_iterations": 3,
                        "steps": [
                            {
                                "id": "branch",
                                "type": "if",
                                "condition": "{{ true }}",
                                "then": [
                                    {
                                        "id": "call",
                                        "type": "workflow",
                                        "workflow": "child",
                                        "input": {"value": "{{ inputs.value }}"},
                                    }
                                ],
                            }
                        ],
                    }
                ],
                inputs={"value": {"type": "string", "default": "loop"}},
            ),
        )

        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        children = [
            child
            for child in state.workflow_scopes.values()
            if child["workflow_id"] == "child"
        ]
        assert len(children) == 3
        assert all(child["inputs"] == {"value": "loop"} for child in children)

    def test_nested_if_workflow_calls_have_distinct_fan_out_invocations(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("capture", "echo {{ inputs.value }}")],
                inputs={"value": {"type": "string", "required": True}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "spread",
                        "type": "fan-out",
                        "items": ["a", "b", "c"],
                        "step": {
                            "id": "branch",
                            "type": "if",
                            "condition": "{{ true }}",
                            "then": [
                                {
                                    "id": "call",
                                    "type": "workflow",
                                    "workflow": "child",
                                    "input": {"value": "{{ item }}"},
                                }
                            ],
                        },
                    }
                ],
            ),
        )

        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        children = [
            child
            for child in state.workflow_scopes.values()
            if child["workflow_id"] == "child"
        ]
        assert {child["inputs"]["value"] for child in children} == {"a", "b", "c"}

    def test_aborted_child_is_not_restarted_when_resuming_fan_out(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "choose",
                        "type": "if",
                        "condition": "{{ inputs.kind == 'pause' }}",
                        "then": [
                            {
                                "id": "pause-gate",
                                "type": "gate",
                                "message": "continue?",
                                "options": ["approve", "reject"],
                                "on_reject": "abort",
                                "verdict_input": "resume",
                            }
                        ],
                        "else": [
                            {
                                "id": "abort-gate",
                                "type": "gate",
                                "message": "continue?",
                                "options": ["approve", "reject"],
                                "on_reject": "abort",
                                "verdict_input": "verdict",
                            }
                        ],
                    },
                    _shell("after-gate", "echo should-not-run"),
                ],
                inputs={
                    "kind": {"type": "string", "required": True},
                    "verdict": {
                        "type": "string",
                        "default": "reject",
                        "enum": ["", "approve", "reject"],
                    },
                    "resume": {
                        "type": "string",
                        "default": "",
                        "enum": ["", "approve", "reject"],
                    },
                },
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "spread",
                        "type": "fan-out",
                        "items": ["pause", "abort"],
                        "max_concurrency": 2,
                        "step": {
                            "id": "call",
                            "type": "workflow",
                            "workflow": "child",
                            "input": {
                                "kind": "{{ item }}",
                                "verdict": "{{ inputs.verdict }}",
                                "resume": "{{ inputs.resume }}",
                            },
                        },
                    }
                ],
                inputs={
                    "verdict": {"type": "string", "default": "reject"},
                    "resume": {"type": "string", "default": ""},
                },
            ),
        )

        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.PAUSED
        aborted = next(
            child
            for child in state.workflow_scopes.values()
            if child["status"] == "aborted"
        )
        assert "after-gate" not in aborted["step_results"]

        resumed = engine.resume(state.run_id, {"resume": "approve"})
        assert resumed.status == RunStatus.ABORTED
        aborted = next(
            child
            for child in resumed.workflow_scopes.values()
            if child["status"] == "aborted"
        )
        assert "after-gate" not in aborted["step_results"]

    def test_fan_out_scopes_are_distinct(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("x", "echo {{ inputs.who | default('?') }}")],
                inputs={"who": {"type": "string", "default": "?"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "spread",
                        "type": "fan-out",
                        "items": ["a", "b", "c"],
                        "max_concurrency": 3,
                        "step": {
                            "id": "call",
                            "type": "workflow",
                            "workflow": "child",
                            "input": {"who": "{{ item }}"},
                        },
                    }
                ],
            ),
        )
        state = _run(project_dir, "parent")
        assert state.status == RunStatus.COMPLETED
        assert set(state.workflow_scopes) == {
            "spread:call:0",
            "spread:call:1",
            "spread:call:2",
        }

    def test_completed_scope_reused_on_reentry(self, project_dir):
        counter = project_dir / "count.txt"
        _install(
            project_dir,
            "child",
            _workflow("child", [_shell("x", f"echo run >> {counter}")]),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "loop",
                        "type": "while",
                        "condition": "{{ inputs.loop == 'yes' }}",
                        "max_iterations": 2,
                        "steps": [
                            {"id": "call", "type": "workflow", "workflow": "child"},
                            {
                                "id": "gate",
                                "type": "gate",
                                "message": "ok?",
                                "options": ["approve", "reject"],
                            },
                        ],
                    }
                ],
                inputs={"loop": {"type": "string", "default": "yes"}},
            ),
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {"loop": "yes"})
        assert state.status == RunStatus.PAUSED
        # Re-run the same enclosing while step on resume; the completed child is reused.
        resumed = engine.resume(state.run_id)
        assert resumed.status == RunStatus.PAUSED
        assert counter.read_text(encoding="utf-8").count("run") == 1


class TestCustomStepInsideScope:
    def test_custom_step_sees_only_child_scope(self, project_dir, monkeypatch):
        from specify_cli.workflows import STEP_REGISTRY
        from specify_cli.workflows.base import StepBase, StepResult

        class _ScopeProbe(StepBase):
            type_key = "scope-probe"

            def execute(self, config, context):
                return StepResult(
                    output={
                        "inputs": dict(context.inputs),
                        "steps": sorted(context.steps),
                    }
                )

        # Register through monkeypatch so the process-global registry is
        # restored after the test instead of leaking a custom step into later
        # tests (mirrors tests/specify_cli/bundles/test_references.py).
        monkeypatch.setitem(STEP_REGISTRY, "scope-probe", _ScopeProbe())

        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {"id": "probe", "type": "scope-probe"},
                ],
                inputs={"only": {"type": "string", "default": "v"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    _shell("caller", "echo x"),
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"only": "v"},
                    },
                ],
            ),
        )
        state = _run(project_dir, "parent")
        probe = state.workflow_scopes["c"]["step_results"]["probe"]["output"]
        assert probe["inputs"] == {"only": "v"}
        assert probe["steps"] == []


# -- CLI tests ------------------------------------------------------------


class TestCliReporting:
    def _install_composed(self, project_dir):
        _install(project_dir, "child", _workflow("child", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )

    def _invoke(self, project_dir, args):
        from unittest.mock import patch

        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir):
            return runner.invoke(app, args, catch_exceptions=False)

    def test_run_json_payload_includes_scopes(self, project_dir):
        self._install_composed(project_dir)
        result = self._invoke(project_dir, ["workflow", "run", "parent", "--json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        assert payload["status"] == "completed"
        assert payload["scopes"][0]["invocation_id"] == "c"
        assert payload["scopes"][0]["workflow_id"] == "child"
        assert payload["scopes"][0]["current_step_id"] == "x"

    def _install_paused_composed(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "g",
                        "type": "gate",
                        "message": "Nested ok?",
                        "options": ["approve", "reject"],
                    }
                ],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )

    def test_composed_pause_surfaces_nested_gate(self, project_dir):
        """A pause inside a composed workflow must expose the nested gate.

        ``_gate_outcome`` otherwise sees only the root ``workflow`` call step,
        leaving orchestrators without the message/options/choice to drive it.
        """
        self._install_paused_composed(project_dir)
        payload = json.loads(
            self._invoke(project_dir, ["workflow", "run", "parent", "--json"]).stdout
        )
        assert payload["status"] == "paused"
        assert payload["gate"] == {
            "step_id": "g",
            "message": "Nested ok?",
            "options": ["approve", "reject"],
            "choice": None,
            "scope_path": ["c"],
        }

    def test_status_json_surfaces_nested_gate(self, project_dir):
        self._install_paused_composed(project_dir)
        run = json.loads(
            self._invoke(project_dir, ["workflow", "run", "parent", "--json"]).stdout
        )
        payload = json.loads(
            self._invoke(
                project_dir, ["workflow", "status", run["run_id"], "--json"]
            ).stdout
        )
        assert payload["gate"]["scope_path"] == ["c"]
        assert payload["gate"]["step_id"] == "g"

    def test_deeply_nested_gate_reports_scope_path(self, project_dir):
        _install(
            project_dir,
            "leaf",
            _workflow(
                "leaf",
                [
                    {
                        "id": "g",
                        "type": "gate",
                        "message": "Leaf?",
                        "options": ["approve", "reject"],
                    }
                ],
            ),
        )
        _install(
            project_dir,
            "mid",
            _workflow(
                "mid", [{"id": "inner", "type": "workflow", "workflow": "leaf"}]
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "mid"}]),
        )
        payload = json.loads(
            self._invoke(project_dir, ["workflow", "run", "parent", "--json"]).stdout
        )
        assert payload["status"] == "paused"
        assert payload["gate"]["scope_path"] == ["c", "inner"]
        assert payload["gate"]["step_id"] == "g"

    def test_inactive_scope_cannot_report_a_stale_nested_gate(self):
        from specify_cli.workflows._commands import _scope_gate

        stale_gate = {
            "status": "paused",
            "current_step_id": "stale",
            "step_results": {
                "stale": {"type": "gate", "output": {"message": "Old gate"}}
            },
        }
        active_gate = {
            "status": "paused",
            "current_step_id": "active",
            "step_results": {
                "active": {"type": "gate", "output": {"message": "Active gate"}}
            },
        }

        gate = _scope_gate(
            {
                "completed": {"status": "completed", "workflow_scopes": {"old": stale_gate}},
                "active": active_gate,
            },
            [],
            "paused",
        )

        assert gate is not None
        assert gate["step_id"] == "active"
        assert gate["scope_path"] == ["active"]

    @pytest.mark.parametrize(
        ("root_status", "expected_scope"),
        [("paused", "paused"), ("aborted", "aborted")],
    )
    def test_mixed_sibling_statuses_report_gate_matching_root_status(
        self, root_status, expected_scope
    ):
        from types import SimpleNamespace

        from specify_cli.workflows._commands import _gate_outcome

        def gate(status, step_id):
            return {
                "status": status,
                "current_step_id": step_id,
                "step_results": {
                    step_id: {
                        "type": "gate",
                        "output": {"message": step_id, "on_reject": "abort"},
                    }
                },
            }

        # The non-matching sibling is deliberately first, reproducing the
        # timing-dependent insertion order from concurrent fan-out execution.
        state = SimpleNamespace(
            status=SimpleNamespace(value=root_status),
            current_step_id="fan-out",
            step_results={},
            workflow_scopes={
                "aborted": gate("aborted", "abort-gate"),
                "paused": gate("paused", "pause-gate"),
            },
        )

        outcome = _gate_outcome(state)
        assert outcome is not None
        assert outcome["scope_path"] == [expected_scope]
        assert outcome["step_id"] == {
            "paused": "pause-gate",
            "aborted": "abort-gate",
        }[expected_scope]

    def test_snapshot_filename_is_bounded_independently_of_workflow_id(self):
        from specify_cli.workflows.composition import ExecutionScope, _snapshot_ref_for

        reference = _snapshot_ref_for(
            ExecutionScope(scope_id="call", workflow_id="a" * 255)
        )

        assert len(reference.encode("ascii")) == 68

    def test_gate_inside_nested_control_flow_reports_gate(self, project_dir):
        """A gate inside an ``if`` body must be reported, not its enclosing step.

        Nested control-flow bodies run with ``step_offset=-1``, so the scope's
        snapshot index still points at the enclosing ``if`` while
        ``current_step_id`` points at the gate. Deriving the id from the index
        alone would surface the ``if`` step and hide the gate from JSON clients.
        """
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "branch",
                        "type": "if",
                        "condition": "true",
                        "then": [
                            {
                                "id": "g",
                                "type": "gate",
                                "message": "Nested control-flow ok?",
                                "options": ["approve", "reject"],
                            }
                        ],
                    }
                ],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        payload = json.loads(
            self._invoke(project_dir, ["workflow", "run", "parent", "--json"]).stdout
        )
        assert payload["status"] == "paused"
        assert payload["gate"] == {
            "step_id": "g",
            "message": "Nested control-flow ok?",
            "options": ["approve", "reject"],
            "choice": None,
            "scope_path": ["c"],
        }
        # The scope's resting step id is persisted, not just derived on read.
        loaded = RunState.load(payload["run_id"], project_dir)
        assert loaded.workflow_scopes["c"]["current_step_id"] == "g"

    def test_run_json_payload_stable_without_scopes(self, project_dir):
        _install(project_dir, "plain", _workflow("plain", [_shell("x", "echo hi")]))
        result = self._invoke(project_dir, ["workflow", "run", "plain", "--json"])
        payload = json.loads(result.stdout)
        assert "scopes" not in payload

    def test_status_human_renders_scopes(self, project_dir):
        self._install_composed(project_dir)
        run = json.loads(
            self._invoke(project_dir, ["workflow", "run", "parent", "--json"]).stdout
        )
        result = self._invoke(project_dir, ["workflow", "status", run["run_id"]])
        assert result.exit_code == 0, result.output
        assert "Workflow scopes" in result.stdout
        assert "c: completed" in result.stdout

    def test_status_escapes_markup_in_scope_ids(self, project_dir):
        """An authored step ID with Rich markup must not crash ``status``.

        The nested scope key is a caller step ID, and validation permits
        brackets, so ``[`` / ``]`` must be escaped rather than parsed as markup.
        """
        _install(project_dir, "leaf", _workflow("leaf", [_shell("x", "echo hi")]))
        _install(
            project_dir,
            "mid",
            _workflow(
                "mid",
                [{"id": "call[/red]", "type": "workflow", "workflow": "leaf"}],
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "mid"}]),
        )
        run = json.loads(
            self._invoke(project_dir, ["workflow", "run", "parent", "--json"]).stdout
        )
        result = self._invoke(project_dir, ["workflow", "status", run["run_id"]])
        assert result.exit_code == 0, result.output
        assert "call[/red]: completed" in result.stdout

    def test_resume_input_forwards_through_parent_mapping(self, project_dir):
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [
                    {
                        "id": "g",
                        "type": "gate",
                        "message": "ok?",
                        "options": ["approve", "reject"],
                        "verdict_input": "verdict",
                    }
                ],
                inputs={
                    "verdict": {
                        "type": "string",
                        "default": "",
                        "enum": ["approve", ""],
                    }
                },
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow(
                "parent",
                [
                    {
                        "id": "c",
                        "type": "workflow",
                        "workflow": "child",
                        "input": {"verdict": "{{ inputs.verdict }}"},
                    }
                ],
                inputs={"verdict": {"type": "string", "default": ""}},
            ),
        )
        run = json.loads(
            self._invoke(project_dir, ["workflow", "run", "parent", "--json"]).stdout
        )
        assert run["status"] == "paused"
        resumed = json.loads(
            self._invoke(
                project_dir,
                ["workflow", "resume", run["run_id"], "--input", "verdict=approve", "--json"],
            ).stdout
        )
        assert resumed["status"] == "completed"
        assert resumed["scopes"][0]["status"] == "completed"
