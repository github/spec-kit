from __future__ import annotations

import json
import os
import stat

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


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits are required")
@pytest.mark.parametrize("portable", [False, True])
def test_state_and_input_writes_are_owner_only(project_dir, monkeypatch, portable):
    from specify_cli.workflows.engine import RunState

    if portable:
        monkeypatch.setattr(
            RunState, "_supports_descriptor_access", staticmethod(lambda: False)
        )
    original_dump = json.dump
    temporary_modes = []

    def check_temporary_permissions(data, file, **kwargs):
        mode = stat.S_IMODE(os.fstat(file.fileno()).st_mode)
        temporary_modes.append(mode)
        assert mode == 0o600
        return original_dump(data, file, **kwargs)

    monkeypatch.setattr(json, "dump", check_temporary_permissions)
    state = _state(project_dir)
    state.inputs = {"value": "private"}
    previous_umask = os.umask(0)
    try:
        state.save()
        for name in ("state.json", "inputs.json"):
            artifact = state.runs_dir / name
            assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
            artifact.chmod(0o666)

        state.save()
        for name in ("state.json", "inputs.json"):
            artifact = state.runs_dir / name
            assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
            assert json.loads(artifact.read_text(encoding="utf-8"))["inputs"] == state.inputs
        assert temporary_modes == [0o600] * 4
    finally:
        os.umask(previous_umask)


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


@pytest.mark.parametrize("portable", [False, True])
def test_load_keeps_open_run_directory_when_path_is_replaced(
    project_dir, tmp_path, monkeypatch, portable
):
    from specify_cli.workflows.engine import RunState

    if portable:
        monkeypatch.setattr(
            RunState, "_supports_descriptor_access", staticmethod(lambda: False)
        )
    descriptor_access = RunState._supports_descriptor_access()
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

    if descriptor_access:
        loaded = RunState.load("run-1", project_dir)
        assert loaded.workflow_id == "workflow"
    else:
        with pytest.raises(ValueError, match="symlinked workflow run path"):
            RunState.load("run-1", project_dir)

    assert swapped
    assert json.loads(outside_state.read_text(encoding="utf-8"))["workflow_id"] == "external"


@pytest.mark.parametrize("portable", [False, True])
def test_save_keeps_open_run_directory_when_path_is_replaced(
    project_dir, tmp_path, monkeypatch, portable
):
    from specify_cli.workflows._execution import CheckpointError
    from specify_cli.workflows.engine import RunState

    if portable:
        monkeypatch.setattr(
            RunState, "_supports_descriptor_access", staticmethod(lambda: False)
        )
    descriptor_access = RunState._supports_descriptor_access()
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

    state.inputs = {"changed": True}
    if descriptor_access:
        state.save()
    else:
        with pytest.raises(CheckpointError, match="symlinked workflow run path"):
            state.save()

    assert swapped
    assert outside_state.read_text(encoding="utf-8") == "external state"
    assert not (outside / "inputs.json").exists()
    assert json.loads((detached_dir / "state.json").read_text(encoding="utf-8"))[
        "run_id"
    ] == "run-1"
    expected_inputs = {"changed": True} if descriptor_access else {}
    assert json.loads((detached_dir / "state.json").read_text(encoding="utf-8"))[
        "inputs"
    ] == expected_inputs
    assert json.loads((detached_dir / "inputs.json").read_text(encoding="utf-8"))[
        "inputs"
    ] == expected_inputs


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


def test_append_log_reports_full_path_when_artifact_is_directory(project_dir):
    import errno
    from specify_cli.workflows.engine import RunState

    if not RunState._supports_descriptor_access():
        pytest.skip("directory descriptors are unavailable")

    log_path = _run_dir(project_dir) / "log.jsonl"
    log_path.mkdir()

    with pytest.raises(IsADirectoryError) as exc_info:
        _state(project_dir).append_log({"event": "test"})

    assert exc_info.value.errno == errno.EISDIR
    assert exc_info.value.filename == str(log_path)


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


