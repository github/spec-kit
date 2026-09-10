"""Pin the spec-vs-plan stage gate in ``templates/commands/clarify.md`` (#1717).

Agents were deferring NFRs, acceptance criteria, and edge cases to Plan
because the template allowed a vague "better deferred to planning" exit.
The gate must stay in the command the agent actually reads.
"""

from pathlib import Path

CLARIFY = Path(__file__).parent.parent / "templates" / "commands" / "clarify.md"


def test_clarify_has_spec_vs_plan_stage_gate() -> None:
    text = CLARIFY.read_text(encoding="utf-8")
    assert "Stage gate (spec vs plan)" in text
    assert "implementation method, tech-stack comparison, or task breakdown" in text
    assert "MUST NOT defer spec-taxonomy items to Plan" in text
    assert "- Information is better deferred to planning phase (note internally)" not in text
