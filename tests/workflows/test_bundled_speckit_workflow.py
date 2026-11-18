"""Guards for the bundled Full SDD Cycle workflow."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from specify_cli.workflows.base import RunStatus
from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow
from specify_cli.workflows.step import gate as gate_module

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLED = REPO_ROOT / "workflows" / "speckit" / "workflow.yml"
REFERENCE_DOC = REPO_ROOT / "docs" / "workflows" / "developing.md"
DOC_INTRO = "Here is the built-in **Full SDD Cycle** workflow that ships with Spec Kit:"


def _documented_workflow() -> object:
    """Return the workflow YAML the reference guide claims is the shipped one."""
    text = REFERENCE_DOC.read_text(encoding="utf-8")
    intro = text.index(DOC_INTRO)
    start = text.index("```yaml", intro) + len("```yaml")
    end = text.index("```", start)
    return yaml.safe_load(text[start:end])


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


def test_reference_doc_matches_the_shipped_workflow() -> None:
    """The reference guide reproduces this workflow, so it must not drift from it.

    ``docs/workflows/developing.md`` introduces its YAML block as the workflow
    that ships with Spec Kit, so a reader is entitled to treat it as the real
    definition. It had drifted on four points -- a stale ``version`` and
    ``speckit_version``, a short ``integrations.any`` list, and an
    ``integration`` default of ``copilot`` where the shipped default is
    ``auto`` -- which is exactly the sort of thing nothing else would catch.

    The comparison is on parsed YAML, not text, so the guide stays free to
    format lists however reads best; only the content has to agree.
    """
    assert _documented_workflow() == yaml.safe_load(BUNDLED.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("gate_id", "input_name", "next_command"),
    [
        ("review-spec", "speckit_review_spec_verdict", "speckit.plan"),
        ("review-plan", "speckit_review_plan_verdict", "speckit.tasks"),
    ],
)
def test_verdict_resume(
    bundled_review, resume_bundled_review, gate_id, input_name, next_command
) -> None:
    _, state, commands = bundled_review("speckit", gate_id)
    previous_commands = commands.copy()

    result, resumed = resume_bundled_review(state, input_name, "approve")

    assert result.exit_code == 0, result.output
    assert resumed.step_results[gate_id]["output"]["choice"] == "approve"
    assert resumed.step_results[gate_id]["status"] == "completed"
    assert commands[:len(previous_commands)] == previous_commands
    assert commands[len(previous_commands)] == next_command
    assert all(commands.count(command) == 1 for command in previous_commands)
    if gate_id == "review-spec":
        assert resumed.status is RunStatus.PAUSED
        assert resumed.current_step_id == "review-plan"
        assert resumed.inputs["speckit_review_plan_verdict"] == ""
        assert resumed.step_results["review-plan"]["output"]["choice"] is None
    else:
        assert resumed.status is RunStatus.COMPLETED


@pytest.mark.parametrize(
    ("gate_id", "input_name"),
    [
        ("review-spec", "speckit_review_spec_verdict"),
        ("review-plan", "speckit_review_plan_verdict"),
    ],
)
@pytest.mark.parametrize("explicit_empty", [False, True], ids=["omitted", "empty"])
@pytest.mark.parametrize("tty", [False, True], ids=["non-tty", "tty"])
def test_empty_verdict_preserves_review(
    bundled_review, monkeypatch, gate_id, input_name, explicit_empty, tty
) -> None:
    engine, state, commands = bundled_review("speckit", gate_id)
    previous_commands = commands.copy()
    assert state.inputs[input_name] == ""
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
        state.run_id, {input_name: ""} if explicit_empty else None
    )

    assert resumed.status is (RunStatus.ABORTED if tty else RunStatus.PAUSED)
    assert len(prompts) == int(tty)
    assert resumed.inputs[input_name] == ""
    assert resumed.step_results[gate_id]["output"]["choice"] == (
        "reject" if tty else None
    )
    assert commands == previous_commands


@pytest.mark.parametrize(
    ("gate_id", "input_name"),
    [
        ("review-spec", "speckit_review_spec_verdict"),
        ("review-plan", "speckit_review_plan_verdict"),
    ],
)
@pytest.mark.parametrize("value", ["reject", "maybe", " ", "aPpRoVe"])
def test_bound_verdict_preserves_decisions(
    bundled_review, gate_id, input_name, value
) -> None:
    engine, state, commands = bundled_review("speckit", gate_id)
    previous_commands = commands.copy()

    resumed = engine.resume(state.run_id, {input_name: value})

    if value == "aPpRoVe":
        assert resumed.step_results[gate_id]["output"]["choice"] == "approve"
        assert resumed.step_results[gate_id]["status"] == "completed"
        assert len(commands) > len(previous_commands)
    else:
        expected = RunStatus.ABORTED if value == "reject" else RunStatus.FAILED
        assert resumed.status is expected
        assert commands == previous_commands
        if value == "reject":
            assert resumed.step_results[gate_id]["output"]["aborted"] is True
        else:
            assert "does not match any configured option" in resumed.error


@pytest.mark.parametrize(
    ("gate_id", "other_input"),
    [
        ("review-spec", "speckit_review_plan_verdict"),
        ("review-plan", "speckit_review_spec_verdict"),
    ],
)
def test_other_review_verdict_does_not_approve_gate(
    bundled_review, gate_id, other_input
) -> None:
    engine, state, commands = bundled_review("speckit", gate_id)
    previous_commands = commands.copy()

    resumed = engine.resume(state.run_id, {other_input: "approve"})

    assert resumed.status is RunStatus.PAUSED
    assert resumed.current_step_id == gate_id
    assert resumed.step_results[gate_id]["output"]["choice"] is None
    assert commands == previous_commands
