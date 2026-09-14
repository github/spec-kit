"""Covers #4431: /constitution's Sync Impact Report must be documented as
temporary, review-only material rather than committed governance content.

The Outline step that produces the Sync Impact Report must state that it is
scratch material for human review and is expected to be removed before the
amended constitution file is committed.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONSTITUTION_TEMPLATE = REPO_ROOT / "templates" / "commands" / "constitution.md"


def test_sync_impact_report_step_documents_temporary_lifecycle():
    content = CONSTITUTION_TEMPLATE.read_text(encoding="utf-8")
    step = content.split("Produce a Sync Impact Report", 1)[1].split("\n\n", 1)[0]
    assert "temporary" in step.lower(), (
        "Step 4 must document that the Sync Impact Report is temporary, "
        "review-only material, not governance content"
    )
    assert "removed before" in step.lower() and "committed" in step.lower(), (
        "Step 4 must state the report is expected to be removed before the "
        "amended constitution file is committed"
    )
