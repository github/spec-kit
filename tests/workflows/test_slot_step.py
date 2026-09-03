"""Tests for the workflow slot step."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from specify_cli.workflows import BUILTIN_STEP_TYPES, get_step_type
from specify_cli.workflows.base import RunStatus, StepContext, StepStatus
from specify_cli.workflows.engine import WorkflowDefinition, WorkflowEngine, validate_workflow
from specify_cli.workflows.overlays import WorkflowResolver
from specify_cli.workflows.steps.slot import SlotStep


def _workflow_data(steps: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "workflow": {"id": "slot-workflow", "name": "Slot Workflow", "version": "1.0.0"},
        "steps": steps,
    }


def _write_workflow(project_root: Path, data: dict[str, object]) -> None:
    workflow_dir = project_root / ".specify" / "workflows" / "slot-workflow"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "workflow.yml").write_text(
        yaml.safe_dump(data), encoding="utf-8"
    )


def _write_overlay(project_root: Path, data: dict[str, object]) -> None:
    overlay_dir = (
        project_root / ".specify" / "workflows" / "overlays" / "slot-workflow"
    )
    overlay_dir.mkdir(parents=True, exist_ok=True)
    (overlay_dir / "fill-slot.yml").write_text(yaml.safe_dump(data), encoding="utf-8")


def test_slot_step_is_registered_as_builtin():
    step = get_step_type("slot")

    assert isinstance(step, SlotStep)
    assert step.type_key == "slot"
    assert "slot" in BUILTIN_STEP_TYPES


def test_slot_step_validate_returns_errors_for_malformed_names():
    step = SlotStep()

    assert any("missing required 'id'" in error for error in step.validate({}))
    assert "requires a 'name' field" in step.validate({"id": "slot"})[0]
    assert "requires a 'name' field" in step.validate({"id": "slot", "name": None})[0]
    for name in ("", "   ", 123):
        errors = step.validate({"id": "slot", "name": name})
        assert len(errors) == 1
        assert "non-blank string" in errors[0]
    assert step.validate({"id": "slot", "name": "lint"}) == []


@pytest.mark.parametrize(
    ("name", "expected_error"),
    [
        (None, "requires a 'name' field"),
        ("", "non-blank string"),
        ("  ", "non-blank string"),
        (123, "non-blank string"),
    ],
)
def test_slot_step_errors_are_reported_through_workflow_validation(
    name: object, expected_error: str
):
    definition = WorkflowDefinition(
        _workflow_data([{"id": "slot", "type": "slot", "name": name}])
    )

    errors = validate_workflow(definition)

    assert any("Slot step 'slot'" in error for error in errors)
    assert any(expected_error in error for error in errors)


def test_addressable_nested_slot_step_validates_cleanly():
    definition = WorkflowDefinition(
        _workflow_data(
            [
                {
                    "id": "conditional",
                    "type": "if",
                    "condition": "true",
                    "then": [{"id": "slot", "type": "slot", "name": "lint"}],
                }
            ]
        )
    )

    assert validate_workflow(definition) == []


def test_slot_step_skips_without_mutating_the_shared_instance():
    step = SlotStep()
    before = vars(step).copy()

    result = step.execute({"id": "slot", "name": "lint"}, StepContext())

    assert result.status is StepStatus.SKIPPED
    assert result.output == {"slot": "lint"}
    assert vars(step) == before


def test_slot_step_fails_when_executed_inside_fan_out():
    step = SlotStep()

    result = step.execute(
        {"id": "slot", "name": "per-item"},
        StepContext(inside_fan_out=True),
    )

    assert result.status is StepStatus.FAILED
    assert "not supported inside fan-out" in result.error
    assert result.output == {}


def test_unfilled_slot_is_persisted_and_does_not_halt_workflow(project_dir):
    _write_workflow(
        project_dir,
        _workflow_data(
            [
                {"id": "slot", "type": "slot", "name": "post-implement"},
                {"id": "marker", "type": "shell", "run": "echo marker"},
            ]
        ),
    )
    engine = WorkflowEngine(project_dir)

    definition = engine.load_workflow("slot-workflow")
    assert engine.validate(definition) == []
    state = engine.execute(definition, run_id="slot-run")

    assert state.status is RunStatus.COMPLETED
    state_data = json.loads((state.runs_dir / "state.json").read_text(encoding="utf-8"))
    assert state_data["step_results"]["slot"]["status"] == "skipped"
    assert state_data["step_results"]["slot"]["output"] == {"slot": "post-implement"}
    assert state_data["step_results"]["marker"]["status"] == "completed"

    log_entries = [
        json.loads(line)
        for line in (state.runs_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    skipped_events = [
        entry
        for entry in log_entries
        if entry["event"] == "step_completed" and entry["step_id"] == "slot"
    ]
    assert len(skipped_events) == 1
    assert skipped_events[0]["status"] == "skipped"


def test_overlay_replaces_slot_and_attributes_it_to_the_overlay(project_dir):
    _write_workflow(
        project_dir,
        _workflow_data(
            [
                {"id": "before", "type": "shell", "run": "echo before"},
                {"id": "slot", "type": "slot", "name": "post-implement"},
                {"id": "after", "type": "shell", "run": "echo after"},
            ]
        ),
    )
    _write_overlay(
        project_dir,
        {
            "id": "fill-slot",
            "extends": "slot-workflow",
            "edits": [
                {
                    "replace": "slot",
                    "step": {"id": "slot", "type": "shell", "run": "echo filled"},
                }
            ],
        },
    )
    engine = WorkflowEngine(project_dir)

    definition = engine.load_workflow("slot-workflow")
    assert [step["id"] for step in definition.steps] == ["before", "slot", "after"]
    assert definition.steps[1]["type"] == "shell"
    assert engine.validate(definition) == []
    state = engine.execute(definition, run_id="filled-slot-run")
    assert state.status is RunStatus.COMPLETED
    assert "filled" in state.step_results["slot"]["output"]["stdout"]

    _definition, _layers, attribution = WorkflowResolver(project_dir).resolve_with_layers(
        "slot-workflow"
    )
    sources = {step.step_id: step.source for step in attribution}
    assert sources == {
        "before": "base",
        "slot": "project:fill-slot",
        "after": "base",
    }


def test_slot_steps_are_rejected_inside_fan_out_templates():
    definition = WorkflowDefinition(
        _workflow_data(
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [],
                    "step": {"id": "slot", "type": "slot", "name": "per-item"},
                }
            ]
        )
    )

    errors = validate_workflow(definition)

    assert any(
        "Slot step 'slot' is not supported inside fan-out templates" in error
        for error in errors
    )


def test_non_slot_fan_out_templates_remain_valid():
    definition = WorkflowDefinition(
        _workflow_data(
            [
                {
                    "id": "fan",
                    "type": "fan-out",
                    "items": [],
                    "step": {"id": "template", "type": "shell", "run": "echo item"},
                }
            ]
        )
    )

    assert validate_workflow(definition) == []
