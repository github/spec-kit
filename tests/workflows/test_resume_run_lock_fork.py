"""A forked child does not release or inherit a workflow run lock.

These checks are POSIX-only. They do not install a fork callback or a
descriptor registry. ``LOCK_UN`` is allowed only in the process that
acquired the lock.
"""

from __future__ import annotations

import json
import os
import time
import traceback
from pathlib import Path
from typing import Callable

import pytest

from specify_cli import shared_infra
from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.engine import WorkflowEngine, _resume_run_lock
from tests.workflows.test_resume_run_lock import (
    _effect_lines,
    _pause_noninteractive_gate,
    _start_paused,
    _state_path,
)

pytestmark = pytest.mark.skipif(
    not hasattr(os, "fork"), reason="os.fork is POSIX only"
)

WAIT = 15.0


def _wait_for(path: Path, timeout: float = WAIT) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(0.02)
    return False


def _publish(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temporary, path)


def _fork(child: Callable[[], dict[str, object]], result: Path) -> int:
    """Run ``child`` in a forked process that publishes its result and exits."""
    pid = os.fork()
    if pid == 0:
        code = 0
        try:
            payload = child()
        except BaseException as exc:  # noqa: BLE001 - reported to the parent
            payload = {
                "crash": f"{type(exc).__name__}: {exc}",
                "tb": traceback.format_exc(),
            }
            code = 1
        try:
            payload.setdefault("pid", os.getpid())
            _publish(result, payload)
        finally:
            os._exit(code)
    return pid


def _reap(pid: int, timeout: float = WAIT) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        waited, status = os.waitpid(pid, os.WNOHANG)
        if waited == pid:
            return os.waitstatus_to_exitcode(status)
        time.sleep(0.02)
    os.kill(pid, 9)
    os.waitpid(pid, 0)
    raise AssertionError(f"child {pid} did not exit in time")


def _lock_is_free(project: Path, run_id: str) -> bool:
    try:
        with _resume_run_lock(project, run_id):
            return True
    except OSError as exc:
        if "already held" in str(exc):
            return False
        raise


def _try_resume(project: Path, run_id: str) -> dict[str, object]:
    payload: dict[str, object] = {}
    try:
        state = WorkflowEngine(project).resume(run_id, {"verdict": "approve"})
        payload.update(ok=True, status=state.status.value)
    except OSError as exc:
        payload.update(ok=False, error=str(exc))
    return payload


def _sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_run(project: Path, run_id: str) -> None:
    (project / ".specify" / "workflows" / "runs" / run_id).mkdir(
        parents=True, exist_ok=True
    )


def test_forked_child_cannot_resume_a_run_the_parent_owns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    log = project / "effect.log"
    run_id = "fork-run"
    _start_paused(project, log, None, run_id, monkeypatch)
    paused = _sha(_state_path(project, run_id))
    result = tmp_path / "child.json"

    with _resume_run_lock(project, run_id):
        pid = _fork(lambda: _try_resume(project, run_id), result)
        assert _reap(pid) == 0
        assert not _lock_is_free(project, run_id)

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["ok"] is False, payload
    assert "already held" in str(payload["error"])
    assert _effect_lines(log) == []
    assert _sha(_state_path(project, run_id)) == paused
    assert _lock_is_free(project, run_id)


def test_forked_child_acquires_its_own_lock_after_the_parent_leaves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    log = project / "effect.log"
    run_id = "late-run"
    _start_paused(project, log, None, run_id, monkeypatch)
    released = tmp_path / "released"
    result = tmp_path / "child.json"
    calls: list[int] = []
    real_flock = __import__("fcntl").flock

    def child() -> dict[str, object]:
        import fcntl

        def spy(fd: int, operation: int) -> None:
            calls.append(operation)
            real_flock(fd, operation)

        fcntl.flock = spy
        if not _wait_for(released):
            return {"ok": False, "error": "parent did not release"}
        payload = _try_resume(project, run_id)
        payload["exclusive_calls"] = sum(1 for op in calls if op & fcntl.LOCK_EX)
        return payload

    with _resume_run_lock(project, run_id):
        pid = _fork(child, result)
    released.write_text("go", encoding="utf-8")
    assert _reap(pid) == 0

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["ok"] is True, payload
    assert payload["status"] == RunStatus.COMPLETED.value
    assert payload["exclusive_calls"] >= 1, payload
    assert len(_effect_lines(log)) == 1
    assert _lock_is_free(project, run_id)


def test_inherited_descriptor_does_not_block_the_next_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Parent unlock lets a new owner in while the child still holds the fd."""
    project = tmp_path / "project"
    run_id = "fd-run"
    _ensure_run(project, run_id)
    ready = tmp_path / "ready"
    finish = tmp_path / "finish"
    result = tmp_path / "child.json"
    opened: list[int] = []
    real_open = os.open

    def spy(path: object, flags: int, mode: int = 0o777) -> int:
        fd = real_open(path, flags, mode)
        if str(path).endswith(".resume.lock"):
            opened.append(fd)
        return fd

    monkeypatch.setattr(os, "open", spy)

    with _resume_run_lock(project, run_id):
        assert opened, "the lock descriptor was not opened"
        inherited = opened[-1]

        def child() -> dict[str, object]:
            try:
                os.fstat(inherited)
                descriptor_open = True
            except OSError:
                descriptor_open = False
            ready.write_text("ready", encoding="utf-8")
            waited = _wait_for(finish)
            return {"descriptor_open": descriptor_open, "waited": waited}

        pid = _fork(child, result)
        assert _wait_for(ready)

    try:
        assert _lock_is_free(project, run_id)
        with _resume_run_lock(project, run_id):
            assert not _lock_is_free(project, run_id)
    finally:
        finish.write_text("go", encoding="utf-8")
        assert _reap(pid) == 0

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["waited"] is True
    assert payload["descriptor_open"] is True, payload
    assert not hasattr(shared_infra, "_held_project_locks")


def test_forked_child_leaving_the_scope_keeps_the_parent_lock(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    run_id = "scope-run"
    _ensure_run(project, run_id)
    result = tmp_path / "child.json"
    parent = os.getpid()

    def unwind_in_child() -> int:
        with _resume_run_lock(project, run_id):
            pid = os.fork()
            if pid == 0:
                return 0
            assert _reap(pid) == 0
            assert not _lock_is_free(project, run_id)
            return pid

    try:
        pid = unwind_in_child()
    except BaseException:
        if os.getpid() != parent:
            os._exit(1)
        raise
    if pid == 0:
        try:
            _publish(result, {"pid": os.getpid(), "unwound": True})
        finally:
            os._exit(0)
    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["unwound"] is True
    assert _lock_is_free(project, run_id)


def test_forked_child_may_resume_a_distinct_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pause_noninteractive_gate(monkeypatch)
    project = tmp_path / "project"
    log_r = project / "r.log"
    log_s = project / "s.log"
    _start_paused(project, log_r, None, "run-r", monkeypatch)
    _start_paused(project, log_s, None, "run-s", monkeypatch)
    paused_r = _sha(_state_path(project, "run-r"))
    result = tmp_path / "child.json"

    with _resume_run_lock(project, "run-r"):
        pid = _fork(lambda: _try_resume(project, "run-s"), result)
        assert _reap(pid) == 0
        assert not _lock_is_free(project, "run-r")

    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["ok"] is True, payload
    assert payload["status"] == RunStatus.COMPLETED.value
    assert len(_effect_lines(log_s)) == 1
    assert _effect_lines(log_r) == []
    assert _sha(_state_path(project, "run-r")) == paused_r
