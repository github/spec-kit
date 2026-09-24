"""Tests for workflow composition (the built-in ``type: workflow`` step).

Covers the composition helpers, engine scoped execution, strict input binding,
persistence/resume, and CLI reporting. See
``spec/workflow_composition/implementation_plan.md``.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Event

import pytest
import yaml

from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.composition import (
    MAX_COMPOSITION_DEPTH,
    RESERVED_OUTPUT_NAMES,
    bind_composed_inputs,
    check_composition_path,
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
        assert state.step_results["c"]["output"].get("aborted") is True


class TestContinueOnError:
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
        assert data["workflow_scopes"]["c"]["workflow_id"] == "child"
        assert data["workflow_scopes"]["c"]["definition"]["workflow"]["id"] == "child"

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

    def test_failed_call_retries_on_resume(self, project_dir):
        marker = project_dir / "marker"
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("x", f"test -f {marker} || {{ touch {marker}; exit 1; }}")],
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

    def test_failed_output_evaluation_retries_on_resume(self, project_dir):
        marker = project_dir / "valid-json"
        _install(
            project_dir,
            "child",
            _workflow(
                "child",
                [_shell("x", f"test -f {marker} && printf '{{\"ok\": true}}' || printf bad")],
                outputs={"parsed": {"value": "{{ steps.x.output.stdout | from_json }}"}},
            ),
        )
        _install(
            project_dir,
            "parent",
            _workflow("parent", [{"id": "c", "type": "workflow", "workflow": "child"}]),
        )
        engine = WorkflowEngine(project_dir)
        state = engine.execute(_definition(project_dir, "parent"), {})
        assert state.status == RunStatus.FAILED
        assert state.workflow_scopes["c"]["status"] == "failed"

        marker.touch()
        resumed = engine.resume(state.run_id)
        assert resumed.status == RunStatus.COMPLETED
        assert resumed.step_results["c"]["output"]["parsed"] == {"ok": True}

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
    def test_custom_step_sees_only_child_scope(self, project_dir):
        from specify_cli.workflows import STEP_REGISTRY, _register_step
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

        if "scope-probe" not in STEP_REGISTRY:
            _register_step(_ScopeProbe())

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
