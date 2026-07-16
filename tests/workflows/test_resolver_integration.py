"""Integration tests for the WorkflowResolver."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specify_cli.workflows.engine import WorkflowDefinition
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

    def test_resolve_with_installed_overlay(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        installed_dir = project_dir / ".specify" / "workflows" / "wf" / "overlays"
        installed_dir.mkdir(parents=True, exist_ok=True)
        installed_dir.joinpath("shipped.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "shipped",
                    "extends": "wf",
                    "priority": 5,
                    "edits": [
                        {
                            "operation": "insert_after",
                            "anchor": "a",
                            "step": {"id": "shipped-new", "type": "command", "command": "echo"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        resolver = WorkflowResolver(project_dir)
        definition = resolver.resolve("wf")
        assert [s["id"] for s in definition.steps] == ["a", "shipped-new"]

    def test_resolve_higher_priority_wins(self, project_dir):
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
        # Higher priority is applied later; both insert_after 'a', so high-step
        # ends up closer to the anchor and wins the conflict.
        assert [s["id"] for s in definition.steps] == ["a", "high-step", "low-step"]

    def test_resolve_project_wins_tie_with_installed(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        installed_dir = project_dir / ".specify" / "workflows" / "wf" / "overlays"
        installed_dir.mkdir(parents=True, exist_ok=True)
        installed_dir.joinpath("shipped.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "shipped",
                    "extends": "wf",
                    "priority": 10,
                    "edits": [
                        {
                            "operation": "insert_after",
                            "anchor": "a",
                            "step": {"id": "installed-step", "type": "command", "command": "echo"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        _write_overlay(
            project_dir,
            "wf",
            "project",
            {
                "id": "project",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "project-step", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        definition = resolver.resolve("wf")
        # Same priority: installed applied first, then project wins tie by
        # ending up closer to the anchor.
        assert [s["id"] for s in definition.steps] == ["a", "project-step", "installed-step"]

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

    def test_resolve_attribution_distinguishes_project_and_installed_same_id(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        installed_dir = project_dir / ".specify" / "workflows" / "wf" / "overlays"
        installed_dir.mkdir(parents=True, exist_ok=True)
        installed_dir.joinpath("same.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "same",
                    "extends": "wf",
                    "priority": 10,
                    "edits": [
                        {
                            "operation": "insert_after",
                            "anchor": "a",
                            "step": {"id": "installed-new", "type": "command", "command": "echo"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        _write_overlay(
            project_dir,
            "wf",
            "same",
            {
                "id": "same",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "project-new", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        resolver = WorkflowResolver(project_dir)
        definition, _layers, attribution = resolver.resolve_with_layers("wf")
        assert [s["id"] for s in definition.steps] == ["a", "project-new", "installed-new"]
        sources = {c.step_id: c.source for c in attribution}
        assert sources["project-new"] == "project:same"
        assert sources["installed-new"] == "installed:same"

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

    def test_resolve_invalid_installed_overlay_fails(self, project_dir):
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)
        installed_dir = project_dir / ".specify" / "workflows" / "wf" / "overlays"
        installed_dir.mkdir(parents=True, exist_ok=True)
        installed_dir.joinpath("broken.yml").write_text(
            yaml.safe_dump(
                {
                    "id": "broken",
                    "extends": "wf",
                    "priority": 10,
                    "edits": "not-a-list",
                }
            ),
            encoding="utf-8",
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

    def test_resolve_validates_composed_result(self, project_dir):
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
        with pytest.raises(ValueError, match="Composed workflow is invalid"):
            resolver.resolve("wf")

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

    def test_resolve_rejects_symlinked_installed_overlay_dir(self, project_dir, tmp_path):
        """InstalledOverlaySource must reject a symlinked installed overlays directory."""
        data = {
            "schema_version": "1.0",
            "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "command", "command": "speckit.specify"}],
        }
        _write_workflow(project_dir, "wf", data)

        # Create a real overlays directory outside the project with a malicious overlay.
        outside_dir = tmp_path / "outside_installed"
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

        # Symlink the installed overlays directory to the outside location.
        wf_dir = project_dir / ".specify" / "workflows" / "wf"
        symlink_dir = wf_dir / "overlays"
        symlink_dir.symlink_to(outside_dir)

        resolver = WorkflowResolver(project_dir)
        with pytest.raises(ValueError, match="Symlinked overlay directories are not allowed"):
            resolver.resolve("wf")

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
