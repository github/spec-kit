"""Artifact contracts shared by the eleven-command workflow helpers.

Component: workflow helpers; target: developer workstation; task: fork workflow.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from common import get_feature_paths


def paths() -> dict[str, Path]:
    selected = get_feature_paths(no_persist=True, script_file=Path(__file__))
    root = selected.repo_root.resolve()
    feature = selected.feature_dir.resolve()
    if not feature.is_relative_to(root) or feature == root:
        raise ValueError("The feature directory must be inside the project")
    return {
        "REPO_ROOT": root,
        "FEATURE_DIR": feature,
        "CONSTITUTION": root / ".specify/memory/constitution.md",
        "SPEC": feature / "spec.md",
        "ARCHITECTURE": root / ".specify/memory/architecture.md",
        "ENVIRONMENT": root / ".specify/memory/environment.md",
        "PLAN": feature / "plan.md",
        "TASKS_CODE": feature / "tasks-code.md",
        "CODE_PROGRESS": feature / "code-progress.json",
        "ANALYSIS": feature / "analysis.md",
        "DEPLOYMENT": feature / "deployment.md",
        "TEST_REPORT": feature / "test-report.md",
        "BUGS": feature / "bugs.md",
    }


def require_files(selected: dict[str, Path], keys: list[str]) -> None:
    for key in keys:
        path = selected[key]
        if not path.is_file() or not path.read_text(encoding="utf-8-sig").strip():
            raise ValueError(f"Missing or empty {key}: {path}")


def read_inventory(path: Path) -> dict:
    """Read the single canonical JSON inventory embedded in an artifact."""
    blocks = re.findall(
        r"^```json\s*\n(.*?)^```\s*$", path.read_text(encoding="utf-8-sig"), re.M | re.S
    )
    if len(blocks) != 1:
        raise ValueError(f"{path.name} must contain exactly one fenced JSON inventory")
    value = json.loads(blocks[0])
    if (
        not isinstance(value, dict)
        or type(value.get("schema_version")) is not int
        or value["schema_version"] != 1
    ):
        raise ValueError(f"Unsupported inventory schema in {path.name}")
    return value


def records(value: object, kind: str) -> dict[str, dict]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{kind} must be a nonempty list")
    result = {}
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError(f"Each {kind} entry needs a string id")
        key = item["id"]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key) or key in result:
            raise ValueError(f"Invalid or duplicate {kind} id: {key}")
        result[key] = item
    return result


def architecture(selected: dict[str, Path]) -> dict[str, dict]:
    return records(
        read_inventory(selected["ARCHITECTURE"]).get("components"), "component"
    )


def environment(selected: dict[str, Path]) -> dict[str, dict]:
    components = architecture(selected)
    assets = records(read_inventory(selected["ENVIRONMENT"]).get("assets"), "asset")
    assigned = set()
    for asset in assets.values():
        for key in ("os", "os_version", "runtime"):
            if not isinstance(asset.get(key), str) or not asset[key].strip():
                raise ValueError(f"Asset {asset['id']} needs {key}")
        minimum, recommended = asset.get("minimum"), asset.get("recommended")
        if (
            not isinstance(minimum, dict)
            or not minimum
            or not isinstance(recommended, dict)
        ):
            raise ValueError(
                f"Asset {asset['id']} needs minimum and recommended resources"
            )
        if set(minimum) != set(recommended):
            raise ValueError(f"Asset {asset['id']} resource dimensions must match")
        for key, value in minimum.items():
            other = recommended[key]
            if (
                isinstance(value, bool)
                or isinstance(other, bool)
                or not isinstance(value, (int, float))
                or not isinstance(other, (int, float))
                or not 0 < value <= other < float("inf")
            ):
                raise ValueError(
                    f"Asset {asset['id']} requires positive minimum <= recommended for {key}"
                )
        members = asset.get("components")
        if (
            not isinstance(members, list)
            or not members
            or any(not isinstance(c, str) or c not in components for c in members)
        ):
            raise ValueError(
                f"Asset {asset['id']} references unknown or missing components"
            )
        if len(set(members)) != len(members):
            raise ValueError(f"Asset {asset['id']} repeats a component")
        assigned.update(members)
    if assigned != set(components):
        raise ValueError(
            f"Components without an asset: {sorted(set(components) - assigned)}"
        )
    return assets


def source_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Task file paths must be project-relative POSIX paths")
    relative = PurePosixPath(value)
    if relative.as_posix() != value or "*" in value or "?" in value:
        raise ValueError(f"Use a concrete, normalized task file path: {value}")
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"Unsafe task file path: {value}")
    if any(
        part.lower()
        in {
            ".git",
            ".specify",
            "specs",
            "tests",
            "test",
            "__tests__",
            "e2e",
            "deploy",
            "deployment",
            "terraform",
            ".github",
        }
        for part in relative.parts
    ):
        raise ValueError(
            f"Coding tasks cannot own governance, specification, or test files: {value}"
        )
    if re.search(r"(^test_|_test\.|\.test\.|\.spec\.)", relative.name, re.I):
        raise ValueError(f"Coding tasks cannot own test files: {value}")
    if relative.name.lower() in {
        "agents.md",
        "claude.md",
        "conftest.py",
        "pytest.ini",
        "dockerfile",
        "docker-compose.yml",
        "compose.yaml",
    }:
        raise ValueError(
            f"Coding tasks cannot own governance, testing or deployment files: {value}"
        )
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"Task file escapes project: {value}")
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError(f"Symlinked task path: {value}")
        current = current.parent
    return path


def tasks(selected: dict[str, Path]) -> dict[str, dict]:
    assets = environment(selected)
    components = architecture(selected)
    result = records(read_inventory(selected["TASKS_CODE"]).get("tasks"), "task")
    spellings = {}
    for key, task in result.items():
        if not re.fullmatch(r"T\d{3,}", key):
            raise ValueError(f"Invalid coding task id: {key}")
        if task.get("category") not in {
            "code",
            "integration",
            "configuration",
            "migration",
        }:
            raise ValueError(f"Task {key} must be a coding category")
        if (
            not isinstance(task.get("component"), str)
            or task["component"] not in components
        ):
            raise ValueError(f"Task {key} references an unknown component")
        for field in ("title", "done_when"):
            if not isinstance(task.get(field), str) or not task[field].strip():
                raise ValueError(f"Task {key} needs {field}")
        for field in ("files", "deployment_targets", "requirement_ids"):
            value = task.get(field)
            if (
                not isinstance(value, list)
                or not value
                or any(not isinstance(v, str) or not v for v in value)
            ):
                raise ValueError(f"Task {key} needs nonempty {field}")
            if len(value) != len(set(value)):
                raise ValueError(f"Task {key} repeats {field}")
        for target in task["deployment_targets"]:
            if (
                target not in assets
                or task["component"] not in assets[target]["components"]
            ):
                raise ValueError(
                    f"Task {key} has an incompatible deployment target: {target}"
                )
        for name in task["files"]:
            canonical = source_path(selected["REPO_ROOT"], name).resolve()
            if canonical in spellings and spellings[canonical] != name:
                raise ValueError(
                    f"Use consistent spelling for shared task file: {name}"
                )
            spellings[canonical] = name
        deps = task.get("depends_on")
        if not isinstance(deps, list) or any(
            not isinstance(d, str) or d not in result or d == key for d in deps
        ):
            raise ValueError(f"Task {key} has unknown or self dependencies")
        if len(deps) != len(set(deps)):
            raise ValueError(f"Task {key} repeats dependencies")
    visiting, visited = set(), set()

    def visit(key: str) -> None:
        if key in visiting:
            raise ValueError(f"Coding dependency cycle at {key}")
        if key in visited:
            return
        visiting.add(key)
        for dep in result[key]["depends_on"]:
            visit(dep)
        visiting.remove(key)
        visited.add(key)

    for key in result:
        visit(key)
    return result


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


def fingerprints(selected: dict[str, Path]) -> dict[str, str]:
    inputs = [
        selected[k]
        for k in ("CONSTITUTION", "SPEC", "ARCHITECTURE", "ENVIRONMENT", "PLAN")
    ]
    inputs.extend(
        selected["FEATURE_DIR"] / name for name in ("research.md", "data-model.md")
    )
    contracts = selected["FEATURE_DIR"] / "contracts"
    if contracts.is_dir():
        inputs.extend(sorted(p for p in contracts.rglob("*") if p.is_file()))
    return {
        str(p.relative_to(selected["REPO_ROOT"])): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for p in inputs
        if p.is_file()
    }
