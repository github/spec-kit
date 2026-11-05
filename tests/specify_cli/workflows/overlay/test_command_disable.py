"""Command-focused workflow overlay tests."""

from __future__ import annotations

from pathlib import Path

import pytest
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

    def test_overlay_disable_and_enable(self, project_dir, monkeypatch):
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

        result = runner.invoke(app, ["workflow", "overlay", "disable", "wf", "ov1"])
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (
                project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
            ).read_text(encoding="utf-8")
        )
        assert data["enabled"] is False

        result = runner.invoke(app, ["workflow", "overlay", "enable", "wf", "ov1"])
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (
                project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
            ).read_text(encoding="utf-8")
        )
        assert data["enabled"] is True

    def test_overlay_list_shows_disabled_overlay(self, project_dir, monkeypatch):
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

        result = runner.invoke(app, ["workflow", "overlay", "list", "wf"])
        assert result.exit_code == 0, result.output
        assert "ov1" in result.output
        assert "disabled" in result.output



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

    def test_enable_disable_with_mismatched_filename(self, project_dir, monkeypatch):
        """enable/disable must work when filename != manifest id."""
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

        result = runner.invoke(app, ["workflow", "overlay", "disable", "wf", "lint"])
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (project_dir / ".specify" / "workflows" / "overlays" / "wf" / "custom.yml").read_text(
                encoding="utf-8"
            )
        )
        assert data["enabled"] is False

        result = runner.invoke(app, ["workflow", "overlay", "enable", "wf", "lint"])
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(
            (project_dir / ".specify" / "workflows" / "overlays" / "wf" / "custom.yml").read_text(
                encoding="utf-8"
            )
        )
        assert data["enabled"] is True


class TestOverlayUppercaseExtension:
    """``disable`` must find every overlay the resolver applies.

    ``ProjectOverlaySource.collect`` matches ``.yml``/``.yaml`` case-insensitively,
    so a ``lint.YML`` overlay is ACTIVE during resolution. ``_find_overlay_file``
    matched the suffix case-sensitively, so ``disable`` reported that same overlay
    "not found" -- applied, but impossible to switch off.
    """

    @pytest.mark.parametrize("filename", ["lint.YML", "lint.Yaml"])
    def test_disable_finds_uppercase_extension_overlay(
        self, project_dir, monkeypatch, filename
    ):
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
        ov_dir = project_dir / ".specify" / "workflows" / "overlays" / "wf"
        ov_dir.mkdir(parents=True, exist_ok=True)
        overlay = ov_dir / filename
        overlay.write_text(
            yaml.safe_dump(
                {
                    "id": "lint",
                    "extends": "wf",
                    "priority": 10,
                    "edits": [{"remove": "a"}],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["workflow", "overlay", "disable", "wf", "lint"])

        assert result.exit_code == 0, result.output
        assert yaml.safe_load(overlay.read_text(encoding="utf-8"))["enabled"] is False
