"""The conductor's deterministic scheduler.

The conductor agent plans epics once (``/speckit.autopilot.epics``). From then
on plain code runs the show, as the design memo asks:

* ``plan_check``  validate the DAG, serialise overlapping epics, pre-assign
                  ``specs/NNN-slug`` directories and branches, render dag.md
* ``drive``       event-driven DAG execution: start each ready epic in its
                  own git worktree as soon as a slot is free, run the
                  ``autopilot-epic`` workflow there, merge passed epics one
                  at a time into an integration branch, re-verify after each
                  merge, block dependents of epics that did not make it
* ``land``        after the human approves, merge the integration branch
                  into the base branch

Caps: parallel pipes, wall time for the run and per pipe, agent-call budget
(a cost proxy: integration CLIs do not report spend uniformly), attempts.
A ``.specify/autopilot/STOP`` file stops new pipes from starting.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import dag as dag_mod
from . import team
from .config import configured_checks
from .gate import LOOP_END, checks_only
from .util import (
    GitError,
    append_jsonl,
    commit_all,
    dirty_paths,
    ensure_state_dir,
    git,
    git_ok,
    identity_args,
    is_clean,
    now_iso,
    read_json,
    run,
    write_json,
)

EPIC_WORKFLOW = "autopilot-epic"
FINAL = {"merged", "failed", "escalated", "blocked"}
SYNC_EXCLUDES = (".specify/autopilot", ".specify/workflows/runs", ".specify/feature.json")


class DriverError(RuntimeError):
    pass


def _state_path(root: Path) -> Path:
    return ensure_state_dir(root) / "state.json"


def load_state(root: Path) -> dict[str, Any]:
    state = read_json(_state_path(root))
    if state is None:
        raise DriverError("no autopilot plan: run `autopilot.py plan-check` after /speckit.autopilot.epics")
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    write_json(_state_path(root), state)


def log(root: Path, event: str, **fields: Any) -> None:
    append_jsonl(ensure_state_dir(root) / "log.jsonl", {"event": event, **fields})
    detail = " ".join(f"{k}={v}" for k, v in fields.items() if k not in ("detail",))
    print(f"[autopilot] {event} {detail}".rstrip(), file=sys.stderr, flush=True)


def _lock_path(root: Path) -> Path:
    return ensure_state_dir(root) / "drive.lock"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        # os.kill(pid, 0) is not a liveness probe on Windows; ask tasklist.
        out = run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], Path.cwd()).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def drive_owner(root: Path) -> dict[str, Any] | None:
    """The live drive holding the lock, or None (a stale lock is ignored)."""
    lock = read_json(_lock_path(root))
    if not isinstance(lock, dict) or not _pid_alive(int(lock.get("pid", 0))):
        return None
    return lock


def _acquire_lock(root: Path) -> None:
    owner = drive_owner(root)
    if owner is not None:
        raise DriverError(f"a drive is already running (pid {owner['pid']}, since {owner['started_at']})")
    write_json(_lock_path(root), {"pid": os.getpid(), "started_at": now_iso()})


def _release_lock(root: Path) -> None:
    lock = read_json(_lock_path(root))
    if isinstance(lock, dict) and lock.get("pid") == os.getpid():
        _lock_path(root).unlink(missing_ok=True)


def worst_case_calls(config: dict[str, Any]) -> int:
    # specify + plan + tasks, then implement + converge + review per iteration.
    # Plus a team-lead consult after specify, after design and in each iteration.
    return 5 + 4 * config["pipe"]["max_iterations"]


# ── preflight ────────────────────────────────────────────────────────────────


def preflight(root: Path, config: dict[str, Any], requirements: str, baseline: bool) -> tuple[int, dict[str, Any]]:
    problems: list[str] = []
    warnings: list[str] = []
    if not git_ok(root, "rev-parse", "--verify", "HEAD"):
        problems.append("not a git repository with at least one commit; the autopilot needs git worktrees")
        return 1, {"ok": False, "problems": problems}
    if not configured_checks(config):
        problems.append(
            "no gate checks configured in .specify/extensions/autopilot/autopilot-config.yml; "
            "run /speckit.autopilot.setup (or fill gate.checks with your test and lint commands)"
        )
    # Untracked Spec Kit / agent files are fine: they are copied into each worktree.
    dirty = dirty_paths(root, config["run"]["sync_paths"])
    if dirty:
        problems.append(
            "working tree has uncommitted changes (" + ", ".join(dirty[:5]) + (", ..." if len(dirty) > 5 else "")
            + "); pipes run in worktrees created from commits, so commit the requirements and any setup first"
        )
    if shutil.which(config["run"]["specify_command"]) is None:
        problems.append(f"`{config['run']['specify_command']}` is not on PATH (set run.specify_command)")
    if not (root / ".specify" / "workflows" / EPIC_WORKFLOW / "workflow.yml").is_file():
        problems.append(f"workflow '{EPIC_WORKFLOW}' is not installed: run `specify workflow add {EPIC_WORKFLOW}`")
    if requirements:
        req = root / requirements
        if not req.exists() or (req.is_dir() and not any(req.iterdir())):
            problems.append(f"requirements path '{requirements}' is missing or empty")
    state = read_json(root / ".specify" / "autopilot" / "state.json")
    if state and any(e["status"] not in ("pending",) for e in state["epics"].values()):
        warnings.append("an earlier autopilot run exists; plan-check will refuse to replace it without --reset")
    checks: list[dict[str, Any]] = []
    if baseline and not problems:
        checks = checks_only(root, config, None)
        failing = [c["name"] for c in checks if not c["passed"]]
        if failing:
            problems.append(
                "gate checks fail on the base commit before any change: " + ", ".join(failing)
                + ". The gate must be green on main first, or no epic can ever pass."
            )
    return (1 if problems else 0), {"ok": not problems, "problems": problems, "warnings": warnings, "baseline": checks}


# ── plan-check ───────────────────────────────────────────────────────────────


def _default_worktree_root(root: Path) -> Path:
    return root.parent / f"{root.name}.worktrees" / "autopilot"


def plan_check(root: Path, config: dict[str, Any], reset: bool = False) -> tuple[int, dict[str, Any]]:
    state_dir = ensure_state_dir(root)
    plan_path = state_dir / "epics.json"
    if not plan_path.is_file():
        return 1, {"ok": False, "problems": [f"{plan_path.relative_to(root)} not found; run /speckit.autopilot.epics"]}
    try:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
        epics = dag_mod.parse_plan(data)
    except json.JSONDecodeError as exc:
        return 1, {"ok": False, "problems": [f"epics.json is not valid JSON: {exc}"]}
    except dag_mod.PlanError as exc:
        return 1, {"ok": False, "problems": exc.problems}

    existing = read_json(state_dir / "state.json")
    if existing and not reset and any(e["status"] != "pending" for e in existing["epics"].values()):
        return 1, {"ok": False, "problems": [
            "an autopilot run is already in progress or finished; re-run with --reset to discard its state "
            "(branches and worktrees are left in place)"
        ]}

    notes = dag_mod.serialise_overlaps(epics)
    feature_dirs = dag_mod.assign_feature_dirs(epics, root / "specs")
    run_cfg = config["run"]
    base_branch = run_cfg["base_branch"] or git(root, "branch", "--show-current")
    if not base_branch:
        return 1, {"ok": False, "problems": ["HEAD is detached; check out the base branch or set run.base_branch"]}
    base_commit = git(root, "rev-parse", base_branch)
    worktree_root = Path(run_cfg["worktree_root"]).expanduser() if run_cfg["worktree_root"] else _default_worktree_root(root)
    if not worktree_root.is_absolute():
        worktree_root = (root / worktree_root).resolve()

    problems = []
    program = state_dir / "program.md"
    if not program.is_file() or not program.read_text(encoding="utf-8").strip():
        problems.append(
            "program.md (the lead's team handbook) is missing; every developer reads it before working, "
            "so /speckit.autopilot.epics must write it"
        )
    epic_states: dict[str, dict[str, Any]] = {}
    for epic in epics:
        dir_name = Path(feature_dirs[epic.id]).name
        branch = f"{run_cfg['branch_prefix']}{dir_name}"
        if git_ok(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}") and not reset:
            problems.append(f"branch {branch} already exists")
        epic_states[epic.id] = {
            "id": epic.id,
            "slug": epic.slug,
            "title": epic.title,
            "brief": epic.brief(),
            "depends_on": epic.depends_on,
            "added_dependencies": epic.added_dependencies,
            "touches": epic.touches,
            "provides": epic.provides,
            "feature_dir": feature_dirs[epic.id],
            "branch": branch,
            "worktree": str(worktree_root / dir_name),
            "status": "pending",
            "attempts": 0,
            "run_id": None,
            "base_commit": None,
            "iterations": 0,
            "agent_calls": 0,
            "reason": "",
            "started_at": None,
            "finished_at": None,
            "merged_commit": None,
        }
    integration_branch = run_cfg["integration_branch"]
    if git_ok(root, "show-ref", "--verify", "--quiet", f"refs/heads/{integration_branch}") and not reset:
        problems.append(f"integration branch {integration_branch} already exists; delete it or pass --reset")
    if problems:
        return 1, {"ok": False, "problems": problems}

    order = [epic.id for epic in dag_mod.topological_order(epics)]
    state = {
        "schema": 1,
        "created_at": now_iso(),
        "started_at": None,
        "base_branch": base_branch,
        "base_commit": base_commit,
        "integration_branch": integration_branch,
        "integration_worktree": str(worktree_root / "_integration"),
        "worktree_root": str(worktree_root),
        "agent_calls_used": 0,
        "notes": notes,
        "order": order,
        "epics": epic_states,
    }
    save_state(root, state)
    (state_dir / "dag.md").write_text(
        render_dag(state, dag_mod.waves(epics), program.read_text(encoding="utf-8")), encoding="utf-8"
    )
    return 0, {"ok": True, "epics": len(order), "waves": dag_mod.waves(epics), "notes": notes,
               "dag": str((state_dir / "dag.md").relative_to(root))}


def render_dag(state: dict[str, Any], wave_list: list[list[str]], program: str = "") -> str:
    epics = state["epics"]
    lines = [
        "# Autopilot epic plan",
        "",
        f"Base: `{state['base_branch']}` @ `{state['base_commit'][:12]}` → integration branch "
        f"`{state['integration_branch']}`. Worktrees under `{state['worktree_root']}`.",
        "",
        "Approve to let the pipes run unattended. Nothing reaches the base branch until the final merge gate.",
        "",
        "| Wave | Epic | Title | Feature dir | Depends on | Touches |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for number, wave in enumerate(wave_list, start=1):
        for epic_id in wave:
            epic = epics[epic_id]
            deps = ", ".join(
                f"{d}{' (added)' if d in epic['added_dependencies'] else ''}" for d in epic["depends_on"]
            ) or "—"
            touches = ", ".join(f"`{t}`" for t in epic["touches"]) or "_undeclared_"
            lines.append(f"| {number} | {epic_id} | {epic['title']} | `{epic['feature_dir']}` | {deps} | {touches} |")
    if state["notes"]:
        lines += ["", "## Dependencies added to keep overlapping epics apart", ""]
        lines += [f"- {note}" for note in state["notes"]]
    if program.strip():
        handbook = program.strip().splitlines()
        lines += ["", "## Team handbook (program.md)", "",
                  "Every developer reads this before every step.", ""]
        lines += [("#" + line if line.startswith("#") else line) for line in handbook]
    lines += ["", "```mermaid", "graph LR"]
    for epic_id in state["order"]:
        lines.append(f"  {epic_id}[\"{epic_id}: {epics[epic_id]['title'][:40]}\"]")
        for dep in epics[epic_id]["depends_on"]:
            lines.append(f"  {dep} --> {epic_id}")
    lines += ["```", ""]
    for epic_id in state["order"]:
        lines += [f"## {epic_id} brief", "", "```text", epics[epic_id]["brief"], "```", ""]
    return "\n".join(lines)


# ── worktrees ────────────────────────────────────────────────────────────────


def _sync_untracked(root: Path, worktree: Path, paths: list[str]) -> int:
    """Copy agent/Spec Kit files the worktree lacks (untracked or ignored in git)."""
    copied = 0
    for rel in paths:
        source = root / rel
        if not source.exists():
            continue
        files = [source] if source.is_file() else [p for p in source.rglob("*") if p.is_file()]
        for path in files:
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() or any(relative == ex or relative.startswith(ex + "/") for ex in SYNC_EXCLUDES):
                continue
            target = worktree / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                copied += 1
    return copied


def ensure_integration(root: Path, state: dict[str, Any], config: dict[str, Any]) -> Path:
    branch = state["integration_branch"]
    path = Path(state["integration_worktree"])
    if not git_ok(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"):
        git(root, "branch", branch, state["base_commit"])
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        git(root, "worktree", "add", "-q", str(path), branch)
        _sync_untracked(root, path, config["run"]["sync_paths"])
        _setup_worktree(root, path, config, "integration")
    return path


def _setup_worktree(root: Path, path: Path, config: dict[str, Any], label: str) -> None:
    command = str(config["run"].get("setup") or "").strip()
    if command:
        result = run(command, path, shell=True, timeout=config["gate"]["check_timeout_seconds"])
        if result.returncode != 0:
            raise DriverError(f"run.setup failed in {label} worktree ({result.returncode}): {(result.stderr or result.stdout)[-800:]}")


def prepare_epic_worktree(root: Path, state: dict[str, Any], epic: dict[str, Any], config: dict[str, Any]) -> None:
    path = Path(epic["worktree"])
    integration_head = git(root, "rev-parse", state["integration_branch"])
    if not git_ok(root, "show-ref", "--verify", "--quiet", f"refs/heads/{epic['branch']}"):
        git(root, "branch", epic["branch"], integration_head)
        epic["base_commit"] = integration_head
    elif not epic.get("base_commit"):
        epic["base_commit"] = git(root, "merge-base", epic["branch"], state["integration_branch"])
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        git(root, "worktree", "add", "-q", str(path), epic["branch"])
        _sync_untracked(root, path, config["run"]["sync_paths"])
        ensure_state_dir(path)
        _setup_worktree(root, path, config, epic["id"])


# ── pipes ────────────────────────────────────────────────────────────────────


def _pipe_state(epic: dict[str, Any]) -> dict[str, Any] | None:
    return read_json(Path(epic["worktree"]) / ".specify" / "autopilot" / "pipes" / Path(epic["feature_dir"]).name / "pipe.json")


def _latest_run(worktree: Path) -> tuple[str | None, str | None]:
    runs = worktree / ".specify" / "workflows" / "runs"
    best: tuple[float, str, str] | None = None
    if runs.is_dir():
        for state_file in runs.glob("*/state.json"):
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("workflow_id") == EPIC_WORKFLOW:
                stamp = state_file.stat().st_mtime
                if best is None or stamp > best[0]:
                    best = (stamp, data.get("run_id"), data.get("status"))
    return (best[1], best[2]) if best else (None, None)


def run_pipe(root: Path, epic: dict[str, Any], config: dict[str, Any], integration: str) -> dict[str, Any]:
    """Run (or resume) one epic's workflow in its worktree. Thread-safe: touches only its worktree."""
    worktree = Path(epic["worktree"])
    existing = _pipe_state(epic)
    if existing and existing.get("status") in LOOP_END:
        return {"pipe": existing, "exit_code": 0, "run_id": epic.get("run_id"), "run_status": "completed", "skipped": True}
    run_id, run_status = _latest_run(worktree)
    specify = config["run"]["specify_command"]
    feature = worktree / epic["feature_dir"]
    if run_id and run_status not in ("completed", "aborted") and not epic.get("fresh_build"):
        # Interrupted or crashed mid-run: the engine replays completed steps and
        # retries the unfinished one.
        command = [specify, "workflow", "resume", run_id, "--json"]
    else:
        # A new run, resuming at the first missing artifact so /speckit.specify
        # never overwrites an existing spec (after a reset, an answered question,
        # or a crash before the run was recorded).
        if (feature / "tasks.md").is_file():
            phase = "build"
        elif (feature / "spec.md").is_file():
            phase = "design"
        else:
            phase = "full"
        command = [specify, "workflow", "run", EPIC_WORKFLOW, "--json",
                   "--input", f"brief={epic['brief']}", "--input", f"phase={phase}"]
        if integration:
            command += ["--input", f"integration={integration}"]
        for key in ("reviewer_model", "lead_model"):
            if config["run"][key]:
                command += ["--input", f"{key}={config['run'][key]}"]
    env = {
        "SPECIFY_FEATURE_DIRECTORY": epic["feature_dir"],
        "SPECIFY_FEATURE": epic["branch"],
        "GIT_BRANCH_NAME": epic["branch"],
        "AUTOPILOT_EPIC": epic["id"],
        "AUTOPILOT_BASE": epic["base_commit"] or "",
        # The lead's handbook and the shared decision log live in the main checkout.
        "AUTOPILOT_ROOT": str(root),
    }
    result = run(command, worktree, timeout=config["pipe"]["timeout_minutes"] * 60, env=env)
    logs = ensure_state_dir(root) / "logs"
    logs.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    (logs / f"{epic['id']}-{stamp}.log").write_text(
        f"$ {' '.join(command[:4])} ...\nexit {result.returncode}\n\n--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}\n",
        encoding="utf-8",
    )
    payload: dict[str, Any] = {}
    for line in reversed(result.stdout.strip().splitlines()):
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "run_id" in candidate:
            payload = candidate
            break
    if not payload:
        start = result.stdout.find("{")
        try:
            payload = json.loads(result.stdout[start:]) if start >= 0 else {}
        except json.JSONDecodeError:
            payload = {}
    latest_id, latest_status = _latest_run(worktree)
    return {
        "pipe": _pipe_state(epic),
        "exit_code": result.returncode,
        "run_id": payload.get("run_id") or latest_id,
        "run_status": payload.get("status") or latest_status,
        "timed_out": result.returncode == -1,
        "error": payload.get("error") or (result.stderr.strip()[-500:] if result.returncode else ""),
    }


