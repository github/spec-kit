"""Task parsing and beads/gastown bridge utilities for SpecKit."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Error message constants
ERROR_TASKS_NOT_FOUND = "tasks.md not found"
ERROR_BEADS_NOT_INIT = "Beads not initialized"
ERROR_BD_NOT_FOUND = "bd CLI not found in PATH"
ERROR_MALFORMED_TASKS = "tasks.md has invalid format"
ERROR_CIRCULAR_DEPS = "Circular dependency detected"
ERROR_PARTIAL_FAILURE = "Some beads failed to create"

CURRENT_MAPPING_VERSION = "1.0"

# Task line format: "- [ ] T001 [P] [US1] Description (depends on T002, T003)"
TASK_PATTERN = re.compile(
    r"^- \[ \] (T\d{3})\s*(\[P\])?\s*(\[US\d+\])?\s+(.+)$"
)
# Explicit dependency notation within a task description
DEPENDS_PATTERN = re.compile(r"\(depends on (T\d{3}(?:,\s*T\d{3})*)\)")
PHASE_HEADER_PATTERN = re.compile(r"^##\s+Phase\s+\d+:\s+(.+)$")
BEAD_ID_PATTERN = re.compile(r"\b(bd-[A-Za-z0-9]+(?:\.\d+)*)\b")
CONVOY_ID_PATTERN = re.compile(r"\b(gt-[A-Za-z0-9]+)\b")

PHASE_PRIORITY_MAP = {
    "Setup": 0,
    "Foundational": 1,
    "User Story 1": 2,
    "User Story 2": 3,
    "User Story 3": 4,
    "User Story 4": 5,
    "Polish": 9,
}

DEFAULT_PRIORITY = 5


@dataclass
class Task:
    task_id: str
    is_parallel: bool
    user_story: Optional[str]
    description: str
    file_path: Optional[str]
    dependencies: list[str]
    phase_name: str
    phase_priority: int
    line_number: int


@dataclass
class BeadMappingEntry:
    bead_id: str
    created_at: str
    title: str
    parent_bead_id: Optional[str] = None


@dataclass
class ConvoyInfo:
    convoy_id: str
    convoy_name: str
    created_at: str
    bead_ids: list[str]


@dataclass
class TaskBeadMapping:
    version: str
    feature_dir: str
    branch_name: str
    created_at: str
    last_updated: str
    mappings: dict[str, BeadMappingEntry]
    convoy: Optional[ConvoyInfo]
    stats: dict[str, Any]


def _now_iso() -> str:
    """Return current timestamp in ISO-8601 UTC format."""
    return datetime.now(timezone.utc).isoformat()


def _log_line(log_file: Optional[Path], message: str) -> None:
    """Append a timestamped line to the log file if configured."""
    if not log_file:
        return
    timestamp = datetime.now(timezone.utc).isoformat()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def check_cli_available(command: str) -> bool:
    """Check if a CLI command is available in PATH."""
    return shutil.which(command) is not None


def _run_command(command: str, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run a CLI command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError as exc:
        raise RuntimeError(f"{command} CLI not found in PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"{command} command timed out after {timeout}s") from exc


def run_bd_command(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run bd CLI command with error handling."""
    return _run_command("bd", args, timeout=timeout)


