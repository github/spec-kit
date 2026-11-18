"""``functions`` is reserved so a workflow cannot occupy the package directory."""

from __future__ import annotations

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.workflows import _commands
from specify_cli.workflows.overlay import schema
from specify_cli.workflows.overlay.schema import validate_overlay_yaml


def test_reserved_sets_agree_and_include_functions():
    assert "functions" in _commands._RESERVED_WORKFLOW_IDS
    assert "functions" in schema._RESERVED_WORKFLOW_IDS
    assert _commands._RESERVED_WORKFLOW_IDS == schema._RESERVED_WORKFLOW_IDS
    assert {"overlays", "runs", "steps"} <= schema._RESERVED_WORKFLOW_IDS


def test_workflow_add_rejects_the_id(project_dir, monkeypatch):
    source = project_dir / "incoming.yml"
    source.write_text(
        yaml.safe_dump({
            "schema_version": "1.0",
            "workflow": {"id": "functions", "name": "Bad", "version": "1.0.0"},
            "steps": [{"id": "a", "type": "shell", "run": "echo hi"}],
        }),
        encoding="utf-8",
    )
    monkeypatch.chdir(project_dir)
    result = CliRunner().invoke(app, ["workflow", "add", str(source)])
    assert result.exit_code != 0
    assert not (project_dir / ".specify" / "workflows" / "functions").exists()


def test_safe_workflow_id_dir_rejects_the_id(project_dir):
    import typer

    workflows_dir = project_dir / ".specify" / "workflows"
    with pytest.raises(typer.Exit):
        _commands._safe_workflow_id_dir(workflows_dir, "functions")
    assert not (workflows_dir / "functions").exists()


def test_overlay_cannot_extend_the_reserved_id():
    _, errors = validate_overlay_yaml({
        "id": "ov", "extends": "functions", "priority": 10,
        "edits": [{"operation": "remove", "anchor": "a"}],
    })
    assert any("extends" in error for error in errors)


def test_overlay_can_still_extend_an_ordinary_id():
    _, errors = validate_overlay_yaml({
        "id": "ov", "extends": "wf", "priority": 10,
        "edits": [{"operation": "remove", "anchor": "a"}],
    })
    assert not any("extends" in error for error in errors)