# ── merge discipline ─────────────────────────────────────────────────────────


def _verify(path: Path, config: dict[str, Any], feature_dir: str) -> list[str]:
    results = checks_only(path, config, path / feature_dir)
    return [f"{r['name']}: {r['summary']}" for r in results if not r["passed"]]


def merge_epic(root: Path, state: dict[str, Any], epic: dict[str, Any], config: dict[str, Any]) -> tuple[bool, str]:
    """Merge one passed epic into the integration branch, re-verifying after."""
    integration = ensure_integration(root, state, config)
    worktree = Path(epic["worktree"])
    message = f"autopilot: merge {epic['id']} {epic['title']} ({epic['feature_dir']})"
    before = git(integration, "rev-parse", "HEAD")

    def attempt() -> bool:
        ok = git_ok(integration, *identity_args(integration), "merge", "--no-ff", "--no-edit", "-m", message, epic["branch"])
        if not ok:
            git(integration, "merge", "--abort", check=False)
        return ok

    if not attempt():
        # Rebase the epic onto the moved integration branch, re-verify it, retry once.
        if not git_ok(worktree, *identity_args(worktree), "rebase", "-q", state["integration_branch"]):
            git(worktree, "rebase", "--abort", check=False)
            return False, f"merge conflict with {state['integration_branch']} and rebase failed; resolve in {worktree}"
        failing = _verify(worktree, config, epic["feature_dir"])
        if failing:
            return False, "checks fail after rebasing onto the integration branch: " + "; ".join(failing)
        if not attempt():
            return False, "merge still conflicts after a clean rebase"
    failing = _verify(integration, config, epic["feature_dir"])
    if failing:
        git(integration, "reset", "-q", "--hard", before)
        return False, "integration checks failed after merge (merge reverted): " + "; ".join(failing)
    epic["merged_commit"] = git(integration, "rev-parse", "HEAD")
    return True, f"merged at {epic['merged_commit'][:12]}"


