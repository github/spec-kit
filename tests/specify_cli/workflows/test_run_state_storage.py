from __future__ import annotations

import json
import os

import pytest


pytestmark = pytest.mark.skipif(
    not hasattr(os, "symlink"), reason="symlinks are unavailable"
)


def _run_dir(project_dir, run_id="run-1"):
    path = project_dir / ".specify" / "workflows" / "runs" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state(project_dir, run_id="run-1"):
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import RunState

    state = RunState(run_id=run_id, workflow_id="workflow", project_root=project_dir)
    state.status = RunStatus.PAUSED
    return state


def test_workflow_operations_use_portable_storage_fallback(
    project_dir, monkeypatch
):
    from specify_cli.workflows.base import RunStatus
    from specify_cli.workflows.engine import (
        RunState,
        WorkflowDefinition,
        WorkflowEngine,
    )

    monkeypatch.setattr(
        RunState, "_supports_descriptor_access", staticmethod(lambda: False)
    )
    definition = WorkflowDefinition.from_string(
        """
schema_version: "1.0"
workflow:
  id: portable-storage
  name: Portable Storage
inputs:
  verdict:
    type: string
    default: ""
steps:
  - id: review
    type: gate
    message: Review
    verdict_input: verdict
"""
    )
    engine = WorkflowEngine(project_dir)

    state = engine.execute(definition, run_id="portable")

    assert state.status == RunStatus.PAUSED
    resumed = engine.resume("portable", {"verdict": "approve"})
    assert resumed.status == RunStatus.COMPLETED
    assert engine.list_runs()[0]["run_id"] == "portable"


def test_portable_storage_fallback_rechecks_artifact_symlinks(
    project_dir, tmp_path, monkeypatch
):
    from specify_cli.workflows.engine import RunState

    monkeypatch.setattr(
        RunState, "_supports_descriptor_access", staticmethod(lambda: False)
    )
    state = _state(project_dir)
    state.save()
    artifact = RunState._run_artifact(project_dir, "run-1", "state.json")
    external = tmp_path / "state.json"
    external.write_text("external state", encoding="utf-8")

    with RunState._open_run_directory(project_dir, "run-1") as run_fd:
        artifact.unlink()
        artifact.symlink_to(external)
        with pytest.raises(ValueError, match="symlinked workflow run artifact"):
            with RunState._open_artifact(
                artifact, "r", dir_fd=run_fd, encoding="utf-8"
            ):
                pass

    assert external.read_text(encoding="utf-8") == "external state"


def test_load_rejects_symlinked_run_directory(project_dir, tmp_path):
    from specify_cli.workflows.engine import RunState

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "state.json").write_text(
        json.dumps({"run_id": "run-1", "workflow_id": "workflow", "status": "paused"}),
        encoding="utf-8",
    )
    runs = project_dir / ".specify" / "workflows" / "runs"
    runs.mkdir(parents=True)
    (runs / "run-1").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlinked workflow run path"):
        RunState.load("run-1", project_dir)


def test_load_keeps_open_run_directory_when_path_is_replaced(
    project_dir, tmp_path, monkeypatch
):
    from specify_cli.workflows.engine import RunState

    state = _state(project_dir)
    state.save()
    run_dir = project_dir / ".specify" / "workflows" / "runs" / "run-1"
    detached_dir = tmp_path / "detached-run"
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_state = outside / "state.json"
    outside_state.write_text(
        json.dumps({
            "run_id": "run-1",
            "workflow_id": "external",
            "status": "paused",
        }),
        encoding="utf-8",
    )
    original_open = RunState._open_artifact
    swapped = False

    def _replace_run_directory(path, mode, *, dir_fd, **kwargs):
        nonlocal swapped
        if path.name == "state.json" and not swapped:
            swapped = True
            os.rename(run_dir, detached_dir)
            run_dir.symlink_to(outside, target_is_directory=True)
        return original_open(path, mode, dir_fd=dir_fd, **kwargs)

    monkeypatch.setattr(
        RunState, "_open_artifact", staticmethod(_replace_run_directory)
    )

    loaded = RunState.load("run-1", project_dir)

    assert loaded.workflow_id == "workflow"
    assert json.loads(outside_state.read_text(encoding="utf-8"))["workflow_id"] == "external"


