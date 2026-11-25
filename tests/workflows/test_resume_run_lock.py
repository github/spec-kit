"""One resume owns a workflow run; a second resume of that run is rejected."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from specify_cli.shared_infra import _exclusive_project_lock
from specify_cli.workflows import STEP_REGISTRY
from specify_cli.workflows.base import (
    RunStatus,
    StepBase,
    StepResult,
    StepStatus,
)
from specify_cli.workflows.engine import RunState, WorkflowDefinition, WorkflowEngine


def _definition(log: Path, release: Path | None) -> WorkflowDefinition:
    command = f'"{sys.executable}" "{log.parent / "effect.py"}" "{log}"'
    if release is not None:
        command += f' "{release}"'
    return WorkflowDefinition(
        {
            "workflow": {"id": "resume-lock", "name": "Resume lock"},
            "inputs": {"verdict": {"type": "string", "default": ""}},
            "steps": [
                {
                    "id": "review",
                    "type": "gate",
                    "message": "hold",
                    "verdict_input": "verdict",
                    "options": ["approve", "reject"],
                },
                {"id": "effect", "type": "shell", "run": command, "timeout": 45},
            ],
        }
    )


def _write_effect_script(project: Path) -> None:
    script = project / "effect.py"
    script.write_text(
        "\n".join(
            [
                "import os, sys, time",
                "from pathlib import Path",
                "log = Path(sys.argv[1])",
                "release = Path(sys.argv[2]) if len(sys.argv) > 2 else None",
                "with log.open('a', encoding='utf-8') as handle:",
                "    handle.write(str(os.getpid()))",
                "    handle.write(chr(10))",
                "if release is not None:",
                "    deadline = time.time() + 30",
                "    while not release.exists():",
                "        if time.time() > deadline:",
                "            raise SystemExit('release timeout')",
                "        time.sleep(0.02)",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _start_paused(project: Path, log: Path, release: Path | None, run_id: str) -> None:
    project.mkdir(parents=True, exist_ok=True)
    _write_effect_script(project)
    sys.stdin.isatty = lambda: False  # type: ignore[method-assign]
    state = WorkflowEngine(project).execute(
        _definition(log, release), run_id=run_id
    )
    if state.status is not RunStatus.PAUSED:
        raise RuntimeError(f"setup status {state.status.value}, expected paused")


def _state_path(project: Path, run_id: str) -> Path:
    return project / ".specify" / "workflows" / "runs" / run_id / "state.json"


def _make_legacy(project: Path, run_id: str) -> bytes:
    path = _state_path(project, run_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("installed_workflow_id", None)
    data.pop("installed_registry_root", None)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path.read_bytes()


def _spawn(mode: str, args: list[str], *, cwd: Path) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.pop("SPECIFY_INIT_DIR", None)
    src = str(Path(__file__).resolve().parents[2] / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), mode, *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _finish(proc: subprocess.Popen[str], timeout: float = 40) -> dict[str, object]:
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return {
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": True,
        }
    return {
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": False,
    }


def _read_result(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _effect_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def _finished_events(project: Path, run_id: str) -> list[dict[str, object]]:
    log = project / ".specify" / "workflows" / "runs" / run_id / "log.jsonl"
    if not log.exists():
        return []
    events = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        entry = json.loads(line)
        if entry.get("event") == "workflow_finished":
            events.append(entry)
    return events


def test_concurrent_resume_of_one_run_has_one_owner(tmp_path: Path) -> None:
    """Two processes resuming one paused run: one owner, one immediate rejection."""
    project = tmp_path / "project"
    log = project / "effect.log"
    release = project / "release"
    gate = project / "gate"
    gate.mkdir(parents=True)
    run_id = "same-run"
    _start_paused(project, log, release, run_id)
    paused = _state_path(project, run_id).read_bytes()
    paused_hash = hashlib.sha256(paused).hexdigest()

    results = [project / "a.json", project / "b.json"]
    procs = [
        _spawn(
            "engine-barrier",
            [str(project), run_id, role, str(gate), str(result)],
            cwd=project,
        )
        for role, result in (("a", results[0]), ("b", results[1]))
    ]
    deadline = time.time() + 25
    released = False
    while time.time() < deadline and not all(path.exists() for path in results):
        if not released and (
            len(_effect_lines(log)) >= 2
            or any(
                path.exists() and not _read_result(path).get("ok") for path in results
            )
        ):
            release.write_text("go", encoding="utf-8")
            released = True
        time.sleep(0.02)
    if not released:
        release.write_text("go", encoding="utf-8")
    finished = [_finish(proc) for proc in procs]

    payloads = [_read_result(path) for path in results]
    owners = [payload for payload in payloads if payload.get("ok") is True]
    rejected = [payload for payload in payloads if payload.get("ok") is not True]
    assert finished[0]["timed_out"] is False and finished[1]["timed_out"] is False, finished
    assert len(owners) == 1, payloads
    assert len(rejected) == 1, payloads
    assert rejected[0]["error_type"] == "OSError", rejected
    assert rejected[0]["state_sha256"] == paused_hash, rejected
    assert len(_effect_lines(log)) == 1
    assert _state_path(project, run_id).read_bytes() != paused
    final = json.loads(_state_path(project, run_id).read_text(encoding="utf-8"))
    assert final["status"] == "completed"
    completed = [
        event for event in _finished_events(project, run_id)
        if event.get("status") == "completed"
    ]
    assert completed == [
        {
            "event": "workflow_finished",
            "status": "completed",
            "timestamp": completed[0]["timestamp"],
        }
    ]
    assert (project / ".specify" / f"workflow-run-{run_id}.lock").is_file()

    with pytest.raises(ValueError, match="Cannot resume run 'same-run' with status 'completed'"):
        WorkflowEngine(project).resume(run_id)


def test_distinct_runs_resume_concurrently(tmp_path: Path) -> None:
    """Different run IDs do not share an owner."""
    project = tmp_path / "project"
    release = project / "release"
    logs = [project / "a.log", project / "b.log"]
    run_ids = ["run-a", "run-b"]
    for log, run_id in zip(logs, run_ids, strict=True):
        _start_paused(project, log, release, run_id)
    results = [project / "a.json", project / "b.json"]
    procs = [
        _spawn("engine-plain", [str(project), run_id, str(result)], cwd=project)
        for run_id, result in zip(run_ids, results, strict=True)
    ]
    deadline = time.time() + 15
    while time.time() < deadline and any(len(_effect_lines(log)) < 1 for log in logs):
        time.sleep(0.02)
    release.write_text("go", encoding="utf-8")
    finished = [_finish(proc) for proc in procs]
    payloads = [_read_result(path) for path in results]
    assert all(item["timed_out"] is False for item in finished), finished
    assert [payload.get("ok") for payload in payloads] == [True, True], payloads
    assert all(len(_effect_lines(log)) == 1 for log in logs)


def test_cli_legacy_second_resume_does_not_write(tmp_path: Path) -> None:
    """The legacy metadata save is inside the same ownership boundary."""
    project = tmp_path / "project"
    log = project / "effect.log"
    gate = project / "gate"
    gate.mkdir(parents=True)
    run_id = "legacy-run"
    _start_paused(project, log, None, run_id)
    paused = _make_legacy(project, run_id)
    paused_hash = hashlib.sha256(paused).hexdigest()
    results = [project / "a.json", project / "b.json"]
    procs = [
        _spawn(
            "cli-barrier",
            [str(project), run_id, role, str(gate), str(result)],
            cwd=project,
        )
        for role, result in (("a", results[0]), ("b", results[1]))
    ]
    finished = [_finish(proc) for proc in procs]
    payloads = [_read_result(path) for path in results]
    owners = [payload for payload in payloads if payload.get("ok") is True]
    rejected = [payload for payload in payloads if payload.get("ok") is not True]
    assert all(item["timed_out"] is False for item in finished), finished
    assert len(owners) == 1, payloads
    assert len(rejected) == 1, payloads
    assert "already held" in str(rejected[0].get("output", "")), rejected
    assert rejected[0]["state_sha256"] == paused_hash, rejected
    assert len(_effect_lines(log)) == 1
    final = json.loads(_state_path(project, run_id).read_text(encoding="utf-8"))
    assert final["status"] == "completed"
    assert "installed_workflow_id" in final
    assert "installed_registry_root" in final
    completed = [
        event for event in _finished_events(project, run_id)
        if event.get("status") == "completed"
    ]
    assert len(completed) == 1
    assert completed[0]["event"] == "workflow_finished"


def test_cli_cannot_overwrite_engine_owner(tmp_path: Path) -> None:
    """A CLI resume shares the engine owner's lock and does not save over it."""
    project = tmp_path / "project"
    log = project / "effect.log"
    release = project / "release"
    run_id = "shared-run"
    _start_paused(project, log, release, run_id)
    _make_legacy(project, run_id)
    holder_result = project / "holder.json"
    holder = _spawn(
        "engine-plain", [str(project), run_id, str(holder_result)], cwd=project
    )
    deadline = time.time() + 15
    while time.time() < deadline and len(_effect_lines(log)) < 1:
        time.sleep(0.02)
    assert _effect_lines(log), "owner never entered the resumed step"
    owned = _state_path(project, run_id).read_bytes()
    cli_result = project / "cli.json"
    cli = _spawn("cli-plain", [str(project), run_id, str(cli_result)], cwd=project)
    cli_done = _finish(cli, timeout=20)
    assert cli_done["timed_out"] is False, cli_done
    assert _state_path(project, run_id).read_bytes() == owned
    rejected = _read_result(cli_result)
    assert rejected["ok"] is False, rejected
    assert "already held" in str(rejected.get("output", "")), rejected
    release.write_text("go", encoding="utf-8")
    holder_done = _finish(holder)
    assert holder_done["timed_out"] is False, holder_done
    assert _read_result(holder_result)["ok"] is True


