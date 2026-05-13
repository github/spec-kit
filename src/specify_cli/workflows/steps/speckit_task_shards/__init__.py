"""Spec Kit task shard step.

Builds conservative implementation handoff shards from the active feature's
``tasks.md`` so a workflow can fan out into repeated ``speckit.implement`` calls.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


_TASK_RE = re.compile(r"^\s*-\s+\[[ xX]\]\s+(?P<id>[A-Za-z]+\d{3,})\b(?P<body>.*)$")
_HEADING_RE = re.compile(r"^\s{0,3}#{2,6}\s+(?P<title>.+?)\s*$")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_PATH_TOKEN_RE = re.compile(
    r"(?<![\w./-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+|[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+)(?![\w./-])"
)


@dataclass
class ParsedTask:
    task_id: str
    text: str
    phase: str
    parallel: bool
    paths: list[str]


@dataclass
class TaskShard:
    shard_id: str
    tasks: list[ParsedTask]

    @property
    def task_ids(self) -> list[str]:
        return [task.task_id for task in self.tasks]

    @property
    def paths(self) -> list[str]:
        seen: dict[str, None] = {}
        for task in self.tasks:
            for path in task.paths:
                seen.setdefault(path, None)
        return list(seen)


class SpeckitTaskShardsStep(StepBase):
    """Generate handoff files from the active feature's ``tasks.md``."""

    type_key = "speckit-task-shards"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        input_data = config.get("input", {})
        resolved_input: dict[str, Any] = {}
        for key, value in input_data.items():
            resolved_input[key] = evaluate_expression(value, context)

        args = str(resolved_input.get("args", "") or "")
        try:
            max_shards = int(resolved_input.get("max_shards", 8) or 8)
        except (TypeError, ValueError):
            return self._failed("max_shards must be a positive integer.", resolved_input)
        if max_shards < 1:
            return self._failed("max_shards must be a positive integer.", resolved_input)

        project_root = Path(context.project_root or ".").resolve()
        try:
            feature_dir = self._resolve_feature_dir(project_root)
            self._require_feature_files(feature_dir)
            tasks = self._parse_tasks(feature_dir / "tasks.md")
            shards = self._build_shards(tasks, max_shards)
            items = self._write_handoffs(
                project_root,
                feature_dir,
                shards,
                args,
                context.run_id or "manual",
            )
        except ValueError as exc:
            return self._failed(str(exc), resolved_input)

        return StepResult(
            status=StepStatus.COMPLETED,
            output={
                "input": resolved_input,
                "feature_dir": str(feature_dir),
                "tasks_path": str(feature_dir / "tasks.md"),
                "item_count": len(items),
                "items": items,
            },
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        input_data = config.get("input", {})
        if input_data is not None and not isinstance(input_data, dict):
            errors.append(
                f"speckit-task-shards step {config.get('id', '?')!r}: 'input' must be a mapping."
            )
        return errors

    @staticmethod
    def _failed(error: str, input_data: dict[str, Any]) -> StepResult:
        return StepResult(
            status=StepStatus.FAILED,
            error=error,
            output={"input": input_data, "error": error, "items": []},
        )

    @classmethod
    def _resolve_feature_dir(cls, project_root: Path) -> Path:
        feature_json = project_root / ".specify" / "feature.json"
        if feature_json.is_file():
            try:
                raw = json.loads(feature_json.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise ValueError(f"Failed to parse .specify/feature.json: {exc}") from exc
            feature_value = raw.get("feature_directory") if isinstance(raw, dict) else None
            if feature_value:
                return cls._normalize_feature_dir(project_root, str(feature_value))

        env_feature = os.environ.get("SPECIFY_FEATURE_DIRECTORY", "").strip()
        if env_feature:
            return cls._normalize_feature_dir(project_root, env_feature)

        branch = cls._current_branch(project_root)
        if not branch:
            raise ValueError(
                "Unable to resolve active feature: no .specify/feature.json, "
                "SPECIFY_FEATURE_DIRECTORY, or git branch is available."
            )
        return cls._find_feature_dir_by_prefix(project_root, branch)

    @staticmethod
    def _normalize_feature_dir(project_root: Path, value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = project_root / path
        return path.resolve()

    @staticmethod
    def _current_branch(project_root: Path) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if proc.returncode != 0:
            return None
        branch = proc.stdout.strip()
        if branch == "HEAD":
            return None
        if "/" in branch:
            branch = branch.rsplit("/", 1)[1]
        return branch or None

    @classmethod
    def _find_feature_dir_by_prefix(cls, project_root: Path, branch: str) -> Path:
        specs_dir = project_root / "specs"
        prefix = ""
        timestamp = re.match(r"^(\d{8}-\d{6})-", branch)
        sequential = re.match(r"^(\d{3,})-", branch)
        if timestamp:
            prefix = timestamp.group(1)
        elif sequential:
            prefix = sequential.group(1)
        else:
            return (specs_dir / branch).resolve()

        matches = sorted(path for path in specs_dir.glob(f"{prefix}-*") if path.is_dir())
        if not matches:
            return (specs_dir / branch).resolve()
        if len(matches) > 1:
            names = ", ".join(path.name for path in matches)
            raise ValueError(
                f"Multiple spec directories found with prefix {prefix!r}: {names}."
            )
        return matches[0].resolve()

    @staticmethod
    def _require_feature_files(feature_dir: Path) -> None:
        if not feature_dir.is_dir():
            raise ValueError(f"Feature directory not found: {feature_dir}")
        missing = [
            name
            for name in ("spec.md", "plan.md", "tasks.md")
            if not (feature_dir / name).is_file()
        ]
        if missing:
            raise ValueError(
                f"Feature directory {feature_dir} is missing required file(s): "
                + ", ".join(missing)
            )

    @classmethod
    def _parse_tasks(cls, tasks_path: Path) -> list[ParsedTask]:
        current_phase = "Tasks"
        tasks: list[ParsedTask] = []
        for line in tasks_path.read_text(encoding="utf-8").splitlines():
            heading = _HEADING_RE.match(line)
            if heading:
                current_phase = heading.group("title").strip()
                continue

            match = _TASK_RE.match(line)
            if not match:
                continue

            task_id = match.group("id")
            text = line.strip()
            body = match.group("body")
            parallel = "[P]" in body
            paths = cls._extract_paths(body)
            if parallel and not paths:
                raise ValueError(
                    f"Parallel task {task_id} must declare at least one explicit path."
                )
            tasks.append(
                ParsedTask(
                    task_id=task_id,
                    text=text,
                    phase=current_phase,
                    parallel=parallel,
                    paths=paths,
                )
            )

        if not tasks:
            raise ValueError(f"No implementation tasks found in {tasks_path}.")
        cls._validate_parallel_conflicts(tasks)
        return tasks

    @classmethod
    def _extract_paths(cls, text: str) -> list[str]:
        candidates: list[str] = []
        for raw in _BACKTICK_RE.findall(text):
            candidates.extend(raw.split())
        candidates.extend(match.group(1) for match in _PATH_TOKEN_RE.finditer(text))

        paths: dict[str, None] = {}
        for candidate in candidates:
            normalized = cls._normalize_task_path(candidate)
            if normalized:
                paths.setdefault(normalized, None)
        return list(paths)

    @staticmethod
    def _normalize_task_path(raw: str) -> str | None:
        value = raw.strip().strip(".,;:()[]{}")
        if not value or value.startswith(("http://", "https://")):
            return None
        value = value.replace("\\", "/")
        if value in {".", ".."} or "/../" in f"/{value}/":
            return None
        if value.startswith("/"):
            value = value.lstrip("/")
        if not ("/" in value or "." in PurePosixPath(value).name):
            return None
        return str(PurePosixPath(value))

    @classmethod
    def _validate_parallel_conflicts(cls, tasks: list[ParsedTask]) -> None:
        by_phase: dict[str, list[ParsedTask]] = {}
        for task in tasks:
            if task.parallel:
                by_phase.setdefault(task.phase, []).append(task)

        for phase, phase_tasks in by_phase.items():
            for idx, left in enumerate(phase_tasks):
                for right in phase_tasks[idx + 1 :]:
                    overlap = cls._overlap(left.paths, right.paths)
                    if overlap:
                        raise ValueError(
                            f"Parallel tasks {left.task_id} and {right.task_id} in "
                            f"{phase!r} write overlapping path {overlap!r}."
                        )

    @classmethod
    def _build_shards(cls, tasks: list[ParsedTask], max_shards: int) -> list[TaskShard]:
        groups: list[list[ParsedTask]] = []
        current: list[ParsedTask] = []

        for task in tasks:
            if task.parallel:
                if current:
                    groups.append(current)
                    current = []
                groups.append([task])
            else:
                current.append(task)
        if current:
            groups.append(current)

        while len(groups) > max_shards:
            merge_index = cls._find_merge_candidate(groups)
            if merge_index is None:
                raise ValueError(
                    f"Unable to cap handoff shards at {max_shards} without merging "
                    "groups that declare overlapping write paths."
                )
            groups[merge_index] = groups[merge_index] + groups[merge_index + 1]
            del groups[merge_index + 1]

        width = max(2, len(str(len(groups))))
        return [
            TaskShard(f"shard-{idx + 1:0{width}d}", group)
            for idx, group in enumerate(groups)
        ]

    @classmethod
    def _find_merge_candidate(cls, groups: list[list[ParsedTask]]) -> int | None:
        for idx in range(len(groups) - 1):
            left_paths = cls._group_paths(groups[idx])
            right_paths = cls._group_paths(groups[idx + 1])
            if not cls._overlap(left_paths, right_paths):
                return idx
        return None

    @staticmethod
    def _group_paths(tasks: list[ParsedTask]) -> list[str]:
        paths: dict[str, None] = {}
        for task in tasks:
            for path in task.paths:
                paths.setdefault(path, None)
        return list(paths)

    @staticmethod
    def _overlap(left_paths: list[str], right_paths: list[str]) -> str | None:
        for left in left_paths:
            left_parts = PurePosixPath(left).parts
            for right in right_paths:
                right_parts = PurePosixPath(right).parts
                if left == right:
                    return left
                min_len = min(len(left_parts), len(right_parts))
                if left_parts[:min_len] == right_parts[:min_len]:
                    return left if len(left_parts) <= len(right_parts) else right
        return None

    @classmethod
    def _write_handoffs(
        cls,
        project_root: Path,
        feature_dir: Path,
        shards: list[TaskShard],
        original_args: str,
        run_id: str,
    ) -> list[dict[str, Any]]:
        handoff_dir = feature_dir / "handoffs" / "implement" / run_id
        handoff_dir.mkdir(parents=True, exist_ok=True)

        items: list[dict[str, Any]] = []
        for shard in shards:
            handoff_path = handoff_dir / f"{shard.shard_id}.json"
            payload = cls._handoff_payload(project_root, feature_dir, shard)
            handoff_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            shard_args = cls._handoff_args(original_args, handoff_path, shard)
            items.append(
                {
                    "shard_id": shard.shard_id,
                    "handoff_path": str(handoff_path),
                    "task_ids": shard.task_ids,
                    "args": shard_args,
                }
            )
        return items

    @classmethod
    def _handoff_payload(
        cls,
        project_root: Path,
        feature_dir: Path,
        shard: TaskShard,
    ) -> dict[str, Any]:
        feature_ref = cls._display_path(project_root, feature_dir)
        context_refs = [
            cls._display_path(project_root, feature_dir / name)
            for name in ("spec.md", "plan.md", "tasks.md")
        ]
        for optional_name in ("data-model.md", "research.md", "quickstart.md"):
            optional_path = feature_dir / optional_name
            if optional_path.is_file():
                context_refs.append(cls._display_path(project_root, optional_path))
        contracts_dir = feature_dir / "contracts"
        if contracts_dir.is_dir():
            context_refs.append(cls._display_path(project_root, contracts_dir))

        return {
            "contract_type": "speckit.implement.handoff.v1",
            "shard_id": shard.shard_id,
            "feature_dir": feature_ref,
            "task_ids": shard.task_ids,
            "task_text": [task.text for task in shard.tasks],
            "allowed_read_paths": list(dict.fromkeys([feature_ref, *context_refs])),
            "allowed_write_paths": shard.paths,
            "required_context_refs": context_refs,
            "validation_commands": [],
            "forbidden_actions": [
                "Do not modify tasks outside task_ids.",
                "Do not modify paths outside allowed_write_paths unless the task explicitly requires a generated adjacent file.",
                "Do not revert user changes or unrelated work.",
            ],
        }

    @staticmethod
    def _handoff_args(original_args: str, handoff_path: Path, shard: TaskShard) -> str:
        prefix = f"{original_args.strip()} " if original_args.strip() else ""
        task_ids = ", ".join(shard.task_ids)
        return (
            f"{prefix}Use handoff JSON {handoff_path}. "
            f"Execute only task IDs: {task_ids}."
        )

    @staticmethod
    def _display_path(project_root: Path, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(project_root))
        except ValueError:
            return str(path)
