"""Regression tests for top-level step numbering in specify.md."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SPECIFY_TEMPLATE = REPO_ROOT / "templates" / "commands" / "specify.md"
MAIN_LIST_START = "Given that feature description, do this:"
MAIN_LIST_END = "## Mandatory Post-Execution Hooks"


def _main_execution_ordinals(text: str) -> list[int]:
    """Extract top-level ordinals from the main execution flow."""
    _, start, execution_flow = text.partition(MAIN_LIST_START)
    execution_flow, end, _ = execution_flow.partition(MAIN_LIST_END)
    if not start or not end:
        return []

    return [
        int(match.group(1))
        for line in execution_flow.splitlines()
        if (match := re.match(r"^(\d+)\. ", line))
    ]


def test_main_execution_list_has_no_duplicate_ordinals():
    """The main execution list must not reuse a step number."""
    ordinals = _main_execution_ordinals(SPECIFY_TEMPLATE.read_text(encoding="utf-8"))
    duplicates = {ordinal for ordinal in ordinals if ordinals.count(ordinal) > 1}

    assert not duplicates, f"Duplicate top-level ordinals found: {sorted(duplicates)}"


def test_main_execution_list_is_sequential():
    """The main execution list must run from 1 through N without gaps."""
    ordinals = _main_execution_ordinals(SPECIFY_TEMPLATE.read_text(encoding="utf-8"))

    assert ordinals, "Could not find the main execution list in specify.md"
    assert ordinals == list(range(1, 9))
