"""Integration tests for the WorkflowResolver."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow
from specify_cli.workflows.overlays import WorkflowResolver
from specify_cli.workflows.overlays.merge import ComposedStep


def _write_workflow(project_root: Path, workflow_id: str, data: dict) -> Path:
    wf_dir = project_root / ".specify" / "workflows" / workflow_id
    wf_dir.mkdir(parents=True, exist_ok=True)
    wf_path = wf_dir / "workflow.yml"
    wf_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return wf_path


def _write_overlay(project_root: Path, workflow_id: str, overlay_id: str, data: dict) -> Path:
    ov_dir = project_root / ".specify" / "workflows" / "overlays" / workflow_id
    ov_dir.mkdir(parents=True, exist_ok=True)
    ov_path = ov_dir / f"{overlay_id}.yml"
    ov_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return ov_path


class TestWorkflowResolver:
    """End-to-end resolution of base workflows plus overlays."""

    @pytest.mark.parametrize(
        "workflow_id",
        [
            "../outside",
            "nested/workflow",
            "wf\n",
            "overlays",
            "runs",
            "steps",
        ],
    )
    def test_rejects_unsafe_id_before_collecting_sources(
        self, project_dir, workflow_id
    ):
        resolver = WorkflowResolver(project_dir)

        class UnexpectedSource:
            def collect(self, _workflow_id):
                pytest.fail("source collection must not run for an unsafe workflow ID")

        resolver._sources = [UnexpectedSource()]

        with pytest.raises(ValueError, match="Invalid workflow ID"):
            resolver.resolve(workflow_id)

    def test_rejects_absolute_id_before_collecting_sources(
        self, project_dir, tmp_path
    ):
        resolver = WorkflowResolver(project_dir)
        outside = tmp_path / "outside"

        class UnexpectedSource:
            def collect(self, _workflow_id):
                pytest.fail("source collection must not run for an absolute workflow ID")

        resolver._sources = [UnexpectedSource()]

        with pytest.raises(ValueError, match="Invalid workflow ID"):
            resolver.resolve(str(outside))

    def test_resolve_without_overlays(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)

        resolver = WorkflowResolver(project_dir)
        definition = resolver.resolve("wf")
        assert isinstance(definition, WorkflowDefinition)
        assert definition.id == "wf"
        assert [s["id"] for s in definition.steps] == ["a"]

    def test_resolve_with_project_overlay_insert(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [
                {"id": "a", "type": "command", "command": "speckit.specify"},
                {"id": "b", "type": "command", "command": "speckit.specify"},
            ],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "new", "type": "command", "command": "speckit.plan"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        definition = resolver.resolve("wf")
        assert [s["id"] for s in definition.steps] == ["a", "new", "b"]

    def test_resolve_lower_priority_wins(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "low",
            {
                "id": "low",
                "extends": "wf",
                "priority": 5,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "low-step", "type": "command", "command": "echo"},
                    }
                ],
            },
        )
        _write_overlay(
            project_dir,
            "wf",
            "high",
            {
                "id": "high",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "high-step", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        definition = resolver.resolve("wf")
        # Lower priority is applied later; both insert_after 'a', so low-step
        # ends up closer to the anchor and wins the conflict.
        assert [s["id"] for s in definition.steps] == ["a", "low-step", "high-step"]

    def test_resolve_with_layers_returns_attribution(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "new", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        definition, layers, attribution = resolver.resolve_with_layers("wf")
        assert [s["id"] for s in definition.steps] == ["a", "new"]
        assert any(layer.tier == "base" for layer in layers)
        assert attribution == [ComposedStep("a", "base"), ComposedStep("new", "project:ov1")]

    def test_resolve_attribution_for_nested_base_steps(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [
                {
                    "id": "if-1",
                    "type": "if",
                    "condition": "true",
                    "then": [{"id": "then-a", "type": "command", "command": "echo"}],
                    "else": [{"id": "else-b", "type": "command", "command": "echo"}],
                }
            ],
        }
        _write_workflow(project_dir, "wf", data)

        resolver = WorkflowResolver(project_dir)
        definition, _layers, attribution = resolver.resolve_with_layers("wf")
        assert [s["id"] for s in definition.steps] == ["if-1"]
        sources = {c.step_id: c.source for c in attribution}
        assert sources["if-1"] == "base"
        assert sources["then-a"] == "base"
        assert sources["else-b"] == "base"

    def test_resolve_invalid_project_overlay_fails(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "broken",
            {
                "id": "broken",
                "extends": "wf",
                "priority": 10,
                "edits": "not-a-list",
            },
        )

        resolver = WorkflowResolver(project_dir)
        with pytest.raises(ValueError):
            resolver.resolve("wf")

    def test_resolve_disabled_overlay_is_skipped(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "disabled",
            {
                "id": "disabled",
                "extends": "wf",
                "priority": 10,
                "enabled": False,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "new", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        definition = resolver.resolve("wf")
        assert [s["id"] for s in definition.steps] == ["a"]

    def test_collect_all_layers_can_include_disabled_overlay_for_listing(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "disabled",
            {
                "id": "disabled",
                "extends": "wf",
                "priority": 10,
                "enabled": False,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "new", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        default_layers = resolver.collect_all_layers("wf")
        listed_layers = resolver.collect_all_layers("wf", include_disabled=True)

        assert [layer.source for layer in default_layers] == ["base"]
        assert [layer.source for layer in listed_layers] == ["project:disabled", "base"]

    def test_resolve_invalid_anchor_raises(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "missing",
                        "step": {"id": "new", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        with pytest.raises(ValueError, match="anchor 'missing' does not match any base step id"):
            resolver.resolve("wf")

    def test_resolve_missing_workflow(self, project_dir):
        resolver = WorkflowResolver(project_dir)
        with pytest.raises(FileNotFoundError, match="Workflow not found"):
            resolver.resolve("missing")

    def test_resolve_returns_composed_result_for_caller_validation(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "replace",
                        "anchor": "a",
                        "step": {"id": "a", "type": "invalid-type", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        definition = resolver.resolve("wf")
        errors = validate_workflow(definition)
        assert any("invalid-type" in err for err in errors)

    def test_resolve_rejects_symlinked_project_overlay_dir(self, project_dir, tmp_path):
        """ProjectOverlaySource must reject a symlinked per-workflow overlay directory."""
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)

        # Create a real overlay directory outside the project with a malicious overlay.
        outside_dir = tmp_path / "outside_overlays" / "wf"
        outside_dir.mkdir(parents=True, exist_ok=True)
        outside_dir.joinpath("evil.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "evil",
                    "extends": "wf",
                    "priority": 100,
                    "edits": [
                        {
                            "operation": "insert_after",
                            "anchor": "a",
                            "step": {"id": "evil-step", "type": "command", "command": "rm -rf /"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        # Symlink the per-workflow overlay directory to the outside location.
        overlays_root = project_dir / ".specify" / "workflows" / "overlays"
        overlays_root.mkdir(parents=True, exist_ok=True)
        symlink_dir = overlays_root / "wf"
        symlink_dir.symlink_to(outside_dir)

        resolver = WorkflowResolver(project_dir)
        with pytest.raises(ValueError, match="Symlinked overlay directories are not allowed"):
            resolver.resolve("wf")

    def test_resolve_rejects_symlinked_overlay_root(self, project_dir, tmp_path):
        """ProjectOverlaySource must reject a symlinked overlay root too."""
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)

        outside_root = tmp_path / "outside-overlays-root"
        outside_root.mkdir(parents=True, exist_ok=True)
        workflow_dir = outside_root / "wf"
        workflow_dir.mkdir()
        workflow_dir.joinpath("evil.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "evil",
                    "extends": "wf",
                    "priority": 100,
                    "edits": [
                        {
                            "operation": "insert_after",
                            "anchor": "a",
                            "step": {"id": "evil-step", "type": "command", "command": "rm -rf /"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        overlays_root = project_dir / ".specify" / "workflows" / "overlays"
        overlays_root.symlink_to(outside_root, target_is_directory=True)

        resolver = WorkflowResolver(project_dir)
        with pytest.raises(ValueError, match="Symlinked overlay directories are not allowed"):
            resolver.resolve("wf")

    def test_resolve_reports_invalid_overlay_yaml_cleanly(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        overlay_dir = project_dir / ".specify" / "workflows" / "overlays" / "wf"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        (overlay_dir / "broken.yml").write_text("id: broken\nextends: wf\npriority: [\n", encoding="utf-8")

        resolver = WorkflowResolver(project_dir)
        with pytest.raises(ValueError, match="Invalid YAML"):
            resolver.resolve("wf")

    def test_resolve_attribution_for_inserted_composite_step(self, project_dir):
        """Inserted composite steps must attribute nested children to the overlay source."""
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {
                            "id": "if-1",
                            "type": "if",
                            "condition": "true",
                            "then": [{"id": "then-x", "type": "command", "command": "echo"}],
                            "else": [{"id": "else-y", "type": "command", "command": "echo"}],
                        },
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        _definition, _layers, attribution = resolver.resolve_with_layers("wf")
        sources = {c.step_id: c.source for c in attribution}
        assert sources["a"] == "base"
        assert sources["if-1"] == "project:ov1"
        assert sources["then-x"] == "project:ov1"
        assert sources["else-y"] == "project:ov1"

    def test_engine_load_workflow_uses_resolver(self, project_dir):
        from specify_cli.workflows.engine import WorkflowEngine

        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        _write_overlay(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "new", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        engine = WorkflowEngine(project_dir)
        definition = engine.load_workflow("wf")
        assert [s["id"] for s in definition.steps] == ["a", "new"]

    def test_engine_rejects_traversal_without_legacy_path_fallback(
        self, project_dir
    ):
        from specify_cli.workflows.engine import WorkflowEngine

        outside = project_dir / ".specify" / "outside"
        outside.mkdir(parents=True)
        (outside / "workflow.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "workflow": {
                        "id": "outside",
                        "name": "Outside",
                        "version": "1.0.0",
                    },
                    "steps": [
                        {
                            "id": "external",
                            "type": "command",
                            "command": "echo",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        engine = WorkflowEngine(project_dir)
        with pytest.raises(ValueError, match="Invalid workflow ID"):
            engine.load_workflow("../outside")
