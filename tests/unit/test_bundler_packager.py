"""Unit tests for the artifact packager (T023): contents, versioning, determinism."""
from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
import yaml

from specify_cli.bundler import BundlerError
from specify_cli.bundler.services.packager import build_bundle
from tests.bundler_helpers import valid_manifest_dict


def _make_bundle(directory: Path, *, extra_files: dict | None = None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (directory / "README.md").write_text("# Demo bundle", encoding="utf-8")
    for rel, content in (extra_files or {}).items():
        target = directory / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return directory


def test_artifact_named_by_id_and_version(tmp_path: Path):
    bundle = _make_bundle(tmp_path / "b")
    result = build_bundle(bundle, output_dir=tmp_path / "out")
    assert result.artifact_path.name == "demo-bundle-1.2.0.zip"


def test_artifact_contains_manifest_and_assets(tmp_path: Path):
    bundle = _make_bundle(tmp_path / "b", extra_files={"assets/logo.txt": "logo"})
    result = build_bundle(bundle, output_dir=tmp_path / "out")
    with zipfile.ZipFile(result.artifact_path) as archive:
        names = set(archive.namelist())
    assert "bundle.yml" in names
    assert "README.md" in names
    assert "assets/logo.txt" in names


def test_build_refuses_invalid_manifest(tmp_path: Path):
    bundle = tmp_path / "b"
    bundle.mkdir()
    data = valid_manifest_dict()
    del data["bundle"]["license"]
    (bundle / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(BundlerError, match="validate"):
        build_bundle(bundle, output_dir=tmp_path / "out")


def test_build_missing_manifest_errors(tmp_path: Path):
    with pytest.raises(BundlerError, match="No bundle.yml"):
        build_bundle(tmp_path, output_dir=tmp_path / "out")


def test_build_is_deterministic(tmp_path: Path):
    bundle = _make_bundle(tmp_path / "b", extra_files={"a.txt": "a", "z.txt": "z"})
    first = build_bundle(bundle, output_dir=tmp_path / "out1")
    second = build_bundle(bundle, output_dir=tmp_path / "out2")
    with zipfile.ZipFile(first.artifact_path) as a, zipfile.ZipFile(second.artifact_path) as b:
        # Same files, same order (sorted) — stable, reproducible manifests.
        assert a.namelist() == b.namelist()
