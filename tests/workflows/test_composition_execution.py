"""Behavioral contracts for scoped calls and durable execution occurrences."""

from collections import Counter
from datetime import date
import json
import threading

import pytest
import yaml

from specify_cli.workflows import STEP_REGISTRY
from specify_cli.workflows.base import RunStatus, StepBase, StepResult, StepStatus
from specify_cli.workflows.engine import (
    RunState,
    WorkflowDefinition,
    WorkflowEngine,
    validate_workflow,
)


def definition(name, steps, **fields):
    return WorkflowDefinition(
        {"workflow": {"id": name, "name": name}, "steps": steps, **fields}
    )


def install(root, child, enabled=True):
    from specify_cli.workflows.catalog import WorkflowRegistry

    directory = root / ".specify" / "workflows" / child.id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "workflow.yml").write_text(
        yaml.safe_dump(child.data), encoding="utf-8"
    )
    registry = WorkflowRegistry(root)
    registry.add(child.id, {"version": "1.0.0", "enabled": enabled})
    return directory


def call(target="child", **extra):
    return {"id": "call", "type": "workflow", "workflow": target, **extra}


@pytest.fixture
def probe(monkeypatch):
    counts = Counter()

    class Probe(StepBase):
        type_key = "probe"

        def execute(self, config, context):
            from specify_cli.workflows.expressions import evaluate_expression

            counts[config["id"]] += 1
            value = evaluate_expression(config.get("value"), context)
            status = config.get("status", "completed")
            if config.get("await") and not context.inputs.get("approve"):
                status = "paused"
            return StepResult(
                StepStatus(status), output={"value": value, **config.get("output", {})}
            )

    monkeypatch.setitem(STEP_REGISTRY, "probe", Probe())
    return counts


def test_declared_output_and_scope_isolation(tmp_path, probe):
    child = definition(
        "child",
        [
            {"id": "inspect", "type": "probe", "value": "{{ inputs.value }}"},
            {
                "id": "private",
                "type": "probe",
                "value": "{{ steps.parent.output.value }}",
            },
        ],
        inputs={"value": {"type": "string"}},
        outputs={
            "value": {"value": "{{ steps.inspect.output.value }}"},
            "hidden": {"value": "{{ steps.private.output.value }}"},
        },
    )
    install(tmp_path, child)
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {"id": "parent", "type": "probe", "value": "secret"},
                call(input={"value": "mapped"}),
                {
                    "id": "consume",
                    "type": "probe",
                    "value": "{{ steps.call.output.value }}",
                },
            ],
        )
    )
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"] == {
        "workflow": "child",
        "status": "completed",
        "value": "mapped",
        "hidden": None,
    }
    assert state.step_results["consume"]["output"]["value"] == "mapped"
    assert "inspect" not in state.step_results
    assert len(list((tmp_path / ".specify/workflows/runs").iterdir())) == 1


def test_called_workflow_dir_resolves_definition_symlink(tmp_path, monkeypatch, probe):
    import specify_cli.workflows._execution as execution

    resolved_dir = tmp_path / "resolved-child"
    resolved_dir.mkdir()
    symlink_dir = tmp_path / "linked-child"
    symlink_dir.symlink_to(resolved_dir, target_is_directory=True)
    child = definition(
        "child",
        [{"id": "path", "type": "probe", "value": "{{ context.workflow_dir }}"}],
        outputs={"workflow-dir": {"value": "{{ steps.path.output.value }}"}},
    )
    child.source_path = symlink_dir / "workflow.yml"
    monkeypatch.setattr(execution, "resolve_target", lambda *_: child)

    state = WorkflowEngine(tmp_path).execute(definition("parent", [call()]))

    assert state.status == RunStatus.COMPLETED, state.error
    assert state.step_results["call"]["output"]["workflow-dir"] == str(
        resolved_dir
    )


def test_concurrent_nested_calls_keep_downstream_aliases_local(
    tmp_path, monkeypatch, probe
):
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "work", "type": "probe"}],
            inputs={"value": {"type": "number"}},
            outputs={"value": {"value": "{{ inputs.value }}"}},
        ),
    )
    barrier = threading.Barrier(2, timeout=5)
    consumed = {}

    class Consume(StepBase):
        type_key = "consume"

        def execute(self, config, context):
            barrier.wait()
            consumed[context.item] = context.steps["call"]["output"]["value"]
            return StepResult(StepStatus.COMPLETED)

    monkeypatch.setitem(STEP_REGISTRY, "consume", Consume())
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "spread",
                    "type": "fan-out",
                    "items": [1, 2],
                    "max_concurrency": 2,
                    "step": {
                        "id": "branch",
                        "type": "if",
                        "condition": True,
                        "then": [
                            call(input={"value": "{{ item }}"}),
                            {"id": "consume", "type": "consume"},
                        ],
                    },
                }
            ],
        )
    )
    assert state.status == RunStatus.COMPLETED
    assert consumed == {1: 1, 2: 2}
    items = RunState.load(state.run_id, tmp_path).execution["sequence"]["nodes"][0][
        "children"
    ]
    results = [
        item["nodes"][0]["children"][0]["nodes"][0]["result"]["output"]["value"]
        for item in items
    ]
    assert results == [1, 2]
    assert "call" not in state.step_results


def test_nested_resume_freezes_branch_binding_and_completed_prefix(tmp_path, probe):
    child = definition(
        "child",
        [
            {"id": "prepare", "type": "probe"},
            {"id": "wait", "type": "probe", "await": True},
        ],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    directory = install(tmp_path, child)
    root = definition(
        "parent",
        [
            {
                "id": "route",
                "type": "if",
                "condition": "{{ inputs.choose }}",
                "then": [call(input={"approve": "{{ inputs.approve }}"})],
                "else": [{"id": "wrong", "type": "probe"}],
            }
        ],
        inputs={
            "choose": {"type": "boolean", "default": True},
            "approve": {"type": "boolean", "default": False},
        },
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    (directory / "workflow.yml").write_text("invalid", encoding="utf-8")
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"choose": False})
    assert state.status == RunStatus.PAUSED
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})
    assert state.status == RunStatus.COMPLETED
    assert probe == {"prepare": 1, "wait": 3}


@pytest.mark.parametrize(
    "status,aborted,handled,expected",
    [
        ("failed", False, False, "failed"),
        ("failed", False, True, "completed"),
        ("failed", True, True, "aborted"),
        ("paused", False, True, "paused"),
    ],
)
def test_call_outcomes(tmp_path, probe, status, aborted, handled, expected):
    install(
        tmp_path,
        definition(
            "child",
            [
                {
                    "id": "work",
                    "type": "probe",
                    "status": status,
                    "output": {"aborted": aborted},
                },
            ],
        ),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                call(continue_on_error=handled),
                {"id": "after", "type": "probe"},
            ],
        )
    )
    assert state.status.value == expected
    assert probe["after"] == (expected == "completed")
    assert state.step_results["call"]["output"]["status"] == (
        "aborted" if aborted else status
    )


@pytest.mark.parametrize(
    "target", [" child", "child\n", "CHILD", "../child", "runs", 123, date(2026, 1, 1)]
)
def test_invalid_targets_are_handled_failures(tmp_path, probe, target):
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [call(target, continue_on_error=True)])
    )
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["status"] == "failed"
    RunState.load(state.run_id, tmp_path)


@pytest.mark.parametrize(
    "mapping",
    [{"unknown": "x"}, {"value": []}, {"value": date(2026, 1, 1)}, [1], None],
)
def test_invalid_inputs_do_not_execute_child(tmp_path, probe, mapping):
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "work", "type": "probe"}],
            inputs={"value": {"type": "string", "required": True}},
        ),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [call(input=mapping)])
    )
    assert state.status == RunStatus.FAILED
    assert not probe
    RunState.load(state.run_id, tmp_path)


def test_child_exception_propagates_despite_continue_on_error(tmp_path, monkeypatch):
    class Explode(StepBase):
        type_key = "explode"

        def execute(self, config, context):
            raise RuntimeError("child exploded")

    monkeypatch.setitem(STEP_REGISTRY, "explode", Explode())
    install(tmp_path, definition("child", [{"id": "work", "type": "explode"}]))

    with pytest.raises(RuntimeError, match="child exploded"):
        WorkflowEngine(tmp_path).execute(
            definition("parent", [call(continue_on_error=True)])
        )


@pytest.mark.parametrize("location", ["input", "output"])
def test_call_expression_errors_propagate_despite_continue_on_error(
    tmp_path, probe, location
):
    child = definition(
        "child",
        [{"id": "work", "type": "probe"}],
        inputs={"value": {"type": "string"}},
        outputs=(
            {"value": {"value": "{{ inputs.value | from_json }}"}}
            if location == "output"
            else {}
        ),
    )
    install(tmp_path, child)
    config = call(
        input={
            "value": (
                "{{ inputs.value | from_json }}" if location == "input" else "not json"
            )
        },
        continue_on_error=True,
    )

    with pytest.raises(ValueError, match="from_json: invalid JSON"):
        WorkflowEngine(tmp_path).execute(
            definition(
                "parent",
                [config],
                inputs={"value": {"type": "string", "default": "not json"}},
            )
        )


@pytest.mark.parametrize("handled", [False, True])
def test_output_failure_retries_only_finalization(
    tmp_path, monkeypatch, probe, handled
):
    import specify_cli.workflows._execution as execution
    from specify_cli.workflows.composition import CallError

    install(tmp_path, definition("child", [{"id": "work", "type": "probe"}]))
    original = execution.evaluate_outputs
    monkeypatch.setattr(
        execution,
        "evaluate_outputs",
        lambda *_: (_ for _ in ()).throw(CallError("bad output")),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [call(continue_on_error=handled)])
    )
    assert state.status == (
        RunStatus.COMPLETED if handled else RunStatus.FAILED
    )
    if handled:
        assert probe["work"] == 1
        return
    state = WorkflowEngine(tmp_path).resume(state.run_id)
    assert state.status == RunStatus.FAILED
    monkeypatch.setattr(execution, "evaluate_outputs", original)
    state = WorkflowEngine(tmp_path).resume(state.run_id)
    assert state.status == RunStatus.COMPLETED
    assert probe["work"] == 1


def test_output_expression_failure_retries_only_finalization(tmp_path, probe):
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "work", "type": "probe"}],
            inputs={"value": {"type": "string"}},
            outputs={"value": {"value": "{{ inputs.value | from_json }}"}},
        ),
    )
    root = definition(
        "parent",
        [call(input={"value": "{{ inputs.value }}"})],
        inputs={"value": {"type": "string", "default": "not json"}},
    )

    with pytest.raises(ValueError, match="from_json: invalid JSON"):
        WorkflowEngine(tmp_path).execute(root, run_id="output-expression")

    state = WorkflowEngine(tmp_path).resume(
        "output-expression",
        {"value": '{"ok": true}'},
    )

    assert state.status == RunStatus.COMPLETED
    assert probe["work"] == 1
    assert state.step_results["call"]["output"]["value"] == {"ok": True}


@pytest.mark.parametrize("status", [RunStatus.PAUSED, RunStatus.FAILED])
def test_resume_accepts_paused_and_failed_tree_backed_runs(tmp_path, probe, status):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [{"id": "wait", "type": "probe", "status": status.value}],
        )
    )
    assert state.status == status

    resumed = WorkflowEngine(tmp_path).resume(state.run_id)

    assert resumed.status == status


def test_resume_rejects_running_tree_backed_run_without_writes(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [{"id": "wait", "type": "probe", "await": True}])
    )
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    data["status"] = RunStatus.RUNNING.value
    path.write_text(json.dumps(data))
    before = path.read_bytes()

    with pytest.raises(ValueError, match="Cannot resume run .* 'running'"):
        WorkflowEngine(tmp_path).resume(state.run_id)

    assert path.read_bytes() == before


def test_legacy_resume_adapts_once(tmp_path, probe):
    root = definition(
        "parent",
        [
            {"id": "before", "type": "probe"},
            {"id": "wait", "type": "probe", "await": True},
        ],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    del data["execution"]
    path.write_text(json.dumps(data))
    state = WorkflowEngine(tmp_path).resume(state.run_id)
    assert state.status == RunStatus.PAUSED
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})
    assert state.status == RunStatus.COMPLETED
    assert probe == {"before": 1, "wait": 3}


