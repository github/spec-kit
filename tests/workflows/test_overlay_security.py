"""Security tests for workflow overlay path handling."""

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


class TestOverlayPathTraversal:
    """Overlay CLI must stay inside the overlay directory."""

    def test_overlay_add_rejects_traversal_in_workflow_id(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
                {
                    "id": "ov1",
                    "extends": "../wf",
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
        assert result.exit_code != 0, result.output
        assert "invalid" in result.output.lower() or "traversal" in result.output.lower()

    def test_overlay_add_rejects_traversal_in_overlay_id(self, project_dir, monkeypatch):
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
                    "id": "../../ov1",
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
        assert result.exit_code != 0, result.output
        assert "invalid" in result.output.lower() or "traversal" in result.output.lower()

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

    def test_overlay_add_rejects_symlinked_target_file(self, project_dir, monkeypatch):
        """overlay add must not overwrite through a symlinked overlay file target."""
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
        real_file = overlay_dir / "other.yml"
        real_file.write_text("sentinel\n", encoding="utf-8")
        (overlay_dir / "ov1.yml").symlink_to(real_file)

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

        result = runner.invoke(app, ["workflow", "overlay", "add", str(overlay_file)])

        assert result.exit_code != 0, result.output
        assert "symlinked path" in result.output.lower()
        assert real_file.read_text(encoding="utf-8") == "sentinel\n"

    @pytest.mark.parametrize("workflow_id", ["overlays", "runs", "steps"])
    def test_overlay_operations_reject_reserved_workflow_id(
        self, project_dir, monkeypatch, workflow_id
    ):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        result = runner.invoke(app, ["workflow", "overlay", "list", workflow_id])
        assert result.exit_code != 0, result.output
        assert "Invalid" in result.output or "reserved" in result.output.lower()

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
