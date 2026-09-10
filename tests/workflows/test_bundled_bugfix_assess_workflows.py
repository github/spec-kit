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
    step_ids = [step["id"] for step in definition.steps]
    assert step_ids == ["assess", "review-assessment", "fix", "test"]

    gate = definition.steps[1]
    assert gate.get("type") == "gate"
    assert gate.get("options") == ["approve", "reject"]
    assert gate.get("on_reject") == "abort"


def test_assess_workflow_has_expected_steps() -> None:
    definition = _load_workflow("assess")
    step_ids = [step["id"] for step in definition.steps]
    assert step_ids == [
        "intake",
        "research",
        "define",
        "shape",
        "decide",
        "review-verdict",
    ]

    final_gate = definition.steps[-1]
    assert final_gate.get("type") == "gate"
    assert final_gate.get("options") == ["approve", "reject"]
    assert final_gate.get("on_reject") == "abort"


@pytest.mark.parametrize("workflow_id", ["bugfix", "assess"])
def test_bundled_workflow_has_required_inputs(workflow_id: str) -> None:
    definition = _load_workflow(workflow_id)
    assert "report" in definition.inputs or "idea" in definition.inputs
    assert "slug" in definition.inputs
    assert definition.inputs["slug"].get("required") is True
    assert definition.inputs.get("integration", {}).get("default") == "auto"
