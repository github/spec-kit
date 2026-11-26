"""One resume owns a workflow run; a second resume of that run is rejected."""

from __future__ import annotations

import asyncio
import contextvars
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli.workflows import STEP_REGISTRY
from specify_cli.workflows.base import (
    RunStatus,
    StepBase,
    StepResult,
    StepStatus,
)
from specify_cli.workflows.engine import (
    RunState,
    WorkflowDefinition,
    WorkflowEngine,
    _is_directory_junction,
    _resume_lock_file,
    _resume_run_lock,
    _resume_sentinel_write_error,
)


def _source_root() -> Path:
    return Path(__file__).resolve().parents[2] / "src"


def _imported_engine_file() -> Path:
    from specify_cli.workflows import engine as engine_module

    return Path(engine_module.__file__).resolve()


def _require_local_source() -> Path:
    """Fail closed when this process imported specify_cli from another tree."""
    engine_file = _imported_engine_file()
    root = _source_root().resolve()
    if root not in engine_file.parents:
        raise RuntimeError(f"imported engine is {engine_file}, expected under {root}")
    return engine_file


_require_local_source()


def _publish_json(path: Path, payload: dict[str, object]) -> None:
    """Publish worker JSON so readers never observe a partial document."""
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temporary, path)


def _both_entered(logs: list[Path]) -> bool:
    return all(len(_effect_lines(log)) >= 1 for log in logs)


def _stop_processes(procs: list[subprocess.Popen[str]]) -> None:
    for proc in procs:
        if proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass


def _pause_noninteractive_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    from specify_cli.workflows.step import gate as gate_module

    monkeypatch.setattr(
        gate_module,
        "sys",
        SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: False)),
    )


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