# ── drive ────────────────────────────────────────────────────────────────────


def _block_dependents(root: Path, state: dict[str, Any]) -> None:
    changed = True
    while changed:
        changed = False
        for epic in state["epics"].values():
            if epic["status"] != "pending":
                continue
            bad = [d for d in epic["depends_on"] if state["epics"][d]["status"] in ("failed", "escalated", "blocked")]
            if bad:
                epic["status"] = "blocked"
                epic["reason"] = "dependency did not merge: " + ", ".join(bad)
                epic["finished_at"] = now_iso()
                log(root, "blocked", epic=epic["id"], reason=epic["reason"])
                changed = True


def _resume_answered(root: Path, state: dict[str, Any]) -> None:
    """Epics whose product-owner questions are all answered go back in the queue."""
    for epic in state["epics"].values():
        if epic["status"] != "awaiting-human" or not team.all_answered(Path(epic["worktree"]), epic["feature_dir"]):
            continue
        pipe_file = Path(epic["worktree"]) / ".specify" / "autopilot" / "pipes" / Path(epic["feature_dir"]).name / "pipe.json"
        pipe = read_json(pipe_file)
        if pipe and pipe.get("status") == "awaiting-human":
            pipe.update(status="running", reason="answered by the product owner")
            write_json(pipe_file, pipe)
        epic.update(status="pending", reason="answered by the product owner", fresh_build=True)
        log(root, "answered", epic=epic["id"])