def test_save_keeps_open_run_directory_when_path_is_replaced(
    project_dir, tmp_path, monkeypatch
):
    from specify_cli.workflows.engine import RunState

    state = _state(project_dir)
    state.save()
    run_dir = project_dir / ".specify" / "workflows" / "runs" / "run-1"
    detached_dir = tmp_path / "detached-run"
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_state = outside / "state.json"
    outside_state.write_text("external state", encoding="utf-8")
    original_write = RunState._atomic_write_json
    swapped = False

    def _replace_run_directory(path, data, *, dir_fd):
        nonlocal swapped
        if path.name == "state.json" and not swapped:
            swapped = True
            os.rename(run_dir, detached_dir)
            run_dir.symlink_to(outside, target_is_directory=True)
        return original_write(path, data, dir_fd=dir_fd)

    monkeypatch.setattr(
        RunState, "_atomic_write_json", staticmethod(_replace_run_directory)
    )

    state.save()

    assert outside_state.read_text(encoding="utf-8") == "external state"
    assert json.loads((detached_dir / "state.json").read_text(encoding="utf-8"))[
        "run_id"
    ] == "run-1"


@pytest.mark.parametrize("artifact", ["state.json", "inputs.json"])
def test_run_state_rejects_symlinked_persisted_artifacts(
    project_dir, tmp_path, artifact
):
    state = _state(project_dir)
    run_dir = _run_dir(project_dir)
    target = tmp_path / artifact
    target.write_text("{}", encoding="utf-8")
    (run_dir / artifact).symlink_to(target)

    if artifact == "state.json":
        with pytest.raises(ValueError, match="symlinked workflow run artifact"):
            type(state).load("run-1", project_dir)
    else:
        state_data = {
            "run_id": "run-1",
            "workflow_id": "workflow",
            "status": "paused",
        }
        (run_dir / "state.json").write_text(json.dumps(state_data), encoding="utf-8")
        with pytest.raises(ValueError, match="symlinked workflow run artifact"):
            type(state).load("run-1", project_dir)


@pytest.mark.parametrize("artifact, operation", [
    ("state.json", "save"),
    ("inputs.json", "save"),
    ("log.jsonl", "log"),
])
def test_run_state_rejects_symlinked_artifact_writes(
    project_dir, tmp_path, artifact, operation
):
    from specify_cli.workflows._execution import CheckpointError

    state = _state(project_dir)
    run_dir = _run_dir(project_dir)
    target = tmp_path / artifact
    target.write_text("", encoding="utf-8")
    (run_dir / artifact).symlink_to(target)

    expected = CheckpointError if operation == "save" else ValueError
    with pytest.raises(expected, match="symlinked workflow run artifact"):
        if operation == "save":
            state.save()
        else:
            state.append_log({"event": "test"})


def test_workflow_snapshot_artifact_is_checked(project_dir, tmp_path):
    from specify_cli.workflows.engine import RunState

    run_dir = _run_dir(project_dir)
    target = tmp_path / "workflow.yml"
    target.write_text("workflow: {}", encoding="utf-8")
    (run_dir / "workflow.yml").symlink_to(target)

    with pytest.raises(ValueError, match="symlinked workflow run artifact"):
        RunState._run_artifact(project_dir, "run-1", "workflow.yml")


def test_execute_rejects_symlinked_workflow_snapshot(project_dir, tmp_path):
    from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine

    run_dir = _run_dir(project_dir)
    target = tmp_path / "workflow.yml"
    target.write_text("external workflow", encoding="utf-8")
    (run_dir / "workflow.yml").symlink_to(target)

    definition = WorkflowDefinition({
        "workflow": {"id": "workflow", "name": "Workflow"},
        "steps": [],
    })
    with pytest.raises(ValueError, match="symlinked workflow run artifact"):
        WorkflowEngine(project_dir).execute(definition, run_id="run-1")

    assert target.read_text(encoding="utf-8") == "external workflow"


def test_resume_rejects_symlinked_workflow_snapshot(project_dir, tmp_path):
    from specify_cli.workflows.engine import WorkflowEngine

    state = _state(project_dir)
    state.save()
    run_dir = _run_dir(project_dir)
    target = tmp_path / "workflow.yml"
    target.write_text(
        "workflow: {id: workflow, name: Workflow}\n"
        "steps:\n  - {id: review, type: gate, message: Review}\n",
        encoding="utf-8",
    )
    (run_dir / "workflow.yml").symlink_to(target)

    with pytest.raises(ValueError, match="symlinked workflow run artifact"):
        WorkflowEngine(project_dir).resume("run-1")

    assert target.read_text(encoding="utf-8").startswith("workflow:")
