"""One gap must produce one appended task, however many inventory items reach it.

Converge now builds a task inventory as well as a requirements inventory, and the two
overlap by construction: `T017` exists because `FR-003` asked for it. Code that is absent
is therefore a gap under both, and a finding per item would append two remediation tasks
for the same work — each with half the trace, and both back again on the next run, which
is the duplication (#4269) the prerequisite gate was added to stop, reintroduced one layer
up.

So the overlap is coalesced into a single finding that keeps every reference. These pin
that, and pin the append contract to one checklist item per finding, so a later edit to
either step cannot quietly split them again.
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


def _section(text: str, heading: str) -> str:
    """The body of the `### <n>. <heading>` section, up to the next `### `."""
    match = re.search(
        rf"^### \d+\. {re.escape(heading)}.*?(?=^### |\Z)", text, re.MULTILINE | re.DOTALL
    )
    assert match, f"no section headed {heading!r} any more"
    return match.group(0)


def _prose(section: str) -> str:
    """*section* with its wrapping collapsed, so a phrase may span a line break."""
    return re.sub(r"\s+", " ", section)


def test_step_4_coalesces_findings_that_share_the_same_work(template_text: str) -> None:
    """Two inventory items pointing at one gap must yield one finding, not two."""
    step4 = _section(template_text, "Assess the Codebase and Classify Findings")
    assert re.search(r"one finding per piece of work", _prose(step4), re.IGNORECASE), (
        "Step 4 no longer tells the agent to coalesce, so a requirement and the task "
        "that implements it each produce their own finding for the same absent code"
    )
    assert re.search(r"coalesce", _prose(step4), re.IGNORECASE), step4
    assert re.search(r"`FR-\d+, T\d+`", _prose(step4)), (
        "the coalescing rule should show the combined form it produces, or the agent has "
        "to guess how to keep both references"
    )


def test_a_coalesced_finding_keeps_every_reference(template_text: str) -> None:
    """Collapsing to one reference loses what the other one carried.

    The requirement says what is owed; the task ID says where the bookkeeping went
    wrong. A remediation task that names only one of them cannot be traced back to the
    other, which is the whole point of appending it.
    """
    step4 = _section(template_text, "Assess the Codebase and Classify Findings")
    assert "source-refs" in step4, (
        "a Finding records a single `source-ref` again, so a coalesced finding has "
        "nowhere to keep the references it was coalesced from"
    )
    assert re.search(r"one or more", _prose(step4)), step4
    assert re.search(r"same work when one change", _prose(step4)), (
        "the rule must say what makes two items the same work, or unrelated findings "
        "that merely sit in the same file get merged too"
    )


def test_the_append_contract_emits_one_task_per_finding(template_text: str) -> None:
    """One finding, one checklist item — the coalescing must survive into `tasks.md`."""
    step7 = _section(template_text, "Append Convergence Tasks (or report converged)")
    assert "one checklist item per actionable finding" in _prose(step7), step7
    assert re.search(r"- \[ \] T042 <imperative description> per <source-refs>", step7), (
        "the appended-task shape still names a single `<source-ref>`, so a coalesced "
        "finding cannot be written without either splitting it or dropping a reference"
    )
    assert re.search(r"comma-separated", _prose(step7)), (
        "the append contract should say how several origins are written in the one item"
    )
    assert re.search(r"in \*\*one\*\* checklist item", _prose(step7)), (
        "nothing stops the agent from emitting one item per origin of a coalesced "
        "finding, which is the duplicate this coalescing exists to prevent"
    )


def test_the_task_inventory_points_at_the_coalescing_rule(template_text: str) -> None:
    """The inventory that creates the overlap has to name where it is resolved."""
    inventory = _section(template_text, "Build the Intent Inventory")
    assert re.search(r"Task inventory", inventory), inventory
    assert re.search(r"coalesce", inventory, re.IGNORECASE), (
        "the task inventory introduces the second path to the same gap without saying "
        "that Step 4 merges them, so the agent can reasonably report both"
    )