def test_version_one_tree_rejected_without_writes(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [{"id": "wait", "type": "probe", "await": True}])
    )
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    data["execution"]["version"] = 1
    path.write_text(json.dumps(data))
    before = {p.name: p.read_bytes() for p in state.runs_dir.iterdir()}

    with pytest.raises(ValueError, match="Unsupported execution version"):
        WorkflowEngine(tmp_path).resume(state.run_id)

    assert {p.name: p.read_bytes() for p in state.runs_dir.iterdir()} == before


@pytest.mark.parametrize(
    "mutation",
    [
        lambda tree: tree.update(version=99),
        lambda tree: tree["sequence"].update(nodes=[]),
        lambda tree: tree["sequence"]["nodes"][0].update(phase="nonsense"),
        lambda tree: tree["sequence"]["nodes"][0]["binding"].pop("workflow_dir"),
        lambda tree: tree["sequence"]["nodes"][0]["binding"].update(
            workflow_dir=42
        ),
        lambda tree: tree["sequence"]["nodes"][0]["binding"].update(
            workflow_dir={}
        ),
        lambda tree: tree["sequence"]["nodes"][0]["binding"].update(
            definition=42
        ),
    ],
)
def test_bad_checkpoint_rejected_without_writes(tmp_path, probe, mutation):
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "wait", "type": "probe", "await": True}],
            inputs={"approve": {"type": "boolean", "default": False}},
        ),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [call(input={"approve": "{{ inputs.approve }}"})],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    mutation(data["execution"])
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    with pytest.raises(ValueError):
        WorkflowEngine(tmp_path).resume(state.run_id)
    assert path.read_bytes() == before


@pytest.mark.parametrize("index", [0, 1])
def test_unbound_workflow_children_rejected_without_writes(tmp_path, probe, index):
    install(tmp_path, definition("child", [{"id": "work", "type": "probe"}]))
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                call(id="first"),
                call(id="second"),
                {"id": "wait", "type": "probe", "await": True},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    data["execution"]["sequence"]["nodes"][index].pop("binding")
    path.write_text(json.dumps(data))
    before = path.read_bytes()

    with pytest.raises(ValueError):
        WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert path.read_bytes() == before


def test_completed_container_with_unfinished_child_rejected(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "route",
                    "type": "if",
                    "condition": True,
                    "then": [{"id": "work", "type": "probe"}],
                },
                {"id": "wait", "type": "probe", "await": True},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    data["execution"]["sequence"]["nodes"][0]["children"][0]["nodes"][0] = {
        "phase": "ready"
    }
    path.write_text(json.dumps(data))
    before = path.read_bytes()

    with pytest.raises(ValueError):
        WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert path.read_bytes() == before
    assert probe["work"] == 1


@pytest.mark.parametrize("child_phase", ["ready", "blocked"])
def test_completed_workflow_call_with_unfinished_child_rejected(
    tmp_path, probe, child_phase
):
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "work", "type": "probe"}, {"id": "wait", "type": "probe", "await": True}],
            inputs={"approve": {"type": "boolean", "default": False}},
        ),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [call(input={"approve": "{{ inputs.approve }}"}), {"id": "pause", "type": "probe", "await": True}],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    call_node = data["execution"]["sequence"]["nodes"][0]
    call_node.update(phase="done", outcome="completed")
    if child_phase == "ready":
        call_node["children"][0]["nodes"][1] = {"phase": "ready"}
    path.write_text(json.dumps(data))
    before = path.read_bytes()

    with pytest.raises(ValueError, match="Completed execution has unfinished children"):
        WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert path.read_bytes() == before


def test_handled_failed_workflow_call_can_retain_blocked_child(tmp_path, probe):
    install(
        tmp_path,
        definition(
            "child",
            [
                {"id": "fail", "type": "probe", "status": "failed"},
                {"id": "unreached", "type": "probe"},
            ],
        ),
    )

    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [call(continue_on_error=True)])
    )

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["status"] == "failed"
    assert RunState.load(state.run_id, tmp_path).status == RunStatus.COMPLETED


def test_bound_call_without_source_path_resumes_with_null_workflow_dir(
    tmp_path, monkeypatch, probe
):
    import specify_cli.workflows._execution as execution

    child = definition(
        "child",
        [{"id": "wait", "type": "probe", "await": True}],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    monkeypatch.setattr(execution, "resolve_target", lambda *_: child)
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [call(input={"approve": "{{ inputs.approve }}"})],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED
    assert state.execution["sequence"]["nodes"][0]["binding"]["workflow_dir"] is None

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED


@pytest.mark.parametrize("failure_after_replace", [False, True])
def test_checkpoint_failure_leaves_running_run_not_resumable(
    tmp_path, monkeypatch, probe, failure_after_replace
):
    from specify_cli.workflows._execution import CheckpointError

    original = RunState._atomic_write_json
    failed = False

    def write(path, data):
        nonlocal failed
        record = data.get("step_results", {}).get("work")
        if path.name == "state.json" and record and not failed:
            failed = True
            if failure_after_replace:
                original(path, data)
            raise OSError("checkpoint failure")
        original(path, data)

    monkeypatch.setattr(RunState, "_atomic_write_json", staticmethod(write))
    with pytest.raises(CheckpointError, match="checkpoint failure"):
        WorkflowEngine(tmp_path).execute(
            definition("parent", [{"id": "work", "type": "probe"}]), run_id="fault"
        )
    disk = json.loads(
        (tmp_path / ".specify/workflows/runs/fault/state.json").read_text()
    )
    node = disk["execution"]["sequence"]["nodes"][0]
    assert node["phase"] == ("done" if failure_after_replace else "ready")
    assert ("work" in disk["step_results"]) is failure_after_replace
    with pytest.raises(
        ValueError, match="Cannot resume run 'fault' with status 'running'"
    ):
        WorkflowEngine(tmp_path).resume("fault")
    assert probe["work"] == 1


def _interrupt_state_write(monkeypatch, when):
    """Raise ``KeyboardInterrupt`` from the first ``state.json`` write matching *when*."""
    original = RunState._atomic_write_json
    fired = []

    def write(path, data):
        if path.name == "state.json" and not fired and when(data):
            fired.append(path)
            raise KeyboardInterrupt
        original(path, data)

    monkeypatch.setattr(RunState, "_atomic_write_json", staticmethod(write))
    return fired


def _logged_events(state):
    log = (state.runs_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line)["event"] for line in log]


@pytest.mark.parametrize("scope", ["root", "workflow-call"])
def test_interrupt_during_checkpoint_pauses_run(tmp_path, monkeypatch, probe, scope):
    steps = [{"id": "first", "type": "probe"}, {"id": "second", "type": "probe"}]
    if scope == "workflow-call":
        install(tmp_path, definition("child", steps))
        steps = [call()]
    # Interrupt the checkpoint that marks ``second`` active, after ``first`` ran.
    fired = _interrupt_state_write(
        monkeypatch, lambda data: data.get("current_step_id") == "second"
    )

    state = WorkflowEngine(tmp_path).execute(definition("parent", steps))

    # A graceful interrupt is not a checkpoint failure: it reaches the engine's
    # pause path, even inside a called workflow.
    assert fired
    assert state.status == RunStatus.PAUSED
    assert RunState.load(state.run_id, tmp_path).status == RunStatus.PAUSED
    assert _logged_events(state)[-1] == "workflow_interrupted"
    assert probe == {"first": 1}

    state = WorkflowEngine(tmp_path).resume(state.run_id)

    assert state.status == RunStatus.COMPLETED
    assert probe == {"first": 1, "second": 1}


def test_interrupt_during_resume_checkpoint_pauses_run(tmp_path, monkeypatch, probe):
    root = definition(
        "parent",
        [
            {"id": "wait", "type": "probe", "await": True},
            {"id": "next", "type": "probe"},
        ],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    # Interrupt the checkpoint that records ``wait`` as completed on resume.
    fired = _interrupt_state_write(
        monkeypatch,
        lambda data: data.get("step_results", {}).get("wait", {}).get("status")
        == "completed",
    )

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert fired
    assert state.status == RunStatus.PAUSED
    assert RunState.load(state.run_id, tmp_path).status == RunStatus.PAUSED
    assert _logged_events(state)[-1] == "workflow_interrupted"

    state = WorkflowEngine(tmp_path).resume(state.run_id)

    # The interrupted checkpoint's transition is saved by the pause, so the
    # completed ``wait`` is not run a third time.
    assert state.status == RunStatus.COMPLETED
    assert probe == {"wait": 2, "next": 1}


@pytest.mark.parametrize("failure", [KeyboardInterrupt, RuntimeError])
def test_leave_failure_preserves_step_exception(tmp_path, monkeypatch, failure):
    from specify_cli.workflows._execution import Execution

    class Explode(StepBase):
        type_key = "explode"

        def execute(self, config, context):
            raise failure("boom")

    original_transition = Execution.transition

    def transition(self, operation, occurrence, *args, **kwargs):
        if operation == "leave":
            raise ValueError("leave failed")
        return original_transition(self, operation, occurrence, *args, **kwargs)

    monkeypatch.setitem(STEP_REGISTRY, "explode", Explode())
    monkeypatch.setattr(Execution, "transition", transition)
    engine = WorkflowEngine(tmp_path)
    root = definition("parent", [{"id": "work", "type": "explode"}])
    if failure is KeyboardInterrupt:
        state = engine.execute(root, run_id="leave-failure")
        assert state.status == RunStatus.PAUSED
        assert _logged_events(state)[-1] == "workflow_interrupted"
    else:
        with pytest.raises(RuntimeError, match="boom"):
            engine.execute(root, run_id="leave-failure")
        state = RunState.load("leave-failure", tmp_path)
        assert state.error == "boom"


def test_checkpoint_failure_stops_concurrent_fan_out_logging(tmp_path, monkeypatch):
    import specify_cli.workflows._execution as execution
    from specify_cli.workflows._execution import CheckpointError

    items = {}
    first_committed = threading.Event()
    second_failed = threading.Event()

    class Sync(StepBase):
        type_key = "sync"

        def execute(self, config, context):
            items[threading.current_thread()] = context.item
            if context.item == 2:
                assert first_committed.wait(5)
            return StepResult(output={"value": context.item})

    original_transition = execution.Execution.transition
    original_notify = execution.Execution.notify
    original_write = RunState._atomic_write_json

    def transition(self, *args, **kwargs):
        item = items.get(threading.current_thread())
        try:
            original_transition(self, *args, **kwargs)
        except CheckpointError:
            if item == 2:
                second_failed.set()
            raise

    def notify(self, operation, occurrence, **kwargs):
        if items.get(threading.current_thread()) == 1 and operation == "finish":
            # Item 1 committed and released the lock; item 2 now fails its
            # checkpoint before item 1 emits its completion event.
            first_committed.set()
            assert second_failed.wait(5)
        return original_notify(self, operation, occurrence, **kwargs)

    def write(path, data):
        if items.get(threading.current_thread()) == 2:
            raise OSError("disk full")
        original_write(path, data)

    monkeypatch.setitem(STEP_REGISTRY, "sync", Sync())
    monkeypatch.setattr(execution.Execution, "transition", transition)
    monkeypatch.setattr(execution.Execution, "notify", notify)
    monkeypatch.setattr(RunState, "_atomic_write_json", staticmethod(write))
    with pytest.raises(CheckpointError):
        WorkflowEngine(tmp_path).execute(
            definition(
                "parent",
                [
                    {
                        "id": "fan",
                        "type": "fan-out",
                        "items": [1, 2],
                        "max_concurrency": 2,
                        "step": {"type": "sync"},
                    }
                ],
            ),
            run_id="concurrent-fault",
        )

    assert second_failed.is_set()
    log = tmp_path / ".specify/workflows/runs/concurrent-fault/log.jsonl"
    events = [json.loads(line) for line in log.read_text().splitlines()]
    item_events = [
        (entry["event"], entry["step_id"])
        for entry in events
        if entry.get("step_id", "").startswith("fan:")
    ]
    assert sorted(item_events) == [
        ("step_started", "fan:item:0"),
        ("step_started", "fan:item:1"),
    ]


def test_completion_log_failure_does_not_replay_committed_step(
    tmp_path, monkeypatch, probe
):
    original = RunState.append_log
    failed = False

    def log(self, entry):
        nonlocal failed
        if entry["event"] == "step_completed" and not failed:
            failed = True
            raise OSError("log failed")
        original(self, entry)

    monkeypatch.setattr(RunState, "append_log", log)
    with pytest.raises(OSError, match="log failed"):
        WorkflowEngine(tmp_path).execute(
            definition("parent", [{"id": "work", "type": "probe"}]), run_id="log"
        )
    state = WorkflowEngine(tmp_path).resume("log")
    assert state.status == RunStatus.COMPLETED
    assert probe["work"] == 1


def test_container_completion_log_failure_does_not_replay_expansion(
    tmp_path, monkeypatch, probe
):
    original = RunState.append_log
    failed = False
    expanded = 0

    class Expand(StepBase):
        type_key = "expand"

        def execute(self, config, context):
            nonlocal expanded
            expanded += 1
            return StepResult(
                StepStatus.COMPLETED,
                next_steps=[{"id": "work", "type": "probe"}],
            )

    def log(self, entry):
        nonlocal failed
        if entry == {
            "event": "step_completed",
            "step_id": "expand",
            "status": "completed",
        } and not failed:
            failed = True
            raise OSError("log failed")
        original(self, entry)

    monkeypatch.setitem(STEP_REGISTRY, "expand", Expand())
    monkeypatch.setattr(RunState, "append_log", log)
    with pytest.raises(OSError, match="log failed"):
        WorkflowEngine(tmp_path).execute(
            definition("parent", [{"id": "expand", "type": "expand"}]),
            run_id="container-log",
        )

    state = WorkflowEngine(tmp_path).resume("container-log")

    assert state.status == RunStatus.COMPLETED
    assert expanded == 1
    assert probe["work"] == 1


@pytest.mark.parametrize("kind", ["if", "while", "do-while", "fan-out"])
def test_expansion_resume_preserves_completed_work(tmp_path, probe, kind):
    body = [
        {"id": "prepare", "type": "probe"},
        {"id": "wait", "type": "probe", "await": True},
    ]
    config = {"id": "outer", "type": kind, "condition": True, "max_iterations": 2}
    if kind == "if":
        config["then"] = body
    elif kind == "fan-out":
        config.update(
            items=[1, 2],
            max_concurrency=2,
            step={"id": "branch", "type": "if", "condition": True, "then": body},
        )
    else:
        config["steps"] = body
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [config],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})
    assert state.status == RunStatus.COMPLETED
    assert probe["prepare"] == (1 if kind == "if" else 2)