def _checkouts(root: Path) -> list[tuple[str | None, Path]]:
    """Every checkout that can hold pipe questions: epic worktrees, then this one."""
    state = read_json(ensure_state_dir(root) / "state.json")
    epics = [(e["id"], Path(e["worktree"])) for e in state["epics"].values()] if state else []
    return [*epics, (None, root)]


def human_questions(root: Path) -> list[dict[str, Any]]:
    return team.open_human_questions(_checkouts(root))


def answer(root: Path, question_id: str, text: str) -> tuple[int, dict[str, Any]]:
    try:
        result = team.answer_question(_checkouts(root), question_id, text)
    except team.TeamError as exc:
        return 1, {"ok": False, "error": str(exc)}
    still_open = [q["id"] for q in human_questions(root)]
    return 0, {**result, "drive_running": drive_owner(root) is not None, "still_open": still_open}


def _ready(state: dict[str, Any], epic: dict[str, Any]) -> bool:
    return epic["status"] in ("pending", "running") and all(
        state["epics"][d]["status"] == "merged" for d in epic["depends_on"]
    )


def drive(root: Path, config: dict[str, Any], integration: str = "", pipe_runner=run_pipe) -> tuple[int, dict[str, Any]]:
    """Run the DAG to completion. Only one drive per checkout: a pid lock guards it."""
    load_state(root)  # fail before locking when there is no plan
    _acquire_lock(root)
    try:
        return _drive(root, config, integration, pipe_runner)
    finally:
        _release_lock(root)


