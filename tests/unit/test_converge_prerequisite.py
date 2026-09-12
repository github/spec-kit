"""`/speckit-converge` assesses a finished implementation, so it enforces that first.

Run while `tasks.md` still had unchecked tasks, converge assessed the code anyway. The
work those tasks track is not built yet, so it came back as fresh gaps and was appended
again under new IDs — every re-run duplicated its own remediation tasks (#4269). And when
nothing new turned up, the run reported `converged`, telling the user the implementation
was complete while tracked work was still open.

The fix is the lifecycle, not a dedup rule: converge stops before analysis while any task
is unchecked and sends the user to `/speckit-implement`. Once every task is checked it
assesses the code against every artifact, each task included, and anything it appends
makes the next run stop again until that work is done. These pin that shape.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = PROJECT_ROOT / "templates" / "commands" / "converge.md"
REFERENCE = PROJECT_ROOT / "docs" / "reference" / "agentic-sdd.md"

GATE_HEADING = "Enforce the implement prerequisite"


@pytest.fixture(scope="module")
def template_text() -> str:
    assert TEMPLATE.is_file(), f"missing command template: {TEMPLATE}"
    return TEMPLATE.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """The body of the `### ` section whose heading contains *heading*."""
    match = re.search(
        rf"^###[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^### |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"no section headed {heading!r} any more"
    return match.group(1)


def _gate(text: str) -> str:
    """The prerequisite paragraph, up to the next blank line."""
    start = text.find(GATE_HEADING)
    assert start != -1, "converge no longer checks that implement has finished"
    end = text.find("\n\n", start)
    return text[start : end if end != -1 else len(text)]


def test_the_gate_runs_before_anything_is_assessed(template_text: str) -> None:
    """It has to sit in Step 1: a check after the assessment cannot stop it."""
    step_one = _section(template_text, "1. Initialize Convergence Context")
    assert GATE_HEADING in step_one, (
        "the prerequisite check is not part of Step 1, so the codebase is assessed "
        "before converge knows whether implement has finished"
    )
    assert "do not continue to Step 2" in _gate(template_text)


def test_an_unchecked_task_stops_the_run_and_names_implement(template_text: str) -> None:
    gate = _gate(template_text)
    assert "STOP" in gate, gate
    assert "__SPECKIT_COMMAND_IMPLEMENT__" in gate, (
        f"the stop must tell the user which command finishes the work:\n{gate}"
    )
    assert re.search(r"list their task IDs", gate), (
        f"the stop must say which tasks are open, not only that some are:\n{gate}"
    )
    assert "byte-for-byte unchanged" in gate, (
        f"a stopped run must not write to tasks.md:\n{gate}"
    )


def test_the_gate_counts_tasks_the_way_implement_does(template_text: str) -> None:
    """An example checkbox inside a fence is not an open task (#4272)."""
    gate = _gate(template_text)
    assert "`- [ ]`" in gate, gate
    assert re.search(r"outside\s+code\s+fences", gate), (
        f"the gate would treat a documented example checkbox as unfinished work:\n{gate}"
    )


def test_a_stopped_run_is_not_reported_as_converged(template_text: str) -> None:
    """`converged` tells the user the implementation is complete; open work says otherwise."""
    gate = _gate(template_text)
    assert "neither outcome of Step 7" in gate, gate
    append_step = _section(template_text, "7. Append Convergence Tasks")
    assert not re.search(r"take the `converged` path", append_step), (
        "already-tracked work is being routed to `converged`, whose report says the "
        "implementation satisfies the spec"
    )


def test_every_task_is_part_of_what_is_assessed(template_text: str) -> None:
    """A task ticked off without its work in the code is a gap too."""
    inventory = _section(template_text, "3. Build the Intent Inventory")
    assert "**Task inventory**" in inventory, (
        "the intent inventory no longer includes the tasks themselves, so a task "
        "marked done but never built is invisible"
    )
    assert re.search(r"marked done whose work is\s+absent", inventory), inventory


def test_the_handoff_describes_the_gate(template_text: str) -> None:
    handoff = _section(template_text, "8. Provide Next Actions")
    assert "prerequisite check" in handoff, (
        "after appending, the handoff should say the next converge stops until the new "
        f"tasks are done:\n{handoff}"
    )


def test_the_reference_docs_describe_the_gate() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    section = text[text.find("## `/speckit.converge`") :]
    assert re.search(r"still unchecked, converge stops", section), (
        "docs/reference/agentic-sdd.md no longer says converge stops on unchecked tasks"
    )
