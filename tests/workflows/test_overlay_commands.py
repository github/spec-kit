"""Tests for workflow overlay CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer
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

    def test_overlay_add_reuses_yaml_extension(self, project_dir, monkeypatch):
        """If <id>.yaml already exists, overlay add must write to it instead of creating <id>.yml."""
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
        # Pre-create the overlay using the .yaml extension.
        existing_yaml = project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yaml"
        existing_yaml.parent.mkdir(parents=True, exist_ok=True)
        existing_yaml.write_text(
            yaml.safe_dump(
                {
                    "id": "ov1",
                    "extends": "wf",
                    "priority": 1,
                    "edits": [{"remove": "a"}],
                }
            ),
            encoding="utf-8",
        )

        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
                {
                    "id": "ov1",
                    "extends": "wf",
                    "priority": 20,
                    "edits": [{"remove": "a"}],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["workflow", "overlay", "add", str(overlay_file)])
        assert result.exit_code == 0, result.output

        # Should have written to the pre-existing .yaml file.
        assert existing_yaml.is_file()
        data = yaml.safe_load(existing_yaml.read_text(encoding="utf-8"))
        assert data["priority"] == 10

        # Must NOT have created a duplicate .yml alongside the .yaml.
        duplicate_yml = existing_yaml.with_suffix(".yml")
        assert not duplicate_yml.exists(), "duplicate .yml was created alongside existing .yaml"
        assert list(existing_yaml.parent.glob(f".{existing_yaml.name}.*.bak")) == []

    def test_overlay_add_with_priority_override_missing_in_file(self, project_dir, monkeypatch):
        """--priority must fix a missing priority in the overlay file."""
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
        # Overlay file has NO priority field
        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
                {
                    "id": "ov1",
                    "extends": "wf",
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

    def test_overlay_add_defaults_priority_to_ten(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
                {
                    "id": "ov1",
                    "extends": "wf",
                    "edits": [{"remove": "a"}],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["workflow", "overlay", "add", str(overlay_file)])

        assert result.exit_code == 0, result.output
        installed = project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
        assert yaml.safe_load(installed.read_text(encoding="utf-8"))["priority"] == 10

    def test_overlay_add_rejects_non_positive_priority(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
                {
                    "id": "ov1",
                    "extends": "wf",
                    "edits": [{"remove": "a"}],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(
            app,
            ["workflow", "overlay", "add", str(overlay_file), "--priority", "0"],
        )

        assert result.exit_code == 1
        assert "must be >= 1" in result.output

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

        from specify_cli.workflows.overlays._commands import workflow_resolve

        payload = workflow_resolve(project_dir, "wf")
        assert payload is not None
        assert payload["layers"][-1]["tier"] == "base"
        assert payload["layers"][-1]["priority"] is None

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

    def test_workflow_add_does_not_copy_overlays(self, project_dir, monkeypatch, tmp_path):
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
        # Overlays in the source directory should NOT be copied — workflow add
        # only installs the workflow.yml, not sibling overlays.
        installed_overlay = (
            project_dir / ".specify" / "workflows" / "wf" / "overlays" / "ov1.yml"
        )
        assert not installed_overlay.exists()


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

        from specify_cli.workflows.overlays._commands import _find_overlay_file

        # Must find by manifest id "lint", not by filename "custom"
        found = _find_overlay_file(project_dir, "wf", "lint")
        assert found is not None
        assert found.name == "custom.yml"

        # Must NOT find by filename stem "custom"
        not_found = _find_overlay_file(project_dir, "wf", "custom")
        assert not_found is None

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

        from specify_cli.workflows.overlays._commands import _find_overlay_file

        with pytest.raises(typer.Exit):
            _find_overlay_file(project_dir, "wf", "lint")
