"""The per-epic janitor gate.

A pipe leaves its loop only through this module. The checks are concrete:

* ``spec-clarity``        no ``[NEEDS CLARIFICATION`` markers left in spec.md
* ``tasks-complete``      no unchecked task in tasks.md (so the last
                          ``/speckit.converge`` pass appended nothing)
* each ``gate.checks``    the project's own test/lint/type commands exit 0
* ``acceptance-coverage`` every acceptance scenario ID appears in a test file
                          (and its ``scenario_command`` passes, when configured)

When those pass, an independent reviewer agent grades the diff against the
spec. ``decide`` reads its JSON verdict; blocker/major findings fail the
iteration regardless of the verdict the reviewer declared. The implementer's
own opinion that it is done never counts.

Failures become new tasks appended to tasks.md (append-only, like converge)
so ``/speckit.implement`` picks them up on the next iteration. Hard caps
(iterations) and repeated-identical-failure detection end the loop.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import spec as spec_mod
from .config import configured_checks
from .util import (
    ensure_state_dir,
    exclude_pathspecs,
    git,
    now_iso,
    read_json,
    run,
    stage_changes,
    tree_fingerprint,
    write_json,
)

TERMINAL = {"passed", "failed", "escalated"}
# The pipe stopped to wait for the product owner; the epic resumes once answered.
PAUSED = {"awaiting-human"}
LOOP_END = TERMINAL | PAUSED
BLOCKING_SEVERITIES = {"blocker", "major"}
VALID_SEVERITIES = {"blocker", "major", "minor", "nit"}
DETAIL_LIMIT = 6000
MAX_SCAN_BYTES = 2_000_000


@dataclass
class CheckResult:
    name: str
    passed: bool
    summary: str
    detail: str = ""
    remediation: list[str] = field(default_factory=list)


class GateError(RuntimeError):
    pass


# ── pipe state ───────────────────────────────────────────────────────────────


def pipe_dir(project_root: Path, feature_dir: Path) -> Path:
    return ensure_state_dir(project_root) / "pipes" / feature_dir.name


def _rel(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_pipe(project_root: Path, feature_dir: Path) -> dict[str, Any] | None:
    return read_json(pipe_dir(project_root, feature_dir) / "pipe.json")


def save_pipe(project_root: Path, feature_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    state["agent_calls"] = (
        3 + 2 * state.get("iteration", 0) + state.get("reviews", 0) + state.get("consults", 0)
    )
    write_json(pipe_dir(project_root, feature_dir) / "pipe.json", state)


def ensure_pipe(project_root: Path, config: dict[str, Any], feature_dir: Path) -> dict[str, Any]:
    """Load the pipe state, creating it (base commit, caps) on first use."""
    state = load_pipe(project_root, feature_dir)
    if state is None:
        base = os.environ.get("AUTOPILOT_BASE", "").strip() or git(project_root, "rev-parse", "HEAD")
        state = {
            "schema": 1,
            "epic_id": os.environ.get("AUTOPILOT_EPIC", "").strip() or None,
            "feature_dir": _rel(project_root, feature_dir),
            "base": base,
            "created_at": now_iso(),
            "iteration": 0,
            "reviews": 0,
            "consults": 0,
            "max_iterations": config["pipe"]["max_iterations"],
            "status": "running",
            "reason": "",
            "history": [],
        }
        save_pipe(project_root, feature_dir, state)
    return state


def _finish(state: dict[str, Any], status: str, reason: str) -> None:
    state["status"] = status
    state["reason"] = reason
    state["finished_at"] = now_iso()


# ── check-spec ───────────────────────────────────────────────────────────────


def check_spec(project_root: Path, config: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    feature_dir = spec_mod.resolve_feature_dir(project_root)
    spec_path = feature_dir / "spec.md"
    if not spec_path.is_file():
        raise GateError(f"{_rel(project_root, spec_path)} does not exist; /speckit.specify did not produce a spec")
    text = spec_path.read_text(encoding="utf-8")
    scenarios = spec_mod.parse_scenarios(text, spec_mod.feature_number(feature_dir))
    markers = spec_mod.clarification_markers(text)

    state = ensure_pipe(project_root, config, feature_dir)
    state["scenarios"] = [s.tag for s in scenarios]
    if state["status"] in PAUSED:
        # A spec question went to the product owner; consult already said so.
        return 1, {"ok": False, "feature_dir": state["feature_dir"], "problems": [state["reason"]]}

    problems = []
    if markers:
        problems.append(
            f"spec.md still has {markers} [NEEDS CLARIFICATION] marker(s); an unattended run "
            "cannot answer them. Resolve them (or run /speckit.clarify) and re-run the pipe."
        )
    if not scenarios and config["gate"]["acceptance"]["required"]:
        problems.append(
            "spec.md has no numbered acceptance scenarios under '**Acceptance Scenarios**:' "
            "in any '### User Story N' section, so the gate has nothing to verify."
        )
    if problems:
        _finish(state, "escalated", " ".join(problems))
        save_pipe(project_root, feature_dir, state)
        return 1, {"ok": False, "feature_dir": state["feature_dir"], "problems": problems}

    save_pipe(project_root, feature_dir, state)
    tags = [s.tag for s in scenarios]
    hint = (
        "Acceptance scenario IDs: " + ", ".join(tags) + ". Every acceptance test must contain its "
        "scenario ID in the test name or a comment (for example `" + (tags[0] if tags else "") + "` or `"
        + (tags[0].replace("-", "_").lower() if tags else "") + "`)."
    ) if tags else ""
    return 0, {"ok": True, "feature_dir": state["feature_dir"], "scenarios": tags, "tag_hint": hint}


# ── checks ───────────────────────────────────────────────────────────────────


def _tail(text: str, limit: int = DETAIL_LIMIT) -> str:
    text = text.strip()
    return text if len(text) <= limit else "…" + text[-limit:]


def _candidate_test_files(project_root: Path, globs: list[str], feature_dir: Path) -> list[Path]:
    listed = run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"], project_root
    ).stdout.splitlines()
    feature_rel = _rel(project_root, feature_dir)
    patterns = []
    for pattern in globs:
        patterns.append(pattern)
        if pattern.startswith("**/"):
            patterns.append(pattern[3:])  # "**/x" also matches at the root
    files = []
    for rel in listed:
        if rel.startswith((".specify/", "specs/", feature_rel + "/")):
            continue  # specs and task lists mention the IDs; they are not tests
        if any(fnmatch.fnmatchcase(rel, pattern) for pattern in patterns):
            path = project_root / rel
            if path.is_file():
                files.append(path)
    return files


def check_acceptance(project_root: Path, config: dict[str, Any], feature_dir: Path) -> CheckResult:
    acceptance = config["gate"]["acceptance"]
    spec_path = feature_dir / "spec.md"
    scenarios = spec_mod.parse_scenarios(
        spec_path.read_text(encoding="utf-8") if spec_path.is_file() else "",
        spec_mod.feature_number(feature_dir),
    )
    if not scenarios:
        passed = not acceptance["required"]
        return CheckResult("acceptance-coverage", passed, "spec.md has no acceptance scenarios")
    remaining = {s.tag: s for s in scenarios}
    for path in _candidate_test_files(project_root, list(acceptance["test_globs"]), feature_dir):
        if not remaining:
            break
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for tag in [tag for tag, s in remaining.items() if s.pattern().search(text)]:
            del remaining[tag]
    problems: list[str] = []
    remediation: list[str] = []
    for tag, scenario in remaining.items():
        problems.append(f"{tag}: no test file mentions this scenario ID")
        remediation.append(
            f"Add an automated acceptance test for scenario {tag} ({scenario.text[:160]}); "
            f"put the ID `{tag}` in the test name or a comment so the autopilot gate can trace it"
        )
    command = str(acceptance.get("scenario_command") or "").strip()
    if command and not remaining:
        timeout = config["gate"]["check_timeout_seconds"]
        for scenario in scenarios:
            concrete = command.replace("{tag}", scenario.tag).replace(
                "{tag_underscore}", scenario.tag.replace("-", "_").lower()
            )
            result = run(concrete, project_root, shell=True, timeout=timeout)
            if result.returncode != 0:
                problems.append(f"{scenario.tag}: `{concrete}` exited {result.returncode}\n{_tail(result.stdout + result.stderr, 1500)}")
                remediation.append(f"Make the acceptance test for {scenario.tag} pass (`{concrete}` exits {result.returncode})")
    covered = len(scenarios) - len(remaining)
    return CheckResult(
        "acceptance-coverage",
        not problems,
        f"{covered}/{len(scenarios)} scenarios traced to tests" + (f", {len(problems)} problem(s)" if problems else ""),
        "\n".join(problems),
        remediation,
    )


def run_checks(project_root: Path, config: dict[str, Any], feature_dir: Path) -> list[CheckResult]:
    results: list[CheckResult] = []
    spec_path = feature_dir / "spec.md"
    tasks_path = feature_dir / "tasks.md"
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.is_file() else ""
    markers = spec_mod.clarification_markers(spec_text)
    results.append(
        CheckResult(
            "spec-clarity",
            markers == 0 and bool(spec_text),
            "spec.md missing" if not spec_text else f"{markers} clarification marker(s)",
        )
    )
    if config["gate"]["require_tasks_complete"]:
        if not tasks_path.is_file():
            results.append(CheckResult("tasks-complete", False, "tasks.md missing"))
        else:
            open_items = spec_mod.open_tasks(tasks_path.read_text(encoding="utf-8"))
            results.append(
                CheckResult(
                    "tasks-complete",
                    not open_items,
                    f"{len(open_items)} open task(s)",
                    "\n".join(f"- [ ] {item}" for item in open_items[:25]),
                )
            )
    timeout = config["gate"]["check_timeout_seconds"]
    for check in configured_checks(config):
        result = run(check["run"], project_root, shell=True, timeout=timeout)
        passed = result.returncode == 0
        results.append(
            CheckResult(
                check["name"],
                passed,
                f"`{check['run']}` exited {result.returncode}",
                "" if passed else _tail(result.stdout + "\n" + result.stderr),
                [] if passed else [
                    f"Make the '{check['name']}' gate check pass: `{check['run']}` exits {result.returncode}; "
                    "the failure output is in the latest autopilot gate report"
                ],
            )
        )
    results.append(check_acceptance(project_root, config, feature_dir))
    return results


def _normalise(text: str) -> str:
    text = re.sub(r"0x[0-9a-fA-F]+", "H", text)
    text = re.sub(r"\d+(?:\.\d+)?", "N", text)
    return " ".join(text.split())


def fingerprint(items: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for name, detail in sorted(items):
        digest.update(name.encode())
        digest.update(_normalise(detail[-2000:]).encode())
    return digest.hexdigest()[:16]


def _is_stuck(history: list[dict[str, Any]], key: str, current: str, stuck_after: int, *, consecutive: bool) -> bool:
    """True when ``current`` repeats the previous ``stuck_after - 1`` fingerprints.

    Gate failures must repeat in consecutive iterations. Review findings are
    compared with earlier reviews only, since a gate-failing iteration in
    between does not mean the reviewer's concern was addressed.
    """
    if stuck_after < 2:
        return False
    resets = [index for index, entry in enumerate(history) if entry.get("reset")]
    if resets:
        history = history[resets[-1] + 1:]  # a human reset starts a fresh count
    previous = [entry.get(key) for entry in history if consecutive or entry.get(key)]
    recent = previous[-(stuck_after - 1):]
    return len(recent) == stuck_after - 1 and all(fp == current for fp in recent)


def _append_remediation(feature_dir: Path, iteration: int, source: str, items: list[str]) -> list[str]:
    tasks_path = feature_dir / "tasks.md"
    existing_open = set(spec_mod.open_tasks(tasks_path.read_text(encoding="utf-8"))) if tasks_path.is_file() else set()
    fresh = [item for item in items if not any(" ".join(item.split()) in task for task in existing_open)]
    return spec_mod.append_task_phase(
        tasks_path, f"Autopilot Remediation (iteration {iteration}, {source})", fresh
    )


def _write_report(path: Path, state: dict[str, Any], entry: dict[str, Any], checks: list[CheckResult]) -> None:
    lines = [
        f"# Autopilot gate — {state['feature_dir']} — iteration {entry['iteration']}",
        "",
        f"Result: **{'PASS' if entry['checks_passed'] else 'FAIL'}**  ",
        f"Time: {entry['at']}",
        "",
        "| Check | Result | Summary |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        lines.append(f"| {check.name} | {'pass' if check.passed else 'FAIL'} | {check.summary.replace('|', '/')} |")
    for check in checks:
        if not check.passed and check.detail:
            lines += ["", f"## {check.name}", "", "```text", check.detail, "```"]
    if entry.get("appended_tasks"):
        lines += ["", "Appended remediation tasks: " + ", ".join(entry["appended_tasks"])]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── gate ─────────────────────────────────────────────────────────────────────


def run_gate(project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    feature_dir = spec_mod.resolve_feature_dir(project_root)
    state = load_pipe(project_root, feature_dir)
    if state is None:
        raise GateError("no pipe state: run `autopilot.py check-spec` after /speckit.specify first")
    if state["status"] in LOOP_END:
        return {"finished": True, "checks_passed": False, "status": state["status"], "reason": state["reason"]}

    state["iteration"] += 1
    iteration = state["iteration"]
    checks = run_checks(project_root, config, feature_dir)
    checks_passed = all(check.passed for check in checks)
    entry: dict[str, Any] = {
        "iteration": iteration,
        "at": now_iso(),
        "checks_passed": checks_passed,
        "checks": [{"name": c.name, "passed": c.passed, "summary": c.summary} for c in checks],
    }
    directory = pipe_dir(project_root, feature_dir)
    report = directory / f"gate-{iteration}.md"
    output: dict[str, Any] = {
        "iteration": iteration,
        "checks_passed": checks_passed,
        "finished": False,
        "report": _rel(project_root, report),
        "review_args": "",
    }

    if checks_passed:
        if config["gate"]["require_review"]:
            stage_changes(project_root, config["run"]["sync_paths"])
            diff = git(project_root, "diff", "--cached", state["base"], "--", ".", *exclude_pathspecs(), check=False)
            diff_path = directory / f"review-{iteration}.diff"
            diff_path.write_text(diff + "\n", encoding="utf-8")
            review_path = directory / f"review-{iteration}.json"
            if review_path.exists():
                review_path.unlink()
            entry["tree_before_review"] = tree_fingerprint(project_root)
            entry["review_file"] = _rel(project_root, review_path)
            output["review_args"] = (
                f"feature_dir={state['feature_dir']} diff_file={_rel(project_root, diff_path)} "
                f"review_file={_rel(project_root, review_path)} base={state['base']}"
            )
        else:
            _finish(state, "passed", f"gate passed on iteration {iteration} (review disabled)")
            output["finished"] = True
    else:
        failed = [c for c in checks if not c.passed]
        entry["fingerprint"] = fingerprint([(c.name, c.summary + "\n" + c.detail) for c in failed])
        if _is_stuck(state["history"], "fingerprint", entry["fingerprint"], config["pipe"]["stuck_after"], consecutive=True):
            _finish(state, "escalated", f"identical gate failure {config['pipe']['stuck_after']} iterations in a row: "
                    + ", ".join(c.name for c in failed))
            output["finished"] = True
        elif iteration >= state["max_iterations"]:
            _finish(state, "failed", f"iteration cap ({state['max_iterations']}) reached; failing: "
                    + ", ".join(c.name for c in failed))
            output["finished"] = True
        else:
            remediation = [item for c in failed for item in c.remediation]
            entry["appended_tasks"] = _append_remediation(feature_dir, iteration, "gate", remediation)

    state["history"].append(entry)
    _write_report(report, state, entry, checks)
    save_pipe(project_root, feature_dir, state)
    output["status"] = state["status"]
    output["reason"] = state["reason"]
    return output


# ── decide ───────────────────────────────────────────────────────────────────


def _load_review(path: Path) -> tuple[dict[str, Any] | None, str]:
    if not path.is_file():
        return None, f"reviewer did not write {path.name}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"{path.name} is not valid JSON: {exc}"
    if not isinstance(data, dict) or data.get("verdict") not in ("pass", "fail"):
        return None, f"{path.name} must be an object with verdict 'pass' or 'fail'"
    findings = data.get("findings", [])
    if not isinstance(findings, list) or not all(
        isinstance(f, dict) and f.get("severity") in VALID_SEVERITIES and isinstance(f.get("summary"), str)
        for f in findings
    ):
        return None, f"{path.name}: every finding needs a severity in {sorted(VALID_SEVERITIES)} and a summary"
    return data, ""


def decide(project_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    feature_dir = spec_mod.resolve_feature_dir(project_root)
    state = load_pipe(project_root, feature_dir)
    if state is None:
        raise GateError("no pipe state: run `autopilot.py check-spec` first")
    if state["status"] in LOOP_END:
        return {"finished": True, "status": state["status"], "reason": state["reason"]}
    entry = state["history"][-1] if state["history"] else None
    if entry is None or not entry.get("checks_passed") or "review_file" not in entry:
        return {"finished": False, "status": state["status"], "reason": "gate checks failing; remediation queued"}

    iteration = state["iteration"]
    state["reviews"] = state.get("reviews", 0) + 1
    if tree_fingerprint(project_root) != entry["tree_before_review"]:
        _finish(state, "escalated", "the reviewer changed the working tree; a reviewer must not edit code")
        save_pipe(project_root, feature_dir, state)
        return {"finished": True, "status": state["status"], "reason": state["reason"]}

    review, problem = _load_review(project_root / entry["review_file"])
    if review is None:
        entry["review"] = {"valid": False, "problem": problem}
        if iteration >= state["max_iterations"]:
            _finish(state, "failed", f"iteration cap reached; last review unusable: {problem}")
        save_pipe(project_root, feature_dir, state)
        return {"finished": state["status"] in LOOP_END, "status": state["status"], "reason": state["reason"] or problem}

    blocking = [f for f in review.get("findings", []) if f["severity"] in BLOCKING_SEVERITIES]
    entry["review"] = {
        "valid": True,
        "declared_verdict": review["verdict"],
        "blocking": len(blocking),
        "findings": len(review.get("findings", [])),
    }
    if not blocking:
        if review["verdict"] == "fail":
            entry["review"]["note"] = "declared fail without blocker/major findings; treated as pass"
        _finish(state, "passed", f"gate and independent review passed on iteration {iteration}")
    else:
        entry["review_fingerprint"] = fingerprint([(f["severity"], f["summary"]) for f in blocking])
        if _is_stuck(state["history"][:-1], "review_fingerprint", entry["review_fingerprint"],
                     config["pipe"]["stuck_after"], consecutive=False):
            _finish(state, "escalated", f"reviewer raised the same blocking findings {config['pipe']['stuck_after']} times")
        elif iteration >= state["max_iterations"]:
            _finish(state, "failed", f"iteration cap ({state['max_iterations']}) reached with {len(blocking)} blocking review finding(s)")
        else:
            items = []
            for finding in blocking:
                where = f" in {finding['file']}" if isinstance(finding.get("file"), str) and finding["file"] else ""
                ref = f" [{finding['requirement']}]" if isinstance(finding.get("requirement"), str) and finding["requirement"] else ""
                fix = f" Fix: {finding['fix']}" if isinstance(finding.get("fix"), str) and finding["fix"] else ""
                items.append(f"Review {finding.get('id', '')} ({finding['severity']}){ref}{where}: {finding['summary']}.{fix}")
            entry["appended_tasks"] = _append_remediation(feature_dir, iteration, "review", items)
    save_pipe(project_root, feature_dir, state)
    return {"finished": state["status"] in LOOP_END, "status": state["status"], "reason": state["reason"]}


def pipe_result(project_root: Path) -> tuple[int, dict[str, Any]]:
    feature_dir = spec_mod.resolve_feature_dir(project_root)
    state = load_pipe(project_root, feature_dir)
    if state is None:
        return 1, {"status": "missing", "reason": "no pipe state"}
    if state["status"] not in LOOP_END:
        _finish(state, "failed", "loop ended without a gate decision (loop ceiling reached)")
        save_pipe(project_root, feature_dir, state)
    summary = {k: state.get(k) for k in ("epic_id", "feature_dir", "status", "reason", "iteration", "agent_calls")}
    return (0 if state["status"] == "passed" else 1), summary


def checks_only(project_root: Path, config: dict[str, Any], feature_dir: Path | None) -> list[dict[str, Any]]:
    """Project checks (and acceptance coverage when a feature is known), no state."""
    results: list[CheckResult] = []
    timeout = config["gate"]["check_timeout_seconds"]
    for check in configured_checks(config):
        result = run(check["run"], project_root, shell=True, timeout=timeout)
        results.append(CheckResult(check["name"], result.returncode == 0, f"`{check['run']}` exited {result.returncode}",
                                   "" if result.returncode == 0 else _tail(result.stdout + "\n" + result.stderr, 3000)))
    if feature_dir is not None:
        results.append(check_acceptance(project_root, config, feature_dir))
    return [asdict(r) for r in results]
