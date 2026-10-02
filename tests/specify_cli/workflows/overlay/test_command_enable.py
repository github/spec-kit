"""Command-focused workflow overlay tests."""

from __future__ import annotations


from typer.testing import CliRunner

from specify_cli import app
from tests.specify_cli.workflows.helpers import (
    write_workflow as _write_workflow,
)

runner = CliRunner()


class TestOverlayPathTraversal:
    """Overlay CLI must stay inside the overlay directory."""

    def test_overlay_enable_rejects_traversal(self, project_dir, monkeypatch):
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
        result = runner.invoke(app, ["workflow", "overlay", "enable", "wf", "../other"])
        assert result.exit_code != 0, result.output
        assert "invalid" in result.output.lower() or "traversal" in result.output.lower()
