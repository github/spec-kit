"""Tests for StepListComposer validation and error handling."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specify_cli.workflows.overlays import WorkflowResolver
from specify_cli.workflows.overlays.composer import StepListComposer
from specify_cli.workflows.overlays.layer_sources import BaseWorkflowSource, Layer
from specify_cli.workflows.overlays.schema import Overlay, OverlayEdit


def _write_workflow(project_root: Path, workflow_id: str, data: dict) -> Path:
    wf_dir = project_root / ".specify" / "workflows" / workflow_id
    wf_dir.mkdir(parents=True, exist_ok=True)
    wf_path = wf_dir / "workflow.yml"
    wf_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return wf_path


class TestStepListComposerValidation:
    """Composer validates edits before applying them."""

    def test_composer_reports_invalid_anchors(self, project_dir):
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "echo"}],
            },
        )
        base_layer = BaseWorkflowSource(project_dir).collect("wf")[0]

        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("insert_after", "missing", {"id": "new", "type": "command", "command": "echo"})],
        )
        layer = Layer(content=overlay, source="project:ov", tier="project-overlay", priority=10)
        composer = StepListComposer()
        with pytest.raises(ValueError, match="does not match any base step id"):
            composer.compose([base_layer, layer])

    def test_composer_validates_edits_before_merge(self, project_dir):
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "echo"}],
            },
        )
        overlay = Overlay(
            id="ov",
            extends="wf",
            priority=10,
            edits=[OverlayEdit("replace", "a", {"id": "bad:id", "type": "command", "command": "echo"})],
        )
        layer = Layer(content=overlay, source="project:ov", tier="project-overlay", priority=10)
        composer = StepListComposer()
        with pytest.raises(ValueError, match="bad:id"):
            composer.compose([BaseWorkflowSource(project_dir).collect("wf")[0], layer])

    def test_resolver_reports_invalid_anchor_as_validation_error(self, project_dir):
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "echo"}],
            },
        )
        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
                {
                    "id": "ov",
                    "extends": "wf",
                    "priority": 10,
                    "edits": [
                        {
                            "operation": "insert_after",
                            "anchor": "missing",
                            "step": {"id": "new", "type": "command", "command": "echo"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        # Manually inject the overlay by writing it to disk in the correct location.
        overlay_dir = project_dir / ".specify" / "workflows" / "overlays" / "wf"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        (overlay_dir / "ov.yml").write_text(overlay_file.read_text(encoding="utf-8"), encoding="utf-8")

        resolver = WorkflowResolver(project_dir)
        with pytest.raises(ValueError, match="missing"):
            resolver.resolve("wf")

    def test_composer_applies_lower_priority_last(self, project_dir):
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "base"}],
            },
        )
        high_number = Overlay(
            id="high-number",
            extends="wf",
            priority=20,
            edits=[
                OverlayEdit(
                    "replace",
                    "a",
                    {"id": "a", "type": "command", "command": "priority-20"},
                )
            ],
        )
        low_number = Overlay(
            id="low-number",
            extends="wf",
            priority=5,
            edits=[
                OverlayEdit(
                    "replace",
                    "a",
                    {"id": "a", "type": "command", "command": "priority-5"},
                )
            ],
        )

        definition, attribution = StepListComposer().compose(
            [
                BaseWorkflowSource(project_dir).collect("wf")[0],
                Layer(high_number, "project:high-number", "project-overlay", 20),
                Layer(low_number, "project:low-number", "project-overlay", 5),
            ]
        )

        assert definition is not None
        assert definition.data["steps"][0]["command"] == "priority-5"
        assert attribution[0].source == "project:low-number"