@pytest.mark.parametrize("ancestor", [".specify", "workflows"])
@pytest.mark.parametrize("operation", ["load", "save", "list"])
def test_ancestor_replacement_never_accesses_external_storage(
    project_dir, tmp_path, monkeypatch, ancestor, operation
):
    from specify_cli.workflows._execution import CheckpointError
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    if not RunState._supports_descriptor_access():
        pytest.skip("directory descriptors are unavailable")

    state = _state(project_dir)
    state.save()
    runs_root = project_dir / ".specify" / "workflows" / "runs"
    ancestor_path = (
        project_dir / ".specify" if ancestor == ".specify" else runs_root.parent
    )
    outside = tmp_path / "outside"
    outside_run = (
        outside / "workflows" / "runs" / "run-1"
        if ancestor == ".specify"
        else outside / "runs" / "run-1"
    )
    outside_run.mkdir(parents=True)
    external_state = outside_run / "state.json"
    external_state.write_text(
        json.dumps({
            "run_id": "run-1",
            "workflow_id": "external",
            "status": "paused",
            "inputs": {},
        }),
        encoding="utf-8",
    )
    original_content = external_state.read_bytes()
    original_open = os.open
    original_artifact_open = RunState._open_artifact
    artifact_attempts = []
    swapped = False

    def replace_ancestor(path, flags, *args, **kwargs):
        nonlocal swapped
        if not swapped and path in (project_dir, runs_root):
            swapped = True
            ancestor_path.rename(tmp_path / "detached")
            ancestor_path.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    def track_artifact_open(*args, **kwargs):
        artifact_attempts.append(args[0])
        return original_artifact_open(*args, **kwargs)

    monkeypatch.setattr(
        RunState, "_supports_descriptor_access", staticmethod(lambda: True)
    )
    monkeypatch.setattr(os, "open", replace_ancestor)
    monkeypatch.setattr(
        RunState, "_open_artifact", staticmethod(track_artifact_open)
    )
    expected = CheckpointError if operation == "save" else ValueError
    with pytest.raises(expected, match="symlinked workflow storage"):
        if operation == "load":
            RunState.load("run-1", project_dir)
        elif operation == "save":
            state.save()
        else:
            WorkflowEngine(project_dir).list_runs()

    if operation == "save":
        assert state._checkpoint_failed

    assert swapped
    assert not artifact_attempts
    assert external_state.read_bytes() == original_content
    assert sorted(path.name for path in outside_run.iterdir()) == ["state.json"]


@pytest.mark.parametrize("portable", [False, True])
def test_list_rejects_dangling_runs_root(project_dir, tmp_path, monkeypatch, portable):
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    if portable:
        monkeypatch.setattr(
            RunState, "_supports_descriptor_access", staticmethod(lambda: False)
        )
    runs_root = project_dir / ".specify" / "workflows" / "runs"
    runs_root.parent.mkdir(parents=True, exist_ok=True)
    runs_root.symlink_to(tmp_path / "missing", target_is_directory=True)

    with pytest.raises(ValueError, match="symlinked"):
        WorkflowEngine(project_dir).list_runs()


@pytest.mark.parametrize("portable", [False, True])
def test_list_ignores_entries_that_cannot_be_runs(
    project_dir, tmp_path, monkeypatch, portable
):
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    if portable:
        monkeypatch.setattr(
            RunState, "_supports_descriptor_access", staticmethod(lambda: False)
        )
    _state(project_dir).save()
    runs_root = project_dir / ".specify" / "workflows" / "runs"
    (runs_root / ".backup").mkdir()
    (runs_root / "not a run").mkdir()
    (runs_root / ".linked").symlink_to(tmp_path, target_is_directory=True)

    runs = WorkflowEngine(project_dir).list_runs()

    assert [run["run_id"] for run in runs] == ["run-1"]


