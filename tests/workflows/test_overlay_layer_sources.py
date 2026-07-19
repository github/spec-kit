"""Tests for ProjectOverlaySource and BaseWorkflowSource."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from specify_cli.workflows.overlays.layer_sources import (
    BaseWorkflowSource,
    OverlayLoadError,
    ProjectOverlaySource,
)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    workflows_dir = tmp_path / ".specify" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


def _write_overlay_file(project_dir: Path, workflow_id: str, overlay_id: str, data: dict) -> Path:
    ov_dir = project_dir / ".specify" / "workflows" / "overlays" / workflow_id
    ov_dir.mkdir(parents=True, exist_ok=True)
    path = ov_dir / f"{overlay_id}.yml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


class TestProjectOverlaySourceFileReadErrors:
    """File-read errors must be wrapped in OverlayLoadError, not leaked as raw tracebacks."""

    def test_oserror_raises_overlay_load_error(self, project_dir: Path) -> None:
        """An OSError from read_text (e.g. permission denied) is wrapped in OverlayLoadError."""
        _write_overlay_file(
            project_dir,
            "wf",
            "ov1",
            {"id": "ov1", "extends": "wf", "priority": 5, "edits": []},
        )
        source = ProjectOverlaySource(project_dir)
        with patch.object(Path, "read_text", side_effect=OSError("Permission denied")):
            with pytest.raises(OverlayLoadError) as exc_info:
                source.collect("wf")
        assert exc_info.value.errors, "OverlayLoadError must carry a non-empty errors list"

    def test_unicode_error_raises_overlay_load_error(self, project_dir: Path) -> None:
        """A file containing non-UTF-8 bytes raises OverlayLoadError, not UnicodeDecodeError."""
        ov_dir = project_dir / ".specify" / "workflows" / "overlays" / "wf"
        ov_dir.mkdir(parents=True, exist_ok=True)
        # Write raw invalid UTF-8 bytes directly so read_text(encoding="utf-8") fails.
        bad_file = ov_dir / "bad.yml"
        bad_file.write_bytes(b"\xff\xfe invalid utf-8")

        source = ProjectOverlaySource(project_dir)
        with pytest.raises(OverlayLoadError) as exc_info:
            source.collect("wf")
        assert exc_info.value.errors, "OverlayLoadError must carry a non-empty errors list"


_UNSAFE_IDS = [
    "../outside",
    "../../escape",
    "nested/workflow",
    "wf\n",
    "overlays",
    "runs",
    "steps",
    "",
    "/absolute",
    "UPPER",
    "has space",
]


class TestProjectOverlaySourceIdValidation:
    """ProjectOverlaySource.collect() must reject unsafe IDs before path construction."""

    @pytest.mark.parametrize("workflow_id", _UNSAFE_IDS)
    def test_rejects_unsafe_id(self, project_dir: Path, workflow_id: str) -> None:
        source = ProjectOverlaySource(project_dir)
        with pytest.raises(OverlayLoadError, match="Invalid workflow ID"):
            source.collect(workflow_id)

    @pytest.mark.parametrize("workflow_id", _UNSAFE_IDS)
    def test_does_not_access_filesystem_for_unsafe_id(
        self, project_dir: Path, workflow_id: str
    ) -> None:
        """No directory walk or file read should happen for an invalid ID."""
        source = ProjectOverlaySource(project_dir)
        with patch.object(Path, "iterdir", side_effect=AssertionError("iterdir called")):
            with pytest.raises(OverlayLoadError, match="Invalid workflow ID"):
                source.collect(workflow_id)


class TestProjectOverlaySourceContainment:
    """ProjectOverlaySource.collect() must enforce containment of the workflow overlay dir."""

    def test_rejects_symlinked_workflow_overlay_dir(self, project_dir: Path, tmp_path: Path) -> None:
        """A symlinked per-workflow overlay directory must be rejected."""
        real_dir = tmp_path / "real-overlay"
        real_dir.mkdir()
        overlay_root = project_dir / ".specify" / "workflows" / "overlays"
        overlay_root.mkdir(parents=True, exist_ok=True)
        link = overlay_root / "wf"
        link.symlink_to(real_dir)

        source = ProjectOverlaySource(project_dir)
        with pytest.raises(OverlayLoadError, match="Symlinked overlay directories are not allowed"):
            source.collect("wf")

    def test_rejects_workflow_overlay_dir_escaping_root(
        self, project_dir: Path, tmp_path: Path
    ) -> None:
        """A workflow overlay dir that resolves outside the overlay root must be rejected.

        This requires the ID itself to pass validation but the resolved path to escape —
        which is possible if the overlay root itself is a junction/mount that resolves
        outside the project root; or in edge cases on case-insensitive file systems.
        We simulate it by patching Path.resolve to return an outside path.
        """
        overlay_root = project_dir / ".specify" / "workflows" / "overlays"
        overlay_root.mkdir(parents=True, exist_ok=True)
        workflow_overlay_dir = overlay_root / "wf"
        workflow_overlay_dir.mkdir()

        outside = tmp_path / "outside" / "wf"
        outside.mkdir(parents=True)

        original_resolve = Path.resolve

        def fake_resolve(self: Path, **kwargs: object) -> Path:
            if self == workflow_overlay_dir:
                return outside
            return original_resolve(self, **kwargs)

        source = ProjectOverlaySource(project_dir)
        with patch.object(Path, "resolve", fake_resolve):
            with pytest.raises(OverlayLoadError, match="Path traversal detected"):
                source.collect("wf")


class TestProjectOverlaySourceDisabledFiltering:
    """ProjectOverlaySource.collect() should expose disabled entries only on opt-in."""

    def test_skips_disabled_by_default(self, project_dir: Path) -> None:
        _write_overlay_file(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 5,
                "enabled": False,
                "edits": [{"remove": "a"}],
            },
        )

        source = ProjectOverlaySource(project_dir)
        assert source.collect("wf") == []

    def test_can_include_disabled_for_management_views(self, project_dir: Path) -> None:
        _write_overlay_file(
            project_dir,
            "wf",
            "ov1",
            {
                "id": "ov1",
                "extends": "wf",
                "priority": 5,
                "enabled": False,
                "edits": [{"remove": "a"}],
            },
        )

        source = ProjectOverlaySource(project_dir)
        layers = source.collect("wf", include_disabled=True)
        assert [layer.content.id for layer in layers] == ["ov1"]
        assert layers[0].content.enabled is False

    def test_skips_invalid_disabled_overlay_during_resolution(self, project_dir: Path) -> None:
        _write_overlay_file(
            project_dir,
            "wf",
            "disabled",
            {
                "id": "disabled",
                "extends": "wf",
                "enabled": False,
                "edits": "not-a-list",
            },
        )

        source = ProjectOverlaySource(project_dir)
        assert source.collect("wf") == []
        with pytest.raises(OverlayLoadError, match="edits"):
            source.collect("wf", include_disabled=True)

    def test_rejects_duplicate_manifest_ids(self, project_dir: Path) -> None:
        data = {
            "id": "duplicate",
            "extends": "wf",
            "edits": [{"remove": "a"}],
        }
        _write_overlay_file(project_dir, "wf", "first", data)
        _write_overlay_file(project_dir, "wf", "second", data)

        with pytest.raises(OverlayLoadError, match="Duplicate overlay id"):
            ProjectOverlaySource(project_dir).collect("wf")


class TestBaseWorkflowSourceIdValidation:
    """BaseWorkflowSource.collect() must reject unsafe IDs before path construction."""

    @pytest.mark.parametrize("workflow_id", _UNSAFE_IDS)
    def test_rejects_unsafe_id(self, project_dir: Path, workflow_id: str) -> None:
        source = BaseWorkflowSource(project_dir)
        with pytest.raises(OverlayLoadError, match="Invalid workflow ID"):
            source.collect(workflow_id)


class TestBaseWorkflowSourceContainment:
    """BaseWorkflowSource.collect() must enforce the same checks as _safe_workflow_id_dir."""

    def test_rejects_symlinked_workflow_dir(self, project_dir: Path, tmp_path: Path) -> None:
        """A symlinked workflow directory must be rejected."""
        real_dir = tmp_path / "real-wf"
        real_dir.mkdir()
        (real_dir / "workflow.yml").write_text("schema_version: '1.0'\n", encoding="utf-8")

        workflows_dir = project_dir / ".specify" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        link = workflows_dir / "wf"
        link.symlink_to(real_dir)

        source = BaseWorkflowSource(project_dir)
        with pytest.raises(OverlayLoadError, match="Symlinked overlay directories are not allowed"):
            source.collect("wf")

    def test_rejects_symlinked_workflow_yml(self, project_dir: Path, tmp_path: Path) -> None:
        """A symlinked workflow.yml must be rejected even if the directory is real."""
        real_yml = tmp_path / "workflow.yml"
        real_yml.write_text("schema_version: '1.0'\n", encoding="utf-8")

        workflows_dir = project_dir / ".specify" / "workflows"
        wf_dir = workflows_dir / "wf"
        wf_dir.mkdir(parents=True, exist_ok=True)
        link = wf_dir / "workflow.yml"
        link.symlink_to(real_yml)

        source = BaseWorkflowSource(project_dir)
        with pytest.raises(OverlayLoadError, match="Symlinked workflow files are not allowed"):
            source.collect("wf")

    def test_missing_workflow_returns_empty(self, project_dir: Path) -> None:
        """A workflow directory that does not exist returns an empty layer list."""
        source = BaseWorkflowSource(project_dir)
        assert source.collect("no-such-wf") == []

    def test_rejects_symlinked_workflows_root(self, project_dir: Path, tmp_path: Path) -> None:
        outside = tmp_path / "outside"
        outside.mkdir()
        workflows_dir = project_dir / ".specify" / "workflows"
        workflows_dir.rmdir()
        workflows_dir.symlink_to(outside)

        with pytest.raises(OverlayLoadError, match="Symlinked workflow directories"):
            BaseWorkflowSource(project_dir).collect("wf")
