"""Behavioral contracts for scoped calls and durable execution occurrences."""

from collections import Counter
from datetime import date
import json
import threading

import pytest
import yaml

from specify_cli.workflows import STEP_REGISTRY
from specify_cli.workflows.base import RunStatus, StepBase, StepResult, StepStatus
from specify_cli.workflows.engine import RunState, WorkflowDefinition, WorkflowEngine


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
    "mapping", [{"unknown": "x"}, {"value": []}, {"value": date(2026, 1, 1)}, [1]]
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


def test_output_failure_retries_only_finalization(tmp_path, monkeypatch, probe):
    import specify_cli.workflows._execution as execution

    install(tmp_path, definition("child", [{"id": "work", "type": "probe"}]))
    original = execution.evaluate_outputs
    monkeypatch.setattr(
        execution,
        "evaluate_outputs",
        lambda *_: (_ for _ in ()).throw(ValueError("bad output")),
    )
    state = WorkflowEngine(tmp_path).execute(definition("parent", [call()]))
    assert state.status == RunStatus.FAILED
    state = WorkflowEngine(tmp_path).resume(state.run_id)
    assert state.status == RunStatus.FAILED
    monkeypatch.setattr(execution, "evaluate_outputs", original)
    state = WorkflowEngine(tmp_path).resume(state.run_id)
    assert state.status == RunStatus.COMPLETED
    assert probe["work"] == 1


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


@pytest.mark.parametrize(
    "mutation",
    [
        lambda tree: tree.update(version=99),
        lambda tree: tree["sequence"].update(nodes=[]),
        lambda tree: tree["sequence"]["nodes"][0].update(phase="nonsense"),
    ],
)
def test_bad_checkpoint_rejected_without_writes(tmp_path, probe, mutation):
    state = WorkflowEngine(tmp_path).execute(
        definition("parent", [{"id": "wait", "type": "probe", "await": True}])
    )
    path = state.runs_dir / "state.json"
    data = json.loads(path.read_text())
    mutation(data["execution"])
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    with pytest.raises(ValueError):
        WorkflowEngine(tmp_path).resume(state.run_id)
    assert path.read_bytes() == before


@pytest.mark.parametrize("failure_after_replace", [False, True])
def test_checkpoint_failure_never_overwrites_committed_progress(
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
    state = WorkflowEngine(tmp_path).resume("fault")
    assert state.status == RunStatus.COMPLETED
    assert probe["work"] == (1 if failure_after_replace else 2)


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
    assert payload["gate"]["step_id"] == "review"
    assert payload["gate"]["scope_path"] == ["route", "call"]
    assert payload["workflow_scopes"][0]["status"] == "paused"


def test_rebind_failure_has_one_failed_caller_outcome(tmp_path, probe):
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
    state = WorkflowEngine(tmp_path).resume(state.run_id, {"approve": "invalid"})
    assert state.status == RunStatus.COMPLETED
    node = RunState.load(state.run_id, tmp_path).execution["sequence"]["nodes"][0]
    assert node["phase"] == "done"
    assert node["result"]["output"]["status"] == "failed"
    from specify_cli.workflows._execution import active_step

    assert active_step(state.execution) is None


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


def test_aborted_fanout_sibling_is_never_restarted(tmp_path, monkeypatch):
    barrier = threading.Barrier(2, timeout=5)
    counts = Counter()

    class Mixed(StepBase):
        type_key = "mixed"

        def execute(self, config, context):
            counts[context.item] += 1
            if not context.is_resume:
                barrier.wait()
            if context.item == 0:
                return StepResult(
                    StepStatus.COMPLETED if context.is_resume else StepStatus.PAUSED
                )
            return StepResult(StepStatus.FAILED, output={"aborted": True})

    monkeypatch.setitem(STEP_REGISTRY, "mixed", Mixed())
    root = definition(
        "parent",
        [
            {
                "id": "spread",
                "type": "fan-out",
                "items": [0, 1],
                "max_concurrency": 2,
                "step": {"id": "mixed", "type": "mixed"},
            }
        ],
    )
    state = WorkflowEngine(tmp_path).execute(root)
    assert state.status == RunStatus.PAUSED
    state = WorkflowEngine(tmp_path).resume(state.run_id)
    assert state.status == RunStatus.ABORTED
    assert counts == {0: 2, 1: 1}