def drive_detached(root: Path, cli: Path, integration: str) -> tuple[int, dict[str, Any]]:
    """Start ``drive`` as a background process that outlives the calling agent's shell."""
    import subprocess

    load_state(root)
    owner = drive_owner(root)
    if owner is not None:
        return 0, {"started": False, "already_running": True, **owner}
    out_path = ensure_state_dir(root) / "drive.out"
    command = [sys.executable, str(cli), "drive"]
    if integration:
        command += ["--integration", integration]
    kwargs: dict[str, Any] = {"cwd": str(root), "stdin": subprocess.DEVNULL, "stderr": subprocess.STDOUT}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        kwargs["start_new_session"] = True
    with out_path.open("ab") as out:
        process = subprocess.Popen(command, stdout=out, **kwargs)
    # Give the child a moment to take the lock or fail fast (no plan, bad config).
    for _ in range(20):
        if drive_owner(root) is not None or process.poll() is not None:
            break
        time.sleep(0.25)
    if process.poll() not in (None, 0):
        return 1, {"started": False, "error": f"drive exited with {process.returncode}; see {out_path.relative_to(root)}"}
    return 0, {"started": True, "pid": process.pid, "output": str(out_path.relative_to(root))}


def stop_file(root: Path) -> Path:
    return root / ".specify" / "autopilot" / "STOP"


