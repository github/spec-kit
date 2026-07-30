"""Regression test for the converge.md template output contract.

Pins the three requirements introduced in issue #3752:
1. Step 6 summary metrics use per-category denominator syntax (checked/total).
2. Step 6 includes a coverage ledger table with key-level status.
3. Step 7 defines an ``incomplete_assessment`` fail-closed outcome.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONVERGE_TEMPLATE = REPO_ROOT / "templates" / "commands" / "converge.md"


def _text() -> str:
    return CONVERGE_TEMPLATE.read_text(encoding="utf-8")


def test_per_category_denominator_syntax_present():
    """Step 6 must expose checked/total per category, not a bare aggregate."""
    text = _text()
    # The template must include the denominator pattern for each major category.
    assert "checked>/<total>" in text or re.search(r"checked>/<total>", text), (
        "converge.md Step 6 must use '<checked>/<total>' denominator syntax "
        "for per-category metrics."
    )


def test_coverage_ledger_table_present():
    """Step 6 must include a key-ledger table so reports are auditable."""
    text = _text()
    assert "Coverage ledger" in text, (
        "converge.md must contain a 'Coverage ledger' section in Step 6."
    )
    # The ledger table must define the three status values.
    assert "✅ satisfied" in text
    assert "⚠️ gap" in text
    assert "unassessed" in text


def test_incomplete_assessment_outcome_present():
    """Step 7 must define an ``incomplete_assessment`` fail-closed outcome."""
    text = _text()
    assert "incomplete_assessment" in text, (
        "converge.md Step 7 must define an 'incomplete_assessment' outcome "
        "to fail closed when inventory keys are unassessed."
    )


def test_incomplete_assessment_blocks_tasks_md_write():
    """The incomplete_assessment branch must NOT write tasks.md."""
    text = _text()
    # Locate the incomplete_assessment section and verify the prohibition.
    idx = text.find("incomplete_assessment` outcome")
    assert idx != -1
    # Within the next 500 chars after the outcome heading, the template must
    # say "Do not modify" tasks.md.
    excerpt = text[idx : idx + 500]
    assert "Do **not** modify" in excerpt or "do not modify" in excerpt.lower(), (
        "The incomplete_assessment branch must instruct the agent NOT to modify tasks.md."
    )


def test_step_8_handoff_covers_incomplete_assessment():
    """Step 8 must provide a next-action note for incomplete_assessment."""
    text = _text()
    # Step 8 handoff section must reference incomplete_assessment explicitly.
    step8_idx = text.find("### 8.")
    assert step8_idx != -1
    step8_text = text[step8_idx : step8_idx + 600]
    assert "incomplete_assessment" in step8_text, (
        "Step 8 handoff must include guidance for the incomplete_assessment outcome."
    )
