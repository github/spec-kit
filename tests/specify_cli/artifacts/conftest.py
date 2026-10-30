from __future__ import annotations

from collections.abc import Iterator
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


@pytest.fixture(
    params=["presets", ".registry", "dangling-presets", "dangling-registry"]
)
def symlinked_preset_registry(
    spec_kit_project: Path, tmp_path: Path, request: pytest.FixtureRequest,
) -> Iterator[Path]:
    outside = tmp_path / "outside-presets"
    outside.mkdir()
    sentinel = outside / ".registry"
    sentinel.write_bytes(b"not registry JSON")
    packs_dir = spec_kit_project / ".specify" / "presets"
    is_directory = request.param.endswith("presets")
    link = packs_dir if is_directory else packs_dir / ".registry"
    target = outside if is_directory else sentinel
    if request.param.startswith("dangling"):
        target = outside / "missing"
    if is_directory:
        packs_dir.rmdir()
    try:
        link.symlink_to(target, target_is_directory=is_directory)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")

    yield spec_kit_project

    assert link.is_symlink()
    assert sentinel.read_bytes() == b"not registry JSON"
    assert not (outside / "missing").exists()
