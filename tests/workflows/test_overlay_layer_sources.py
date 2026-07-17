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


class TestBaseWorkflowSourceIdValidation:
    """BaseWorkflowSource.collect() must reject unsafe IDs before path construction."""

    @pytest.mark.parametrize("workflow_id", _UNSAFE_IDS)
    def test_rejects_unsafe_id(self, project_dir: Path, workflow_id: str) -> None:
        source = BaseWorkflowSource(project_dir)
        with pytest.raises(OverlayLoadError, match="Invalid workflow ID"):
            source.collect(workflow_id)