def test_replay_restores_fan_out_item_aliases_from_completed_if(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "route",
                    "type": "if",
                    "condition": True,
                    "then": [
                        {
                            "id": "fan",
                            "type": "fan-out",
                            "items": [1],
                            "step": {
                                "id": "template",
                                "type": "probe",
                                "value": "{{ item }}",
                            },
                        }
                    ],
                },
                {"id": "wait", "type": "probe", "await": True},
                {
                    "id": "join",
                    "type": "fan-in",
                    "wait_for": ["fan"],
                    "output": {"merged": "{{ steps.fan.output.results }}"},
                },
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["fan:template:0"]["output"] == {"value": 1}
    assert state.step_results["join"]["output"]["merged"] == [{"value": 1}]


def test_resume_restores_completed_fan_out_item_aliases(tmp_path, monkeypatch, probe):
    class PauseSecond(StepBase):
        type_key = "pause-second"

        def execute(self, config, context):
            if context.item == 2 and not context.inputs["approve"]:
                return StepResult(StepStatus.PAUSED)
            return StepResult(output={"value": context.item})

    monkeypatch.setitem(STEP_REGISTRY, "pause-second", PauseSecond())
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "step": {"id": "template", "type": "pause-second"},
                },
                {
                    "id": "join",
                    "type": "fan-in",
                    "wait_for": ["fan"],
                    "output": {"merged": "{{ steps.fan.output.results }}"},
                },
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["fan:template:0"]["output"] == {"value": 1}
    assert state.step_results["fan:template:1"]["output"] == {"value": 2}
    assert state.step_results["join"]["output"]["merged"] == [
        {"value": 1},
        {"value": 2},
    ]


def test_replay_keeps_private_nested_fan_out_aliases_private(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "outer",
                    "type": "fan-out",
                    "items": [1],
                    "step": {
                        "id": "outer-item",
                        "type": "fan-out",
                        "items": [1],
                        "step": {"id": "inner", "type": "probe"},
                    },
                },
                {"id": "wait", "type": "probe", "await": True},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert "outer:outer-item:0" in state.step_results
    assert "outer:outer-item:0:inner:0" not in state.step_results


def test_replay_does_not_execute_completed_fan_out_or_emit_callbacks(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)
    root = definition(
        "parent",
        [
            {
                "id": "fan",
                "type": "fan-out",
                "items": [1, 2],
                "step": {
                    "id": "template",
                    "type": "probe",
                    "value": "{{ item }}",
                },
            },
            {"id": "wait", "type": "probe", "await": True},
        ],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    state = engine.execute(root)
    assert state.status == RunStatus.PAUSED
    assert probe == {"template": 2, "wait": 1}
    callbacks.clear()

    state = engine.resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert probe == {"template": 2, "wait": 2}
    assert callbacks == ["wait"]
    assert [
        (entry["event"], entry["step_id"])
        for entry in state.log_entries
        if entry["event"] in {"step_started", "step_completed"}
    ] == [("step_started", "wait"), ("step_completed", "wait")]


def test_fan_out_item_aliases_are_projected_under_run_lock(tmp_path, monkeypatch):
    from specify_cli.workflows._execution import Execution

    class PauseSecond(StepBase):
        type_key = "pause-second"

        def execute(self, config, context):
            if context.item == 2 and not context.inputs["approve"]:
                return StepResult(StepStatus.PAUSED)
            return StepResult(output={"value": context.item})

    monkeypatch.setitem(STEP_REGISTRY, "pause-second", PauseSecond())
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "max_concurrency": 2,
                    "step": {"id": "template", "type": "pause-second"},
                }
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED
    owned = []
    original = Execution.project_alias

    def spy(self, context, name, result):
        owned.append(self.state._lock._is_owned())
        return original(self, context, name, result)

    monkeypatch.setattr(Execution, "project_alias", spy)
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert owned and all(owned)
    assert state.step_results["fan:template:0"]["output"] == {"value": 1}
    assert state.step_results["fan:template:1"]["output"] == {"value": 2}


def test_replay_does_not_start_worker_threads(tmp_path, monkeypatch, probe):
    import specify_cli.workflows._execution as execution

    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "max_concurrency": 2,
                    "step": {"id": "template", "type": "probe"},
                },
                {"id": "wait", "type": "probe", "await": True},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED

    class NoThreads:
        def __init__(self, *args, **kwargs):
            raise AssertionError("replay must not start worker threads")

    monkeypatch.setattr(execution, "ThreadPoolExecutor", NoThreads)
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert probe == {"template": 2, "wait": 2}


def test_fan_out_without_children_survives_replay(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {"id": "fan", "type": "fan-out", "items": [1, 2], "step": {}},
                {"id": "wait", "type": "probe", "await": True},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["fan"]["output"]["results"] == []


def test_replay_does_not_evaluate_completed_loop_condition(
    tmp_path, monkeypatch, probe
):
    import specify_cli.workflows._execution as execution

    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": False,
                    "steps": [{"id": "work", "type": "probe"}],
                },
                {"id": "wait", "type": "probe", "await": True},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED
    monkeypatch.setattr(
        execution,
        "evaluate_condition",
        lambda *_: pytest.fail("replay must not evaluate loop conditions"),
    )

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert probe == {"work": 1, "wait": 2}


def test_replay_does_not_commit_completed_nodes(tmp_path, monkeypatch, probe):
    import specify_cli.workflows._execution as execution

    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {"id": "done", "type": "probe"},
                {"id": "wait", "type": "probe", "await": True},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED
    original = execution.Execution.transition
    committed = []

    def transition(self, operation, occurrence, changes=None, **kwargs):
        if occurrence.node["phase"] == "done":
            committed.append(occurrence.node)
        return original(self, operation, occurrence, changes, **kwargs)

    monkeypatch.setattr(execution.Execution, "transition", transition)

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    assert committed == []


def test_composed_fan_out_joins_container_results(tmp_path, probe):
    install(
        tmp_path,
        definition(
            "child",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "step": {
                        "id": "template",
                        "type": "probe",
                        "value": "{{ item }}",
                    },
                },
                {
                    "id": "join",
                    "type": "fan-in",
                    "wait_for": ["fan"],
                    "output": {"merged": "{{ steps.fan.output.results }}"},
                },
            ],
            outputs={"results": {"value": "{{ steps.join.output.merged }}"}},
        ),
    )

    state = WorkflowEngine(tmp_path).execute(definition("parent", [call()]))

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"]["results"] == [
        {"value": 1},
        {"value": 2},
    ]
    assert "fan:template:0" not in state.step_results
    assert "fan:template:1" not in state.step_results


def test_fan_in_rejects_fan_out_item_alias():
    for alias in ("fan:template:0", "fan:template:not-an-item"):
        errors = validate_workflow(
            definition(
                "parent",
                [
                    {
                        "id": "fan",
                        "type": "fan-out",
                        "items": [1],
                        "step": {"id": "template", "type": "probe"},
                    },
                    {"id": "join", "type": "fan-in", "wait_for": [alias]},
                ],
            )
        )

        assert any("unknown or not-yet-declared" in error for error in errors), alias


def test_fan_in_rejects_item_alias_at_runtime():
    from specify_cli.workflows.base import StepContext
    from specify_cli.workflows.step.fan_in import FanInStep

    result = FanInStep().execute(
        {"id": "join", "type": "fan-in", "wait_for": ["fan:template:0"]},
        StepContext(),
    )

    assert result.status == StepStatus.FAILED
    assert "fan-out item alias" in (result.error or "")


def test_fan_in_container_join_in_loop_sees_current_iteration(tmp_path, monkeypatch, probe):
    calls = []

    class Varying(StepBase):
        type_key = "varying"

        def execute(self, config, context):
            calls.append(1)
            items = [10, 20] if len(calls) == 1 else [30, 40]
            return StepResult(output={"items": items})

    monkeypatch.setitem(STEP_REGISTRY, "varying", Varying())
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": True,
                    "max_iterations": 2,
                    "steps": [
                        {"id": "varying", "type": "varying"},
                        {
                            "id": "fan",
                            "type": "fan-out",
                            "items": "{{ steps.varying.output.items }}",
                            "step": {
                                "id": "template",
                                "type": "probe",
                                "value": "{{ item }}",
                            },
                        },
                        {
                            "id": "join",
                            "type": "fan-in",
                            "wait_for": ["fan"],
                            "output": {"merged": "{{ steps.fan.output.results }}"},
                        },
                    ],
                }
            ],
        )
    )

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["join"]["output"]["merged"] == [
        {"value": 30},
        {"value": 40},
    ]


def test_fan_out_in_later_loop_iteration_uses_qualified_aliases(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": True,
                    "max_iterations": 2,
                    "steps": [
                        {
                            "id": "fan",
                            "type": "fan-out",
                            "items": [1, 2],
                            "step": {
                                "id": "template",
                                "type": "probe",
                                "value": "{{ item }}",
                            },
                        }
                    ],
                }
            ],
        )
    )

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["fan:template:0"]["output"]["value"] == 1
    assert state.step_results["fan:template:1"]["output"]["value"] == 2
    assert state.step_results["loop:fan:1:template:0"]["output"]["value"] == 1
    assert state.step_results["loop:fan:1:template:1"]["output"]["value"] == 2


