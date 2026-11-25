"""Epic plan validation and DAG ordering.

The conductor agent writes ``.specify/autopilot/epics.json`` once. This module
checks it and turns it into a schedule. Two rules come from the design memo:

* Cycles are rejected; the plan goes back to the conductor.
* Epics whose ``touches`` globs may overlap are never run in parallel. When
  neither depends on the other, the later epic (plan order) gets a dependency
  on the earlier one, and the change is reported so the human gate sees it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,48}[a-z0-9]$|^[a-z0-9]$")
ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")
WILDCARD_CHARS = set("*?[")


class PlanError(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


@dataclass
class Epic:
    id: str
    slug: str
    title: str
    goal: str = ""
    scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    acceptance: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    touches: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    added_dependencies: list[str] = field(default_factory=list)

    def brief(self) -> str:
        """Feature description handed to ``/speckit.specify``."""
        lines = [f"{self.title}", "", self.goal.strip()] if self.goal.strip() else [self.title]
        if self.scope:
            lines += ["", "In scope:"] + [f"- {item}" for item in self.scope]
        if self.out_of_scope:
            lines += ["", "Out of scope (another epic or later):"] + [f"- {item}" for item in self.out_of_scope]
        if self.acceptance:
            lines += ["", "Acceptance criteria to turn into user stories and acceptance scenarios:"]
            lines += [f"- {item}" for item in self.acceptance]
        if self.requirements:
            lines += ["", "Source requirements (read these files):"] + [f"- {item}" for item in self.requirements]
        return "\n".join(lines).strip()


def _string_list(value: Any, where: str, problems: list[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        problems.append(f"{where} must be a list of strings")
        return []
    return [item.strip() for item in value if item.strip()]


def parse_plan(data: Any) -> list[Epic]:
    problems: list[str] = []
    if not isinstance(data, dict) or not isinstance(data.get("epics"), list):
        raise PlanError(["epics.json must be an object with an 'epics' list"])
    if not data["epics"]:
        raise PlanError(["epics.json has no epics"])
    epics: list[Epic] = []
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    for index, raw in enumerate(data["epics"]):
        where = f"epics[{index}]"
        if not isinstance(raw, dict):
            problems.append(f"{where} must be an object")
            continue
        epic_id = raw.get("id")
        slug = raw.get("slug")
        title = raw.get("title")
        if not isinstance(epic_id, str) or not ID_RE.match(epic_id):
            problems.append(f"{where}.id must match {ID_RE.pattern}")
            continue
        where = f"epic {epic_id}"
        if epic_id in seen_ids:
            problems.append(f"{where}: duplicate id")
        seen_ids.add(epic_id)
        if not isinstance(slug, str) or not SLUG_RE.match(slug):
            problems.append(f"{where}: slug must be lowercase kebab-case, 1-50 chars")
            slug = ""
        elif slug in seen_slugs:
            problems.append(f"{where}: duplicate slug {slug!r}")
        seen_slugs.add(slug or "")
        if not isinstance(title, str) or not title.strip():
            problems.append(f"{where}: title is required")
            title = ""
        goal = raw.get("goal", "")
        if not isinstance(goal, str):
            problems.append(f"{where}: goal must be a string")
            goal = ""
        epic = Epic(
            id=epic_id,
            slug=slug,
            title=title.strip(),
            goal=goal,
            scope=_string_list(raw.get("scope"), f"{where}.scope", problems),
            out_of_scope=_string_list(raw.get("out_of_scope"), f"{where}.out_of_scope", problems),
            requirements=_string_list(raw.get("requirements"), f"{where}.requirements", problems),
            acceptance=_string_list(raw.get("acceptance"), f"{where}.acceptance", problems),
            depends_on=_string_list(raw.get("depends_on"), f"{where}.depends_on", problems),
            touches=_string_list(raw.get("touches"), f"{where}.touches", problems),
            provides=_string_list(raw.get("provides"), f"{where}.provides", problems),
        )
        if not epic.acceptance:
            problems.append(f"{where}: at least one acceptance criterion is required")
        epics.append(epic)
    ids = {epic.id for epic in epics}
    for epic in epics:
        for dep in epic.depends_on:
            if dep == epic.id:
                problems.append(f"epic {epic.id}: depends on itself")
            elif dep not in ids:
                problems.append(f"epic {epic.id}: unknown dependency {dep!r}")
    if problems:
        raise PlanError(problems)
    cycle = find_cycle(epics)
    if cycle:
        raise PlanError([f"dependency cycle: {' -> '.join(cycle)}"])
    return epics


def find_cycle(epics: list[Epic]) -> list[str]:
    graph = {epic.id: list(epic.depends_on) for epic in epics}
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        state[node] = 1
        stack.append(node)
        for dep in graph.get(node, []):
            if state.get(dep) == 1:
                return stack[stack.index(dep):] + [dep]
            if dep not in state:
                found = visit(dep)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return []

    for epic in epics:
        if epic.id not in state:
            found = visit(epic.id)
            if found:
                return found
    return []


def _static_prefix(pattern: str) -> list[str]:
    """Path segments before the first wildcard."""
    segments = [seg for seg in pattern.replace("\\", "/").strip("/").split("/") if seg not in ("", ".")]
    prefix: list[str] = []
    for segment in segments:
        if WILDCARD_CHARS & set(segment):
            break
        prefix.append(segment)
    return prefix


def globs_may_overlap(left: str, right: str) -> bool:
    """Conservative overlap test: false only when the globs are provably disjoint.

    Over-reporting serialises epics that could have run in parallel, which is
    slower but safe; under-reporting would let two pipes edit the same files.
    """
    # Paths are told apart only by the segments before any wildcard. Literal
    # paths overlap when equal or when one is a directory of the other; a glob
    # overlaps anything under or above its static prefix.
    left_prefix = _static_prefix(left)
    right_prefix = _static_prefix(right)
    shorter = min(len(left_prefix), len(right_prefix))
    return left_prefix[:shorter] == right_prefix[:shorter]


def ancestors(epics: list[Epic]) -> dict[str, set[str]]:
    by_id = {epic.id: epic for epic in epics}
    memo: dict[str, set[str]] = {}

    def walk(epic_id: str) -> set[str]:
        if epic_id not in memo:
            memo[epic_id] = set()
            for dep in by_id[epic_id].depends_on:
                memo[epic_id] |= {dep} | walk(dep)
        return memo[epic_id]

    for epic in epics:
        walk(epic.id)
    return memo


def serialise_overlaps(epics: list[Epic]) -> list[str]:
    """Add dependencies between independent epics whose touches overlap."""
    notes: list[str] = []
    for later_index, later in enumerate(epics):
        for earlier in epics[:later_index]:
            related = ancestors(epics)
            if earlier.id in related[later.id] or later.id in related[earlier.id]:
                continue
            overlap = next(
                ((a, b) for a in earlier.touches for b in later.touches if globs_may_overlap(a, b)),
                None,
            )
            if overlap is None and (not earlier.touches or not later.touches):
                # An epic that declares no touches could edit anything.
                overlap = ("<undeclared>", "<undeclared>")
            if overlap:
                later.depends_on.append(earlier.id)
                later.added_dependencies.append(earlier.id)
                notes.append(
                    f"{later.id} now depends on {earlier.id}: touches may overlap "
                    f"({overlap[0]} / {overlap[1]})"
                )
    return notes


def topological_order(epics: list[Epic]) -> list[Epic]:
    """Kahn's algorithm, stable on plan order."""
    remaining = list(epics)
    done: set[str] = set()
    ordered: list[Epic] = []
    while remaining:
        ready = [epic for epic in remaining if all(dep in done for dep in epic.depends_on)]
        if not ready:  # pragma: no cover - parse_plan rejects cycles first
            raise PlanError(["dependency cycle"])
        for epic in ready:
            ordered.append(epic)
            done.add(epic.id)
            remaining.remove(epic)
    return ordered


def waves(epics: list[Epic]) -> list[list[str]]:
    """Group epics by DAG depth, for the human-readable plan."""
    depth: dict[str, int] = {}
    for epic in topological_order(epics):
        depth[epic.id] = 1 + max((depth[dep] for dep in epic.depends_on), default=-1)
    grouped: dict[int, list[str]] = {}
    for epic in epics:
        grouped.setdefault(depth[epic.id], []).append(epic.id)
    return [grouped[level] for level in sorted(grouped)]


def next_feature_number(specs_dir: Path) -> int:
    highest = 0
    if specs_dir.is_dir():
        for child in specs_dir.iterdir():
            match = re.match(r"^(\d+)-", child.name)
            if child.is_dir() and match and len(match.group(1)) < 8:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def assign_feature_dirs(epics: list[Epic], specs_dir: Path) -> dict[str, str]:
    """``{epic_id: "specs/NNN-slug"}`` in topological order."""
    number = next_feature_number(specs_dir)
    assigned: dict[str, str] = {}
    for epic in topological_order(epics):
        assigned[epic.id] = f"specs/{number:03d}-{epic.slug}"
        number += 1
    return assigned
