"""Regression tests for the converge command's task-assessment contract.

The converge prompt must assess the current implementation against every task,
including tasks marked complete or added during an earlier Convergence phase.
These tests read the template as text because the behavior is encoded in the
prompt itself.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONVERGE_TEMPLATE = REPO_ROOT / "templates" / "commands" / "converge.md"


def _normalized_template() -> str:
    return " ".join(CONVERGE_TEMPLATE.read_text(encoding="utf-8").split())


def test_converge_assesses_every_task_against_current_behavior():
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
        assert clause in text, f"converge.md is missing prompt contract: {clause!r}"


def test_converge_does_not_define_a_separate_assessment_inventory():
    assert "assessment inventory" not in _normalized_template()
