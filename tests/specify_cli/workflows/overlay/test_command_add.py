"""Command-focused workflow overlay tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from tests.specify_cli.workflows.helpers import (
    write_workflow as _write_workflow,
)

runner = CliRunner()


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

    def test_overlay_add_keeps_non_ascii_text_readable(
        self, project_dir, monkeypatch
    ):
        """``overlay add`` must not escape non-ASCII text in the written file.

        Overlay files are documented as hand-authored, so writing them back
        with ``\\uXXXX`` escapes makes the user's own file unreadable.
        """
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
        overlay_file = project_dir / "overlay.yml"
        overlay_file.write_text(
            yaml.safe_dump(
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
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["workflow", "overlay", "add", str(overlay_file)])
        assert result.exit_code == 0, result.output

        installed = (
            project_dir / ".specify" / "workflows" / "overlays" / "wf" / "ov1.yml"
        )
        text = installed.read_text(encoding="utf-8")
        assert message in text, text
        assert "\\u" not in text and "\\x" not in text, text
        # The value must still round-trip identically.
        data = yaml.safe_load(text)
        assert data["edits"][0]["step"]["message"] == message



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


class TestOverlayAddDoesNotClobber:
    """`overlay add` must not destroy a different overlay sitting at <id>.yml.

    Overlay identity is the manifest `id`, not the filename, so `lint.yml` can
    legitimately contain `id: format`. The fallback filename-derived target
    must not overwrite an occupant with a different or unreadable identity.
    """

    def _setup(self, project_dir: Path, occupant_id: str | None) -> tuple[Path, Path]:
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
        if occupant_id is not None:
            (overlay_dir / "lint.yml").write_text(
                yaml.safe_dump(
                    {
                        "id": occupant_id,
                        "extends": "wf",
                        "priority": 3,
                        "edits": [{"remove": "a"}],
                    }
                ),
                encoding="utf-8",
            )
        incoming = project_dir / "incoming.yml"
        incoming.write_text(
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
        return overlay_dir, incoming

    def test_add_does_not_clobber_a_different_overlay(
        self, project_dir, monkeypatch
    ):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_dir, incoming = self._setup(project_dir, occupant_id="format")

        result = runner.invoke(app, ["workflow", "overlay", "add", str(incoming)])

        assert result.exit_code == 1, result.output
        survivor = yaml.safe_load(
            (overlay_dir / "lint.yml").read_text(encoding="utf-8")
        )
        assert survivor["id"] == "format", survivor
        assert survivor["priority"] == 3, survivor
        assert [path.name for path in overlay_dir.iterdir() if "bak" in path.name] == []

    def test_add_still_updates_the_same_overlay_in_place(
        self, project_dir, monkeypatch
    ):
        """The guard must only fire for a different overlay id."""
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_dir, incoming = self._setup(project_dir, occupant_id="lint")

        result = runner.invoke(app, ["workflow", "overlay", "add", str(incoming)])

        assert result.exit_code == 0, result.output
        updated = yaml.safe_load(
            (overlay_dir / "lint.yml").read_text(encoding="utf-8")
        )
        assert updated["id"] == "lint"
        assert updated["priority"] == 10

    def test_add_refuses_a_directory_occupant(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_dir, incoming = self._setup(project_dir, occupant_id=None)
        occupant = overlay_dir / "lint.yml"
        occupant.mkdir()
        (occupant / "precious.txt").write_text("user data", encoding="utf-8")

        result = runner.invoke(app, ["workflow", "overlay", "add", str(incoming)])

        assert result.exit_code == 1, result.output
        assert "not a regular file" in " ".join(result.output.split())
        assert occupant.is_dir()
        assert (occupant / "precious.txt").read_text(encoding="utf-8") == "user data"
        assert [path.name for path in overlay_dir.iterdir() if "bak" in path.name] == []

    @pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are POSIX-only")
    def test_add_refuses_a_fifo_occupant(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_dir, incoming = self._setup(project_dir, occupant_id=None)
        occupant = overlay_dir / "lint.yml"
        os.mkfifo(occupant)

        result = runner.invoke(app, ["workflow", "overlay", "add", str(incoming)])

        assert result.exit_code == 1, result.output
        assert "not a regular file" in " ".join(result.output.split())
        assert occupant.is_fifo()
        assert [path.name for path in overlay_dir.iterdir() if "bak" in path.name] == []

    @pytest.mark.parametrize(
        "raw",
        [
            "id: [1, 2\n  bad: yaml:\n",
            "- just\n- a\n- sequence\n",
            "just a scalar\n",
            "extends: wf\npriority: 3\n",
            "id: 5\nextends: wf\npriority: 3\n",
        ],
        ids=["malformed", "sequence", "scalar", "missing_id", "non_string_id"],
    )
    def test_add_fails_closed_when_the_occupant_cannot_be_identified(
        self, project_dir, monkeypatch, raw
    ):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_dir, incoming = self._setup(project_dir, occupant_id=None)
        occupant = overlay_dir / "lint.yml"
        occupant.write_text(raw, encoding="utf-8")

        result = runner.invoke(app, ["workflow", "overlay", "add", str(incoming)])

        assert result.exit_code == 1, result.output
        assert occupant.read_text(encoding="utf-8") == raw
        assert [path.name for path in overlay_dir.iterdir() if "bak" in path.name] == []

    def test_add_creates_the_file_when_absent(self, project_dir, monkeypatch):
        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        overlay_dir, incoming = self._setup(project_dir, occupant_id=None)

        result = runner.invoke(app, ["workflow", "overlay", "add", str(incoming)])

        assert result.exit_code == 0, result.output
        created = yaml.safe_load(
            (overlay_dir / "lint.yml").read_text(encoding="utf-8")
        )
        assert created["id"] == "lint"
