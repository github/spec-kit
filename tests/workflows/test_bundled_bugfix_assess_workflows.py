"""Guards for the bundled bugfix and assess workflows."""

from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli._assets import _locate_bundled_workflow
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow


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
