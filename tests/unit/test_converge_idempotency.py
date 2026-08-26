"""`/speckit-converge` must not append work that an unchecked task already tracks.

The command's only write is appending remediation tasks to `tasks.md`. It knew how to
compute the next task ID, but not whether a finding was already represented — so running
it twice, or running it before `/speckit-implement` had worked through the list, appended
the same work again under fresh IDs and split one piece of work across two entries
(#4269). The dedup rule is what makes the command idempotent, so it is pinned here rather
than left to survive on prose alone.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = PROJECT_ROOT / "templates" / "commands" / "converge.md"


@pytest.fixture(scope="module")
def template_text() -> str:
    assert TEMPLATE.is_file(), f"missing command template: {TEMPLATE}"
    return TEMPLATE.read_text(encoding="utf-8")


def test_the_append_step_still_exists(template_text: str) -> None:
    """Guard against the assertions below passing vacuously if the step is renamed away."""
    assert re.search(r"Append Convergence Tasks", template_text), (
        "the append step is gone; the rules below no longer describe this command"
    )


def test_findings_are_compared_against_existing_unchecked_tasks(template_text: str) -> None:
    assert re.search(r"unchecked task", template_text, re.IGNORECASE), (
        "converge no longer says to compare findings against existing unchecked tasks, so "
        "a second run appends the same work again under new IDs"
    )
    assert re.search(r"`- \[ \]`", template_text), (
        "the comparison should name the marker it scans for, so the rule is executable"
    )


def test_the_comparison_skips_code_fences(template_text: str) -> None:
    """Same rule the other commands apply — an example checkbox is not a tracked task."""
    assert re.search(r"outside\s+(?:of\s+)?code\s+fences", template_text, re.IGNORECASE), (
        "the scan must exclude fenced blocks, or a checklist documenting the checkbox "
        "format reads as tracked work"
    )


def test_already_tracked_findings_are_reported_not_silently_dropped(template_text: str) -> None:
    assert re.search(r"already tracked", template_text, re.IGNORECASE), (
        "a finding dropped as already-tracked must be reported; dropping it silently is "
        "indistinguishable from not having found it"
    )