def test_fan_out_events_and_callbacks_use_qualified_item_ids(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)

    state = engine.execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "step": {"id": "template", "type": "probe"},
                }
            ],
        )
    )

    events = [
        (entry["event"], entry["step_id"])
        for entry in state.log_entries
        if entry["event"] in {"step_started", "step_completed"}
    ]
    assert callbacks == ["fan", "fan:template:0", "fan:template:1"]
    assert events == [
        ("step_started", "fan"),
        ("step_completed", "fan"),
        ("step_started", "fan:template:0"),
        ("step_completed", "fan:template:0"),
        ("step_started", "fan:template:1"),
        ("step_completed", "fan:template:1"),
    ]


def test_unnamed_fan_out_templates_use_item_id_for_results_and_events(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)

    state = engine.execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1],
                    "step": {"type": "probe", "value": "{{ item }}"},
                }
            ],
        )
    )

    item_events = [
        entry["step_id"]
        for entry in state.log_entries
        if entry["event"] in {"step_started", "step_completed"}
        and entry["step_id"].startswith("fan:")
    ]
    assert callbacks == ["fan", "fan:item:0"]
    assert item_events == ["fan:item:0", "fan:item:0"]
    assert state.step_results["fan:item:0"]["output"] == {"value": 1}


def test_loop_events_and_callbacks_use_qualified_iteration_ids(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)

    state = engine.execute(
        definition(
            "parent",
            [
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": True,
                    "max_iterations": 2,
                    "steps": [{"id": "body", "type": "probe"}],
                }
            ],
        )
    )

    events = [
        (entry["event"], entry["step_id"])
        for entry in state.log_entries
        if entry["event"] in {"step_started", "step_completed"}
    ]
    assert callbacks == ["loop", "body", "loop:body:1"]
    assert events == [
        ("step_started", "loop"),
        ("step_completed", "loop"),
        ("step_started", "body"),
        ("step_completed", "body"),
        ("step_started", "loop:body:1"),
        ("step_completed", "loop:body:1"),
    ]


def test_private_scope_events_include_execution_path_and_workflow_id(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)
    install(tmp_path, definition("child", [{"id": "work", "type": "probe"}]))
    state = engine.execute(definition("parent", [call()]))

    call_entries = [
        entry
        for entry in state.log_entries
        if entry.get("step_id") == "call" and entry["event"].startswith("step_")
    ]
    child_entries = [
        entry
        for entry in state.log_entries
        if entry.get("step_id") == "work" and entry["event"].startswith("step_")
    ]
    assert all("execution_path" not in entry for entry in call_entries)
    assert all("workflow_id" not in entry for entry in call_entries)
    assert all(entry["workflow_id"] == "child" for entry in child_entries)
    assert all(entry["execution_path"] == [0, "workflow", 0] for entry in child_entries)
    assert callbacks == ["call", "work"]


def test_completed_workflow_call_replay_emits_no_events(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)
    install(tmp_path, definition("child", [{"id": "work", "type": "probe"}]))
    root = definition(
        "parent",
        [
            call(),
            {"id": "wait", "type": "probe", "await": True},
        ],
        inputs={"approve": {"type": "boolean", "default": False}},
    )

    state = engine.execute(root)
    assert state.status == RunStatus.PAUSED
    callbacks.clear()

    state = engine.resume(state.run_id, {"approve": True})

    events = [
        (entry["event"], entry["step_id"])
        for entry in state.log_entries
        if entry["event"] in {"step_started", "step_completed"}
    ]
    assert state.status == RunStatus.COMPLETED
    assert callbacks == ["wait"]
    assert events == [("step_started", "wait"), ("step_completed", "wait")]


def test_unfinished_workflow_call_emits_events_on_resume(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "wait", "type": "probe", "await": True}],
            inputs={"approve": {"type": "boolean", "default": False}},
        ),
    )
    root = definition(
        "parent",
        [call(input={"approve": "{{ inputs.approve }}"})],
        inputs={"approve": {"type": "boolean", "default": False}},
    )

    state = engine.execute(root)
    assert state.status == RunStatus.PAUSED
    callbacks.clear()

    state = engine.resume(state.run_id, {"approve": True})

    events = [
        (entry["event"], entry["step_id"])
        for entry in state.log_entries
        if entry["event"] in {"step_started", "step_completed"}
    ]
    assert state.status == RunStatus.COMPLETED
    assert callbacks == ["call", "wait"]
    assert events == [
        ("step_started", "call"),
        ("step_started", "wait"),
        ("step_completed", "wait"),
        ("step_completed", "call"),
    ]


@pytest.mark.parametrize(
    "failure, expected",
    [(RuntimeError, RunStatus.FAILED), (KeyboardInterrupt, RunStatus.PAUSED)],
)
def test_resumed_call_discards_status_of_previous_attempt(
    tmp_path, monkeypatch, probe, failure, expected
):
    from specify_cli.workflows._execution import scope_summaries

    explode = {"enabled": True}

    class Explode(StepBase):
        type_key = "explode"

        def execute(self, config, context):
            if explode["enabled"]:
                raise failure("boom")
            return StepResult(StepStatus.COMPLETED)

    monkeypatch.setitem(STEP_REGISTRY, "explode", Explode())
    install(
        tmp_path,
        definition(
            "child",
            [
                {"id": "wait", "type": "probe", "await": True},
                {"id": "work", "type": "explode"},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        ),
    )
    root = definition(
        "parent",
        [call(input={"approve": "{{ inputs.approve }}"})],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    engine = WorkflowEngine(tmp_path)
    state = engine.execute(root)
    assert state.status == RunStatus.PAUSED
    run_id = state.run_id

    if failure is RuntimeError:
        with pytest.raises(RuntimeError, match="boom"):
            engine.resume(run_id, {"approve": True})
    else:
        engine.resume(run_id, {"approve": True})

    state = RunState.load(run_id, tmp_path)
    node = state.execution["sequence"]["nodes"][0]
    assert state.status == expected
    assert node["phase"] == "children"
    assert not {"result", "outcome", "error"} & node.keys()
    assert scope_summaries(state.execution, state.status.value) == [
        {"scope_path": ["call"], "workflow_id": "child", "status": expected.value}
    ]

    explode["enabled"] = False
    state = engine.resume(run_id)
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"]["status"] == "completed"
    assert probe["wait"] == 2


@pytest.mark.parametrize(
    "failure, expected",
    [(RuntimeError, RunStatus.FAILED), (KeyboardInterrupt, RunStatus.PAUSED)],
)
def test_retried_unbound_call_discards_status_of_failed_binding(
    tmp_path, monkeypatch, probe, failure, expected
):
    from specify_cli.workflows._execution import scope_summaries

    explode = {"enabled": True}

    class Explode(StepBase):
        type_key = "explode"

        def execute(self, config, context):
            if explode["enabled"]:
                raise failure("boom")
            return StepResult(StepStatus.COMPLETED)

    monkeypatch.setitem(STEP_REGISTRY, "explode", Explode())
    engine = WorkflowEngine(tmp_path)
    state = engine.execute(definition("parent", [call()]))
    run_id = state.run_id
    node = state.execution["sequence"]["nodes"][0]
    assert state.status == RunStatus.FAILED
    assert node["phase"] == "blocked"
    assert node["result"]["output"]["status"] == "failed"
    assert "binding" not in node

    # The target becomes available; the retry binds and its child then halts.
    install(tmp_path, definition("child", [{"id": "work", "type": "explode"}]))
    if failure is RuntimeError:
        with pytest.raises(RuntimeError, match="boom"):
            engine.resume(run_id)
    else:
        engine.resume(run_id)

    state = RunState.load(run_id, tmp_path)
    node = state.execution["sequence"]["nodes"][0]
    assert state.status == expected
    assert scope_summaries(state.execution, state.status.value) == [
        {"scope_path": ["call"], "workflow_id": "child", "status": expected.value}
    ]
    assert node["phase"] == "children"
    assert node["binding"]["workflow"] == "child"
    assert not {"result", "outcome", "error"} & node.keys()

    explode["enabled"] = False
    state = engine.resume(run_id)
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"]["status"] == "completed"


def test_retried_unbound_call_that_fails_again_records_new_failure(tmp_path, probe):
    engine = WorkflowEngine(tmp_path)
    state = engine.execute(definition("parent", [call()]))
    assert state.status == RunStatus.FAILED

    state = engine.resume(state.run_id)

    node = state.execution["sequence"]["nodes"][0]
    assert state.status == RunStatus.FAILED
    assert node["phase"] == "blocked"
    assert "binding" not in node
    assert node["result"]["output"]["status"] == "failed"
    assert not probe


@pytest.mark.parametrize(
    "template, expected_event, status",
    [
        ({"status": "failed"}, "step_failed", RunStatus.FAILED),
        (
            {"status": "failed", "continue_on_error": True},
            "step_continue_on_error",
            RunStatus.COMPLETED,
        ),
        (
            {"status": "failed", "output": {"aborted": True}},
            "workflow_aborted",
            RunStatus.ABORTED,
        ),
    ],
)
def test_fan_out_failure_events_use_qualified_item_ids(
    tmp_path, probe, template, expected_event, status
):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1],
                    "step": {"id": "template", "type": "probe", **template},
                }
            ],
        )
    )

    failures = [
        entry
        for entry in state.log_entries
        if entry["event"] in {
            "step_failed",
            "step_continue_on_error",
            "workflow_aborted",
        }
    ]
    assert state.status == status
    assert len(failures) == 1
    assert failures[0]["step_id"] == "fan:template:0"
    assert failures[0]["event"] == expected_event


@pytest.mark.parametrize("mode", ["unknown", "disabled", "mismatch", "cycle"])
def test_resolution_failures_are_call_failures(tmp_path, probe, mode):
    if mode != "unknown":
        child = definition(
            "child",
            [call("parent") if mode == "cycle" else {"id": "work", "type": "probe"}],
        )
        directory = install(tmp_path, child, enabled=mode != "disabled")
        if mode == "mismatch":
            child.data["workflow"]["id"] = "other"
            (directory / "workflow.yml").write_text(yaml.safe_dump(child.data))
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [call(continue_on_error=True)])
    )
    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["status"] == "failed"
    assert not probe


@pytest.mark.parametrize(
    "error, handled",
    [
        (ValueError("bad overlay"), True),
        (FileNotFoundError("gone"), True),
        (RuntimeError("resolver bug"), False),
    ],
)
def test_only_resolver_contract_errors_are_call_failures(
    tmp_path, monkeypatch, probe, error, handled
):
    from specify_cli.workflows.overlay.resolver import WorkflowResolver

    install(tmp_path, definition("child", [{"id": "work", "type": "probe"}]))

    def resolve(self, workflow_id):
        raise error

    monkeypatch.setattr(WorkflowResolver, "resolve", resolve)
    parent = definition("parent", [call(continue_on_error=True)])
    if handled:
        state = WorkflowEngine(tmp_path).execute(parent)
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["call"]["status"] == "failed"
    else:
        with pytest.raises(RuntimeError, match="resolver bug"):
            WorkflowEngine(tmp_path).execute(parent)
    assert not probe