def _drive(root: Path, config: dict[str, Any], integration: str, pipe_runner) -> tuple[int, dict[str, Any]]:
    state = load_state(root)
    if state["started_at"] is None:
        state["started_at"] = now_iso()
    started = datetime.fromisoformat(state["started_at"])
    deadline = started.timestamp() + config["run"]["timeout_minutes"] * 60
    integration = integration if integration and integration != "auto" else config["run"]["integration"]
    ensure_integration(root, state, config)
    save_state(root, state)
    log(root, "drive", epics=len(state["order"]), max_parallel=config["run"]["max_parallel"])

    stop = stop_file(root)
    reserved: dict[str, int] = {}
    running: dict[Future, str] = {}
    halted = ""
    with ThreadPoolExecutor(max_workers=config["run"]["max_parallel"]) as pool:
        while True:
            _block_dependents(root, state)
            _resume_answered(root, state)
            if stop.exists():
                halted = halted or "STOP file present"
            elif time.time() > deadline:
                halted = halted or f"run timeout ({config['run']['timeout_minutes']} min)"
            if not halted:
                for epic_id in state["order"]:
                    if len(running) >= config["run"]["max_parallel"]:
                        break
                    epic = state["epics"][epic_id]
                    if epic_id in running.values() or not _ready(state, epic):
                        continue
                    cost = worst_case_calls(config)
                    if state["agent_calls_used"] + sum(reserved.values()) + cost > config["run"]["max_agent_calls"]:
                        halted = f"agent-call budget ({config['run']['max_agent_calls']}) would be exceeded"
                        break
                    try:
                        prepare_epic_worktree(root, state, epic, config)
                    except (GitError, DriverError, OSError) as exc:
                        epic.update(status="escalated", reason=f"worktree setup failed: {exc}", finished_at=now_iso())
                        log(root, "escalated", epic=epic_id, reason=epic["reason"])
                        continue
                    if epic["status"] == "pending":
                        epic["attempts"] += 1
                        epic["started_at"] = epic["started_at"] or now_iso()
                    epic["status"] = "running"
                    # Onboarding brief, regenerated at every launch so it shows who is
                    # working in parallel now and the latest decisions.
                    team.write_epic_context(root, Path(epic["worktree"]), state, epic_id)
                    reserved[epic_id] = cost
                    running[pool.submit(pipe_runner, root, dict(epic), config, integration)] = epic_id
                    log(root, "start", epic=epic_id, attempt=epic["attempts"], worktree=epic["worktree"])
                save_state(root, state)
            if halted and halted != state.get("halted"):
                state["halted"] = halted
                log(root, "halt", reason=halted)
                save_state(root, state)
            if not running:
                break
            done, _ = wait(list(running), timeout=60, return_when=FIRST_COMPLETED)
            for future in done:
                epic_id = running.pop(future)
                reserved.pop(epic_id, None)
                epic = state["epics"][epic_id]
                try:
                    outcome = future.result()
                except Exception as exc:  # noqa: BLE001 - a crashed runner must not stop the others
                    outcome = {"pipe": None, "exit_code": 1, "error": f"pipe runner crashed: {exc}"}
                _settle(root, state, epic, outcome, config)
                save_state(root, state)

    _block_dependents(root, state)
    save_state(root, state)
    summary = status_summary(state)
    log(root, "drive-finished", **{k: v for k, v in summary["counts"].items()})
    return 0, summary


