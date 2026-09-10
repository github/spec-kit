"""The planning deferral in ``templates/commands/clarify.md`` must stay bounded (#1717).

The old catch-all ("Information is better deferred to planning phase") let
agents skip NFRs, acceptance criteria, and edge cases. Defer only
implementation method, tech-stack comparison, or task breakdown.
"""

from pathlib import Path

CLARIFY = Path(__file__).parent.parent / "templates" / "commands" / "clarify.md"


def test_clarify_planning_deferral_is_bounded() -> None:
    text = CLARIFY.read_text(encoding="utf-8")
    assert "- Information is better deferred to planning phase (note internally)" not in text
    assert (
        "implementation method, tech-stack comparison, or task breakdown"
        in text
    )
