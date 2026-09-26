"""Private persisted cursors for exact sequential workflow resume.

The cursor is deliberately independent of the step registry.  Commands which
only inspect a run must be able to validate its progress even when a custom
step plugin is not installed in the current process.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

CONTINUATION_VERSION = 1
_PHASES = frozenset({"running", "paused", "failed", "interrupted", "children"})
_SOURCE_KINDS = frozenset({"workflow", "expansion"})


@dataclass
class SequenceSource:
    kind: str
    snapshot: str | None = None


@dataclass
class ActivationCursor:
    activation_path: list[dict[str, Any]]
    step_id: str
    step_type: str
    attempt: int
    phase: str
    child_sequence: SequenceCursor | None = None


@dataclass
class SequenceCursor:
    source: SequenceSource
    next_index: int = 0
    active: ActivationCursor | None = None


@dataclass
class Continuation:
    version: int
    sequence: SequenceCursor

    def serialize(self) -> dict[str, Any]:
        return asdict(self)


def new_continuation() -> dict[str, Any]:
    """Return the initial root cursor in its JSON-persisted form."""
    return Continuation(
        version=CONTINUATION_VERSION,
        sequence=SequenceCursor(source=SequenceSource(kind="workflow")),
    ).serialize()


def _continuations_dir(run_dir: Path) -> Path:
    return run_dir / "continuations"


def _safe_snapshot_path(run_dir: Path, ref: str) -> Path:
    if not isinstance(ref, str) or not ref.startswith("continuations/"):
        raise ValueError("Invalid continuation: unsafe snapshot reference")
    name = ref.removeprefix("continuations/")
    if "/" in name or "\\" in name or not name.endswith(".yml"):
        raise ValueError("Invalid continuation: unsafe snapshot reference")
    digest = name[:-4]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("Invalid continuation: unsafe snapshot reference")
    directory = _continuations_dir(run_dir)
    path = directory / name
    try:
        path.relative_to(directory)
    except ValueError as exc:  # pragma: no cover - defensive containment check
        raise ValueError("Invalid continuation: unsafe snapshot reference") from exc
    if path.is_symlink():
        raise ValueError("Invalid continuation: snapshot must not be a symlink")
    return path


def _normalize_steps(steps: Any) -> list[dict[str, Any]]:
    if not isinstance(steps, list):
        raise ValueError("Continuation expansion must be a list of step mappings")
    normalized: list[dict[str, Any]] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(
                "Continuation expansion entries must be step mappings"
            )
        copy = dict(step)
        step_id = copy.get("id")
        if step_id is None:
            copy["id"] = f"step-{index}"
        elif not isinstance(step_id, str) or not step_id:
            raise ValueError("Continuation expansion step IDs must be non-empty strings")
        normalized.append(copy)
    return normalized


def write_expansion_snapshot(run_dir: Path, steps: Any) -> tuple[str, list[dict[str, Any]]]:
    """Write an immutable normalized child sequence before state references it."""
    normalized = _normalize_steps(steps)
    content = yaml.safe_dump(normalized, sort_keys=False, allow_unicode=False).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    directory = _continuations_dir(run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink():
        raise ValueError("Invalid continuation: continuations directory must not be a symlink")
    ref = f"continuations/{digest}.yml"
    path = _safe_snapshot_path(run_dir, ref)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != content:
            raise ValueError("Invalid continuation: conflicting expansion snapshot")
        return ref, normalized
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
    except BaseException:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return ref, normalized


def read_expansion_snapshot(run_dir: Path, ref: str) -> list[dict[str, Any]]:
    """Load and verify an immutable expansion snapshot."""
    path = _safe_snapshot_path(run_dir, ref)
    try:
        content = path.read_bytes()
    except FileNotFoundError as exc:
        raise ValueError("Invalid continuation: expansion snapshot is missing") from exc
    digest = hashlib.sha256(content).hexdigest()
    if path.name != f"{digest}.yml":
        raise ValueError("Invalid continuation: expansion snapshot hash mismatch")
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError("Invalid continuation: malformed expansion snapshot") from exc
    normalized = _normalize_steps(parsed)
    if normalized != parsed:
        raise ValueError("Invalid continuation: expansion snapshot is not normalized")
    return normalized


def _validate_path(path: Any) -> None:
    if not isinstance(path, list) or not path:
        raise ValueError("Invalid continuation: activation_path must be a non-empty list")
    for segment in path:
        if not isinstance(segment, dict) or not isinstance(segment.get("kind"), str):
            raise ValueError("Invalid continuation: invalid activation path segment")


def validate_continuation(
    data: Any,
    *,
    run_dir: Path,
    root_steps: list[dict[str, Any]] | None = None,
) -> None:
    """Validate a persisted cursor and every snapshot it references."""
    if not isinstance(data, dict):
        raise ValueError("Invalid continuation: expected a JSON object")
    version = data.get("version")
    if version != CONTINUATION_VERSION:
        if isinstance(version, int) and version > CONTINUATION_VERSION:
            raise ValueError("Unsupported continuation version: run was created by a newer Specify version")
        raise ValueError(f"Unsupported continuation version: {version!r}")
    _validate_sequence(data.get("sequence"), run_dir=run_dir, root_steps=root_steps)


def _validate_sequence(
    data: Any,
    *,
    run_dir: Path,
    root_steps: list[dict[str, Any]] | None,
) -> None:
    if not isinstance(data, dict):
        raise ValueError("Invalid continuation: sequence must be a JSON object")
    source = data.get("source")
    if not isinstance(source, dict) or source.get("kind") not in _SOURCE_KINDS:
        raise ValueError("Invalid continuation: unknown sequence source")
    kind = source["kind"]
    ref = source.get("snapshot")
    if kind == "expansion":
        steps = read_expansion_snapshot(run_dir, ref)
    elif ref is not None:
        raise ValueError("Invalid continuation: workflow source must not have a snapshot")
    else:
        steps = root_steps
    next_index = data.get("next_index")
    if isinstance(next_index, bool) or not isinstance(next_index, int) or next_index < 0:
        raise ValueError("Invalid continuation: next_index must be a non-negative integer")
    if steps is not None and next_index > len(steps):
        raise ValueError("Invalid continuation: next_index is outside its sequence")
    active = data.get("active")
    if active is None:
        return
    if not isinstance(active, dict):
        raise ValueError("Invalid continuation: active must be a JSON object or null")
    _validate_path(active.get("activation_path"))
    if not isinstance(active.get("step_id"), str) or not active["step_id"]:
        raise ValueError("Invalid continuation: active step_id must be a non-empty string")
    if not isinstance(active.get("step_type"), str) or not active["step_type"]:
        raise ValueError("Invalid continuation: active step_type must be a non-empty string")
    attempt = active.get("attempt")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise ValueError("Invalid continuation: active attempt must be a positive integer")
    if active.get("phase") not in _PHASES:
        raise ValueError("Invalid continuation: unknown activation phase")
    if steps is not None:
        if next_index >= len(steps):
            raise ValueError("Invalid continuation: active activation is past its sequence")
        step = steps[next_index]
        if active["step_id"] != step.get("id") or active["step_type"] != step.get("type", "command"):
            raise ValueError("Invalid continuation: active activation does not match its sequence")
    child = active.get("child_sequence")
    if active["phase"] == "children":
        if child is None:
            raise ValueError("Invalid continuation: children activation requires child_sequence")
        _validate_sequence(child, run_dir=run_dir, root_steps=None)
    elif child is not None:
        raise ValueError("Invalid continuation: only children activations may have child_sequence")


def sequence_steps(cursor: dict[str, Any], *, root_steps: list[dict[str, Any]], run_dir: Path) -> list[dict[str, Any]]:
    """Resolve a cursor source to its immutable full sequence."""
    source = cursor["source"]
    if source["kind"] == "workflow":
        return root_steps
    return read_expansion_snapshot(run_dir, source["snapshot"])


def allows_expansion_index(continuation: dict[str, Any], index: int) -> bool:
    """Accept an expansion-relative compatibility index from early cursor runs."""
    sequence = continuation["sequence"]
    active = sequence.get("active")
    while active is not None and active.get("phase") == "children":
        sequence = active["child_sequence"]
        if sequence["next_index"] == index and sequence.get("active") is not None:
            return True
        active = sequence.get("active")
    return False


def active_leaf(sequence: dict[str, Any]) -> dict[str, Any] | None:
    """Return the deepest active activation in a cursor tree."""
    active = sequence.get("active")
    if active is None:
        return None
    child = active.get("child_sequence")
    if child is not None:
        leaf = active_leaf(child)
        if leaf is not None:
            return leaf
    return active
