#!/usr/bin/env python3
"""Validate template front matter and required sections."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

TEMPLATES = {
    "templates/spec-template.md": {
        "sections": [
            "## Executive Summary",
            "## Assumptions",
            "## Out of Scope",
            "## Risks",
            "## Open Questions",
            "## User Scenarios & Testing",
            "## Requirements",
            "## Success Criteria",
            "## Traceability Matrix",
            "## Clarifications History",
        ]
    },
    "templates/plan-template.md": {
        "sections": [
            "## Phase Exit Criteria",
            "## Technical Context",
            "## Constitution Check",
            "## Decision Log",
            "## Risk Register",
            "## Research Backlog",
            "## Architecture & Contracts",
            "## Implementation Readiness",
            "## Project Structure",
            "## Complexity Tracking",
        ]
    },
    "templates/tasks-template.md": {
        "sections": [
            "## Task Formatting Rules",
            "## Dependency Registry",
            "## Mermaid Dependency Graph",
            "## Phase Overview",
            "## Definition of Done per User Story",
            "## Phase 1",
            "## Phase 2",
            "## Task Metrics Summary",
        ]
    },
}

REQUIRED_FRONT_MATTER_KEYS = {
    "feature_id",
    "branch",
    "created_at",
    "generator_version",
    "constitution_version",
}


def parse_front_matter(content: str) -> tuple[dict[str, str], str]:
    lines = content.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError("missing front matter delimiter")
    end_index = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = idx
            break
    if end_index is None:
        raise ValueError("front matter not terminated")
    fm_lines = lines[1:end_index]
    body = "\n".join(lines[end_index + 1 :])
    fm = {}
    for raw in fm_lines:
        if not raw.strip():
            continue
        if ":" not in raw:
            raise ValueError(f"invalid front matter line: {raw!r}")
        key, value = raw.split(":", 1)
        fm[key.strip()] = value.strip()
    return fm, body


def validate_template(path: Path, config: dict[str, object]) -> list[str]:
    errors: list[str] = []
    content = path.read_text(encoding="utf-8")
    fm, body = parse_front_matter(content)
    missing_keys = REQUIRED_FRONT_MATTER_KEYS - set(fm)
    if missing_keys:
        errors.append(f"{path}: missing front matter keys {sorted(missing_keys)}")
    for section in config["sections"]:
        if section not in body:
            errors.append(f"{path}: missing section '{section}'")
    return errors


def main() -> int:
    all_errors: list[str] = []
    for rel_path, config in TEMPLATES.items():
        path = ROOT / rel_path
        if not path.exists():
            all_errors.append(f"missing template {rel_path}")
            continue
        all_errors.extend(validate_template(path, config))
    if all_errors:
        for err in all_errors:
            print(err, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