@pytest.mark.parametrize(
    "child_continue, call_continue", [(False, False), (True, False), (False, True)]
)
def test_unknown_child_step_is_a_reported_call_failure(
    tmp_path, monkeypatch, probe, child_continue, call_continue
):
    class TemporarilyInstalled(StepBase):
        type_key = "temporarily-installed"

        def execute(self, config, context):
            return StepResult(StepStatus.COMPLETED)

    monkeypatch.setitem(STEP_REGISTRY, "temporarily-installed", TemporarilyInstalled())
    install(
        tmp_path,
        definition(
            "child",
            [
                {"id": "wait", "type": "probe", "await": True},
                {
                    "id": "missing",
                    "type": "temporarily-installed",
                    "continue_on_error": child_continue,
                }
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        ),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                call(
                    input={"approve": "{{ inputs.approve }}"},
                    continue_on_error=call_continue,
                ),
                {"id": "after", "type": "probe"},
            ],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    assert state.status == RunStatus.PAUSED
    monkeypatch.delitem(STEP_REGISTRY, "temporarily-installed")
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    error = "Unknown step type: 'temporarily-installed'"
    events = [entry["event"] for entry in state.log_entries]
    # The missing step itself is terminal inside the child, as at the root.
    assert [
        entry["event"]
        for entry in state.log_entries
        if entry.get("step_id") == "missing" and entry.get("workflow_id") == "child"
    ] == ["step_started", "step_failed"]
    if call_continue:
        # At the call boundary it is a reported child failure.
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["call"]["status"] == "failed"
        assert state.step_results["call"]["output"]["error"] == error
        assert probe == {"wait": 2, "after": 1}
        assert "step_continue_on_error" in events
    else:
        assert state.status == RunStatus.FAILED
        assert state.error == error
        assert probe == {"wait": 2}
        assert "step_continue_on_error" not in events


@pytest.mark.parametrize("call_continue", [False, True])
def test_unknown_child_step_at_bind_is_a_reported_call_failure(
    tmp_path, monkeypatch, probe, call_continue
):
    install(
        tmp_path,
        definition("child", [{"id": "missing", "type": "later-installed"}]),
    )
    parent = definition(
        "parent",
        [call(continue_on_error=call_continue), {"id": "after", "type": "probe"}],
    )
    state = WorkflowEngine(tmp_path).execute(parent, run_id="bind")

    assert "invalid type 'later-installed'" in state.step_results["call"]["error"]
    assert "binding" not in state.execution["sequence"]["nodes"][0]
    if call_continue:
        # Same treatment as an implementation that disappears after binding.
        assert state.status == RunStatus.COMPLETED
        assert state.step_results["call"]["status"] == "failed"
        assert probe == {"after": 1}
        return

    assert state.status == RunStatus.FAILED
    assert not probe

    class LaterInstalled(StepBase):
        type_key = "later-installed"

        def execute(self, config, context):
            return StepResult(StepStatus.COMPLETED)

    monkeypatch.setitem(STEP_REGISTRY, "later-installed", LaterInstalled())
    state = WorkflowEngine(tmp_path).resume("bind")

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["status"] == "completed"
    assert probe == {"after": 1}


def test_step_reported_unknown_type_error_is_handled_like_any_failure(
    tmp_path, monkeypatch, probe
):
    class Mimic(StepBase):
        type_key = "mimic"

        def execute(self, config, context):
            return StepResult(StepStatus.FAILED, error="Unknown step type: 'mimic'")

    monkeypatch.setitem(STEP_REGISTRY, "mimic", Mimic())
    install(tmp_path, definition("child", [{"id": "work", "type": "mimic"}]))
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {"id": "direct", "type": "mimic", "continue_on_error": True},
                call(continue_on_error=True),
                {"id": "after", "type": "probe"},
            ],
        )
    )

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["direct"]["status"] == "failed"
    assert state.step_results["call"]["status"] == "failed"
    assert probe == {"after": 1}


def test_unknown_step_type_resumes_after_reinstall(tmp_path, monkeypatch, probe):
    class Reinstalled(StepBase):
        type_key = "temporarily-installed"

        def execute(self, config, context):
            return StepResult(StepStatus.COMPLETED)

    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [{"id": "missing", "type": "temporarily-installed"}],
        ),
        run_id="reinstall",
    )
    assert state.status == RunStatus.FAILED

    monkeypatch.setitem(STEP_REGISTRY, "temporarily-installed", Reinstalled())
    state = WorkflowEngine(tmp_path).resume("reinstall")

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["missing"]["status"] == "completed"


@pytest.mark.parametrize("workers", [1, 2])
@pytest.mark.parametrize("named", [False, True])
def test_unknown_fan_out_template_step_always_fails_despite_continue_on_error(
    tmp_path, monkeypatch, probe, workers, named
):
    local_name = "missing" if named else "step-0"
    alias_name = "missing" if named else "item"
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                # An inherited same-name result must not become the item result.
                {"id": local_name, "type": "probe", "value": "parent"},
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "max_concurrency": workers,
                    "step": {
                        **({"id": "missing"} if named else {}),
                        "type": "not-installed",
                        "continue_on_error": True,
                    },
                },
                {"id": "after", "type": "probe"},
            ],
        )
    )

    assert state.status == RunStatus.FAILED
    assert state.error == "Unknown step type: 'not-installed'"
    assert probe == {local_name: 1}
    assert set(state.step_results) == {local_name, "fan"}
    saved = RunState.load(state.run_id, tmp_path)
    assert saved.step_results == state.step_results
    assert saved.step_results["fan"]["output"]["results"] == [{}]
    events = [entry["event"] for entry in state.log_entries]
    assert "step_failed" in events
    assert "step_continue_on_error" not in events
    item_events = {}
    for entry in state.log_entries:
        if entry.get("step_id", "").startswith("fan:"):
            item_events.setdefault(entry["step_id"], []).append(entry["event"])
    assert item_events
    assert all(
        events == ["step_started", "step_failed"] for events in item_events.values()
    )

    class Reinstalled(StepBase):
        type_key = "not-installed"

        def execute(self, config, context):
            return StepResult(output={"value": context.item})

    monkeypatch.setitem(STEP_REGISTRY, "not-installed", Reinstalled())
    state = WorkflowEngine(tmp_path).resume(state.run_id)

    assert state.status == RunStatus.COMPLETED
    assert probe == {local_name: 1, "after": 1}
    assert state.step_results["fan"]["output"]["results"] == [
        {"value": 1}, {"value": 2}
    ]
    for index, value in enumerate([1, 2]):
        assert state.step_results[f"fan:{alias_name}:{index}"]["output"] == {
            "value": value
        }
    assert RunState.load(state.run_id, tmp_path).step_results == state.step_results


def test_diamond_and_depth_limit(tmp_path, probe):
    install(tmp_path, definition("leaf", [{"id": "work", "type": "probe"}]))
    for name in ("left", "right"):
        install(tmp_path, definition(name, [call("leaf")]))
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {**call("left"), "id": "left"},
                {**call("right"), "id": "right"},
            ],
        )
    )
    assert state.status == RunStatus.COMPLETED
    assert probe["work"] == 2
    for index in range(1, 18):
        install(
            tmp_path,
            definition(
                f"level-{index}",
                [call(f"level-{index + 1}")]
                if index < 17
                else [{"id": "too-deep", "type": "probe"}],
            ),
        )
    state = WorkflowEngine(tmp_path).execute(definition("parent", [call("level-1")]))
    assert state.status == RunStatus.FAILED
    assert "depth 16" in state.error
    assert probe["too-deep"] == 0


def test_output_validation_rejects_reserved_and_yaml_native_values(tmp_path, probe):
    from specify_cli.workflows.composition import require_json, validate_outputs

    circular = []
    circular.append(circular)
    for value in (circular, date(2026, 1, 1), {1: "key"}, float("nan")):
        with pytest.raises(ValueError, match="JSON-safe"):
            require_json(value)
    for outputs in (
        {"status": {"value": "oops"}},
        {"value": {"wrong": 1}},
        {"value": {"value": date(2026, 1, 1)}},
    ):
        assert validate_outputs(outputs)


def test_nested_gate_reporting_uses_active_occurrence(tmp_path, probe):
    from specify_cli.workflows._commands import _workflow_run_payload

    install(
        tmp_path,
        definition(
            "child",
            [{"id": "review", "type": "gate", "message": "Approve", "mode": "manual"}],
        ),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "route",
                    "type": "if",
                    "condition": True,
                    "then": [call()],
                }
            ],
        )
    )
    assert state.status == RunStatus.PAUSED
    payload = _workflow_run_payload(RunState.load(state.run_id, tmp_path))
    # Private scopes report the child-relative occurrence ID (own namespace).
    assert payload["current_step_id"] == "review"
    assert payload["gate"]["step_id"] == "review"
    assert payload["gate"]["scope_path"] == ["route", "call"]
    assert payload["workflow_scopes"][0]["status"] == "paused"


@pytest.mark.parametrize("failure, expected", [
    (KeyboardInterrupt, "paused"),
    (RuntimeError, "failed"),
])
def test_interrupted_bound_call_reports_run_outcome(tmp_path, monkeypatch, probe, failure, expected):
    from specify_cli.workflows._commands import _workflow_run_payload

    class Explode(StepBase):
        type_key = "explode"

        def execute(self, config, context):
            raise failure("boom")

    monkeypatch.setitem(STEP_REGISTRY, "explode", Explode())
    install(tmp_path, definition("first", [{"id": "done", "type": "probe"}]))
    install(tmp_path, definition("child", [{"id": "work", "type": "explode"}]))
    engine = WorkflowEngine(tmp_path)
    root = definition("parent", [call("first", id="prior"), call()])
    if failure is RuntimeError:
        with pytest.raises(RuntimeError, match="boom"):
            engine.execute(root, run_id="interrupted-call")
    else:
        assert engine.execute(root, run_id="interrupted-call").status == RunStatus.PAUSED

    saved = RunState.load("interrupted-call", tmp_path)
    payload = _workflow_run_payload(saved)
    assert payload["status"] == expected
    assert payload["workflow_scopes"] == [
        {"scope_path": ["prior"], "workflow_id": "first", "status": "completed"},
        {"scope_path": ["call"], "workflow_id": "child", "status": expected},
    ]


def test_rebind_failure_has_one_failed_caller_outcome(tmp_path, probe):
    from specify_cli.workflows._execution import scope_summaries

    install(
        tmp_path,
        definition(
            "child",
            [{"id": "wait", "type": "probe", "await": True}],
            inputs={"approve": {"type": "boolean"}},
        ),
    )
    root = definition(
        "parent",
        [call(input={"approve": "{{ inputs.approve }}"}, continue_on_error=True)],
        inputs={"approve": {"type": "string", "default": "false"}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    before = RunState.load(state.run_id, tmp_path).execution["sequence"]["nodes"][0]

    with pytest.raises(ValueError, match="expected a boolean"):
        WorkflowEngine(tmp_path).resume(state.run_id, {"approve": "invalid"})

    failed = RunState.load(state.run_id, tmp_path)
    node = failed.execution["sequence"]["nodes"][0]
    assert failed.status == RunStatus.FAILED
    # Invalid inputs fail the run, not the call: the re-entered call keeps its
    # binding and children and records no outcome of its own.
    assert node["phase"] == "children"
    assert not {"result", "outcome", "error"} & node.keys()
    assert node["binding"] == before["binding"]
    assert node["children"] == before["children"]
    assert scope_summaries(failed.execution, failed.status.value) == [
        {"scope_path": ["call"], "workflow_id": "child", "status": "failed"}
    ]
    assert WorkflowEngine(tmp_path).resume(
        state.run_id, {"approve": "true"}
    ).status == RunStatus.COMPLETED


@pytest.mark.parametrize("depth", [1, 2])
def test_verdict_input_remains_forbidden_through_calls_in_fan_out(
    tmp_path, probe, depth
):
    child = definition(
        "child",
        [
            {
                "id": "review",
                "type": "gate",
                "message": "Review",
                "verdict_input": "approve",
            }
        ],
        inputs={"approve": {"type": "string", "default": ""}},
    )
    install(tmp_path, child)
    if depth == 2:
        install(
            tmp_path,
            definition(
                "middle",
                [call("child", input={"approve": "{{ inputs.approve }}"})],
                inputs={"approve": {"type": "string", "default": ""}},
            ),
        )
    target = "middle" if depth == 2 else "child"
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": ["item"],
                    "step": {
                        "id": "call",
                        "type": "workflow",
                        "workflow": target,
                        "input": {"approve": ""},
                    },
                }
            ],
        )
    )

    assert state.status == RunStatus.FAILED
    assert "not supported inside fan-out templates" in state.error


def test_workflow_result_does_not_inherit_parent_defaults(tmp_path, probe):
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "work", "type": "probe"}],
            workflow={
                "id": "child",
                "name": "child",
                "integration": "child",
                "model": "child-model",
                "options": {"x": 2},
            },
        ),
    )
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [call()],
            workflow={
                "id": "parent",
                "name": "parent",
                "integration": "parent",
                "model": "parent-model",
                "options": {"x": 1},
            },
        )
    )

    call_result = state.step_results["call"]
    assert call_result["integration"] is None
    assert call_result["model"] is None
    assert call_result["options"] == {}
    assert call_result["input"] == {}


