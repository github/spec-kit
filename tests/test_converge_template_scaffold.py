"""Scaffold checks for the converge command's task-assessment guidance.

These tests verify that the generated prompt includes the instructions needed
to scaffold assessment of every task, including tasks marked complete or added
during an earlier Convergence phase. They do not execute an LLM or assert how
an LLM will respond.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONVERGE_TEMPLATE = REPO_ROOT / "templates" / "commands" / "converge.md"


def _normalized_template() -> str:
    return " ".join(CONVERGE_TEMPLATE.read_text(encoding="utf-8").split())


def test_converge_scaffold_includes_every_task_and_evidence_source():
    text = _normalized_template()
    required_clauses = (
        "Include every existing task in the intent inventory",
        "regardless of checkbox state or Convergence phase",
        "completion claims are not evidence",
        "Verify current behavior against the spec, plan, tasks, and constitution",
        "for corrective task chains, assess the resulting behavior, "
        "not superseded implementation details",
    )

    for clause in required_clauses:
        assert clause in text, f"converge.md is missing scaffold guidance: {clause!r}"


def test_converge_scaffold_uses_the_defined_intent_inventory():
    assert "assessment inventory" not in _normalized_template()
