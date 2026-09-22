"""Command-focused workflow overlay tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer
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

    def test_overlay_list(self, project_dir, monkeypatch):
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

        result = runner.invoke(app, ["workflow", "overlay", "list", "wf"])
        assert result.exit_code == 0, result.output
        assert "ov1" in result.output



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

    def test_find_overlay_by_manifest_id_not_filename(self, project_dir, monkeypatch):
        """_find_overlay_file must locate overlays by manifest id, not filename."""
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
        # File is named "custom.yml" but manifest declares id: "lint"
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

        from specify_cli.workflows.overlay.operations import _find_overlay_file

        # Must find by manifest id "lint", not by filename "custom"
        found = _find_overlay_file(project_dir, "wf", "lint")
        assert found is not None
        assert found.name == "custom.yml"

        # Must NOT find by filename stem "custom"
        not_found = _find_overlay_file(project_dir, "wf", "custom")
        assert not_found is None

    def test_duplicate_manifest_id_is_rejected(self, project_dir, monkeypatch):
        """Two files with the same manifest ID are ambiguous."""
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
        # Two files, both declare id: "lint"
        self._write_mismatched_overlay(
            project_dir,
            "wf",
            "aaa.yml",
            "lint",
            {
                "id": "lint",
                "extends": "wf",
                "priority": 10,
                "edits": [{"remove": "a"}],
            },
        )
        self._write_mismatched_overlay(
            project_dir,
            "wf",
            "zzz.yml",
            "lint",
            {
                "id": "lint",
                "extends": "wf",
                "priority": 20,
                "edits": [{"remove": "a"}],
            },
        )

        from specify_cli.workflows.overlay.operations import _find_overlay_file

        with pytest.raises(typer.Exit):
            _find_overlay_file(project_dir, "wf", "lint")



class TestOverlayPathTraversal:
    """Overlay CLI must stay inside the overlay directory."""

    @pytest.mark.parametrize("workflow_id", ["overlays", "runs", "steps"])
    def test_overlay_operations_reject_reserved_workflow_id(
        self, project_dir, monkeypatch, workflow_id
    ):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        result = runner.invoke(app, ["workflow", "overlay", "list", workflow_id])
        assert result.exit_code != 0, result.output
        assert "Invalid" in result.output or "reserved" in result.output.lower()

    def test_overlay_rejects_symlinked_overlays_dir(self, project_dir, monkeypatch, tmp_path):
        """Overlay commands must reject a symlinked .specify/workflows/overlays directory."""
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)

        # Create a symlinked overlays directory pointing outside the project
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        overlays_dir = project_dir / ".specify" / "workflows" / "overlays"
        overlays_dir.symlink_to(outside_dir)

        result = runner.invoke(app, ["workflow", "overlay", "list", "wf"])
        assert result.exit_code != 0, result.output
        assert "symlink" in result.output.lower()

    def test_overlay_list_rejects_symlinked_per_workflow_dir(self, project_dir, monkeypatch, tmp_path):
        """Overlay list must reject a symlinked per-workflow overlay directory."""
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)

        # Create a real overlay directory outside the project.
        outside_dir = tmp_path / "outside_wf"
        outside_dir.mkdir()
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
                            "step": {"id": "evil-step", "type": "command", "command": "echo"},
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

        result = runner.invoke(app, ["workflow", "overlay", "list", "wf"])
        assert result.exit_code != 0, result.output
        assert "symlink" in result.output.lower()

    def test_overlay_list_reports_invalid_yaml_cleanly(self, project_dir, monkeypatch):
        """Overlay list should surface malformed overlay YAML as a clean user error."""
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
        overlay_dir = project_dir / ".specify" / "workflows" / "overlays" / "wf"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        (overlay_dir / "broken.yml").write_text("id: broken\nextends: wf\npriority: [\n", encoding="utf-8")

        result = runner.invoke(app, ["workflow", "overlay", "list", "wf"])

        assert result.exit_code != 0, result.output
        assert "Invalid YAML" in result.output