def run_gt_command(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run gt CLI command with error handling."""
    return _run_command("gt", args, timeout=timeout)


def parse_phase_header(line: str) -> Optional[str]:
    """Extract phase name from a markdown header line."""
    match = PHASE_HEADER_PATTERN.match(line.strip())
    if not match:
        return None
    return match.group(1).strip()


def _map_priority_from_phase(phase_name: str) -> int:
    """Map a phase name to a beads priority number."""
    for key, priority in PHASE_PRIORITY_MAP.items():
        if key in phase_name:
            return priority
    match = re.search(r"Priority:\s*P(\d+)", phase_name)
    if match:
        return int(match.group(1)) + 1
    return DEFAULT_PRIORITY


def _extract_file_path(description: str) -> Optional[str]:
    """Try to extract a file path from a task description."""
    match = re.search(r"([A-Za-z0-9_./-]+/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)", description)
    if match:
        return match.group(1)
    return None


def parse_dependencies(description: str) -> tuple[list[str], str]:
    """Extract dependencies and return (dependencies, cleaned_description)."""
    match = DEPENDS_PATTERN.search(description)
    if not match:
        return [], description.strip()
    deps_str = match.group(1)
    deps = [dep.strip() for dep in deps_str.split(",") if dep.strip()]
    cleaned = DEPENDS_PATTERN.sub("", description).strip()
    return deps, cleaned


def parse_tasks_file(tasks_path: Path) -> list[Task]:
    """Parse tasks.md and return a list of Task objects."""
    if not tasks_path.exists():
        raise FileNotFoundError(f"{ERROR_TASKS_NOT_FOUND} at {tasks_path}")

    tasks: list[Task] = []
    current_phase: Optional[str] = None
    last_non_parallel_by_phase: dict[str, Optional[str]] = {}

    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    for index, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip()
        phase_name = parse_phase_header(line)
        if phase_name:
            current_phase = phase_name
            if current_phase not in last_non_parallel_by_phase:
                last_non_parallel_by_phase[current_phase] = None
            continue

        if not line.strip().startswith("- [ ]"):
            continue

        if not current_phase:
            raise ValueError(f"{ERROR_MALFORMED_TASKS} at line {index}: missing phase header")

        match = TASK_PATTERN.match(line.strip())
        if not match:
            # Malformed task line handling: warn and skip
            sys.stderr.write(
                f"Warning: Malformed task line at {index}: {line.strip()}\n"
            )
            continue

        task_id = match.group(1)
        is_parallel = bool(match.group(2))
        user_story_raw = match.group(3)
        user_story = user_story_raw.strip("[]") if user_story_raw else None
        description_raw = match.group(4).strip()

        dependencies, description = parse_dependencies(description_raw)
        file_path = _extract_file_path(description)
        phase_priority = _map_priority_from_phase(current_phase)

        implicit_dep = None
        if not is_parallel:
            implicit_dep = last_non_parallel_by_phase.get(current_phase)

        if implicit_dep and implicit_dep not in dependencies:
            dependencies.append(implicit_dep)

        if not is_parallel:
            last_non_parallel_by_phase[current_phase] = task_id

        tasks.append(
            Task(
                task_id=task_id,
                is_parallel=is_parallel,
                user_story=user_story,
                description=description,
                file_path=file_path,
                dependencies=dependencies,
                phase_name=current_phase,
                phase_priority=phase_priority,
                line_number=index,
            )
        )

    if not tasks:
        raise ValueError("tasks.md contains no tasks")

    return tasks


def validate_task_ids(tasks: list[Task]) -> None:
    """Validate task IDs for format and uniqueness."""
    seen: set[str] = set()
    for task in tasks:
        if not re.fullmatch(r"T\d{3}", task.task_id):
            raise ValueError(f"Invalid task ID: {task.task_id}")
        if task.task_id in seen:
            raise ValueError(f"Duplicate task ID detected: {task.task_id}")
        seen.add(task.task_id)


def validate_dependencies(tasks: list[Task]) -> None:
    """Validate dependency targets exist in task list."""
    task_ids = {task.task_id for task in tasks}
    for task in tasks:
        for dep in task.dependencies:
            if dep not in task_ids:
                raise ValueError(f"Dependency {dep} not found for task {task.task_id}")


def validate_dependency_targets(tasks: list[Task]) -> None:
    """Alias for validate_dependencies to match contract naming."""
    validate_dependencies(tasks)


def detect_circular_dependencies(tasks: list[Task]) -> Optional[list[str]]:
    """Detect circular dependencies. Returns cycle path if found."""
    graph = {task.task_id: task.dependencies for task in tasks}
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> Optional[list[str]]:
        visiting.add(node)
        stack.append(node)
        for neighbor in graph.get(node, []):
            if neighbor in visiting:
                cycle_start = stack.index(neighbor)
                return stack[cycle_start:] + [neighbor]
            if neighbor not in visited:
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
        visiting.remove(node)
        visited.add(node)
        stack.pop()
        return None

    for node in graph:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return None


def validate_beads_initialized(repo_root: Path) -> bool:
    """Check if .beads/ directory exists in repo root."""
    beads_dir = repo_root / ".beads"
    return beads_dir.exists() and beads_dir.is_dir()


def load_mapping(feature_dir: Path) -> Optional[TaskBeadMapping]:
    """Load existing mapping file or return None if it doesn't exist."""
    mapping_path = feature_dir / "beads-mapping.json"
    if not mapping_path.exists():
        return None
    try:
        data = json.loads(mapping_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = mapping_path.with_suffix(".json.bak")
        mapping_path.rename(backup)
        return None

    version = data.get("version", CURRENT_MAPPING_VERSION)
    if version != CURRENT_MAPPING_VERSION:
        raise ValueError(f"Unsupported mapping version: {version}")

    mappings_raw = data.get("mappings", {})
    mappings: dict[str, BeadMappingEntry] = {}
    for key, entry in mappings_raw.items():
        mappings[key] = BeadMappingEntry(
            bead_id=entry["bead_id"],
            created_at=entry.get("created_at", ""),
            title=entry.get("title", ""),
            parent_bead_id=entry.get("parent_bead_id"),
        )

    convoy_data = data.get("convoy")
    convoy = None
    if convoy_data:
        convoy = ConvoyInfo(
            convoy_id=convoy_data["convoy_id"],
            convoy_name=convoy_data["convoy_name"],
            created_at=convoy_data.get("created_at", ""),
            bead_ids=convoy_data.get("bead_ids", []),
        )

    return TaskBeadMapping(
        version=version,
        feature_dir=data.get("feature_dir", str(feature_dir)),
        branch_name=data.get("branch_name", ""),
        created_at=data.get("created_at", ""),
        last_updated=data.get("last_updated", ""),
        mappings=mappings,
        convoy=convoy,
        stats=data.get("stats", {}),
    )


def save_mapping(mapping: TaskBeadMapping, feature_dir: Path) -> None:
    """Save mapping file with atomic write."""
    mapping.last_updated = _now_iso()
    mapping_path = feature_dir / "beads-mapping.json"
    tmp_path = mapping_path.with_suffix(".json.tmp")

    serialized = {
        "version": mapping.version,
        "feature_dir": mapping.feature_dir,
        "branch_name": mapping.branch_name,
        "created_at": mapping.created_at,
        "last_updated": mapping.last_updated,
        "mappings": {key: asdict(entry) for key, entry in mapping.mappings.items()},
        "convoy": asdict(mapping.convoy) if mapping.convoy else None,
        "stats": mapping.stats,
    }

    tmp_path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    tmp_path.replace(mapping_path)


def load_existing_mapping(feature_dir: Path) -> TaskBeadMapping:
    """Load mapping or return a new initialized mapping."""
    mapping = load_mapping(feature_dir)
    if mapping:
        return mapping
    created_at = _now_iso()
    return TaskBeadMapping(
        version=CURRENT_MAPPING_VERSION,
        feature_dir=str(feature_dir),
        branch_name="",
        created_at=created_at,
        last_updated=created_at,
        mappings={},
        convoy=None,
        stats={},
    )


def is_duplicate(task_id: str, mapping: TaskBeadMapping) -> bool:
    """Check if a task already has a bead mapping."""
    return task_id in mapping.mappings


def filter_duplicate_tasks(tasks: list[Task], mapping: TaskBeadMapping) -> tuple[list[Task], list[Task]]:
    """Split tasks into new and existing based on mapping."""
    new_tasks: list[Task] = []
    existing_tasks: list[Task] = []
    for task in tasks:
        if is_duplicate(task.task_id, mapping):
            existing_tasks.append(task)
        else:
            new_tasks.append(task)
    return new_tasks, existing_tasks


def _truncate_title(title: str, max_len: int = 200) -> str:
    """Ensure bead titles stay within a practical length limit."""
    if len(title) <= max_len:
        return title
    return title[: max_len - 3].rstrip() + "..."


def get_context_files(feature_dir: Path) -> list[Path]:
    """Find context files (spec.md, plan.md) for the feature."""
    candidates = [feature_dir / "spec.md", feature_dir / "plan.md"]
    return [path for path in candidates if path.exists()]


def format_bead_description(task: Task, context_files: list[Path], repo_root: Optional[Path]) -> str:
    """Format bead description with task details and context file references."""
    lines = [task.description]
    if task.file_path:
        lines.append("")
        lines.append(f"File: {task.file_path}")
    if context_files:
        lines.append("")
        lines.append("Context:")
        for path in context_files:
            display = str(path)
            if repo_root:
                try:
                    display = str(path.relative_to(repo_root))
                except ValueError:
                    display = str(path)
            lines.append(f"- {display}")
    return "\n".join(lines).strip()


def determine_parent_bead(task: Task) -> tuple[str, str]:
    """Return a (parent_key, parent_title) for the task."""
    if task.user_story:
        return f"us:{task.user_story}", task.phase_name
    phase_lower = task.phase_name.lower()
    if "setup" in phase_lower:
        return "phase:setup", "Setup"
    if "foundational" in phase_lower:
        return "phase:foundational", "Foundational"
    if "polish" in phase_lower:
        return "phase:polish", "Polish"
    return f"phase:{phase_lower.replace(' ', '-')}", task.phase_name


def _parse_bead_id(output: str) -> Optional[str]:
    """Extract bead ID from bd stdout."""
    match = BEAD_ID_PATTERN.search(output)
    return match.group(1) if match else None


def _parse_convoy_id(output: str) -> Optional[str]:
    """Extract convoy ID from gt stdout."""
    match = CONVOY_ID_PATTERN.search(output)
    return match.group(1) if match else None


def create_bead(
    title: str,
    priority: int,
    description: str,
    parent_id: Optional[str] = None,
    timeout: int = 30,
) -> str:
    """Create a bead via bd CLI and return the bead ID."""
    args = ["create", "-p", str(priority)]
    if parent_id:
        args += ["--parent", parent_id]
    if description:
        args += ["--desc", description]
    args.append(title)

    code, stdout, stderr = run_bd_command(args, timeout=timeout)
    if code != 0:
        raise RuntimeError(stderr or "bd create failed")

    bead_id = _parse_bead_id(stdout)
    if not bead_id:
        raise RuntimeError("Unable to parse bead ID from bd output")

    return bead_id


def _get_parent_beads_from_stats(mapping: TaskBeadMapping) -> dict[str, str]:
    """Load cached parent bead IDs from mapping stats."""
    parent_beads = mapping.stats.get("parent_beads")
    if isinstance(parent_beads, dict):
        return {str(key): str(value) for key, value in parent_beads.items()}
    return {}


def _set_parent_beads_in_stats(mapping: TaskBeadMapping, parent_beads: dict[str, str]) -> None:
    """Persist parent bead IDs into mapping stats."""
    mapping.stats["parent_beads"] = parent_beads


def create_beads_from_tasks(
    tasks: list[Task],
    mapping: TaskBeadMapping,
    repo_root: Path,
    feature_dir: Path,
    log_file: Optional[Path],
) -> dict[str, Any]:
    """Create beads for tasks and update mapping. Returns result stats."""
    context_files = get_context_files(feature_dir)
    parent_beads = _get_parent_beads_from_stats(mapping)
    created_beads: list[tuple[str, str]] = []
    created_parents: list[tuple[str, str]] = []
    failed: dict[str, str] = {}
    skipped: list[str] = []

    new_tasks, existing_tasks = filter_duplicate_tasks(tasks, mapping)
    skipped = [task.task_id for task in existing_tasks]

    for task in new_tasks:
        parent_key, parent_title = determine_parent_bead(task)
        parent_id = parent_beads.get(parent_key)
        if not parent_id:
            try:
                parent_id = create_bead(
                    title=_truncate_title(parent_title),
                    priority=task.phase_priority,
                    description=parent_title,
                )
                parent_beads[parent_key] = parent_id
                created_parents.append((parent_title, parent_id))
                _set_parent_beads_in_stats(mapping, parent_beads)
                _log_line(log_file, f"Created parent bead {parent_id} for {parent_key}")
                save_mapping(mapping, feature_dir)
            except Exception as exc:
                failed[task.task_id] = str(exc)
                _log_line(log_file, f"Failed to create parent bead for {task.task_id}: {exc}")
                continue

        description = format_bead_description(task, context_files, repo_root)
        try:
            bead_id = create_bead(
                title=_truncate_title(task.description),
                priority=task.phase_priority,
                description=description,
                parent_id=parent_id,
            )
            mapping.mappings[task.task_id] = BeadMappingEntry(
                bead_id=bead_id,
                created_at=_now_iso(),
                title=task.description,
                parent_bead_id=parent_id,
            )
            created_beads.append((task.task_id, bead_id))
            save_mapping(mapping, feature_dir)
            _log_line(log_file, f"Created bead {bead_id} for {task.task_id}")
        except Exception as exc:
            failed[task.task_id] = str(exc)
            _log_line(log_file, f"Failed to create bead for {task.task_id}: {exc}")
            continue

    return {
        "created": created_beads,
        "created_parents": created_parents,
        "skipped": skipped,
        "failed": failed,
        "parent_beads": parent_beads,
    }


def create_bead_dependencies(tasks: list[Task], mapping: TaskBeadMapping, log_file: Optional[Path]) -> list[str]:
    """Create bead dependencies via bd dep add. Returns warnings."""
    warnings: list[str] = []
    for task in tasks:
        if not task.dependencies:
            continue
        child_entry = mapping.mappings.get(task.task_id)
        if not child_entry:
            continue
        for dep_id in task.dependencies:
            parent_entry = mapping.mappings.get(dep_id)
            if not parent_entry:
                continue
            args = ["dep", "add", child_entry.bead_id, parent_entry.bead_id]
            code, _, stderr = run_bd_command(args)
            if code != 0:
                message = (
                    f"Failed to create dependency: {task.task_id} ({child_entry.bead_id}) "
                    f"depends on {dep_id} ({parent_entry.bead_id}): {stderr}"
                )
                warnings.append(message)
                _log_line(log_file, message)
    return warnings


def check_gastown_available() -> bool:
    """Check if gastown CLI is available."""
    return check_cli_available("gt")


def _read_spec_title(feature_dir: Path) -> Optional[str]:
    """Extract the top-level title from spec.md if available."""
    spec_path = feature_dir / "spec.md"
    if not spec_path.exists():
        return None
    for line in spec_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            return title
    return None


def _get_git_branch(repo_root: Path) -> Optional[str]:
    """Return the current git branch name, if available."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    if branch and branch != "HEAD":
        return branch
    return None


def get_branch_name(repo_root: Path, feature_dir: Path) -> str:
    """Determine branch name with fallback to spec title or feature directory name."""
    branch = _get_git_branch(repo_root)
    if branch:
        return branch
    spec_title = _read_spec_title(feature_dir)
    if spec_title:
        return spec_title
    return feature_dir.name


def get_convoy_name(repo_root: Path, feature_dir: Path) -> str:
    """Determine convoy name from branch name or spec title."""
    branch = _get_git_branch(repo_root)
    if branch:
        return branch
    spec_title = _read_spec_title(feature_dir)
    if spec_title:
        return spec_title
    return feature_dir.name


def create_convoy(
    convoy_name: str,
    bead_ids: list[str],
    timeout: int = 30,
) -> Optional[ConvoyInfo]:
    """Create a gastown convoy and return ConvoyInfo if successful."""
    if not bead_ids:
        return None
    args = ["convoy", "create", convoy_name] + bead_ids
    code, stdout, stderr = run_gt_command(args, timeout=timeout)
    if code != 0:
        raise RuntimeError(stderr or "gt convoy create failed")
    convoy_id = _parse_convoy_id(stdout)
    if not convoy_id:
        raise RuntimeError("Unable to parse convoy ID from gt output")
    return ConvoyInfo(
        convoy_id=convoy_id,
        convoy_name=convoy_name,
        created_at=_now_iso(),
        bead_ids=bead_ids,
    )


def _collect_bead_ids(mapping: TaskBeadMapping) -> list[str]:
    """Collect all bead IDs (including parent beads) for convoy creation."""
    bead_ids = {entry.bead_id for entry in mapping.mappings.values()}
    parent_beads = _get_parent_beads_from_stats(mapping)
    bead_ids.update(parent_beads.values())
    return sorted(bead_ids)


def run_taskstoepic(
    tasks_path: Path,
    feature_dir: Path,
    repo_root: Path,
    user_input: str = "",
) -> tuple[int, dict[str, Any]]:
    """Run end-to-end tasks-to-epic flow. Returns (exit_code, result)."""
    log_file = feature_dir / "taskstoepic.log"
    phase_timings: dict[str, float] = {}
    start_total = time.monotonic()

    try:
        start = time.monotonic()
        tasks = parse_tasks_file(tasks_path)
        validate_task_ids(tasks)
        validate_dependency_targets(tasks)
        cycle = detect_circular_dependencies(tasks)
        if cycle:
            raise ValueError(f"{ERROR_CIRCULAR_DEPS}: {' -> '.join(cycle)}")
        phase_timings["parse"] = time.monotonic() - start
    except FileNotFoundError as exc:
        return 1, {"error": str(exc)}
    except ValueError as exc:
        message = str(exc)
        if message.startswith(ERROR_CIRCULAR_DEPS):
            return 5, {"error": message}
        if ERROR_MALFORMED_TASKS in message or "tasks.md contains no tasks" in message:
            return 4, {"error": message}
        return 4, {"error": message}

    mapping = load_existing_mapping(feature_dir)
    mapping.branch_name = get_branch_name(repo_root, feature_dir)

    start = time.monotonic()
    bead_results = create_beads_from_tasks(
        tasks=tasks,
        mapping=mapping,
        repo_root=repo_root,
        feature_dir=feature_dir,
        log_file=log_file,
    )
    phase_timings["beads"] = time.monotonic() - start

    start = time.monotonic()
    dep_warnings = create_bead_dependencies(tasks, mapping, log_file=log_file)
    phase_timings["dependencies"] = time.monotonic() - start

    convoy_info = None
    convoy_warning = None
    if check_gastown_available():
        if bead_results["created"]:
            start = time.monotonic()
            try:
                convoy_name = get_convoy_name(repo_root, feature_dir)
                # Batch all bead IDs into a single convoy create call.
                convoy_info = create_convoy(convoy_name, _collect_bead_ids(mapping))
                mapping.convoy = convoy_info
                save_mapping(mapping, feature_dir)
            except Exception as exc:
                convoy_warning = str(exc)
            phase_timings["convoy"] = time.monotonic() - start
        else:
            convoy_info = mapping.convoy
    else:
        convoy_warning = "Gastown CLI not found. Beads were created without convoy."

    duration = time.monotonic() - start_total
    stats = mapping.stats
    stats["total_beads_created"] = stats.get("total_beads_created", 0) + len(
        bead_results["created"]
    )
    stats["skipped_duplicates"] = stats.get("skipped_duplicates", 0) + len(
        bead_results["skipped"]
    )
    stats["last_run_duration_seconds"] = round(duration, 2)
    stats["phase_timings_seconds"] = phase_timings
    mapping.stats = stats
    save_mapping(mapping, feature_dir)

    result = {
        "created": bead_results["created"],
        "created_parents": bead_results["created_parents"],
        "skipped": bead_results["skipped"],
        "failed": bead_results["failed"],
        "dependency_warnings": dep_warnings,
        "convoy": asdict(convoy_info) if convoy_info else None,
        "convoy_warning": convoy_warning,
        "duration": duration,
        "user_input": user_input,
    }

    if bead_results["failed"]:
        return 6, result

    return 0, result


def _render_report(exit_code: int, result: dict[str, Any], feature_dir: Path) -> None:
    """Print a user-facing summary report."""
    created = result.get("created", [])
    created_parents = result.get("created_parents", [])
    skipped = result.get("skipped", [])
    failed = result.get("failed", {})
    convoy = result.get("convoy")
    convoy_warning = result.get("convoy_warning")

    if exit_code == 0:
        print("✓ Tasks-to-Epic Bridge Complete")
    elif exit_code == 6:
        print("⚠ Tasks-to-Epic Bridge Completed with Warnings")
    else:
        sys.stderr.write(result.get("error", "Unknown error") + "\n")
        return

    if convoy_warning and exit_code in (0, 6):
        print(convoy_warning)

    print("")
    print(f"Beads Created: {len(created)}")
    print(f"Skipped (duplicates): {len(skipped)}")
    print(f"Failed: {len(failed)}")

    if created_parents or created:
        print("")
        print("Created Beads:")
        for title, bead_id in created_parents:
            print(f"  - {bead_id} ({title})")
        for task_id, bead_id in created:
            print(f"  - {bead_id} ({task_id})")

    if failed:
        print("")
        print("Failed Tasks:")
        for task_id, message in failed.items():
            print(f"  - {task_id}: {message}")

    if convoy:
        print("")
        print(f"Convoy Created: {convoy['convoy_id']} ({convoy['convoy_name']})")
        print("")
        print("Next Steps:")
        print("  1. Verify beads: bd list")
        print("  2. Check dependencies: bd ready")
        print("  3. Start epic work with the Mayor:")
        print("     gt mayor attach")
    else:
        print("")
        print("Next Steps:")
        print("  1. Verify beads: bd list")
        print("  2. Check dependencies: bd ready")

    print("")
    print(f"Mapping File: {feature_dir / 'beads-mapping.json'}")


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point for taskstoepic helper."""
    args = argv or sys.argv[1:]
    if len(args) < 3:
        sys.stderr.write(
            "Usage: task_parser.py <feature_dir> <tasks_path> <repo_root> [user_input]\n"
        )
        return 4

    feature_dir = Path(args[0]).resolve()
    tasks_path = Path(args[1]).resolve()
    repo_root = Path(args[2]).resolve()
    user_input = " ".join(args[3:]) if len(args) > 3 else ""

    if not validate_beads_initialized(repo_root):
        sys.stderr.write(
            "Beads not initialized. Run 'bd init' to initialize beads in this repository.\n"
        )
        return 2

    if not check_cli_available("bd"):
        sys.stderr.write("bd CLI not found in PATH.\n")
        return 3

    exit_code, result = run_taskstoepic(tasks_path, feature_dir, repo_root, user_input)
    _render_report(exit_code, result, feature_dir)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