def _settle(root: Path, state: dict[str, Any], epic: dict[str, Any], outcome: dict[str, Any], config: dict[str, Any]) -> None:
    pipe = outcome.get("pipe") or {}
    epic.pop("fresh_build", None)
    epic["run_id"] = outcome.get("run_id") or epic.get("run_id")
    epic["iterations"] = pipe.get("iteration", epic["iterations"])
    calls = pipe.get("agent_calls", 3 if outcome.get("exit_code") else 0)
    state["agent_calls_used"] += max(0, calls - epic.get("agent_calls", 0))
    epic["agent_calls"] = max(calls, epic.get("agent_calls", 0))
    pipe_status = pipe.get("status")
    if pipe_status == "passed":
        try:
            committed = commit_all(Path(epic["worktree"]), f"autopilot: {epic['id']} {epic['title']}",
                                   config["run"]["sync_paths"])
        except GitError as exc:
            epic.update(status="escalated", reason=f"commit failed (hooks?): {exc}", finished_at=now_iso())
            log(root, "escalated", epic=epic["id"], reason=epic["reason"])
            return
        epic["status"] = "passed"
        log(root, "passed", epic=epic["id"], iterations=epic["iterations"], committed=committed)
        merged, reason = merge_epic(root, state, epic, config)
        epic["status"] = "merged" if merged else "escalated"
        epic["reason"] = reason
        epic["finished_at"] = now_iso()
        log(root, epic["status"], epic=epic["id"], reason=reason)
        return
    if pipe_status == "awaiting-human":
        # Only this developer waits; the slot frees and the rest of the team continues.
        epic.update(status="awaiting-human", reason=pipe.get("reason", ""))
        log(root, "question", epic=epic["id"], reason=epic["reason"])
        return
    if pipe_status in ("failed", "escalated"):
        epic.update(status=pipe_status, reason=pipe.get("reason", ""), finished_at=now_iso())
    elif outcome.get("timed_out"):
        epic.update(status="failed", reason=f"pipe timeout ({config['pipe']['timeout_minutes']} min)", finished_at=now_iso())
    elif outcome.get("run_status") == "paused":
        epic.update(status="escalated", reason="pipe workflow paused for input; resume it in the worktree", finished_at=now_iso())
    elif epic["attempts"] < config["pipe"]["max_attempts"]:
        epic.update(status="pending", reason=f"retrying after: {outcome.get('error', 'pipe exited early')}")
        log(root, "retry", epic=epic["id"], attempt=epic["attempts"])
        return
    else:
        epic.update(status="failed", reason=outcome.get("error") or "pipe exited without a gate decision", finished_at=now_iso())
    log(root, epic["status"], epic=epic["id"], reason=epic["reason"])


# ── status, report, land, reset ──────────────────────────────────────────────


def run_status(root: Path) -> dict[str, Any]:
    """Everything an agent needs to decide the next step, in one call."""
    state = read_json(ensure_state_dir(root) / "state.json")
    owner = drive_owner(root)
    if state is None:
        has_plan = (root / ".specify" / "autopilot" / "epics.json").is_file()
        return {"stage": "planned-unchecked" if has_plan else "no-plan", "drive_running": False}
    summary = status_summary(state)
    questions = human_questions(root)
    if state.get("landed_commit"):
        stage = "landed"
    elif owner is not None:
        stage = "driving"
    elif questions:
        stage = "awaiting-human"
    elif summary["finished"] or state.get("halted"):
        stage = "awaiting-land" if summary["counts"].get("merged") else "finished-nothing-merged"
    elif state["started_at"] is None:
        stage = "awaiting-plan-approval"
    else:
        stage = "interrupted"  # started, not finished, no live drive
    log_path = root / ".specify" / "autopilot" / "log.jsonl"
    recent = log_path.read_text(encoding="utf-8").splitlines()[-15:] if log_path.is_file() else []
    return {
        "stage": stage,
        "drive_running": owner is not None,
        "drive_pid": owner["pid"] if owner else None,
        "stop_requested": stop_file(root).exists(),
        "questions_for_human": questions,
        **summary,
        "recent_events": [json.loads(line) for line in recent if line.strip()],
    }