def test_child_context_does_not_inherit_item_or_fan_in(tmp_path, probe):
    install(
        tmp_path,
        definition(
            "child",
            [
                {"id": "item", "type": "probe", "value": "{{ item }}"},
                {"id": "fan-in", "type": "probe", "value": "{{ fan_in }}"},
            ],
            outputs={
                "item": {"value": "{{ steps.item.output.value }}"},
                "fan-in": {"value": "{{ steps.fan-in.output.value }}"},
            },
        ),
    )

    state = WorkflowEngine(tmp_path).execute(definition("parent", [call()]))

    assert state.status == RunStatus.COMPLETED
    assert state.step_results["call"]["output"] == {
        "workflow": "child",
        "status": "completed",
        "item": None,
        "fan-in": {},
    }


def test_rebind_keeps_unmapped_auto_input(tmp_path, probe):
    marker = tmp_path / ".specify" / "integration.json"
    marker.parent.mkdir()
    marker.write_text('{"version": 1, "default_integration": "first"}')
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "wait", "type": "probe", "await": True}],
            inputs={
                "approve": {"type": "boolean", "default": False},
                "integration": {"type": "string", "default": "auto"},
            },
        ),
    )
    root = definition(
        "parent",
        [call(input={"approve": "{{ inputs.approve }}"})],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    marker.write_text('{"version": 1, "default_integration": "second"}')

    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    binding = state.execution["sequence"]["nodes"][0]["binding"]
    assert binding["inputs"] == {"approve": True, "integration": "first"}


@pytest.mark.parametrize("change", ["disable", "uninstall"])
def test_bound_call_uses_snapshot_after_target_changes(tmp_path, probe, change):
    child = definition(
        "child",
        [{"id": "wait", "type": "probe", "await": True}],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    directory = install(tmp_path, child)
    root = definition(
        "parent",
        [call(input={"approve": "{{ inputs.approve }}"})],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    if change == "disable":
        from specify_cli.workflows.catalog import WorkflowRegistry

        WorkflowRegistry(tmp_path).add("child", {"version": "1.0.0", "enabled": False})
    else:
        directory.rename(tmp_path / "removed-child")

    resumed = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert resumed.status == RunStatus.COMPLETED


@pytest.mark.parametrize("change", ["disable", "uninstall"])
def test_unbound_call_checks_target_when_resume_reaches_it(tmp_path, probe, change):
    child = definition("child", [{"id": "work", "type": "probe"}])
    directory = install(tmp_path, child)
    root = definition(
        "parent",
        [
            {
                "id": "wait",
                "type": "gate",
                "message": "Wait",
                "verdict_input": "approve",
            },
            call(continue_on_error=True),
        ],
        inputs={"approve": {"type": "string", "default": ""}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    if change == "disable":
        from specify_cli.workflows.catalog import WorkflowRegistry

        WorkflowRegistry(tmp_path).add("child", {"version": "1.0.0", "enabled": False})
    else:
        directory.rename(tmp_path / "removed-child")

    resumed = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": "approve"})

    assert resumed.status == RunStatus.COMPLETED
    assert resumed.step_results["call"]["status"] == "failed"
    assert not probe


@pytest.mark.parametrize(
    "status,handled", [("failed", False), ("paused", False), ("failed", True)]
)
def test_unsuccessful_expansion_never_executes_children(
    tmp_path, monkeypatch, probe, status, handled
):
    class Expand(StepBase):
        type_key = "expand"

        def execute(self, config, context):
            return StepResult(
                StepStatus(status), next_steps=[{"id": "wrong", "type": "probe"}]
            )

    monkeypatch.setitem(STEP_REGISTRY, "expand", Expand())
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "expand",
                    "type": "expand",
                    "continue_on_error": handled,
                }
            ],
        )
    )
    assert state.status.value == ("completed" if handled else status)
    assert not probe
    RunState.load(state.run_id, tmp_path)


def test_custom_expansion_is_frozen_across_resume(tmp_path, monkeypatch, probe):
    class Expand(StepBase):
        type_key = "expand"

        def execute(self, config, context):
            probe["expand"] += 1
            return StepResult(
                StepStatus.COMPLETED,
                next_steps=[
                    {"id": f"prefix-{probe['expand']}", "type": "probe"},
                    {"id": "wait", "type": "probe", "await": True},
                ],
            )

    monkeypatch.setitem(STEP_REGISTRY, "expand", Expand())
    root = definition(
        "parent",
        [{"id": "expand", "type": "expand"}],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})
    assert state.status == RunStatus.COMPLETED
    assert probe == {"expand": 1, "prefix-1": 1, "wait": 2}


def test_native_yaml_definition_and_long_id_roundtrip(tmp_path, probe):
    target = "a" * 240
    child = definition(
        target, [{"id": "review", "type": "gate", "message": date(2026, 1, 1)}]
    )
    install(tmp_path, child)
    state = WorkflowEngine(tmp_path).execute(definition("parent", [call(target)]))
    assert state.status == RunStatus.PAUSED
    saved = RunState.load(state.run_id, tmp_path)
    binding = saved.execution["sequence"]["nodes"][0]["binding"]
    assert yaml.safe_load(binding["definition"])["steps"][0]["message"] == date(
        2026, 1, 1
    )
    assert WorkflowEngine(tmp_path).resume(state.run_id).status == RunStatus.PAUSED


@pytest.mark.parametrize("scope", ["root", "if", "workflow", "fan-out"])
def test_yaml_native_gate_template_survives_checkpoint_and_resume(tmp_path, monkeypatch, scope):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    gate = {"id": "wait", "type": "gate", "message": date(2026, 1, 1)}
    steps = [gate]
    if scope == "if":
        steps = [{"id": "branch", "type": "if", "condition": True, "then": steps}]
    elif scope == "workflow":
        install(tmp_path, definition("child", steps))
        steps = [call()]
    elif scope == "fan-out":
        steps = [{"id": "fan", "type": "fan-out", "items": [0, 1], "step": gate}]
    engine = WorkflowEngine(tmp_path)
    state = engine.execute(definition("parent", steps))
    assert state.status == RunStatus.PAUSED
    state = engine.resume(state.run_id)
    assert state.status == RunStatus.PAUSED
    from specify_cli.workflows._execution import walk_execution

    gates = [config for config, _, _, _ in walk_execution(state.execution["sequence"])
             if config.get("type") == "gate"]
    assert gates and all(config["message"] == date(2026, 1, 1) for config in gates)


@pytest.mark.parametrize("offset", [1, 2, 3])
def test_resume_rejects_offset_skipping_blocked_step_without_writes(tmp_path, probe, offset):
    steps = [{"id": "wait", "type": "probe", "await": True},
             {"id": "later", "type": "probe"}]
    engine = WorkflowEngine(tmp_path)
    state = engine.execute(definition("parent", steps))
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    data["execution"].update(offset=offset, sequence={
        "source": yaml.safe_dump(steps[offset:]),
        "nodes": [{"phase": "ready"} for _ in steps[offset:]],
    })
    path.write_text(json.dumps(data))
    before = {p.name: p.read_bytes() for p in state.runs_dir.iterdir()}
    with pytest.raises(ValueError, match="offset"):
        engine.resume(state.run_id)
    assert {p.name: p.read_bytes() for p in state.runs_dir.iterdir()} == before
    assert probe == {"wait": 1}


@pytest.mark.parametrize("scope", ["step", "if", "workflow", "fan-out"])
def test_lifecycle_start_is_tree_backed_and_replay_does_not_restart(tmp_path, probe, scope):
    from specify_cli.workflows._execution import walk_execution

    work = {"id": "work", "type": "probe"}
    steps = [work]
    if scope == "if":
        steps = [{"id": "branch", "type": "if", "condition": True, "then": steps}]
    elif scope == "workflow":
        install(tmp_path, definition("child", steps))
        steps = [call()]
    elif scope == "fan-out":
        steps = [{"id": "fan", "type": "fan-out", "items": [0, 1],
                  "max_concurrency": 2, "step": work}]
    steps.append({"id": "wait", "type": "probe", "await": True})
    engine = WorkflowEngine(tmp_path)
    announced = []

    def started(step_id, label):
        saved = RunState.load("lifecycle", tmp_path)
        matches = [node for _, node, _, name in walk_execution(saved.execution["sequence"])
                   if name == step_id]
        assert any(node.get("active") for node in matches)
        announced.append(step_id)

    engine.on_step_start = started
    state = engine.execute(definition("parent", steps), run_id="lifecycle")
    assert state.status == RunStatus.PAUSED
    assert all(not node.get("active") for _, node, _, _ in walk_execution(state.execution["sequence"]))
    before = probe.copy()
    announced.clear()
    engine.resume(state.run_id)
    assert announced == ["wait"]
    assert probe["work"] == before["work"]


@pytest.mark.parametrize("mutation", [
    lambda node: node.update(active=True),
    lambda node: node.update(active="yes"),
    lambda node: node.update(template="- invalid\n"),
    lambda node: node.update(fan_results={}),
    lambda node: node.update(fan_results={"a": 1}),
])
def test_lifecycle_rejects_invalid_completed_fan_out_without_writes(tmp_path, probe, mutation):
    engine = WorkflowEngine(tmp_path)
    state = engine.execute(definition("parent", [
        {"id": "fan", "type": "fan-out", "items": [0],
         "step": {"id": "work", "type": "probe"}},
        {"id": "wait", "type": "probe", "await": True},
    ]))
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    mutation(data["execution"]["sequence"]["nodes"][0])
    path.write_text(json.dumps(data))
    before = {p.name: p.read_bytes() for p in state.runs_dir.iterdir()}
    with pytest.raises(ValueError):
        engine.resume(state.run_id)
    assert {p.name: p.read_bytes() for p in state.runs_dir.iterdir()} == before


@pytest.mark.parametrize("field,value", [("fan_results", []), ("template", "{}\n")])
def test_non_fan_out_rejects_fan_out_fields(tmp_path, probe, field, value):
    state = WorkflowEngine(tmp_path).execute(definition("parent", [
        {"id": "work", "type": "probe"},
        {"id": "wait", "type": "probe", "await": True},
    ]))
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    data["execution"]["sequence"]["nodes"][0][field] = value
    path.write_text(json.dumps(data))
    before = {p.name: p.read_bytes() for p in state.runs_dir.iterdir()}

    with pytest.raises(ValueError, match="Invalid fan-out"):
        WorkflowEngine(tmp_path).resume(state.run_id)

    assert {p.name: p.read_bytes() for p in state.runs_dir.iterdir()} == before


@pytest.mark.parametrize("invalid", ["restart-completed", "override-phase", "finish-unfinished", "foreign-field"])
def test_lifecycle_rejects_invalid_transitions_before_mutation(tmp_path, probe, invalid):
    from copy import deepcopy
    from specify_cli.workflows._execution import Execution, Occurrence
    from specify_cli.workflows.base import StepContext

    config = {"id": "branch", "type": "if", "condition": True,
              "then": [{"id": "wait", "type": "probe", "await": True}]}
    engine = WorkflowEngine(tmp_path)
    state = engine.execute(definition("parent", [config]))
    node = state.execution["sequence"]["nodes"][0]
    occurrence = Occurrence(config, node, StepContext(), ("parent",), (0,), True, "branch")
    executor = Execution(engine, state, STEP_REGISTRY)
    if invalid == "restart-completed":
        occurrence = Occurrence(
            {"id": "done", "type": "probe"},
            {"phase": "done", "result": {"status": "completed", "output": {}}},
            StepContext(), ("parent",), (0,), True, "done",
        )
        operation, changes = "begin", {}
    elif invalid == "override-phase":
        operation, changes = "begin", {"phase": "done"}
    elif invalid == "foreign-field":
        operation, changes = "iterate", {"result": {"status": "completed", "output": {}}}
    else:
        operation, changes = "settle", {"outcome": "completed", "error": None}
    before_node = deepcopy(occurrence.node)
    before_files = {p.name: p.read_bytes() for p in state.runs_dir.iterdir()}
    with pytest.raises(ValueError):
        executor.transition(operation, occurrence, changes)
    assert occurrence.node == before_node
    assert {p.name: p.read_bytes() for p in state.runs_dir.iterdir()} == before_files


