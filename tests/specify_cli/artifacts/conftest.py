from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def spec_kit_project(tmp_path: Path) -> Path:
    """Create a minimal but valid Spec Kit project layout."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / ".specify").mkdir()
    (root / ".specify" / "presets").mkdir()
    (root / ".specify" / "extensions").mkdir()
    (root / ".specify" / "templates").mkdir()
    return root


@pytest.fixture
def non_project(tmp_path: Path) -> Path:
    """Create a directory that intentionally lacks ``.specify/``."""
    root = tmp_path / "not-proj"
    root.mkdir()
    return root