def status_summary(state: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for epic in state["epics"].values():
        counts[epic["status"]] = counts.get(epic["status"], 0) + 1
    return {
        "counts": counts,
        "agent_calls_used": state["agent_calls_used"],
        "halted": state.get("halted", ""),
        "epics": [
            {k: state["epics"][i][k] for k in ("id", "status", "feature_dir", "branch", "iterations", "reason")}
            for i in state["order"]
        ],
        "finished": all(e["status"] in FINAL for e in state["epics"].values()),
    }


def report(root: Path, config: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    state = load_state(root)
    summary = status_summary(state)
    merged = [e for e in summary["epics"] if e["status"] == "merged"]
    lines = [
        "# Autopilot run report",
        "",
        f"Base `{state['base_branch']}` · integration `{state['integration_branch']}` · "
        f"agent calls used ≈ {state['agent_calls_used']} / {config['run']['max_agent_calls']}",
        "",
    ]
    if summary["halted"]:
        lines += [f"> Halted early: {summary['halted']}", ""]
    lines += ["| Epic | Status | Iterations | Feature dir | Branch | Note |", "| --- | --- | --- | --- | --- | --- |"]
    for epic in summary["epics"]:
        lines.append(
            f"| {epic['id']} | **{epic['status']}** | {epic['iterations']} | `{epic['feature_dir']}` | "
            f"`{epic['branch']}` | {epic['reason'].replace('|', '/')[:200]} |"
        )
    lines += ["", "## Final merge", ""]
    if merged:
        lines.append(
            f"Approving merges `{state['integration_branch']}` ({len(merged)} epic(s)) into `{state['base_branch']}` "
            "with a merge commit. Inspect it first with "
            f"`git log --oneline {state['base_branch']}..{state['integration_branch']}`."
        )
    else:
        lines.append("No epic merged, so there is nothing to land. Reject to end the run.")
    questions = human_questions(root)
    if questions:
        lines += ["", "## Questions for the product owner", "",
                  "These developers wait for a product decision; the rest of the team continued. Answer each "
                  "(`autopilot.py answer <id> --text ...`, or `/speckit.autopilot.run` in chat), then drive again.", ""]
        for question in questions:
            options = "; ".join(question["options"]) or "open"
            lines.append(f"- **{question['id']}** ({question['epic']}): {question['question']} Options: {options}. "
                         f"Lead recommends: {question['lead_recommendation'] or '—'}.")
    stuck = [e for e in summary["epics"] if e["status"] in ("failed", "escalated", "blocked")]
    if stuck:
        lines += [
            "",
            "## Needs a human",
            "",
            "Each pipe's worktree, gate reports (`.specify/autopilot/pipes/<feature>/gate-N.md`) and reviews are kept. "
            "After fixing the cause, `autopilot.py reset <EPIC>` puts an epic (and the epics it blocked) back to "
            "pending and `autopilot.py drive` continues the run.",
            "",
        ]
        for epic in stuck:
            lines.append(f"- **{epic['id']}** ({epic['status']}): {epic['reason']}")
    path = ensure_state_dir(root) / "report.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0, {**summary, "report": str(path.relative_to(root))}


def land(root: Path, config: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    state = load_state(root)
    merged = [e for e in state["epics"].values() if e["status"] == "merged"]
    if not merged:
        return 0, {"landed": False, "reason": "no merged epics"}
    current = git(root, "branch", "--show-current")
    if current != state["base_branch"]:
        return 1, {"landed": False, "reason": f"check out {state['base_branch']} first (on {current or 'detached HEAD'})"}
    if not is_clean(root):
        return 1, {"landed": False, "reason": "working tree has uncommitted changes"}
    message = f"autopilot: land {len(merged)} epic(s): " + ", ".join(e["id"] for e in merged)
    if not git_ok(root, *identity_args(root), "merge", "--no-ff", "-m", message, state["integration_branch"]):
        git(root, "merge", "--abort", check=False)
        return 1, {"landed": False, "reason": f"merge of {state['integration_branch']} conflicts; merge it by hand"}
    state["landed_commit"] = git(root, "rev-parse", "HEAD")
    save_state(root, state)
    return 0, {"landed": True, "commit": state["landed_commit"], "epics": [e["id"] for e in merged]}


def reset_epic(root: Path, config: dict[str, Any], epic_id: str) -> tuple[int, dict[str, Any]]:
    state = load_state(root)
    if epic_id not in state["epics"]:
        return 1, {"ok": False, "reason": f"unknown epic {epic_id}"}
    if state["epics"][epic_id]["status"] == "merged":
        return 1, {"ok": False, "reason": f"{epic_id} is already merged"}
    # The epic itself plus every blocked epic downstream of it.
    targets = [epic_id]
    for candidate in state["order"]:
        epic = state["epics"][candidate]
        if epic["status"] == "blocked" and any(dep in targets for dep in epic["depends_on"]):
            targets.append(candidate)
    for target in targets:
        epic = state["epics"][target]
        pipe_file = Path(epic["worktree"]) / ".specify" / "autopilot" / "pipes" / Path(epic["feature_dir"]).name / "pipe.json"
        pipe = read_json(pipe_file)
        if pipe and pipe.get("status") in LOOP_END:
            # Re-open the pipe with a fresh iteration allowance on top of what it
            # used; the marker stops stuck-detection comparing against old failures.
            pipe.update(status="running", reason="reset by human",
                        max_iterations=pipe["iteration"] + config["pipe"]["max_iterations"])
            pipe.setdefault("history", []).append({"reset": True, "at": now_iso()})
            write_json(pipe_file, pipe)
        epic.update(status="pending", reason="reset by human", attempts=0, finished_at=None,
                    fresh_build=pipe is not None)
    reset = targets
    state.pop("halted", None)
    save_state(root, state)
    return 0, {"ok": True, "reset": reset}