def test_execution_shares_workflow_fan_out_and_loop_sources(tmp_path, probe):
    child = definition(
        "child",
        [{"id": "work", "type": "probe"}],
    )
    install(tmp_path, child)
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                call(),
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "step": {"id": "item", "type": "probe"},
                },
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": True,
                    "max_iterations": 2,
                    "steps": [{"id": "body", "type": "probe"}],
                },
                {"id": "wait", "type": "probe", "await": True},
            ],
        )
    )

    tree = json.loads((state.runs_dir / "state.json").read_text())["execution"]
    call_node, fan_node, loop_node, _ = tree["sequence"]["nodes"]
    assert "source" not in call_node["children"][0]
    assert "source" not in fan_node["children"][0]
    assert "source" not in fan_node["children"][1]
    assert "source" in loop_node["children"][0]
    assert "source" not in loop_node["children"][1]
    assert yaml.safe_load(call_node["binding"]["definition"])["steps"] == [
        {"id": "work", "type": "probe"}
    ]
    RunState.load(state.run_id, tmp_path)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda tree: tree["sequence"]["nodes"][0]["children"][0].update(
            source="[]\n"
        ),
        lambda tree: tree["sequence"]["nodes"][1]["children"][0].update(
            source="[]\n"
        ),
        lambda tree: tree["sequence"]["nodes"][2]["children"][1].update(
            source="[]\n"
        ),
        lambda tree: tree["sequence"]["nodes"][0]["children"][0]["nodes"].append(
            {"phase": "ready"}
        ),
    ],
)
def test_shared_execution_sources_reject_local_copies(tmp_path, probe, mutation):
    child = definition("child", [{"id": "work", "type": "probe"}])
    install(tmp_path, child)
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                call(),
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1],
                    "step": {"id": "item", "type": "probe"},
                },
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": True,
                    "max_iterations": 2,
                    "steps": [{"id": "body", "type": "probe"}],
                },
                {"id": "wait", "type": "probe", "await": True},
            ],
        )
    )
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    mutation(data["execution"])
    path.write_text(json.dumps(data))
    before = path.read_bytes()

    with pytest.raises(ValueError, match="Invalid execution sequence"):
        WorkflowEngine(tmp_path).resume(state.run_id)

    assert path.read_bytes() == before


@pytest.mark.parametrize("items", [1, 4])
def test_fan_out_saves_once_per_item_transition(tmp_path, monkeypatch, probe, items):
    original = RunState.save
    saves = 0

    def save(self):
        nonlocal saves
        saves += 1
        original(self)

    monkeypatch.setattr(RunState, "save", save)
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": list(range(items)),
                    "max_concurrency": 1,
                    "step": {"id": "item", "type": "probe"},
                }
            ],
        )
    )

    assert state.status == RunStatus.COMPLETED
    # Each started occurrence (fan and items) is checkpointed before it runs,
    # and each item result once more before it is done.
    assert saves == 2 * items + 6


def test_fan_out_snapshot_size_does_not_scale_with_template_length(tmp_path, probe):
    def size(items, length):
        root = tmp_path / f"fan-{items}-{length}"
        state = WorkflowEngine(root).execute(
            definition(
                "parent",
                [
                    {
                        "id": "fan",
                        "type": "fan-out",
                        "items": list(range(items)),
                        "max_concurrency": 1,
                        "step": {
                            "id": "item",
                            "type": "probe",
                            "payload": "x" * length,
                        },
                    }
                ],
            )
        )
        return (state.runs_dir / "state.json").stat().st_size

    small_one, large_one = size(1, 128), size(1, 4096)
    small_many, large_many = size(4, 128), size(4, 4096)

    assert large_many - small_many <= large_one - small_one + 256


def test_loop_snapshot_size_does_not_scale_with_body_length(tmp_path, probe):
    def size(iterations, length):
        root = tmp_path / f"loop-{iterations}-{length}"
        state = WorkflowEngine(root).execute(
            definition(
                "parent",
                [
                    {
                        "id": "loop",
                        "type": "do-while",
                        "condition": True,
                        "max_iterations": iterations,
                        "steps": [
                            {
                                "id": "body",
                                "type": "probe",
                                "payload": "x" * length,
                            }
                        ],
                    }
                ],
            )
        )
        return (state.runs_dir / "state.json").stat().st_size

    small_one, large_one = size(1, 128), size(1, 4096)
    small_many, large_many = size(4, 128), size(4, 4096)

    assert large_many - small_many <= large_one - small_one + 256


def test_loop_transition_validation_does_not_rewalk_prior_iterations(
    tmp_path, monkeypatch, probe
):
    import specify_cli.workflows._execution as execution

    original = execution.yaml.safe_load
    counts = []

    def parse(source):
        counts[-1] += 1
        return original(source)

    monkeypatch.setattr(execution.yaml, "safe_load", parse)
    for iterations in (20, 40):
        counts.append(0)
        state = WorkflowEngine(tmp_path / str(iterations)).execute(
            definition("parent", [{
                "id": "loop", "type": "do-while", "condition": True,
                "max_iterations": iterations,
                "steps": [{"id": "body", "type": "probe"}],
            }])
        )
        assert state.status == RunStatus.COMPLETED
    assert counts[1] < counts[0] * 2.5


def test_tree_backed_resume_has_no_setup_checkpoint(tmp_path, monkeypatch, probe):
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [{"id": "wait", "type": "probe", "await": True}],
            inputs={"approve": {"type": "boolean", "default": False}},
        )
    )
    original = RunState.save
    saves = 0

    def save(self):
        nonlocal saves
        saves += 1
        original(self)

    monkeypatch.setattr(RunState, "save", save)
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    # Restarting ``wait`` persists it as active before it runs, then its result.
    assert saves == 4


def test_exact_depth_limit_is_allowed(tmp_path, probe):
    for index in range(1, 17):
        install(
            tmp_path,
            definition(
                f"level-{index}",
                [call(f"level-{index + 1}")]
                if index < 16
                else [{"id": "work", "type": "probe"}],
            ),
        )
    state = WorkflowEngine(tmp_path).execute(definition("parent", [call("level-1")]))
    assert state.status == RunStatus.COMPLETED
    assert probe["work"] == 1


@pytest.mark.parametrize(
    "template",
    [
        {"id": "mixed", "type": "mixed"},
        {
            "id": "mixed",
            "type": "if",
            "condition": True,
            "then": [{"id": "inner", "type": "mixed"}],
        },
        call("child", id="mixed", input={"n": "{{ item }}"}),
    ],
    ids=["step", "if-container", "workflow-call"],
)
def test_aborted_fanout_sibling_is_never_restarted(tmp_path, monkeypatch, template):
    barrier = threading.Barrier(2, timeout=5)
    counts = Counter()

    class Mixed(StepBase):
        type_key = "mixed"

        def execute(self, config, context):
            item = context.item if context.item is not None else context.inputs["n"]
            counts[item] += 1
            if not context.is_resume:
                barrier.wait()
            if item == 0:
                return StepResult(
                    StepStatus.COMPLETED if context.is_resume else StepStatus.PAUSED
                )
            return StepResult(StepStatus.FAILED, output={"aborted": True})

    monkeypatch.setitem(STEP_REGISTRY, "mixed", Mixed())
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "inner", "type": "mixed"}],
            inputs={"n": {"type": "number"}},
        ),
    )
    root = definition(
        "parent",
        [
            {
                "id": "spread",
                "type": "fan-out",
                "items": [0, 1],
                "max_concurrency": 2,
                "step": template,
            }
        ],
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    state = WorkflowEngine(tmp_path).resume(state.run_id)
    assert state.status == RunStatus.ABORTED
    assert counts == {0: 2, 1: 1}
    # Replaying the aborted item keeps the result it published when it ran.
    published = state.step_results["spread:mixed:1"]["output"]
    assert published
    for results in (
        state.step_results["spread"]["output"]["results"],
        RunState.load(state.run_id, tmp_path).step_results["spread"]["output"][
            "results"
        ],
    ):
        assert results[1] == published


FAN_OUT_ITEM_TEMPLATES = [
    {"id": "tmpl", "type": "snap"},
    {
        "id": "tmpl",
        "type": "if",
        "condition": True,
        "then": [{"id": "inner", "type": "snap"}],
    },
    call("child", id="tmpl", input={"n": "{{ item }}"}),
]
FAN_OUT_ITEM_TEMPLATE_IDS = ["step", "if-container", "workflow-call"]


@pytest.mark.parametrize("max_concurrency", [1, 3], ids=["sequential", "parallel"])
@pytest.mark.parametrize(
    "template", FAN_OUT_ITEM_TEMPLATES, ids=FAN_OUT_ITEM_TEMPLATE_IDS
)
def test_resumed_fan_out_item_sees_its_uninterrupted_context(
    tmp_path, monkeypatch, probe, template, max_concurrency
):
    """Exact resume must re-run a fan-out item in the context it has in a run
    that never paused. Replay reconstructs item contexts from the checkpoint,
    so any difference (for example, a result the live run adds only after its
    items) is a live/replay gap."""
    from dataclasses import asdict

    pause = {"enabled": False}
    seen = {}

    class Snap(StepBase):
        type_key = "snap"

        def execute(self, config, context):
            item = context.item if context.item is not None else context.inputs["n"]
            view = asdict(context)
            del view["run_id"], view["is_resume"]
            phase = "resume" if context.is_resume else pause["enabled"]
            seen.setdefault(phase, {})[item] = view
            if item == 1 and pause["enabled"] and not context.is_resume:
                return StepResult(StepStatus.PAUSED, output={"item": item})
            return StepResult(output={"item": item})

    monkeypatch.setitem(STEP_REGISTRY, "snap", Snap())
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "inner", "type": "snap"}],
            inputs={"n": {"type": "number"}},
        ),
    )
    root = definition(
        "parent",
        [
            {"id": "setup", "type": "probe", "value": "ready"},
            {
                "id": "fan",
                "type": "fan-out",
                "items": [0, 1, 2],
                "max_concurrency": max_concurrency,
                "step": template,
            },
        ],
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.COMPLETED
    pause["enabled"] = True
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED

    state = WorkflowEngine(tmp_path).resume(state.run_id)

    assert state.status == RunStatus.COMPLETED
    resumed = seen["resume"]
    assert 1 in resumed
    for item, view in resumed.items():
        assert view == seen[False][item], f"item {item} context differs on resume"


def test_resumed_fan_out_items_do_not_see_partial_results(tmp_path, monkeypatch):
    seen = []

    class Look(StepBase):
        type_key = "look"

        def execute(self, config, context):
            seen.append("results" in context.steps["fan"]["output"])
            if context.item == 1 and not context.is_resume:
                return StepResult(StepStatus.PAUSED, output={"item": 1})
            return StepResult(output={"item": context.item})

    monkeypatch.setitem(STEP_REGISTRY, "look", Look())
    root = definition(
        "parent",
        [
            {
                "id": "fan",
                "type": "fan-out",
                "items": [0, 1, 2],
                "step": {"id": "look", "type": "look"},
            }
        ],
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    # The paused fan-out still reports its partial results.
    assert state.step_results["fan"]["output"]["results"] == [{"item": 0}, {"item": 1}]

    state = WorkflowEngine(tmp_path).resume(state.run_id)

    assert state.status == RunStatus.COMPLETED
    # Items never see the engine-added results: not live, not after resume.
    assert seen == [False, False, False, False]
    assert state.step_results["fan"]["output"]["results"] == [
        {"item": 0},
        {"item": 1},
        {"item": 2},
    ]


NAN_SNAPSHOT = """
schema_version: "1.0"
workflow:
  id: nan-snapshot
  name: NaN Snapshot
  version: "1.0.0"
inputs:
  approve:
    type: boolean
    default: false
steps:
  - id: fan
    type: fan-out
    items: [1, 2]
    max_concurrency: .nan
    step:
      type: probe
      value: "{{ item }}"
  - id: wait
    type: probe
    await: true
"""


def test_resume_accepts_native_yaml_nan_in_snapshot(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        WorkflowDefinition.from_string(NAN_SNAPSHOT), run_id="nan"
    )
    assert state.status == RunStatus.PAUSED
    copy = tmp_path / ".specify/workflows/runs/nan/workflow.yml"
    data = yaml.safe_load(copy.read_text(encoding="utf-8"))
    # Key order is not part of the snapshot identity.
    data["steps"][0] = dict(reversed(list(data["steps"][0].items())))
    copy.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    state = WorkflowEngine(tmp_path).resume("nan", {"approve": True})

    assert state.status == RunStatus.COMPLETED, state.error
    assert state.step_results["fan"]["output"]["results"] == [
        {"value": 1}, {"value": 2}
    ]
    assert probe == {"item": 2, "wait": 2}


def test_resume_rejects_changed_workflow_snapshot(tmp_path, probe):
    state = WorkflowEngine(tmp_path).execute(
        WorkflowDefinition.from_string(NAN_SNAPSHOT), run_id="changed"
    )
    assert state.status == RunStatus.PAUSED
    copy = tmp_path / ".specify/workflows/runs/changed/workflow.yml"
    data = yaml.safe_load(copy.read_text(encoding="utf-8"))
    data["steps"][0]["items"] = [1, 2, 3]
    copy.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="root sequence differs"):
        WorkflowEngine(tmp_path).resume("changed", {"approve": True})

def test_paused_fan_out_item_reports_qualified_current_step_id(tmp_path, probe):
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, _label: callbacks.append(step_id)

    state = engine.execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1],
                    "step": {"id": "item", "type": "probe", "status": "paused"},
                }
            ],
        )
    )

    assert state.status == RunStatus.PAUSED
    assert state.current_step_id == "fan:item:0"
    assert "fan:item:0" in state.step_results
    assert RunState.load(state.run_id, tmp_path).current_step_id == "fan:item:0"
    assert callbacks[-1] == "fan:item:0"


