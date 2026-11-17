"""Guards for the bundled bugfix and assess workflows."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from specify_cli._assets import _locate_bundled_workflow
from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow
from specify_cli.workflows.step import gate as gate_module


def _load_workflow(workflow_id: str) -> WorkflowDefinition:
    directory = _locate_bundled_workflow(workflow_id)
    assert directory is not None, f"bundled workflow '{workflow_id}' not found"
    return WorkflowDefinition.from_yaml(directory / "workflow.yml")


@pytest.mark.parametrize("workflow_id", ["bugfix", "assess"])
def test_bundled_workflow_validates_cleanly(workflow_id: str) -> None:
    definition = _load_workflow(workflow_id)
    assert validate_workflow(definition) == []


def test_bugfix_workflow_has_expected_steps() -> None:
    definition = _load_workflow("bugfix")
    assert [step["id"] for step in definition.steps] == [
        "assess",
        "review-assessment",
        "fix",
        "test",
    ]

    expected_commands = {
        "assess": ("speckit.bug.assess", "{{ inputs.report }} slug={{ inputs.slug }}"),
        "fix": ("speckit.bug.fix", "slug={{ inputs.slug }}"),
        "test": ("speckit.bug.test", "slug={{ inputs.slug }}"),
    }
    for step in definition.steps:
        if step["id"] not in expected_commands:
            continue
        command, args = expected_commands[step["id"]]
        assert step["command"] == command
        assert step["integration"] == "{{ inputs.integration }}"
        assert step["input"]["args"] == args

    gate = definition.steps[1]
    assert gate.get("type") == "gate"
    assert gate.get("options") == ["approve", "reject"]
    assert gate.get("on_reject") == "abort"


def test_assess_workflow_has_expected_steps() -> None:
    definition = _load_workflow("assess")
    assert [step["id"] for step in definition.steps] == [
        "intake",
        "research",
        "define",
        "shape",
        "decide",
        "review-verdict",
    ]

    expected_commands = {
        "intake": ("speckit.assess.intake", "{{ inputs.idea }} slug={{ inputs.slug }}"),
        "research": ("speckit.assess.research", "slug={{ inputs.slug }}"),
        "define": ("speckit.assess.define", "slug={{ inputs.slug }}"),
        "shape": ("speckit.assess.shape", "slug={{ inputs.slug }}"),
        "decide": ("speckit.assess.decide", "slug={{ inputs.slug }}"),
    }
    for step in definition.steps:
        if step["id"] not in expected_commands:
            continue
        command, args = expected_commands[step["id"]]
        assert step["command"] == command
        assert step["integration"] == "{{ inputs.integration }}"
        assert step["input"]["args"] == args

    final_gate = definition.steps[-1]
    assert final_gate.get("type") == "gate"
    assert final_gate.get("options") == ["approve", "reject"]
    assert final_gate.get("on_reject") == "abort"


@pytest.mark.parametrize(
    ("workflow_id", "required_inputs"),
    [("bugfix", ("report", "slug")), ("assess", ("idea", "slug"))],
)
def test_bundled_workflow_has_required_inputs(
    workflow_id: str, required_inputs: tuple[str, ...]
) -> None:
    definition = _load_workflow(workflow_id)
    for input_id in required_inputs:
        assert definition.inputs[input_id].get("required") is True
    assert definition.inputs.get("integration", {}).get("default") == "auto"


def test_verdict_resume(bundled_review, resume_bundled_review) -> None:
    _, state, commands = bundled_review("bugfix", "review-assessment")

    result, resumed = resume_bundled_review(
        state, "bug_review_assessment_verdict", "approve"
    )

    assert result.exit_code == 0, result.output
    assert resumed.status is RunStatus.COMPLETED
    assert resumed.step_results["review-assessment"]["output"]["choice"] == "approve"
    assert resumed.step_results["review-assessment"]["status"] == "completed"
    assert commands == ["speckit.bug.assess", "speckit.bug.fix", "speckit.bug.test"]


@pytest.mark.parametrize("explicit_empty", [False, True], ids=["omitted", "empty"])
@pytest.mark.parametrize("tty", [False, True], ids=["non-tty", "tty"])
def test_empty_verdict_preserves_review(
    bundled_review, monkeypatch, explicit_empty, tty
) -> None:
    engine, state, commands = bundled_review("bugfix", "review-assessment")
    assert state.inputs["bug_review_assessment_verdict"] == ""
    prompts = []

    def prompt(message, options):
        prompts.append((message, options))
        return "reject"

    monkeypatch.setattr(
        gate_module, "sys",
        SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: tty)),
    )
    monkeypatch.setattr(gate_module.GateStep, "_prompt", staticmethod(prompt))

    resumed = engine.resume(
        state.run_id,
        {"bug_review_assessment_verdict": ""} if explicit_empty else None,
    )

    assert resumed.status is (RunStatus.ABORTED if tty else RunStatus.PAUSED)
    assert len(prompts) == int(tty)
    assert resumed.inputs["bug_review_assessment_verdict"] == ""
    assert resumed.step_results["review-assessment"]["output"]["choice"] == (
        "reject" if tty else None
    )
    assert commands == ["speckit.bug.assess"]


@pytest.mark.parametrize("value", ["reject", "maybe", " ", "aPpRoVe"])
def test_bound_verdict_preserves_decisions(bundled_review, value) -> None:
    engine, state, commands = bundled_review("bugfix", "review-assessment")

    resumed = engine.resume(
        state.run_id, {"bug_review_assessment_verdict": value}
    )

    if value == "aPpRoVe":
        assert resumed.status is RunStatus.COMPLETED
        assert resumed.step_results["review-assessment"]["output"]["choice"] == "approve"
        assert commands == ["speckit.bug.assess", "speckit.bug.fix", "speckit.bug.test"]
    else:
        expected = RunStatus.ABORTED if value == "reject" else RunStatus.FAILED
        assert resumed.status is expected
        assert commands == ["speckit.bug.assess"]
        if value == "reject":
            assert resumed.step_results["review-assessment"]["output"]["aborted"] is True
        else:
            assert "does not match any configured option" in resumed.error
