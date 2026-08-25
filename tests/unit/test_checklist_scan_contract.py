"""Every command that scans checkbox markers must say it skips code fences.

A checklist is free to *document* the checkbox format inside a fenced block. Counting
those example markers reports items nobody can tick, and `/speckit-implement` treats a
non-zero unchecked count as a reason to stop — so an example fence blocks implementation
(#4272). `/speckit-clarify` already scoped its scan to markers outside code fences; this
keeps the two commands from drifting apart again, and holds any future command that
starts counting markers to the same rule.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COMMAND_DIRS = [
    PROJECT_ROOT / "templates" / "commands",
    *sorted((PROJECT_ROOT / "presets").glob("*/commands")),
]

# The instruction that tells the agent which lines are checkbox markers. Written to catch
# the phrasing both commands use rather than one exact sentence.
SCAN_INSTRUCTION = re.compile(r"lines matching\s+`- \[ \]`", re.IGNORECASE)
FENCE_EXCLUSION = re.compile(r"outside\s+(?:of\s+)?code\s+fences", re.IGNORECASE)


def scan_instructions() -> list[tuple[Path, int, str]]:
    """Every line in a command template that defines what counts as a checkbox marker."""
    found: list[tuple[Path, int, str]] = []
    for directory in COMMAND_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if SCAN_INSTRUCTION.search(line):
                    found.append((path, number, line))
    return found


def test_the_contract_is_actually_stated_somewhere() -> None:
    """Guard against the regex silently matching nothing and the test passing vacuously."""
    assert scan_instructions(), "no command template defines a checkbox-marker scan any more"


@pytest.mark.parametrize(
    ("path", "number", "line"),
    scan_instructions(),
    ids=lambda value: value.name if isinstance(value, Path) else str(value),
)
def test_marker_scans_exclude_code_fences(path: Path, number: int, line: str) -> None:
    assert FENCE_EXCLUSION.search(line), (
        f"{path.relative_to(PROJECT_ROOT)}:{number} tells the agent to match checkbox "
        f"markers without excluding fenced code blocks, so an example fence is counted "
        f"as real work:\n  {line.strip()}"
    )
