"""Command-focused workflow overlay tests."""

from __future__ import annotations


import pytest
from typer.testing import CliRunner

from specify_cli import app
from tests.specify_cli.workflows.helpers import (
    write_overlay as _write_overlay,
    write_workflow as _write_workflow,
)

runner = CliRunner()


class TestOverlayCli:
    """CLI-level tests for ``specify workflow overlay *``."""

    def test_workflow_resolve(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "echo"}],
            },
        )
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

        result = runner.invoke(app, ["workflow", "resolve", "wf"])
        assert result.exit_code == 0, result.output
        assert "base" in result.output
        assert "project:ov1" in result.output
        assert "new" in result.output
        assert "priority=n/a" in result.output

        from specify_cli.workflows.overlay.operations import workflow_resolve

        payload = workflow_resolve(project_dir, "wf")
        assert payload is not None
        assert payload["layers"][-1]["tier"] == "base"
        assert payload["layers"][-1]["priority"] is None

    def test_workflow_resolve_prints_tier_labels(self, project_dir, monkeypatch):
        """Layer tiers render literally; an unescaped ``[base]`` is eaten as markup."""
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "echo"}],
            },
        )
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

        result = runner.invoke(app, ["workflow", "resolve", "wf"])
        assert result.exit_code == 0, result.output
        assert "[base]" in result.output
        assert "[project-overlay]" in result.output

    @pytest.mark.parametrize(
        "step_id",
        [
            # Balanced tag: silently swallowed, so the step vanishes from output.
            "new[stuff]",
            # Unbalanced closer: raises MarkupError -> traceback and exit 1.
            "new[/red]",
        ],
    )
    def test_workflow_resolve_escapes_rich_markup_in_step_id(
        self, project_dir, monkeypatch, step_id
    ):
        """Step IDs are unvalidated for brackets, so they must be escaped."""
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "echo"}],
            },
        )
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
                        "step": {"id": step_id, "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        result = runner.invoke(app, ["workflow", "resolve", "wf"])
        assert result.exit_code == 0, result.output
        assert step_id in result.output

    def test_workflow_resolve_equal_priority_layers_sort_by_source(self, project_dir, monkeypatch):
        """Equal-priority overlays are listed alphabetically by source."""
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        _write_workflow(
            project_dir,
            "wf",
            {
                "schema_version": "1.0",
                "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                "steps": [{"id": "a", "type": "command", "command": "echo"}],
            },
        )
        # "zzz" sorts last alphabetically, so the composer applies it last and wins.
        # Resolver layer output follows the common priority/source sort order.
        _write_overlay(
            project_dir,
            "wf",
            "aaa",
            {
                "id": "aaa",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "aaa-step", "type": "command", "command": "echo"},
                    }
                ],
            },
        )
        _write_overlay(
            project_dir,
            "wf",
            "zzz",
            {
                "id": "zzz",
                "extends": "wf",
                "priority": 10,
                "edits": [
                    {
                        "operation": "insert_after",
                        "anchor": "a",
                        "step": {"id": "zzz-step", "type": "command", "command": "echo"},
                    }
                ],
            },
        )

        result = runner.invoke(app, ["workflow", "resolve", "wf"])
        assert result.exit_code == 0, result.output
        zzz_pos = result.output.index("project:zzz")
        aaa_pos = result.output.index("project:aaa")
        assert aaa_pos < zzz_pos
