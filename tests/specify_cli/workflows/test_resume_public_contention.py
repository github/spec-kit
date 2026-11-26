"""Public CLI contention for one workflow run.

This module imports only public Specify surfaces so it can be collected
against the upstream baseline. Two processes resuming one paused run must
produce one effect and one rejection. The baseline executes both.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine


def _require_same_engine_as_parent(payloads: list[dict[str, object]]) -> Path:
    """Workers must import the engine module this process is testing.

    Two workers that agree with each other still fail when that shared file
    is not the parent's engine. Baseline and candidate runs both compare
    against whichever engine the parent actually imported.
    """
    from specify_cli.workflows import engine as engine_module

    parent = Path(str(engine_module.__file__)).resolve()
    imported = {Path(str(item["import_file"])).resolve() for item in payloads}
    if imported != {parent}:
        raise AssertionError(
            f"worker engine {sorted(imported)!s} is not the parent engine {parent}"
        )
    return parent


def test_worker_engine_identity_rejects_a_shared_wrong_origin(tmp_path: Path) -> None:
    wrong = tmp_path / "other-engine.py"
    payloads = [
        {"import_file": str(wrong)},
        {"import_file": str(wrong.resolve())},
    ]
    with pytest.raises(AssertionError, match="not the parent engine"):
        _require_same_engine_as_parent(payloads)


def _pause_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    from specify_cli.workflows.step import gate as gate_module

    monkeypatch.setattr(
        gate_module,
        "sys",
        SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: False)),
    )


def _definition(log: Path, release: Path) -> WorkflowDefinition:
    command = (
        f'"{sys.executable}" "{log.parent / "effect.py"}" "{log}" "{release}"'
    )
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


def _write_effect(project: Path) -> None:
    script = project / "effect.py"
    script.write_text(
        "\n".join(
            [
                "import os, sys, time",
                "from pathlib import Path",
                "log = Path(sys.argv[1])",
                "release = Path(sys.argv[2])",
                "with log.open('a', encoding='utf-8') as handle:",
                "    handle.write(str(os.getpid()))",
                "    handle.write(chr(10))",
                "deadline = time.time() + 30",
                "while not release.exists():",
                "    if time.time() > deadline:",
                "        raise SystemExit('release timeout')",
                "    time.sleep(0.02)",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _effect_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len([line for line in path.read_text(encoding="utf-8").splitlines() if line])


def test_public_cli_same_run_resume_has_one_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One public CLI resume owns the run; the other is rejected."""
    project = tmp_path / "project"
    project.mkdir()
    log = project / "effect.log"
    release = project / "release"
    run_id = "public-run"
    _write_effect(project)
    _pause_gate(monkeypatch)
    state = WorkflowEngine(project).execute(
        _definition(log, release), run_id=run_id
    )
    assert state.status is RunStatus.PAUSED
    gate = project / "gate"
    gate.mkdir()
    results = [project / "a.json", project / "b.json"]
    procs = [
        _spawn(project, run_id, result, role=role, gate=gate)
        for role, result in (("a", results[0]), ("b", results[1]))
    ]
    try:
        deadline = time.time() + 25
        released = False
        while time.time() < deadline and not all(path.exists() for path in results):
            if not released and (
                _effect_count(log) >= 2
                or any(path.exists() and not _read(path).get("ok") for path in results)
            ):
                release.write_text("go", encoding="utf-8")
                released = True
            time.sleep(0.02)
        if not released:
            release.write_text("go", encoding="utf-8")
        finished = [_finish(proc) for proc in procs]
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
                proc.wait(5)

    payloads = [_read(path) for path in results]
    owners = [item for item in payloads if item.get("ok") is True]
    rejected = [item for item in payloads if item.get("ok") is not True]
    assert all(item["timed_out"] is False for item in finished), finished
    assert _effect_count(log) == 1, payloads
    assert len(owners) == 1, payloads
    assert len(rejected) == 1, payloads
    assert "already held" in str(rejected[0].get("output", "")), rejected
    _require_same_engine_as_parent(payloads)


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _spawn(
    project: Path,
    run_id: str,
    result: Path,
    *,
    role: str,
    gate: Path,
) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.pop("SPECIFY_INIT_DIR", None)
    return subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            str(project),
            run_id,
            str(result),
            role,
            str(gate),
        ],
        cwd=project,
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


def _main(argv: list[str]) -> None:
    from specify_cli import app
    from specify_cli.workflows import engine as engine_module
    from specify_cli.workflows.engine import RunState
    from typer.testing import CliRunner

    project = Path(argv[1])
    os.chdir(project)
    run_id = argv[2]
    result = Path(argv[3])
    role = argv[4] if len(argv) > 5 else None
    gate = Path(argv[5]) if len(argv) > 5 else None
    if gate is not None and role is not None:
        real = RunState.load.__func__
        calls = {"n": 0}

        def wrapped(cls: type[RunState], rid: str, root: Path) -> RunState:
            state = real(cls, rid, root)
            calls["n"] += 1
            marker = gate / f"{role}.loaded.{calls['n']}"
            marker.write_text(state.status.value, encoding="utf-8")
            peer = "b" if role == "a" else "a"
            peer_marker = gate / f"{peer}.loaded.{calls['n']}"
            deadline = time.time() + 20
            while time.time() < deadline:
                if peer_marker.exists() or (gate / f"{peer}.rejected").exists():
                    return state
                time.sleep(0.02)
            raise TimeoutError("peer did not load or reject")

        RunState.load = classmethod(wrapped)  # type: ignore[method-assign]
    outcome = CliRunner().invoke(
        app,
        ["workflow", "resume", run_id, "--input", "verdict=approve", "--json"],
    )
    if outcome.exit_code != 0 and gate is not None and role is not None:
        (gate / f"{role}.rejected").write_text("1", encoding="utf-8")
    text = f"{outcome.output or ''}{getattr(outcome, 'stderr', '') or ''}"
    payload: dict[str, object] = {
        "ok": outcome.exit_code == 0,
        "exit_code": outcome.exit_code,
        "output": text,
        "import_file": str(Path(engine_module.__file__).resolve()),
    }
    temporary = result.with_name(f".{result.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(temporary, result)


if __name__ == "__main__":
    _main(sys.argv)