def test_unsafe_run_id_does_not_create_a_lock(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(ValueError, match="Invalid run_id"):
        WorkflowEngine(project).resume("../escape")
    assert list(project.rglob("*.lock")) == []
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize(
    ("mode", "expected"),
    [("ok", RunStatus.COMPLETED), ("interrupt", RunStatus.PAUSED), ("error", RunStatus.FAILED)],
)
def test_run_lock_covers_resume_and_is_released(tmp_path: Path, monkeypatch, mode, expected) -> None:
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    entered = threading.Event()
    release = threading.Event()

    class Hold(StepBase):
        type_key = "hold"

        def execute(self, config, context):
            entered.set()
            if not release.wait(10):
                raise AssertionError("resume step was not released")
            if mode == "interrupt":
                raise KeyboardInterrupt
            if mode == "error":
                raise RuntimeError("boom")
            return StepResult(StepStatus.COMPLETED, output={})

    monkeypatch.setitem(STEP_REGISTRY, "hold", Hold())
    sys.stdin.isatty = lambda: False  # type: ignore[method-assign]
    run_id = "held-run"
    state = WorkflowEngine(project).execute(
        WorkflowDefinition(
            {
                "workflow": {"id": "resume-lock", "name": "Resume lock"},
                "inputs": {"verdict": {"type": "string", "default": ""}},
                "steps": [
                    {
                        "id": "review",
                        "type": "gate",
                        "message": "hold",
                        "verdict_input": "verdict",
                        "options": ["approve", "reject"],
                    },
                    {"id": "work", "type": "hold"},
                ],
            }
        ),
        run_id=run_id,
    )
    assert state.status is RunStatus.PAUSED
    outcome: dict[str, object] = {}

    def _resume() -> None:
        try:
            resumed = WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
            outcome["status"] = resumed.status
        except Exception as exc:  # noqa: BLE001 - recorded for the assertion below
            outcome["error"] = exc

    worker = threading.Thread(target=_resume, name="resume-owner")
    worker.start()
    assert entered.wait(10)
    lock_name = f"workflow-run-{run_id}.lock"
    with pytest.raises(OSError, match="already held"):
        with _exclusive_project_lock(
            project, lock_name, context="workflow run", blocking=False
        ):
            pass
    release.set()
    worker.join(10)
    assert not worker.is_alive()
    if mode == "error":
        assert isinstance(outcome.get("error"), RuntimeError)
    else:
        assert outcome.get("status") is expected
        assert "error" not in outcome
    with _exclusive_project_lock(
        project, lock_name, context="workflow run", blocking=False
    ):
        assert (project / ".specify" / lock_name).is_file()
    assert (project / ".specify" / lock_name).is_file()


def _signal_loaded(gate: Path, role: str, status: str) -> None:
    (gate / f"{role}.loaded").write_text(status, encoding="utf-8")


def _wait_peer(gate: Path, role: str) -> None:
    peer = "b" if role == "a" else "a"
    deadline = time.time() + 20
    while time.time() < deadline:
        if (gate / f"{peer}.loaded").exists() or (gate / f"{peer}.rejected").exists():
            return
        time.sleep(0.02)
    raise TimeoutError("peer did not load or reject")


def _mark_rejected(gate: Path, role: str) -> None:
    (gate / f"{role}.rejected").write_text("1", encoding="utf-8")


def _state_bytes(project: Path, run_id: str) -> bytes:
    path = _state_path(project, run_id)
    if not path.exists():
        return b""
    return path.read_bytes()


def _engine_barrier(project: Path, run_id: str, role: str, gate: Path, result: Path) -> None:
    real = RunState.load.__func__

    def wrapped(cls: type[RunState], rid: str, root: Path) -> RunState:
        state = real(cls, rid, root)
        _signal_loaded(gate, role, state.status.value)
        _wait_peer(gate, role)
        return state

    RunState.load = classmethod(wrapped)  # type: ignore[method-assign]
    try:
        state = WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
        payload: dict[str, object] = {
            "ok": True,
            "status": state.status.value,
            "pid": str(os.getpid()),
            "error": state.error,
        }
    except OSError as exc:
        observed = _state_bytes(project, run_id)
        payload = {
            "ok": False,
            "error_type": "OSError",
            "error": str(exc),
            "state_sha256": hashlib.sha256(observed).hexdigest(),
        }
        _mark_rejected(gate, role)
    except Exception as exc:  # noqa: BLE001 - the parent asserts the recorded failure
        payload = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        _mark_rejected(gate, role)
    result.write_text(json.dumps(payload), encoding="utf-8")


def _engine_plain(project: Path, run_id: str, result: Path) -> None:
    try:
        state = WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
        payload: dict[str, object] = {
            "ok": True,
            "status": state.status.value,
            "error": state.error,
        }
    except Exception as exc:  # noqa: BLE001 - the parent asserts the recorded failure
        payload = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    result.write_text(json.dumps(payload), encoding="utf-8")


def _cli_resume(
    project: Path,
    run_id: str,
    result: Path,
    *,
    role: str | None = None,
    gate: Path | None = None,
) -> None:
    if gate is not None and role is not None:
        real = RunState.load.__func__

        def wrapped(cls: type[RunState], rid: str, root: Path) -> RunState:
            state = real(cls, rid, root)
            _signal_loaded(gate, role, state.status.value)
            _wait_peer(gate, role)
            return state

        RunState.load = classmethod(wrapped)  # type: ignore[method-assign]
    from typer.testing import CliRunner
    from specify_cli import app

    outcome = CliRunner().invoke(
        app,
        ["workflow", "resume", run_id, "--input", "verdict=approve", "--json"],
    )
    text = f"{outcome.output or ''}{getattr(outcome, 'stderr', '') or ''}"
    payload: dict[str, object] = {
        "ok": outcome.exit_code == 0,
        "exit_code": outcome.exit_code,
        "output": text,
    }
    if outcome.exit_code != 0:
        payload["state_sha256"] = hashlib.sha256(_state_bytes(project, run_id)).hexdigest()
        if gate is not None and role is not None:
            _mark_rejected(gate, role)
    result.write_text(json.dumps(payload), encoding="utf-8")


def _main(argv: list[str]) -> None:
    mode = argv[1]
    if mode == "engine-barrier":
        _engine_barrier(Path(argv[2]), argv[3], argv[4], Path(argv[5]), Path(argv[6]))
        return
    if mode == "engine-plain":
        _engine_plain(Path(argv[2]), argv[3], Path(argv[4]))
        return
    if mode == "cli-barrier":
        _cli_resume(
            Path(argv[2]), argv[3], Path(argv[6]), role=argv[4], gate=Path(argv[5])
        )
        return
    if mode == "cli-plain":
        _cli_resume(Path(argv[2]), argv[3], Path(argv[4]))
        return
    raise SystemExit(f"unknown worker mode {mode!r}")


if __name__ == "__main__":
    _main(sys.argv)