def _start_paused(
    project: Path,
    log: Path,
    release: Path | None,
    run_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project.mkdir(parents=True, exist_ok=True)
    _write_effect_script(project)
    _pause_noninteractive_gate(monkeypatch)
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


def _is_lock_rejection(payload: dict[str, object]) -> bool:
    """True only for the exclusive-lock rejection, not any OSError.

    ``TimeoutError`` is an ``OSError`` and the barrier records it with
    ``error_type`` ``OSError``. A permission error is an ``OSError`` too.
    Neither message is the lock contention outcome.
    """
    return (
        payload.get("ok") is not True
        and payload.get("error_type") == "OSError"
        and "already held" in str(payload.get("error", ""))
    )


def test_lock_rejection_oracle_rejects_timeout_and_unrelated_oserror() -> None:
    timeout = {
        "ok": False,
        "error_type": "OSError",
        "error": "peer did not load or reject",
    }
    unrelated = {"ok": False, "error_type": "OSError", "error": "Permission denied"}
    held = {
        "ok": False,
        "error_type": "OSError",
        "error": "Exclusive workflow run lock is already held",
    }
    assert _is_lock_rejection(timeout) is False
    assert _is_lock_rejection(unrelated) is False
    assert _is_lock_rejection(held) is True


def test_concurrent_resume_of_one_run_has_one_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two processes resuming one paused run: one owner, one immediate rejection."""
    project = tmp_path / "project"
    log = project / "effect.log"
    release = project / "release"
    gate = project / "gate"
    gate.mkdir(parents=True)
    run_id = "same-run"
    _start_paused(project, log, release, run_id, monkeypatch)
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
    try:
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
    finally:
        _stop_processes(procs)

    payloads = [_read_result(path) for path in results]
    owners = [payload for payload in payloads if payload.get("ok") is True]
    rejected = [payload for payload in payloads if payload.get("ok") is not True]
    assert finished[0]["timed_out"] is False and finished[1]["timed_out"] is False, finished
    assert len(owners) == 1, payloads
    assert len(rejected) == 1, payloads
    assert _is_lock_rejection(rejected[0]), rejected
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
    lock_file = _resume_lock_file(
        project / ".specify" / "workflows" / "runs" / run_id
    )
    assert lock_file.is_file()
    assert lock_file.name == ".resume.lock"
    assert not list((project / ".specify").glob("workflow-run-*.lock"))

    with pytest.raises(ValueError, match="Cannot resume run 'same-run' with status 'completed'"):
        WorkflowEngine(project).resume(run_id)


def test_distinct_runs_resume_concurrently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Different run IDs do not share an owner."""
    project = tmp_path / "project"
    release = project / "release"
    logs = [project / "a.log", project / "b.log"]
    run_ids = ["run-a", "run-b"]
    for log, run_id in zip(logs, run_ids, strict=True):
        _start_paused(project, log, release, run_id, monkeypatch)
    results = [project / "a.json", project / "b.json"]
    procs = [
        _spawn("engine-plain", [str(project), run_id, str(result)], cwd=project)
        for run_id, result in zip(run_ids, results, strict=True)
    ]
    overlapped = False
    try:
        deadline = time.time() + 15
        while time.time() < deadline and not _both_entered(logs):
            time.sleep(0.02)
        overlapped = _both_entered(logs)
        if overlapped:
            release.write_text("go", encoding="utf-8")
        finished = [_finish(proc, timeout=10 if overlapped else 1) for proc in procs]
    finally:
        _stop_processes(procs)
    assert overlapped, "distinct runs did not both enter before release"
    payloads = [_read_result(path) for path in results]
    assert all(item["timed_out"] is False for item in finished), finished
    assert [payload.get("ok") for payload in payloads] == [True, True], payloads
    assert all(len(_effect_lines(log)) == 1 for log in logs)


def test_unsafe_run_id_does_not_create_a_lock(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(ValueError, match="Invalid run_id"):
        WorkflowEngine(project).resume("../escape")
    assert list(project.rglob("*.lock")) == []
    assert not (tmp_path / "escape").exists()


def test_visible_result_file_is_complete_json(tmp_path: Path) -> None:
    """A partial document is not a published result; atomic replace is."""
    path = tmp_path / "result.json"
    path.write_text("{", encoding="utf-8")
    assert path.exists()
    with pytest.raises(json.JSONDecodeError):
        json.loads(path.read_text(encoding="utf-8"))
    path.unlink()
    _publish_json(path, {"ok": True, "run": "same-run"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"ok": True, "run": "same-run"}


def test_paused_setup_does_not_replace_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = sys.stdin.isatty
    project = tmp_path / "project"
    _start_paused(project, project / "effect.log", None, "stdin-run", monkeypatch)
    assert sys.stdin.isatty == original


def test_serialized_execution_does_not_count_as_overlap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One shared lock can finish both runs without their effects overlapping."""
    from specify_cli.workflows import engine as engine_module

    def one_file(run_dir: Path) -> Path:
        return run_dir.parents[1] / "shared-resume.lock"

    monkeypatch.setattr(engine_module, "_resume_lock_file", one_file)
    project = tmp_path / "project"
    release = project / "release"
    logs = [project / "a.log", project / "b.log"]
    run_ids = ["run-a", "run-b"]
    for log, run_id in zip(logs, run_ids, strict=True):
        _start_paused(project, log, release, run_id, monkeypatch)
    errors: list[BaseException] = []

    def resume(run_id: str) -> None:
        try:
            WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
        except BaseException as exc:  # noqa: BLE001 - the oracle records the rejection
            errors.append(exc)

    threads = [threading.Thread(target=resume, args=(run_id,)) for run_id in run_ids]
    for thread in threads:
        thread.start()
    try:
        deadline = time.time() + 5
        while time.time() < deadline and not any(_effect_lines(log) for log in logs):
            time.sleep(0.02)
        overlapped = _both_entered(logs)
        entered = sum(1 for log in logs if _effect_lines(log))
    finally:
        release.write_text("go", encoding="utf-8")
        for thread in threads:
            thread.join(15)
    assert entered == 1
    assert overlapped is False
    assert any(isinstance(exc, OSError) for exc in errors)


def test_public_resume_does_not_reenter_under_the_held_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The public entry always locks; the protected body does not lock again."""
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    log = project / "effect.log"
    run_id = "nested-run"
    _start_paused(project, log, None, run_id, monkeypatch)
    engine = WorkflowEngine(project)
    with _resume_run_lock(project, run_id):
        with pytest.raises(OSError, match="already held"):
            engine.resume(run_id, {"verdict": "approve"})
        state = engine._resume_owned(run_id, {"verdict": "approve"})
    assert state.status is RunStatus.COMPLETED
    assert len(_effect_lines(log)) == 1


def _hold_resume_lock(project: Path, run_id: str, held: threading.Event, release: threading.Event) -> None:
    with _resume_run_lock(project, run_id):
        held.set()
        if not release.wait(20):
            raise AssertionError("lock holder was not released")


def test_copied_context_cannot_bypass_the_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    log = project / "effect.log"
    release_file = project / "release"
    run_id = "copy-run"
    _start_paused(project, log, release_file, run_id, monkeypatch)
    copied: dict[str, contextvars.Context] = {}
    held = threading.Event()
    let_go = threading.Event()

    def owner() -> None:
        with _resume_run_lock(project, run_id):
            copied["ctx"] = contextvars.copy_context()
            held.set()
            let_go.wait(20)

    thread = threading.Thread(target=owner)
    thread.start()
    assert held.wait(10)
    release_file.write_text("go", encoding="utf-8")
    outcome: dict[str, object] = {}

    def intruder() -> None:
        try:
            copied["ctx"].run(
                lambda: WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
            )
            outcome["ok"] = True
        except OSError as exc:
            outcome["error"] = str(exc)

    other = threading.Thread(target=intruder)
    other.start()
    other.join(20)
    let_go.set()
    thread.join(10)
    assert "already held" in str(outcome.get("error", "")), outcome
    assert _effect_lines(log) == []


def test_stale_context_cannot_bypass_a_new_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    log = project / "effect.log"
    release_file = project / "release"
    run_id = "stale-run"
    _start_paused(project, log, release_file, run_id, monkeypatch)
    copied: dict[str, contextvars.Context] = {}

    def owner() -> None:
        with _resume_run_lock(project, run_id):
            copied["ctx"] = contextvars.copy_context()

    owner_thread = threading.Thread(target=owner)
    owner_thread.start()
    owner_thread.join(10)
    assert "ctx" in copied
    held = threading.Event()
    let_go = threading.Event()
    newbie = threading.Thread(target=_hold_resume_lock, args=(project, run_id, held, let_go))
    newbie.start()
    assert held.wait(10)
    release_file.write_text("go", encoding="utf-8")
    outcome: dict[str, object] = {}

    def intruder() -> None:
        try:
            copied["ctx"].run(
                lambda: WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
            )
            outcome["ok"] = True
        except OSError as exc:
            outcome["error"] = str(exc)

    other = threading.Thread(target=intruder)
    other.start()
    other.join(20)
    let_go.set()
    newbie.join(10)
    assert "already held" in str(outcome.get("error", "")), outcome
    assert _effect_lines(log) == []


def test_asyncio_to_thread_does_not_inherit_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    log = project / "effect.log"
    release_file = project / "release"
    run_id = "async-run"
    _start_paused(project, log, release_file, run_id, monkeypatch)
    release_file.write_text("go", encoding="utf-8")
    outcome: dict[str, object] = {}

    async def main() -> None:
        with _resume_run_lock(project, run_id):
            def attempt() -> None:
                try:
                    WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
                    outcome["ok"] = True
                except OSError as exc:
                    outcome["error"] = str(exc)

            await asyncio.to_thread(attempt)

    asyncio.run(main())
    assert "already held" in str(outcome.get("error", "")), outcome
    assert _effect_lines(log) == []


def _windows_lock_events(monkeypatch: pytest.MonkeyPatch) -> list[tuple[object, ...]]:
    import msvcrt

    events: list[tuple[object, ...]] = []
    real_lock = msvcrt.locking
    real_close = os.close

    def spy_lock(fd: int, mode: int, nbytes: int) -> None:
        events.append(("lock", mode, nbytes, os.lseek(fd, 0, os.SEEK_CUR)))
        real_lock(fd, mode, nbytes)

    def spy_close(fd: int) -> None:
        events.append(("close", fd))
        real_close(fd)

    monkeypatch.setattr(msvcrt, "locking", spy_lock)
    monkeypatch.setattr(os, "close", spy_close)
    return events


def _assert_windows_unlock_before_close(events: list[tuple[object, ...]]) -> None:
    import msvcrt

    unlocks = [
        index
        for index, event in enumerate(events)
        if event[0] == "lock" and event[1] == msvcrt.LK_UNLCK
    ]
    assert unlocks, events
    unlock = events[unlocks[-1]]
    assert unlock[2] == 1
    assert unlock[3] == 0
    closes = [
        index
        for index, event in enumerate(events)
        if event[0] == "close" and index > unlocks[-1]
    ]
    assert closes, events


def test_windows_release_unlocks_the_acquired_byte_before_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("Windows byte-range locks")
    import msvcrt

    project = tmp_path / "project"
    run_dir = project / ".specify" / "workflows" / "runs" / "win-unlock"
    run_dir.mkdir(parents=True)
    events = _windows_lock_events(monkeypatch)
    with _resume_run_lock(project, "win-unlock"):
        pass
    locks = [event for event in events if event[0] == "lock" and event[1] == msvcrt.LK_NBLCK]
    assert locks == [("lock", msvcrt.LK_NBLCK, 1, 0)]
    _assert_windows_unlock_before_close(events)

    events.clear()
    with pytest.raises(RuntimeError, match="boom"):
        with _resume_run_lock(project, "win-unlock"):
            raise RuntimeError("boom")
    _assert_windows_unlock_before_close(events)

    events.clear()
    with _resume_run_lock(project, "win-unlock"):
        with pytest.raises(OSError, match="already held"):
            with _resume_run_lock(project, "win-unlock"):
                pass
        assert [event for event in events if event[0] == "lock" and event[1] == msvcrt.LK_UNLCK] == []
    _assert_windows_unlock_before_close(events)


def test_ownership_is_released_when_the_body_raises(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_dir = project / ".specify" / "workflows" / "runs" / "boom-run"
    run_dir.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="boom"):
        with _resume_run_lock(project, "boom-run"):
            raise RuntimeError("boom")
    with _resume_run_lock(project, "boom-run"):
        held = True
    assert held
    assert _resume_lock_file(run_dir).is_file()


def test_distinct_run_locks_are_independent(tmp_path: Path) -> None:
    project = tmp_path / "project"
    for run_id in ("run-a", "run-b"):
        (project / ".specify" / "workflows" / "runs" / run_id).mkdir(parents=True)
    with _resume_run_lock(project, "run-a"):
        with _resume_run_lock(project, "run-b"):
            held = True
    assert held


def test_case_alias_cannot_take_a_second_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    run_id = "CaseRun"
    alias = "caserun"
    _start_paused(project, project / "effect.log", None, run_id, monkeypatch)
    state = _state_path(project, run_id)
    alias_state = _state_path(project, alias)
    if not alias_state.exists() or not os.path.samefile(state, alias_state):
        pytest.skip("filesystem does not alias this run directory")
    held = threading.Event()
    let_go = threading.Event()
    thread = threading.Thread(target=_hold_resume_lock, args=(project, run_id, held, let_go))
    thread.start()
    try:
        assert held.wait(10)
        with pytest.raises(OSError, match="already held"):
            with _resume_run_lock(project, alias):
                pass
    finally:
        let_go.set()
        thread.join(10)


def test_long_run_id_gets_a_bounded_exclusive_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    run_id = "r" + ("a" * 239)
    _start_paused(project, project / "effect.log", None, run_id, monkeypatch)
    held = threading.Event()
    let_go = threading.Event()
    errors: list[BaseException] = []

    def hold() -> None:
        try:
            _hold_resume_lock(project, run_id, held, let_go)
        except BaseException as exc:  # noqa: BLE001 - the assertion reports it
            errors.append(exc)
            held.set()

    thread = threading.Thread(target=hold)
    thread.start()
    try:
        assert held.wait(10)
        assert not errors, errors
        lock_file = _resume_lock_file(
            project / ".specify" / "workflows" / "runs" / run_id
        )
        assert lock_file.is_file()
        assert lock_file.name == ".resume.lock"
        assert len(lock_file.name) < len(run_id)
        with pytest.raises(OSError, match="already held"):
            with _resume_run_lock(project, run_id):
                pass
    finally:
        let_go.set()
        thread.join(10)


def test_failed_acquire_clears_previous_execution_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    project.mkdir(parents=True)
    _write_effect_script(project)
    log = project / "effect.log"
    run_id = "state-run"
    engine = WorkflowEngine(project)
    state = engine.execute(_definition(log, None), run_id=run_id)
    assert state.status is RunStatus.PAUSED
    assert engine._execution_state.get() is state
    held = threading.Event()
    let_go = threading.Event()
    thread = threading.Thread(target=_hold_resume_lock, args=(project, run_id, held, let_go))
    thread.start()
    try:
        assert held.wait(10)
        with pytest.raises(OSError, match="already held"):
            engine.resume(run_id, {"verdict": "approve"})
        assert engine._execution_state.get() is None
    finally:
        let_go.set()
        thread.join(10)


def test_execution_state_reports_the_run_after_acquire(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    run_id = "report-run"

    class Boom(StepBase):
        type_key = "boom"

        def execute(self, config, context):
            raise RuntimeError("boom")

    monkeypatch.setitem(STEP_REGISTRY, "boom", Boom())
    engine = WorkflowEngine(project)
    state = engine.execute(
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
                    {"id": "work", "type": "boom"},
                ],
            }
        ),
        run_id=run_id,
    )
    assert state.status is RunStatus.PAUSED
    with pytest.raises(RuntimeError, match="boom"):
        engine.resume(run_id, {"verdict": "approve"})
    current = engine._execution_state.get()
    assert current is not None and current.run_id == run_id


def test_worker_imports_this_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    log = project / "effect.log"
    run_id = "import-run"
    _start_paused(project, log, None, run_id, monkeypatch)
    result = project / "worker.json"
    proc = _spawn("engine-plain", [str(project), run_id, str(result)], cwd=project)
    try:
        finished = _finish(proc)
    finally:
        _stop_processes([proc])
    assert finished["timed_out"] is False, finished
    payload = _read_result(result)
    assert payload["ok"] is True, payload
    imported = Path(str(payload["import_file"])).resolve()
    assert _source_root().resolve() in imported.parents


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
    _pause_noninteractive_gate(monkeypatch)
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
    lock_file = _resume_lock_file(
        project / ".specify" / "workflows" / "runs" / run_id
    )
    with pytest.raises(OSError, match="already held"):
        with _resume_run_lock(project, run_id):
            pass
    release.set()
    worker.join(10)
    assert not worker.is_alive()
    if mode == "error":
        assert isinstance(outcome.get("error"), RuntimeError)
    else:
        assert outcome.get("status") is expected
        assert "error" not in outcome
    with _resume_run_lock(project, run_id):
        assert lock_file.is_file()
    listed = WorkflowEngine(project).list_runs()
    assert [item["run_id"] for item in listed] == [run_id]


def _symlink_or_skip(link: Path, target: Path, *, target_is_directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")


def test_missing_run_creates_nothing(tmp_path: Path) -> None:
    project = tmp_path / "bare"
    project.mkdir()
    with pytest.raises(FileNotFoundError, match="Run state not found"):
        WorkflowEngine(project).resume("missing-run")
    assert list(project.iterdir()) == []


def test_symlinked_run_directory_is_refused(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside-run"
    outside.mkdir()
    (outside / "state.json").write_text("{}", encoding="utf-8")
    runs = project / ".specify" / "workflows" / "runs"
    runs.mkdir(parents=True)
    _symlink_or_skip(runs / "linked-run", outside, target_is_directory=True)
    with pytest.raises(ValueError, match="Refusing to use symlinked workflow run path"):
        with _resume_run_lock(project, "linked-run"):
            pass
    assert not (outside / ".resume.lock").exists()


def test_symlinked_lock_file_is_refused(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_dir = project / ".specify" / "workflows" / "runs" / "link-lock"
    run_dir.mkdir(parents=True)
    outside = tmp_path / "outside.lock"
    outside.write_bytes(b"keep")
    _symlink_or_skip(run_dir / ".resume.lock", outside)
    with pytest.raises(OSError, match="symlinked workflow run lock"):
        with _resume_run_lock(project, "link-lock"):
            pass
    assert outside.read_bytes() == b"keep"


def test_junction_run_directory_is_refused(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("directory junctions are Windows reparse points")
    project = tmp_path / "project"
    outside = tmp_path / "outside-run"
    outside.mkdir()
    runs = project / ".specify" / "workflows" / "runs"
    runs.mkdir(parents=True)
    link = runs / "joined-run"
    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        pytest.skip(f"cannot create a junction: {completed.stderr}")
    with pytest.raises(ValueError, match="Refusing to use junction workflow run path"):
        with _resume_run_lock(project, "joined-run"):
            pass
    assert not (outside / ".resume.lock").exists()


def _hide_is_junction(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    """Force the pre-3.12 attribute fallback without running Python 3.11.

    ``is_junction`` can sit on more than one class in the path MRO. Hiding
    only the first leaves the base method in place, so the fallback never runs.
    """
    found = False
    for owner in type(path).__mro__:
        if "is_junction" in getattr(owner, "__dict__", {}):
            monkeypatch.delattr(owner, "is_junction")
            found = True
    if not found:
        pytest.skip("this runtime has no Path.is_junction to hide")


def _snapshot(root: Path) -> list[str]:
    return sorted(
        item.relative_to(root).as_posix()
        for item in root.rglob("*")
        if item.is_file() or item.is_dir()
    )


def test_junction_fallback_distinguishes_reparse_points(tmp_path: Path, monkeypatch) -> None:
    """Compatibility branch only. This process is not Python 3.11."""
    if os.name != "nt":
        pytest.skip("the junction fallback is Windows-only")
    ordinary = tmp_path / "ordinary"
    ordinary.mkdir()
    _hide_is_junction(monkeypatch, ordinary)
    assert _is_directory_junction(ordinary) is False

    linked = tmp_path / "linked"
    target = tmp_path / "target"
    target.mkdir()
    _symlink_or_skip(linked, target, target_is_directory=True)
    assert _is_directory_junction(linked) is False

    outside = tmp_path / "joined-target"
    outside.mkdir()
    junction = tmp_path / "joined"
    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        pytest.skip(f"cannot create a junction: {completed.stderr}")
    assert _is_directory_junction(junction) is True


def test_sentinel_write_codes_keep_access_failures() -> None:
    contention = _resume_sentinel_write_error(33)
    sharing = _resume_sentinel_write_error(32)
    denied = _resume_sentinel_write_error(5)
    assert "already held" in str(contention)
    assert "already held" in str(sharing)
    assert "already held" not in str(denied)
    assert getattr(denied, "winerror", None) == 5


def test_windows_empty_observation_while_held_is_contention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("byte-range lock writes are Windows-only")
    project = tmp_path / "project"
    run_dir = project / ".specify" / "workflows" / "runs" / "first-write"
    run_dir.mkdir(parents=True)
    real_fstat = os.fstat

    def fstat(fd: int):
        stat = real_fstat(fd)
        values = list(stat)
        values[6] = 0
        return os.stat_result(values)

    with _resume_run_lock(project, "first-write"):
        monkeypatch.setattr(os, "fstat", fstat)
        with pytest.raises(OSError, match="already held"):
            with _resume_run_lock(project, "first-write"):
                pass


def test_windows_sentinel_io_error_is_not_contention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("the sentinel write is Windows-only")
    project = tmp_path / "project"
    run_dir = project / ".specify" / "workflows" / "runs" / "io-error"
    run_dir.mkdir(parents=True)

    def fail_write(fd: int) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(
        "specify_cli.workflows.engine._write_resume_lock_sentinel", fail_write
    )
    with pytest.raises(OSError, match="No space left on device") as raised:
        with _resume_run_lock(project, "io-error"):
            pass
    assert "already held" not in str(raised.value)
    assert not (run_dir / ".resume.lock").exists() or (run_dir / ".resume.lock").stat().st_size == 0


def test_non_directory_component_creates_no_run_artifacts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    workflows = project / ".specify" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "runs").write_text("not a directory", encoding="utf-8")
    before = _snapshot(project)
    with pytest.raises(ValueError, match="not a directory"):
        with _resume_run_lock(project, "blocked-run"):
            pass
    assert _snapshot(project) == before
    assert not (workflows / "runs" / "blocked-run").exists()


def test_root_escape_creates_no_run_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    outside.mkdir()
    runs = project / ".specify" / "workflows" / "runs"
    runs.mkdir(parents=True)
    junction = runs / "escape-run"
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(outside)],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            pytest.skip(f"cannot create a junction: {completed.stderr}")
    else:
        _symlink_or_skip(junction, outside, target_is_directory=True)
    before = _snapshot(outside)
    monkeypatch.setattr(
        "specify_cli.workflows.engine._is_directory_junction", lambda path: False
    )
    monkeypatch.setattr(Path, "is_symlink", lambda self: False)
    with pytest.raises(ValueError, match="escapes project root"):
        with _resume_run_lock(project, "escape-run"):
            pass
    assert _snapshot(outside) == before
    assert not (outside / ".resume.lock").exists()


def test_case_distinct_directories_keep_independent_locks(tmp_path: Path) -> None:
    project = tmp_path / "project"
    runs = project / ".specify" / "workflows" / "runs"
    runs.mkdir(parents=True)
    if os.name == "nt":
        completed = subprocess.run(
            ["fsutil", "file", "setCaseSensitiveInfo", str(runs), "enable"],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            pytest.skip(f"cannot enable case-sensitive directory: {completed.stderr}")
    first = runs / "CaseRun"
    second = runs / "caserun"
    first.mkdir()
    try:
        second.mkdir()
    except FileExistsError:
        if os.path.samefile(first, second):
            pytest.skip("filesystem aliases the two run directories")
        raise
    if os.path.samefile(first, second):
        pytest.skip("filesystem aliases the two run directories")
    with _resume_run_lock(project, "CaseRun"):
        with _resume_run_lock(project, "caserun"):
            held = True
    assert held


def test_terminated_holder_releases_the_lock(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_id = "kill-run"
    (project / ".specify" / "workflows" / "runs" / run_id).mkdir(parents=True)
    held = project / "held"
    proc = _spawn("hold-until-killed", [str(project), run_id, str(held)], cwd=project)
    try:
        deadline = time.time() + 15
        while time.time() < deadline and not held.exists():
            if proc.poll() is not None:
                break
            time.sleep(0.02)
        assert held.exists(), "holder did not acquire the lock"
        proc.kill()
        proc.wait(10)
    finally:
        _stop_processes([proc])
    deadline = time.time() + 5
    while True:
        try:
            with _resume_run_lock(project, run_id):
                acquired = True
            break
        except OSError as exc:
            if "already held" not in str(exc) or time.time() >= deadline:
                raise
            time.sleep(0.05)
    assert acquired
    assert proc.poll() is not None


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
    _publish_json(result, payload)


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
    payload["import_file"] = str(_imported_engine_file())
    _publish_json(result, payload)


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
    payload["import_file"] = str(_imported_engine_file())
    _publish_json(result, payload)


def _main(argv: list[str]) -> None:
    _require_local_source()
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
    if mode == "hold-until-killed":
        project = Path(argv[2])
        run_id = argv[3]
        held = Path(argv[4])
        with _resume_run_lock(project, run_id):
            held.write_text("held", encoding="utf-8")
            time.sleep(60)
        return
    raise SystemExit(f"unknown worker mode {mode!r}")


if __name__ == "__main__":
    _main(sys.argv)