def test_paused_later_loop_iteration_reports_qualified_current_step_id(
    tmp_path, monkeypatch
):
    calls = Counter()

    class PauseSecond(StepBase):
        type_key = "pause-second"

        def execute(self, config, context):
            calls[config["id"]] += 1
            if calls[config["id"]] == 2:
                return StepResult(StepStatus.PAUSED)
            return StepResult(output={})

    monkeypatch.setitem(STEP_REGISTRY, "pause-second", PauseSecond())
    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": True,
                    "max_iterations": 3,
                    "steps": [{"id": "body", "type": "pause-second"}],
                }
            ],
        )
    )

    assert state.status == RunStatus.PAUSED
    assert state.current_step_id == "loop:body:1"
    assert "loop:body:1" in state.step_results
    assert RunState.load(state.run_id, tmp_path).current_step_id == "loop:body:1"


@pytest.mark.parametrize(
    ("steps", "expected"),
    [
        (
            [{"id": "first", "type": "probe"}, {"id": "observe", "type": "observe"}],
            [("observe", 1)],
        ),
        (
            [
                {"id": "first", "type": "probe"},
                {
                    "id": "loop",
                    "type": "do-while",
                    "condition": True,
                    "max_iterations": 2,
                    "steps": [{"id": "observe", "type": "observe"}],
                },
            ],
            [("observe", 1), ("loop:observe:1", 1)],
        ),
        (
            [
                {"id": "first", "type": "probe"},
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1, 2],
                    "step": {"id": "observe", "type": "observe"},
                },
            ],
            [("fan:observe:0", 1), ("fan:observe:1", 1)],
        ),
    ],
    ids=["root", "later-loop-iteration", "fan-out-item"],
)
def test_running_step_is_persisted_before_it_executes(
    tmp_path, monkeypatch, probe, steps, expected
):
    seen = []

    class Observe(StepBase):
        type_key = "observe"

        def execute(self, config, context):
            persisted = RunState.load(context.run_id, tmp_path)
            seen.append((persisted.current_step_id, persisted.current_step_index))
            return StepResult(output={})

    monkeypatch.setitem(STEP_REGISTRY, "observe", Observe())

    state = WorkflowEngine(tmp_path).execute(definition("parent", steps))

    assert state.status == RunStatus.COMPLETED
    assert seen == expected


def _record_persisted_step_on_start(engine, tmp_path, seen):
    """Record the persisted ``current_step_id`` whenever a step start is announced."""

    def on_step_start(step_id, label):
        (path,) = (tmp_path / ".specify/workflows/runs").glob("*/state.json")
        persisted = json.loads(path.read_text(encoding="utf-8"))["current_step_id"]
        seen.append((step_id, label, persisted))

    engine.on_step_start = on_step_start
    return engine


def test_workflow_call_is_persisted_before_it_starts(tmp_path, probe):
    install(tmp_path, definition("grandchild", [{"id": "leaf", "type": "probe"}]))
    install(
        tmp_path,
        definition(
            "child",
            [
                {"id": "prepare", "type": "probe"},
                {"id": "nested", "type": "workflow", "workflow": "grandchild"},
            ],
        ),
    )
    seen = []
    engine = _record_persisted_step_on_start(WorkflowEngine(tmp_path), tmp_path, seen)

    state = engine.execute(definition("parent", [{"id": "first", "type": "probe"}, call()]))

    assert state.status == RunStatus.COMPLETED
    # Like every other step, a call (top-level and nested inside a called
    # workflow, by its workflow-relative ID) is checkpointed as the active step
    # before its start is logged and announced.
    assert seen == [
        ("first", "probe", "first"),
        ("call", "workflow", "call"),
        ("prepare", "probe", "prepare"),
        ("nested", "workflow", "nested"),
        ("leaf", "probe", "leaf"),
    ]


def test_resumed_bound_workflow_call_is_persisted_before_it_starts(tmp_path, probe):
    install(
        tmp_path,
        definition(
            "child",
            [{"id": "wait", "type": "probe", "await": True}],
            inputs={"approve": {"type": "boolean", "default": False}},
        ),
    )
    root = definition(
        "parent",
        [call(input={"approve": "{{ inputs.approve }}"})],
        inputs={"approve": {"type": "boolean", "default": False}},
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    assert RunState.load(state.run_id, tmp_path).current_step_id == "wait"
    seen = []
    engine = _record_persisted_step_on_start(WorkflowEngine(tmp_path), tmp_path, seen)

    state = engine.resume(state.run_id, {"approve": True})

    assert state.status == RunStatus.COMPLETED
    # The already-bound call skips binding, which previously held the only
    # pre-child checkpoint; it must still persist itself before re-announcing.
    assert seen == [("call", "workflow", "call"), ("wait", "probe", "wait")]


def test_workflow_call_start_checkpoint_failure_logs_no_start(tmp_path, monkeypatch, probe):
    from specify_cli.workflows._execution import CheckpointError

    install(tmp_path, definition("child", [{"id": "inner", "type": "probe"}]))
    original = RunState._atomic_write_json

    def write(path, data):
        if path.name == "state.json" and data.get("current_step_id") == "call":
            raise OSError("checkpoint failure")
        original(path, data)

    monkeypatch.setattr(RunState, "_atomic_write_json", staticmethod(write))
    callbacks = []
    engine = WorkflowEngine(tmp_path)
    engine.on_step_start = lambda step_id, label: callbacks.append(step_id)

    with pytest.raises(CheckpointError, match="checkpoint failure"):
        engine.execute(
            definition("parent", [{"id": "first", "type": "probe"}, call()]),
            run_id="fault",
        )

    runs = tmp_path / ".specify/workflows/runs/fault"
    started = [
        entry["step_id"]
        for entry in map(json.loads, (runs / "log.jsonl").read_text().splitlines())
        if entry["event"] == "step_started"
    ]
    disk = json.loads((runs / "state.json").read_text())
    node = disk["execution"]["sequence"]["nodes"][1]
    # The failed start checkpoint is not followed by a start event, a callback,
    # or target binding.
    assert started == ["first"]
    assert callbacks == ["first"]
    assert disk["current_step_id"] == "first"
    assert node["phase"] == "ready"
    assert "binding" not in node
    assert probe["inner"] == 0


def test_failed_fan_out_item_exception_reports_qualified_current_step_id(
    tmp_path, monkeypatch
):
    class Boom(StepBase):
        type_key = "boom"

        def execute(self, config, context):
            raise RuntimeError("boom")

    monkeypatch.setitem(STEP_REGISTRY, "boom", Boom())
    engine = WorkflowEngine(tmp_path)
    with pytest.raises(RuntimeError, match="boom"):
        engine.execute(
            definition(
                "parent",
                [
                    {
                        "id": "fan",
                        "type": "fan-out",
                        "items": [1],
                        "step": {"id": "blast", "type": "boom"},
                    }
                ],
            ),
            run_id="boom",
        )

    loaded = RunState.load("boom", tmp_path)
    assert loaded.status == RunStatus.FAILED
    assert loaded.current_step_id == "fan:blast:0"


def test_paused_fan_out_gate_payload_reports_qualified_step_id(tmp_path):
    from specify_cli.workflows._commands import _workflow_run_payload

    state = WorkflowEngine(tmp_path).execute(
        definition(
            "parent",
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [1],
                    "step": {"id": "review", "type": "gate", "message": "Approve"},
                }
            ],
        )
    )

    assert state.status == RunStatus.PAUSED
    payload = _workflow_run_payload(RunState.load(state.run_id, tmp_path))
    assert payload["current_step_id"] == "fan:review:0"
    assert payload["gate"]["step_id"] == "fan:review:0"
    assert payload["gate"]["message"] == "Approve"


def test_gate_message_keeps_typed_template_result(tmp_path):
    from specify_cli.workflows._commands import _workflow_run_payload

    workflow = definition(
        "parent",
        [{"id": "gate", "type": "gate", "message": "{{ inputs.notice }}"}],
        inputs={"notice": {"type": "number"}},
    )
    assert validate_workflow(workflow) == []

    state = WorkflowEngine(tmp_path).execute(workflow, {"notice": 42})

    assert state.status == RunStatus.PAUSED
    loaded = RunState.load(state.run_id, tmp_path)
    message = loaded.step_results["gate"]["output"]["message"]
    assert message == 42
    assert isinstance(message, int)
    assert _workflow_run_payload(loaded)["gate"]["message"] == "42"


def test_gate_message_stores_non_json_literal_as_text(tmp_path):
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [{"id": "gate", "type": "gate", "message": date(2026, 1, 1)}])
    )

    assert state.status == RunStatus.PAUSED
    loaded = RunState.load(state.run_id, tmp_path)
    assert loaded.step_results["gate"]["output"]["message"] == "2026-01-01"


def test_fan_out_worker_exception_stops_dispatch_before_earlier_items_finish(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    from specify_cli.workflows import _execution

    halted_seen = threading.Event()

    class ObservedEvent(threading.Event):
        def set(self):
            super().set()
            halted_seen.set()

    monkeypatch.setattr(_execution, "threading", SimpleNamespace(Event=ObservedEvent))
    started = set()
    lock = threading.Lock()

    class Blow(StepBase):
        type_key = "blow"

        def execute(self, config, context):
            with lock:
                started.add(context.item)
            if context.item == 2:
                raise RuntimeError("boom")
            if context.item in {0, 1}:
                # Earlier items finish only after the failure halts dispatch.
                halted_seen.wait(2)
            return StepResult(output={"value": context.item})

    monkeypatch.setitem(STEP_REGISTRY, "blow", Blow())
    with pytest.raises(RuntimeError, match="boom"):
        WorkflowEngine(tmp_path).execute(
            definition(
                "parent",
                [
                    {
                        "id": "fan",
                        "type": "fan-out",
                        "items": [0, 1, 2, 3, 4, 5],
                        "max_concurrency": 3,
                        "step": {"id": "item", "type": "blow"},
                    }
                ],
            )
        )

    assert started == {0, 1, 2}
