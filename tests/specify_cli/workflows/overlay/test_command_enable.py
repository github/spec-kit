"""Command-focused workflow overlay tests."""

from __future__ import annotations

import pytest
import yaml
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


class TestOverlayUppercaseExtension:
    """``enable`` must find every overlay the resolver applies.

    ``ProjectOverlaySource.collect`` matches ``.yml``/``.yaml`` case-insensitively,
    so a ``lint.YML`` overlay is ACTIVE during resolution. ``_find_overlay_file``
    matched the suffix case-sensitively, so ``enable`` reported that same overlay
    "not found" -- disabled, and impossible to switch back on.
    """

    @pytest.mark.parametrize("filename", ["lint.YML", "lint.Yaml"])
    def test_enable_finds_uppercase_extension_overlay(
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
                    "enabled": False,
                    "edits": [{"remove": "a"}],
                }
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["workflow", "overlay", "enable", "wf", "lint"])

        assert result.exit_code == 0, result.output
        assert yaml.safe_load(overlay.read_text(encoding="utf-8"))["enabled"] is True
