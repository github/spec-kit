"""Read Spec Kit feature artifacts: feature directory, scenarios and tasks.

Acceptance scenarios get stable IDs derived from ``spec.md`` structure, so the
gate can check traceability without an LLM:

    ### User Story 2 - ... (Priority: P1)
    **Acceptance Scenarios**:
    1. **Given** ...      ->  <feature-number>-US2-AS1

A test covers a scenario when a test file contains that ID, with ``-`` or
``_`` between the parts and any letter case (``test_003_us2_as1_login`` and
``// 003-US2-AS1`` both match).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

STORY_RE = re.compile(r"^#{2,4}\s+User Story\s+(\d+)\b", re.IGNORECASE)
ACCEPTANCE_RE = re.compile(r"^\*\*Acceptance Scenarios\*\*\s*:?", re.IGNORECASE)
NUMBERED_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
HEADING_RE = re.compile(r"^#{1,6}\s")
BOLD_LABEL_RE = re.compile(r"^\*\*[^*]+\*\*\s*:")
CLARIFY_MARKER = "[NEEDS CLARIFICATION"
TASK_OPEN_RE = re.compile(r"^\s*[-*]\s+\[ \]\s+(.*)$")
TASK_DONE_RE = re.compile(r"^\s*[-*]\s+\[[xX]\]\s+(.*)$")
TASK_ID_RE = re.compile(r"\bT(\d{3,})\b")
PHASE_RE = re.compile(r"^##\s+Phase\s+(\d+)\b", re.IGNORECASE)
FEATURE_PREFIX_RE = re.compile(r"^(\d+(?:-\d{6})?)-")


@dataclass(frozen=True)
class Scenario:
    tag: str
    story: int
    index: int
    text: str

    def pattern(self) -> re.Pattern[str]:
        parts = [re.escape(part) for part in self.tag.split("-")]
        return re.compile(r"(?<![0-9A-Za-z])" + r"[-_]".join(parts) + r"(?![0-9])", re.IGNORECASE)


class FeatureError(RuntimeError):
    """The feature directory cannot be resolved or is incomplete."""


def resolve_feature_dir(project_root: Path) -> Path:
    """Mirror ``scripts/python/common.py``: env var first, then feature.json."""
    raw = os.environ.get("SPECIFY_FEATURE_DIRECTORY", "").strip()
    if not raw:
        feature_json = project_root / ".specify" / "feature.json"
        if feature_json.is_file():
            try:
                raw = str(json.loads(feature_json.read_text(encoding="utf-8")).get("feature_directory", ""))
            except (json.JSONDecodeError, AttributeError) as exc:
                raise FeatureError(f"{feature_json} is not valid JSON: {exc}") from exc
    if not raw:
        raise FeatureError(
            "Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY or run "
            "/speckit.specify so .specify/feature.json exists."
        )
    path = Path(raw)
    if not path.is_absolute():
        path = project_root / path
    return path


def feature_number(feature_dir: Path) -> str:
    match = FEATURE_PREFIX_RE.match(feature_dir.name)
    return match.group(1) if match else "F"


def parse_scenarios(spec_text: str, number: str) -> list[Scenario]:
    scenarios: list[Scenario] = []
    story: int | None = None
    in_acceptance = False
    for line in spec_text.splitlines():
        story_match = STORY_RE.match(line)
        if story_match:
            story = int(story_match.group(1))
            in_acceptance = False
            continue
        if HEADING_RE.match(line) or line.strip() == "---":
            in_acceptance = False
            if HEADING_RE.match(line) and len(line) - len(line.lstrip("#")) <= 3:
                story = None  # a sibling/parent section ends the story
            continue
        if ACCEPTANCE_RE.match(line.strip()):
            in_acceptance = story is not None
            continue
        if in_acceptance and BOLD_LABEL_RE.match(line.strip()):
            in_acceptance = False
            continue
        if in_acceptance and story is not None:
            numbered = NUMBERED_RE.match(line)
            if numbered:
                index = int(numbered.group(1))
                text = numbered.group(2).strip()
                scenarios.append(Scenario(f"{number}-US{story}-AS{index}", story, index, text))
    return scenarios


def clarification_markers(spec_text: str) -> int:
    return spec_text.count(CLARIFY_MARKER)


def open_tasks(tasks_text: str) -> list[str]:
    return [m.group(1).strip() for line in tasks_text.splitlines() if (m := TASK_OPEN_RE.match(line))]


def done_tasks(tasks_text: str) -> list[str]:
    return [m.group(1).strip() for line in tasks_text.splitlines() if (m := TASK_DONE_RE.match(line))]


def append_task_phase(tasks_path: Path, title: str, descriptions: list[str]) -> list[str]:
    """Append ``## Phase N: <title>`` with new unchecked tasks; return their IDs.

    Append-only, like ``/speckit.converge``: existing content is never edited.
    Nothing is written when ``descriptions`` is empty.
    """
    if not descriptions:
        return []
    text = tasks_path.read_text(encoding="utf-8") if tasks_path.is_file() else ""
    next_id = max((int(m) for m in TASK_ID_RE.findall(text)), default=0) + 1
    next_phase = max((int(m.group(1)) for line in text.splitlines() if (m := PHASE_RE.match(line))), default=0) + 1
    width = max(3, len(str(next_id + len(descriptions))))
    ids: list[str] = []
    block = [f"## Phase {next_phase}: {title}", ""]
    for offset, description in enumerate(descriptions):
        task_id = f"T{next_id + offset:0{width}d}"
        ids.append(task_id)
        one_line = " ".join(description.split())
        block.append(f"- [ ] {task_id} [AP] {one_line}")
    separator = "" if not text or text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    with tasks_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(separator + "\n".join(block) + "\n")
    return ids
