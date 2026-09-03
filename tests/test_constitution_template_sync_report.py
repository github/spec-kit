"""Covers #4431: /constitution must not stack Sync Impact Report comments.

The Outline step that produces the Sync Impact Report only said to "prepend"
it as an HTML comment, with no instruction to remove a previous one. Every
run of /constitution therefore added another comment block on top of the
last, growing the raw constitution file (and the token cost of reading it)
without bound.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONSTITUTION_TEMPLATE = REPO_ROOT / "templates" / "commands" / "constitution.md"


def test_sync_impact_report_step_instructs_removing_prior_report():
    content = CONSTITUTION_TEMPLATE.read_text(encoding="utf-8")
    step = content.split("Produce a Sync Impact Report", 1)[1].split("\n\n", 1)[0]
    assert "remove" in step.lower(), (
        "Step 4 must instruct removing/replacing any existing Sync Impact "
        "Report comment before adding the new one, otherwise reports stack "
        "on every /constitution run"
    )
    assert "never stack" in step.lower() or "not stack" in step.lower()
