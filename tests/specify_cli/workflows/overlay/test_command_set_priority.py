"""Command-focused workflow overlay tests."""

from __future__ import annotations

from pathlib import Path

import yaml
from typer.testing import CliRunner

from specify_cli import app
from tests.specify_cli.workflows.helpers import (
    write_overlay as _write_overlay,
    write_workflow as _write_workflow,
)

runner = CliRunner()


class TestOverlayCli:
    """CLI-level tests for ``specify workflow overlay *``."""

    def test_overlay_set_priority_keeps_non_ascii_text_readable(
        self, project_dir, monkeypatch
    ):
        """Toggling an overlay must not mangle non-ASCII text already in it."""
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
        message = "Revisar el plan — ¿aprobar? 日本語"
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
                        "step": {
                            "id": "a",
                            "type": "gate",
                            "message": message,
                            "options": ["approve"],
                        },
                    }
                ],
            },
        )

        result = runner.invoke(
            app, ["workflow", "overlay", "set-priority", "wf", "ov1", "20"]
        )
        assert result.exit_code == 0, result.output

        text = (
            project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
        ).read_text(encoding="utf-8")
        assert message in text, text
        assert "\\u" not in text and "\\x" not in text, text
        data = yaml.safe_load(text)
        assert data["priority"] == 20
        assert data["edits"][0]["step"]["message"] == message

    def test_overlay_set_priority(self, project_dir, monkeypatch):
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

        result = runner.invoke(
            app, ["workflow", "overlay", "set-priority", "wf", "ov1", "20"]
        )
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (
                project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
            ).read_text(encoding="utf-8")
        )
        assert data["priority"] == 20
        assert list(
            (project_dir / ".specify" / "workflows" / "overlays" / "wf").glob(
                ".ov1.yml.*.bak"
            )
        ) == []

    def test_overlay_set_priority_rejects_zero(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)

        result = runner.invoke(
            app, ["workflow", "overlay", "set-priority", "wf", "ov1", "0"]
        )

        assert result.exit_code == 1
        assert "must be >= 1" in result.output

    def test_overlay_set_priority_rejects_ids_with_trailing_newline(self, project_dir, monkeypatch):
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

        result = runner.invoke(
            app, ["workflow", "overlay", "set-priority", "wf", "ov1\n", "20"]
        )
        assert result.exit_code == 1
        assert "Invalid overlay ID" in result.output

        result = runner.invoke(
            app, ["workflow", "overlay", "set-priority", "wf\n", "ov1", "20"]
        )
        assert result.exit_code == 1
        assert "Invalid workflow ID" in result.output



class TestOverlayFilenameVsManifestId:
    """Overlay identity must come from the manifest ``id`` field, not the filename.

    This matches the project-wide convention: presets use ``preset.id``,
    extensions use ``extension.id``, workflows use ``workflow.id``, and
    workflow steps use ``step.type_key``. Overlays must follow the same pattern.
    """

    def _write_mismatched_overlay(
        self, project_root: Path, workflow_id: str, filename: str, manifest_id: str, data: dict
    ) -> Path:
        """Write an overlay file where filename != manifest id."""
        ov_dir = project_root / ".specify" / "workflows" / "overlays" / workflow_id
        ov_dir.mkdir(parents=True, exist_ok=True)
        ov_path = ov_dir / filename
        ov_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        return ov_path

    def test_set_priority_with_mismatched_filename(self, project_dir, monkeypatch):
        """set-priority must work when filename != manifest id."""
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
        self._write_mismatched_overlay(
            project_dir,
            "wf",
            "custom.yml",
            "lint",
            {
                "id": "lint",
                "extends": "wf",
                "priority": 10,
                "edits": [{"remove": "a"}],
            },
        )

        result = runner.invoke(app, ["workflow", "overlay", "set-priority", "wf", "lint", "25"])
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (project_dir / ".specify" / "workflows" / "overlays" / "wf" / "custom.yml").read_text(
                encoding="utf-8"
            )
        )
        assert data["priority"] == 25



class TestOverlayPathTraversal:
    """Overlay CLI must stay inside the overlay directory."""

    def test_overlay_set_priority_rejects_traversal(self, project_dir, monkeypatch):
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
        result = runner.invoke(
            app, ["workflow", "overlay", "set-priority", "wf", "../other", "10"]
        )
        assert result.exit_code != 0, result.output
        assert "invalid" in result.output.lower() or "traversal" in result.output.lower()
