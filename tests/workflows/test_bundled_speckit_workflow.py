"""Guards for the bundled Full SDD Cycle workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

BUNDLED = (
    Path(__file__).resolve().parents[2] / "workflows" / "speckit" / "workflow.yml"
)


def test_bundled_speckit_workflow_has_no_unused_scope_input() -> None:
    """Every declared input must be referenced; scope was a dead prompt (#4384)."""
    text = BUNDLED.read_text(encoding="utf-8")
    definition = WorkflowDefinition.from_string(text)
    assert validate_workflow(definition) == []
    assert "scope" not in definition.inputs
    assert "spec" in definition.inputs

    raw = yaml.safe_load(text)
    assert "scope" not in raw.get("inputs", {})
    assert "inputs.scope" not in text

    for step in raw["steps"]:
        args = (step.get("input") or {}).get("args")
        if args is None:
            continue
        assert "inputs.scope" not in str(args)
