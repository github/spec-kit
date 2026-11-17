#!/usr/bin/env python3
"""Component: coding progress; target: developer workstation; task: fork workflow.

Persistent coding-only task state. This helper never executes application tools.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True

from workflow_common import (  # noqa: E402 - disable cache writes before local imports
    digest,
    fingerprints,
    paths,
    require_files,
    source_path,
    tasks,
)

MAX_ATTEMPTS = 3


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def locked(path: Path):
    lock = path.with_suffix(".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError(
            f"Progress is locked: {lock}. Check for an active writer before removing a stale lock."
        ) from exc
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        lock.unlink()


def save(path: Path, state: dict) -> None:
    state["updated_at"] = now()
    descriptor, temporary = tempfile.mkstemp(prefix=".code-progress-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(state, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_state(path: Path) -> dict | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or type(value.get("schema_version")) is not int
        or value["schema_version"] != 1
        or not isinstance(value.get("tasks"), dict)
        or not isinstance(value.get("inputs"), dict)
        or not isinstance(value.get("history"), list)
    ):
        raise ValueError(
            "Invalid code-progress.json; preserve it and recover from the last valid copy"
        )
    for key, item in value["tasks"].items():
        if (
            not isinstance(item, dict)
            or item.get("status")
            not in {
                "PENDING",
                "IN_PROGRESS",
                "CODE_COMPLETE",
                "BLOCKED",
                "NEEDS_REVIEW",
            }
            or type(item.get("attempts")) is not int
            or not 0 <= item["attempts"] <= MAX_ATTEMPTS
            or not isinstance(item.get("definition_hash"), str)
            or not isinstance(item.get("file_hashes"), dict)
            or not isinstance(item.get("starting_hashes", {}), dict)
        ):
            raise ValueError(f"Invalid progress entry: {key}")
    return value


def file_hash(root: Path, name: str) -> str:
    path = source_path(root, name)
    return (
        hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
    )


def effective_status(
    state: dict, definitions: dict, root: Path, starting_hashes: dict | None = None
) -> dict[str, str]:
    starting_hashes = starting_hashes or {}
    statuses = {key: entry["status"] for key, entry in state["tasks"].items()}
    for key, entry in state["tasks"].items():
        if entry["status"] == "CODE_COMPLETE":
            recorded = entry.get("file_hashes", {})
            if any(
                recorded.get(name)
                != (
                    starting_hashes[name]
                    if name in starting_hashes
                    else file_hash(root, name)
                )
                for name in definitions[key]["files"]
            ):
                statuses[key] = "NEEDS_REVIEW"
    # A changed prerequisite invalidates completion of its dependent code.
    changed = True
    while changed:
        changed = False
        for key, task in definitions.items():
            if statuses[key] == "CODE_COMPLETE" and any(
                statuses[d] != "CODE_COMPLETE" for d in task["depends_on"]
            ):
                statuses[key] = "NEEDS_REVIEW"
                changed = True
    return statuses


def prerequisite_statuses(
    state: dict, definitions: dict, root: Path, key: str
) -> dict[str, str]:
    entry = state["tasks"][key]
    # A resumed integration may have edited its prerequisites' shared files.
    # Compare only its owned paths to the snapshot taken before this attempt;
    # unrelated prerequisite files must still match their actual current bytes.
    starting = (
        entry.get("starting_hashes", {})
        if entry["status"] in {"IN_PROGRESS", "BLOCKED"}
        else {}
    )
    owned = {
        name: starting[name] for name in definitions[key]["files"] if name in starting
    }
    return effective_status(state, definitions, root, owned)


def operate(action: str, task_id: str | None = None, note: str = "") -> dict:
    selected = paths()
    require_files(
        selected,
        ["CONSTITUTION", "SPEC", "ARCHITECTURE", "ENVIRONMENT", "PLAN", "TASKS_CODE"],
    )
    definitions = tasks(selected)
    if action == "validate":
        return {"valid": True, "task_count": len(definitions)}
    path = selected["CODE_PROGRESS"]
    # Reject linked state files/ancestors before either reading or writing.
    current = path
    while current != selected["REPO_ROOT"]:
        if current.is_symlink():
            raise ValueError(f"Symlinked progress path: {current}")
        current = current.parent
    if action == "status":
        return status(selected, definitions, read_state(path))
    with locked(path):
        state = read_state(path)
        inputs = fingerprints(selected)
        if action == "sync":
            previous = state or {"tasks": {}, "inputs": inputs, "history": []}
            historical_ids = set()
            for revision in previous.get("history", []):
                if not isinstance(revision, dict) or not isinstance(
                    revision.get("tasks"), dict
                ):
                    raise ValueError(
                        "Invalid progress history; preserve it for recovery"
                    )
                historical_ids.update(revision["tasks"])
            reused = set(definitions) & (historical_ids - set(previous["tasks"]))
            if reused:
                raise ValueError(f"Retired task IDs cannot be reused: {sorted(reused)}")
            entries = {}
            for key, task in definitions.items():
                old = previous["tasks"].get(key)
                same = old is not None and old.get("definition_hash") == digest(task)
                if same:
                    entry = old.copy()
                    if previous["inputs"] != inputs:
                        entry["status"] = "NEEDS_REVIEW"
                        entry["note"] = (
                            "Design inputs changed; inspect existing code against the revised design"
                        )
                        entry["attempts"] = 0
                else:
                    entry = {
                        "status": "NEEDS_REVIEW" if old else "PENDING",
                        "attempts": 0,
                        "note": "Task changed; preserve and review existing code"
                        if old
                        else "",
                        "definition_hash": digest(task),
                        "file_hashes": {},
                    }
                entries[key] = entry
            history = previous.get("history", [])
            if state and (previous["inputs"] != inputs or previous["tasks"] != entries):
                history.append(
                    {
                        "at": now(),
                        "inputs": previous["inputs"],
                        "tasks": previous["tasks"],
                    }
                )
            state = {
                "schema_version": 1,
                "inputs": inputs,
                "tasks": entries,
                "history": history,
            }
        else:
            status(
                selected, definitions, state
            )  # Reject stale definitions/design before mutation.
            if task_id not in definitions:
                raise ValueError(f"Unknown task: {task_id}")
            entry = state["tasks"][task_id]
            task = definitions[task_id]
            statuses = effective_status(state, definitions, selected["REPO_ROOT"])
            prerequisites = prerequisite_statuses(
                state, definitions, selected["REPO_ROOT"], task_id
            )
            if action == "start":
                if any(prerequisites[d] != "CODE_COMPLETE" for d in task["depends_on"]):
                    raise ValueError(
                        f"Task {task_id} has unfinished coding dependencies"
                    )
                for other, other_entry in state["tasks"].items():
                    if (
                        other != task_id
                        and other_entry["status"] == "IN_PROGRESS"
                        and set(task["files"]) & set(definitions[other]["files"])
                    ):
                        raise ValueError(
                            f"Task {task_id} shares files with active task {other}"
                        )
                if entry["status"] != "IN_PROGRESS":
                    if entry["attempts"] >= MAX_ATTEMPTS:
                        raise ValueError(
                            f"Task {task_id} exhausted {MAX_ATTEMPTS} attempts; record the obstacle and continue independent tasks"
                        )
                    if statuses[task_id] == "CODE_COMPLETE":
                        raise ValueError(f"Task {task_id} is already CODE_COMPLETE")
                    entry["attempts"] += 1
                    if entry["status"] != "BLOCKED":
                        entry["starting_hashes"] = {
                            name: file_hash(selected["REPO_ROOT"], name)
                            for name in task["files"]
                        }
                entry["status"] = "IN_PROGRESS"
            elif action in {"complete", "block"}:
                if entry["status"] != "IN_PROGRESS":
                    raise ValueError(
                        "Only IN_PROGRESS tasks can be completed or blocked"
                    )
                if not note.strip():
                    raise ValueError(
                        "Record coding evidence or the actual obstacle with --note"
                    )
                if action == "complete":
                    if any(
                        prerequisites[d] != "CODE_COMPLETE" for d in task["depends_on"]
                    ):
                        raise ValueError(
                            "A coding prerequisite changed; review it before completing this task"
                        )
                    hashes = {
                        name: file_hash(selected["REPO_ROOT"], name)
                        for name in task["files"]
                    }
                    if "missing" in hashes.values() or any(
                        source_path(selected["REPO_ROOT"], name).stat().st_size == 0
                        for name in task["files"]
                    ):
                        raise ValueError(
                            "Task outputs must exist and be nonempty before CODE_COMPLETE"
                        )
                    entry["file_hashes"] = hashes
                    # Authorized shared-file integration updates the recorded revision of earlier tasks.
                    # The agent must inspect their contracts as part of this integration task.
                    for other in state["tasks"].values():
                        if other["status"] == "CODE_COMPLETE":
                            for name in set(other.get("file_hashes", {})) & set(hashes):
                                other["file_hashes"][name] = hashes[name]
                    entry["status"] = "CODE_COMPLETE"
                else:
                    entry["status"] = "BLOCKED"
                entry["note"] = note
            else:
                raise ValueError(f"Unknown progress action: {action}")
            entry["updated_at"] = now()
        save(path, state)
        return status(selected, definitions, state)


def status(selected: dict, definitions: dict, state: dict | None) -> dict:
    if state is None:
        raise ValueError(
            "No coding progress; run taskscode and code-progress sync first"
        )
    if (
        state.get("inputs") != fingerprints(selected)
        or set(state["tasks"]) != set(definitions)
        or any(
            state["tasks"][key].get("definition_hash") != digest(task)
            for key, task in definitions.items()
        )
    ):
        raise ValueError(
            "Design or task definitions changed; taskscode must review and sync progress before coding resumes"
        )
    statuses = effective_status(state, definitions, selected["REPO_ROOT"])
    ready = []
    for key, task in definitions.items():
        if statuses[key] == "CODE_COMPLETE":
            continue
        if (
            statuses[key] != "IN_PROGRESS"
            and state["tasks"][key]["attempts"] >= MAX_ATTEMPTS
        ):
            continue
        if any(
            other != key
            and entry["status"] == "IN_PROGRESS"
            and set(task["files"]) & set(definitions[other]["files"])
            for other, entry in state["tasks"].items()
        ):
            continue
        prerequisites = (
            prerequisite_statuses(state, definitions, selected["REPO_ROOT"], key)
            if statuses[key] in {"IN_PROGRESS", "BLOCKED"}
            else statuses
        )
        if all(prerequisites[d] == "CODE_COMPLETE" for d in task["depends_on"]):
            ready.append(key)
    ready.sort(key=lambda key: statuses[key] not in {"IN_PROGRESS", "BLOCKED"})
    return {
        "tasks": {
            key: {**entry, "status": statuses[key]}
            for key, entry in state["tasks"].items()
        },
        "ready": ready,
        "code_complete": all(s == "CODE_COMPLETE" for s in statuses.values()),
        "tests_run": False,
        "meaning": "CODE_COMPLETE records coding output, not correctness or acceptance",
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["validate", "sync", "status", "start", "complete", "block"]
    )
    parser.add_argument("--task")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(operate(args.action, args.task, args.note), ensure_ascii=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
