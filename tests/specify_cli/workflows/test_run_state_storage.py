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
