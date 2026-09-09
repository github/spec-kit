"""Guards for the bundled Full SDD Cycle workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLED = REPO_ROOT / "workflows" / "speckit" / "workflow.yml"
REFERENCE_DOC = REPO_ROOT / "docs" / "reference" / "workflows.md"
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

    ``docs/reference/workflows.md`` introduces its YAML block as the workflow
    that ships with Spec Kit, so a reader is entitled to treat it as the real
    definition. It had drifted on four points -- a stale ``version`` and
    ``speckit_version``, a short ``integrations.any`` list, and an
    ``integration`` default of ``copilot`` where the shipped default is
    ``auto`` -- which is exactly the sort of thing nothing else would catch.

    The comparison is on parsed YAML, not text, so the guide stays free to
    format lists however reads best; only the content has to agree.
    """
    assert _documented_workflow() == yaml.safe_load(BUNDLED.read_text(encoding="utf-8"))
