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

    def test_overlay_remove(self, project_dir, monkeypatch):
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

        result = runner.invoke(app, ["workflow", "overlay", "remove", "wf", "ov1"])
        assert result.exit_code == 0, result.output
        assert not (
            project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
        ).exists()



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

    def test_remove_with_mismatched_filename(self, project_dir, monkeypatch):
        """remove must work when filename != manifest id."""
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

        result = runner.invoke(app, ["workflow", "overlay", "remove", "wf", "lint"])
        assert result.exit_code == 0, result.output
        assert not (
            project_dir / ".specify" / "workflows" / "overlays" / "wf" / "custom.yml"
        ).exists()



class TestOverlayPathTraversal:
    """Overlay CLI must stay inside the overlay directory."""

    def test_overlay_remove_cannot_escape_overlays_dir(self, project_dir, monkeypatch):
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
        # Create a base workflow file that would be the traversal target.
        target = project_dir / ".specify" / "workflows" / "wf" / "workflow.yml"
        assert target.is_file()

        result = runner.invoke(
            app, ["workflow", "overlay", "remove", "wf", "../wf/workflow"]
        )
        assert result.exit_code != 0, result.output
        assert target.is_file()
        assert "Invalid" in result.output or "traversal" in result.output.lower()

    def test_overlay_remove_rejects_symlink(self, project_dir, monkeypatch):
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

        overlay_dir = project_dir / ".specify" / "workflows" / "overlays" / "wf"
        real_file = overlay_dir / "ov1.yml"
        symlink_file = overlay_dir / "symlink.yml"
        symlink_file.symlink_to(real_file)

        result = runner.invoke(app, ["workflow", "overlay", "remove", "wf", "symlink"])
        assert result.exit_code != 0, result.output
        assert real_file.is_file()
        assert "symlink" in result.output.lower() or "Invalid" in result.output
