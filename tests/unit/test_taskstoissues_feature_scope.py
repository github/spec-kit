"""Issue dedup in `/speckit-taskstoissues` must be scoped to one feature.

Task IDs are local to a feature: every `tasks.md` restarts at `T001`. Matching existing
issues by task ID alone means the first feature to reach the tracker permanently
suppresses `T001` for every later feature — the tasks are silently never created, which
is worse than the duplicates the matching was tightened to prevent (#4271).

These assert the template still carries the scoping, so a later edit to that step cannot
quietly drop it again.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = PROJECT_ROOT / "templates" / "commands" / "taskstoissues.md"


@pytest.fixture(scope="module")
def template_text() -> str:
    assert TEMPLATE.is_file(), f"missing command template: {TEMPLATE}"
    return TEMPLATE.read_text(encoding="utf-8")


def _line_containing(text: str, needle: str) -> str:
    matches = [line for line in text.splitlines() if needle in line]
    assert matches, f"no instruction line contains {needle!r} any more"
    return "\n".join(matches)


def test_the_canonical_title_carries_the_feature_identifier(template_text: str) -> None:
    """Without the feature in the title there is nothing for the dedup to scope on."""
    title_rule = _line_containing(template_text, "canonical title")
    assert re.search(r"`\[<feature>\]\s+T001:", title_rule), (
        "the canonical issue title no longer names the feature, so two features' T001 "
        f"issues are indistinguishable:\n  {title_rule.strip()}"
    )
    assert "FEATURE_DIR" in title_rule, (
        "the title rule should say where <feature> comes from (the FEATURE_DIR parsed in "
        f"step 1):\n  {title_rule.strip()}"
    )


def test_the_skip_rule_requires_both_feature_and_task_id(template_text: str) -> None:
    skip_rule = _line_containing(template_text, "**Skip**")
    assert "both" in skip_rule.lower(), (
        "the skip rule must require the feature identity as well as the task ID, or a "
        f"sibling feature's T001 suppresses this one:\n  {skip_rule.strip()}"
    )
    assert "feature" in skip_rule.lower(), skip_rule.strip()


def test_pre_existing_unscoped_issues_are_still_recognised(template_text: str) -> None:
    """Upgrading must not re-create issues that were filed before the prefix existed."""
    assert re.search(r"before this scoping exists|bare `T001", template_text), (
        "the template no longer says what to do with issues created before the feature "
        "prefix, so an upgrade would duplicate every already-tracked task"
    )