@pytest.mark.parametrize("replaced", ["run-directory", "state.json"])
def test_descriptor_open_reports_policy_for_late_symlink(
    project_dir, tmp_path, monkeypatch, replaced
):
    from specify_cli.workflows.engine import RunState

    if not RunState._supports_descriptor_access():
        pytest.skip("directory descriptors are unavailable")
    state = _state(project_dir)
    state.save()
    run_dir = project_dir / ".specify" / "workflows" / "runs" / "run-1"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "state.json").write_text(
        (run_dir / "state.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    original_open = RunState._open_no_follow
    swapped = False

    def swap_before_open(name, flags, **kwargs):
        nonlocal swapped
        target = "run-1" if replaced == "run-directory" else "state.json"
        if not swapped and name == target:
            swapped = True
            if replaced == "run-directory":
                os.rename(run_dir, tmp_path / "detached")
                run_dir.symlink_to(outside, target_is_directory=True)
            else:
                (run_dir / "state.json").unlink()
                (run_dir / "state.json").symlink_to(outside / "state.json")
        return original_open(name, flags, **kwargs)

    monkeypatch.setattr(RunState, "_open_no_follow", staticmethod(swap_before_open))
    label = "workflow run path" if replaced == "run-directory" else (
        "workflow run artifact 'state.json' path"
    )

    with pytest.raises(ValueError, match=f"symlinked {label}"):
        RunState.load("run-1", project_dir)

    assert swapped


@pytest.mark.parametrize("portable", [False, True])
def test_atomic_json_writes_request_binary_descriptors(
    project_dir, monkeypatch, portable
):
    from specify_cli.workflows.engine import RunState

    supports_descriptors = RunState._supports_descriptor_access()
    if not portable and not supports_descriptors:
        pytest.skip("directory descriptors are unavailable")
    monkeypatch.setattr(
        RunState, "_supports_descriptor_access", staticmethod(lambda: not portable)
    )
    binary_flag = 1 << 30
    monkeypatch.setattr(os, "O_BINARY", binary_flag, raising=False)
    original_open = os.open
    temporary_opens = []

    def record_flags(path, flags, *args, **kwargs):
        if str(path).endswith(".tmp"):
            temporary_opens.append((flags, kwargs.get("dir_fd")))
        return original_open(path, flags & ~binary_flag, *args, **kwargs)

    monkeypatch.setattr(os, "open", record_flags)

    _state(project_dir).save()

    assert len(temporary_opens) == 2
    assert all(flags & binary_flag for flags, _ in temporary_opens)
    assert all((dir_fd is None) == portable for _, dir_fd in temporary_opens)


@pytest.mark.parametrize(
    ("winerror", "blocked", "attempts"),
    [(5, 1, 2), (32, 1, 2), (5, 5, 5), (None, 5, 1)],
)
def test_checkpoint_retries_only_windows_replace_contention(
    project_dir, monkeypatch, winerror, blocked, attempts
):
    import errno
    from specify_cli.workflows._execution import CheckpointError
    from specify_cli.workflows.engine import RunState

    monkeypatch.setattr(
        RunState, "_supports_descriptor_access", staticmethod(lambda: False)
    )
    state = _state(project_dir)
    state.save()
    state_path = state.runs_dir / "state.json"
    previous = state_path.read_bytes()
    state.inputs = {"value": "updated"}
    failure = PermissionError(errno.EACCES, "replace blocked")
    failure.winerror = winerror
    real_replace = os.replace
    real_validate = RunState._validate_fallback_path
    replacements = []
    validated = []

    def validate(path):
        real_validate(path)
        validated.append(path)

    def replace(src, dst):
        if dst == state_path:
            if replacements:
                assert set(validated) == {src, dst}
            validated.clear()
            replacements.append(src)
            if len(replacements) <= blocked:
                raise failure
        return real_replace(src, dst)

    monkeypatch.setattr(RunState, "_validate_fallback_path", staticmethod(validate))
    monkeypatch.setattr(os, "replace", replace)
    if attempts > blocked:
        state.save()
        assert RunState.load(state.run_id, project_dir).inputs == state.inputs
        assert not state._checkpoint_failed
    else:
        with pytest.raises(CheckpointError, match="replace blocked") as exc_info:
            state.save()
        assert exc_info.value.__cause__ is failure
        assert state._checkpoint_failed
        assert state_path.read_bytes() == previous
    assert len(replacements) == attempts
    assert not list(state.runs_dir.glob(".state.json.*.tmp"))


@pytest.mark.skipif(os.name != "nt", reason="Windows file-sharing semantics are required")
def test_windows_checkpoint_replaces_state_after_reader_closes(project_dir, monkeypatch):
    from contextlib import ExitStack
    from specify_cli._file_handles import _windows_handle
    from specify_cli.workflows.engine import RunState

    state = _state(project_dir)
    state.save()
    state_path = state.runs_dir / "state.json"
    state.inputs = {"value": "updated"}
    real_replace = os.replace
    blocked = []
    with ExitStack() as reader:
        reader.enter_context(_windows_handle(state_path, directory=False))

        def replace(src, dst):
            try:
                return real_replace(src, dst)
            except PermissionError as exc:
                if dst == state_path:
                    blocked.append(exc.winerror)
                    reader.close()
                raise

        monkeypatch.setattr(os, "replace", replace)
        state.save()

    assert len(blocked) == 1 and blocked[0] in (5, 32)
    assert RunState.load(state.run_id, project_dir).inputs == state.inputs


@pytest.mark.parametrize("component", ["ancestor", "run-directory"])
def test_portable_storage_rejects_windows_reparse_points(
    project_dir, monkeypatch, component
):
    from pathlib import Path
    from types import SimpleNamespace
    from specify_cli.workflows._execution import CheckpointError
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    monkeypatch.setattr(
        RunState, "_supports_descriptor_access", staticmethod(lambda: False)
    )
    state = _state(project_dir)
    state.save()
    runs_root = project_dir / ".specify" / "workflows" / "runs"
    reparse_target = runs_root if component == "ancestor" else runs_root / "run-1"
    original_lstat = Path.lstat

    def reparse_lstat(path, *args, **kwargs):
        result = original_lstat(path, *args, **kwargs)
        if path == reparse_target:
            return SimpleNamespace(
                st_mode=result.st_mode,
                st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
            )
        return result

    monkeypatch.setattr(Path, "lstat", reparse_lstat)

    with pytest.raises(ValueError, match="Windows reparse point"):
        RunState.load("run-1", project_dir)
    with pytest.raises(ValueError, match="Windows reparse point"):
        WorkflowEngine(project_dir).list_runs()
    with pytest.raises(ValueError, match="Windows reparse point"):
        state.append_log({"event": "blocked"})
    with pytest.raises(CheckpointError, match="Windows reparse point"):
        state.save()
    assert state._checkpoint_failed


def test_windows_symlink_reparse_attributes_still_report_symlink_policy(
    project_dir, tmp_path, monkeypatch
):
    from pathlib import Path
    from types import SimpleNamespace
    from specify_cli.workflows.engine import RunState

    outside = tmp_path / "outside"
    outside.mkdir()
    runs_root = project_dir / ".specify" / "workflows" / "runs"
    runs_root.mkdir(parents=True)
    linked_run = runs_root / "run-1"
    linked_run.symlink_to(outside, target_is_directory=True)
    original_lstat = Path.lstat

    def symlink_with_reparse_attr(path, *args, **kwargs):
        result = original_lstat(path, *args, **kwargs)
        if path == linked_run:
            return SimpleNamespace(
                st_mode=result.st_mode,
                st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT,
            )
        return result

    monkeypatch.setattr(Path, "lstat", symlink_with_reparse_attr)

    with pytest.raises(ValueError, match="Refusing to use symlinked workflow run path"):
        RunState.load("run-1", project_dir)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows junction creation required")
@pytest.mark.parametrize("component", ["ancestor", "run-directory"])
def test_native_windows_junctions_rejected_in_storage(
    project_dir, tmp_path, component
):
    import subprocess
    from specify_cli.workflows._execution import CheckpointError
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    outside = tmp_path / "outside"
    outside_run = outside / "run-1" if component == "ancestor" else outside
    outside_run.mkdir(parents=True)
    external_state = outside_run / "state.json"
    external_state.write_text(
        json.dumps({
            "run_id": "run-1",
            "workflow_id": "external",
            "status": "paused",
        }),
        encoding="utf-8",
    )
    original_bytes = external_state.read_bytes()

    runs_root = project_dir / ".specify" / "workflows" / "runs"
    if component == "ancestor":
        runs_root.parent.mkdir(parents=True, exist_ok=True)
        junction_path = runs_root
    else:
        runs_root.mkdir(parents=True, exist_ok=True)
        junction_path = runs_root / "run-1"

    created = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(junction_path), str(outside)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if created.returncode:
        pytest.skip(
            f"Windows junction creation unavailable: {created.stderr or created.stdout}"
        )
    assert not junction_path.is_symlink()

    state = _state(project_dir)
    with pytest.raises(ValueError, match="Windows reparse point"):
        RunState.load("run-1", project_dir)
    with pytest.raises(ValueError, match="Windows reparse point"):
        WorkflowEngine(project_dir).list_runs()
    with pytest.raises(ValueError, match="Windows reparse point"):
        state.append_log({"event": "blocked"})
    with pytest.raises(CheckpointError, match="Windows reparse point"):
        state.save()
    assert state._checkpoint_failed

    assert external_state.read_bytes() == original_bytes
    assert not (outside_run / "inputs.json").exists()
    assert not (outside_run / "log.jsonl").exists()


def test_open_artifact_closes_descriptor_when_fdopen_fails(
    project_dir, monkeypatch
):
    import errno
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    if not RunState._supports_descriptor_access():
        pytest.skip("directory descriptors are unavailable")

    state_path = _run_dir(project_dir) / "state.json"
    state_path.mkdir()
    original_open_no_follow = RunState._open_no_follow
    opened_fds = []

    def record_artifact_fd(name, flags, **kwargs):
        fd = original_open_no_follow(name, flags, **kwargs)
        if name == "state.json":
            opened_fds.append(fd)
        return fd

    monkeypatch.setattr(
        RunState, "_open_no_follow", staticmethod(record_artifact_fd)
    )

    with pytest.raises(IsADirectoryError) as artifact_error:
        RunState.load("run-1", project_dir)
    assert artifact_error.value.errno == errno.EISDIR
    assert artifact_error.value.filename == str(state_path)
    assert len(opened_fds) == 1
    with pytest.raises(OSError) as exc_info:
        os.fstat(opened_fds[-1])
    assert exc_info.value.errno == errno.EBADF

    assert WorkflowEngine(project_dir).list_runs() == []
    assert len(opened_fds) == 2
    with pytest.raises(OSError) as exc_info:
        os.fstat(opened_fds[-1])
    assert exc_info.value.errno == errno.EBADF


@pytest.mark.parametrize("target", ["runs-ancestor", "run-directory"])
def test_save_wraps_symlinked_storage_in_checkpoint_error(
    project_dir, tmp_path, target
):
    from specify_cli.workflows._execution import CheckpointError

    outside = tmp_path / "outside"
    outside.mkdir()
    runs_root = project_dir / ".specify" / "workflows" / "runs"
    if target == "runs-ancestor":
        runs_root.parent.mkdir(parents=True, exist_ok=True)
        runs_root.symlink_to(outside, target_is_directory=True)
    else:
        runs_root.mkdir(parents=True, exist_ok=True)
        (runs_root / "run-1").symlink_to(outside, target_is_directory=True)

    state = _state(project_dir)
    with pytest.raises(CheckpointError, match="Refusing to use symlinked"):
        state.save()

    assert state._checkpoint_failed is True
    with pytest.raises(CheckpointError, match="previous checkpoint failed"):
        state.save()


def test_load_legacy_inputs_sidecar_rejects_null_and_allows_missing(project_dir):
    from specify_cli.workflows.engine import RunState

    run_dir = _run_dir(project_dir)
    (run_dir / "state.json").write_text(
        json.dumps({
            "run_id": "run-1",
            "workflow_id": "workflow",
            "status": "paused",
        }),
        encoding="utf-8",
    )

    loaded = RunState.load("run-1", project_dir)
    assert loaded.inputs == {}

    (run_dir / "inputs.json").write_text("null", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid run inputs: expected a JSON object"):
        RunState.load("run-1", project_dir)


@pytest.mark.parametrize("portable", [False, True])
def test_dangling_run_directory_symlink_reports_policy_error(
    project_dir, tmp_path, monkeypatch, portable
):
    from specify_cli.workflows._execution import CheckpointError
    from specify_cli.workflows.engine import (
        RunState,
        WorkflowDefinition,
        WorkflowEngine,
    )

    if portable:
        monkeypatch.setattr(
            RunState, "_supports_descriptor_access", staticmethod(lambda: False)
        )
    runs_root = project_dir / ".specify" / "workflows" / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    (runs_root / "run-1").symlink_to(tmp_path / "missing", target_is_directory=True)

    definition = WorkflowDefinition({
        "workflow": {"id": "workflow", "name": "Workflow"},
        "steps": [],
    })
    with pytest.raises(ValueError, match="Refusing to use symlinked workflow run path"):
        WorkflowEngine(project_dir).execute(definition, run_id="run-1")

    state = _state(project_dir)
    with pytest.raises(ValueError, match="Refusing to use symlinked workflow run path"):
        state.append_log({"event": "blocked"})
    with pytest.raises(
        CheckpointError, match="Refusing to use symlinked workflow run path"
    ):
        state.save()


def test_read_with_file_helper_enforces_deny_policy_and_directory_errors(
    project_dir, tmp_path, monkeypatch
):
    import errno
    from specify_cli.file_helper import (
        FileHelper,
        SymlinkDeniedError,
        UnsupportedPathError,
    )
    from specify_cli.workflows.engine import RunState

    state = _state(project_dir)
    state.save()
    state_path = project_dir / ".specify" / "workflows" / "runs" / "run-1" / "state.json"

    with RunState._read_with_file_helper(state_path, encoding="utf-8") as stream:
        assert json.load(stream)["run_id"] == "run-1"

    state_path.unlink()
    state_path.mkdir()
    with pytest.raises(IsADirectoryError):
        RunState._read_with_file_helper(state_path, encoding="utf-8")
    state_path.rmdir()

    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    state_path.symlink_to(outside)
    with pytest.raises(
        SymlinkDeniedError,
        match="Refusing to use symlinked workflow run artifact 'state.json' path",
    ):
        RunState._read_with_file_helper(state_path, encoding="utf-8")
    state_path.unlink()
    state.save()

    monkeypatch.setattr(
        FileHelper,
        "read_bytes",
        lambda self, path: (_ for _ in ()).throw(
            OSError(errno.ELOOP, "Refusing a reparse-point filesystem path")
        ),
    )
    with pytest.raises(UnsupportedPathError, match="Windows reparse point"):
        RunState._read_with_file_helper(state_path, encoding="utf-8")


@pytest.mark.skipif(
    os.name != "posix" or getattr(os, "geteuid", lambda: -1)() == 0,
    reason="POSIX non-root directory permission enforcement is required",
)
def test_search_only_storage_directories_allow_run_access_and_listing(project_dir):
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    state = _state(project_dir)
    state.save()
    runs_dir = project_dir / ".specify" / "workflows" / "runs"
    run_dir = runs_dir / "run-1"
    search_only = [
        project_dir / ".specify",
        project_dir / ".specify" / "workflows",
        runs_dir,
        run_dir,
    ]
    try:
        for directory in search_only:
            directory.chmod(0o111)

        loaded = RunState.load("run-1", project_dir)
        assert loaded.run_id == "run-1"

        runs_dir.chmod(0o511)
        assert [run["run_id"] for run in WorkflowEngine(project_dir).list_runs()] == [
            "run-1"
        ]
    finally:
        for directory in reversed(search_only):
            directory.chmod(0o755)


@pytest.mark.skipif(
    os.name != "posix" or getattr(os, "geteuid", lambda: -1)() == 0,
    reason="POSIX non-root directory permission enforcement is required",
)
@pytest.mark.parametrize("portable", [False, True])
def test_list_runs_skips_unsearchable_run_directory(
    project_dir, monkeypatch, portable
):
    from specify_cli.workflows.engine import RunState, WorkflowEngine

    if portable:
        monkeypatch.setattr(
            RunState, "_supports_descriptor_access", staticmethod(lambda: False)
        )
    _state(project_dir, "run-1").save()
    _state(project_dir, "run-2").save()
    blocked_dir = project_dir / ".specify" / "workflows" / "runs" / "run-1"
    try:
        blocked_dir.chmod(0o000)
        runs = WorkflowEngine(project_dir).list_runs()
        assert [run["run_id"] for run in runs] == ["run-2"]
    finally:
        blocked_dir.chmod(0o755)
