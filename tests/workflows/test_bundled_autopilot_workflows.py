"""Guards for the bundled autopilot and autopilot-epic workflows."""

from __future__ import annotations

import pytest

from specify_cli._assets import _locate_bundled_workflow
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

CLI = "python3 .specify/extensions/autopilot/scripts/python/autopilot.py"


def _load(workflow_id: str) -> WorkflowDefinition:
    directory = _locate_bundled_workflow(workflow_id)
    assert directory is not None, f"bundled workflow '{workflow_id}' not found"
    return WorkflowDefinition.from_yaml(directory / "workflow.yml")


def _walk(steps):
    for step in steps:
        yield step
        for key in ("then", "else", "steps"):
            yield from _walk(step.get(key) or [])


@pytest.mark.parametrize("workflow_id", ["autopilot-epic", "autopilot"])
def test_workflow_validates_cleanly(workflow_id):
    assert validate_workflow(_load(workflow_id)) == []


@pytest.mark.parametrize("workflow_id", ["autopilot-epic", "autopilot"])
def test_shell_steps_are_strict_and_only_call_the_autopilot_cli(workflow_id):
    shells = [s for s in _walk(_load(workflow_id).steps) if s.get("type") == "shell"]
    assert shells
    for step in shells:
        assert step.get("strict") is True, step["id"]
        assert step["run"].startswith(CLI + " "), step["id"]
        assert "{{" not in step["run"]


def test_epic_pipe_structure():
    definition = _load("autopilot-epic")
    assert [s["id"] for s in definition.steps] == [
        "define", "spec-consult", "spec-ask", "spec-record", "check-spec",
        "design", "design-consult", "design-ask", "design-record",
        "build-when-ready", "result",
    ]
    by_id = {s["id"]: s for s in _walk(definition.steps)}
    assert by_id["specify"]["command"] == "speckit.specify"
    assert by_id["plan"]["command"] == "speckit.plan"
    assert by_id["tasks"]["command"] == "speckit.tasks"
    assert "tag_hint" in by_id["tasks"]["input"]["args"]

    build = by_id["build"]
    assert build["type"] == "do-while"
    assert [s["id"] for s in build["steps"]] == [
        "implement", "converge", "consult", "ask", "record", "gate", "review-when-green", "decide",
    ]
    assert build["condition"] == "{{ not steps.decide.output.data.finished }}"
    assert by_id["implement"]["command"] == "speckit.implement"
    assert by_id["converge"]["command"] == "speckit.converge"
    assert by_id["review"]["command"] == "speckit.autopilot.review"
    assert by_id["review"]["model"] == "{{ inputs.reviewer_model }}"
    assert by_id["gate"]["run"].endswith(" gate")
    assert by_id["decide"]["run"].endswith(" decide")
    assert by_id["result"]["run"].endswith(" pipe-result")
    # phase=design/build skip specify (and plan/tasks) so a resumed epic never overwrites its spec.
    assert definition.inputs["phase"]["enum"] == ["full", "design", "build"]


def test_every_developer_step_reads_the_team_context_and_every_consult_has_a_lead():
    by_id = {s["id"]: s for s in _walk(_load("autopilot-epic").steps)}
    for step_id in ("specify", "plan", "tasks", "implement"):
        assert ".specify/autopilot/context/epic-context.md" in by_id[step_id]["input"]["args"], step_id
    for prefix in ("spec-", "design-", ""):
        consult, ask, record = by_id[f"{prefix}consult"], by_id[f"{prefix}ask"], by_id[f"{prefix}record"]
        assert consult["run"].endswith(" consult --stage " + (prefix.rstrip("-") or "build"))
        assert record["run"].endswith(" record --stage " + (prefix.rstrip("-") or "build"))
        lead = ask["then"][0]
        assert lead["command"] == "speckit.autopilot.lead"
        assert lead["model"] == "{{ inputs.lead_model }}"
        assert lead["input"]["args"] == f"{{{{ steps.{prefix}consult.output.data.lead_args }}}}"
        assert ask["condition"] == f"{{{{ steps.{prefix}consult.output.data.open > 0 }}}}"


def test_conductor_has_human_gates_on_plan_and_final_merge_only():
    definition = _load("autopilot")
    ids = [s["id"] for s in definition.steps]
    assert ids == ["preflight", "plan-epics", "check-plan", "review-epics", "drive", "report", "review-land", "land"]
    gates = [s for s in definition.steps if s.get("type") == "gate"]
    assert [g["id"] for g in gates] == ["review-epics", "review-land"]
    for gate in gates:
        assert gate["on_reject"] == "abort"
        assert gate["verdict_input"] in definition.inputs
        assert gate["show_file"].startswith(".specify/autopilot/")
    assert {s["id"]: s for s in definition.steps}["plan-epics"]["command"] == "speckit.autopilot.epics"
