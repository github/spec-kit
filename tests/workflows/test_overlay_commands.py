"""Tests for workflow overlay CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    """Create a mock spec-kit project with ``.specify/workflows/`` directory."""
    workflows_dir = tmp_path / ".specify" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


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


class TestOverlayCli:
    """CLI-level tests for ``specify workflow overlay *``."""

    def test_overlay_add(self, project_dir, monkeypatch):
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
        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
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
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            app, ["workflow", "overlay", "add", str(overlay_file), "--priority", "5"]
        )
        assert result.exit_code == 0, result.output
        assert "Overlay 'ov1' added" in result.output

        installed = project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
        assert installed.is_file()
        data = yaml.safe_load(installed.read_text(encoding="utf-8"))
        assert data["priority"] == 5

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

    def test_workflow_add_copies_overlays(self, project_dir, monkeypatch, tmp_path):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        source_dir = tmp_path / "source-wf"
        source_dir.mkdir()
        (source_dir / "workflow.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "workflow": {"id": "wf", "name": "WF", "version": "1.0.0"},
                    "steps": [{"id": "a", "type": "command", "command": "echo"}],
                }
            ),
            encoding="utf-8",
        )
        overlays_dir = source_dir / "overlays"
        overlays_dir.mkdir()
        (overlays_dir / "ov1.yml").write_text(
            yaml.safe_dump(
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
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["workflow", "add", str(source_dir)])
        assert result.exit_code == 0, result.output
        installed_overlay = (
            project_dir / ".specify" / "workflows" / "wf" / "overlays" / "ov1.yml"
        )
        assert installed_overlay.is_file()
