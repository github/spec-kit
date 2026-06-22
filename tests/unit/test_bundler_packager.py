"""Unit tests for the artifact packager (T023): contents, versioning, determinism."""
from __future__ import annotations

import os
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
    (bundle / "README.md").write_text("# x", encoding="utf-8")
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
        # Same files, same order (sorted).
        assert a.namelist() == b.namelist()
        # Fixed timestamps + permissions make each member byte-identical.
        for left, right in zip(a.infolist(), b.infolist()):
            assert left.date_time == right.date_time
            assert left.external_attr == right.external_attr
    # The whole artifact is byte-for-byte reproducible.
    assert first.artifact_path.read_bytes() == second.artifact_path.read_bytes()


def test_output_dir_inside_bundle_excludes_prior_artifacts(tmp_path: Path):
    bundle = _make_bundle(tmp_path / "b", extra_files={"a.txt": "a"})
    out_dir = bundle / "dist"
    # Build twice into a dir nested in the bundle; the second build must not
    # re-package the first artifact, so contents stay identical and bounded.
    first = build_bundle(bundle, output_dir=out_dir)
    second = build_bundle(bundle, output_dir=out_dir)
    with zipfile.ZipFile(second.artifact_path) as archive:
        names = archive.namelist()
    assert not any(name.startswith("dist/") for name in names)
    assert not any(name.endswith(".zip") for name in names)
    assert first.file_count == second.file_count


def test_prior_version_artifact_not_repackaged(tmp_path: Path):
    # An older artifact sitting next to bundle.yml must not be packaged.
    bundle = _make_bundle(tmp_path / "b", extra_files={"a.txt": "a"})
    (bundle / "demo-bundle-0.9.0.zip").write_bytes(b"PK\x03\x04 old artifact")
    result = build_bundle(bundle, output_dir=bundle)
    with zipfile.ZipFile(result.artifact_path) as archive:
        names = archive.namelist()
    assert not any(name.endswith(".zip") for name in names)
    assert "demo-bundle-0.9.0.zip" not in names


def test_symlinked_directory_is_not_followed(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    bundle = _make_bundle(tmp_path / "b", extra_files={"a.txt": "a"})
    link = bundle / "linkdir"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    # Build must succeed (no ensure_within failure) and must not pull in the
    # out-of-tree file behind the symlinked directory.
    result = build_bundle(bundle, output_dir=tmp_path / "out")
    with zipfile.ZipFile(result.artifact_path) as archive:
        names = archive.namelist()
    assert "linkdir/secret.txt" not in names
    assert not any("secret" in name for name in names)


def test_unsafe_bundle_id_is_rejected_before_build(tmp_path: Path):
    data = valid_manifest_dict()
    data["bundle"]["id"] = "../evil"
    bundle = tmp_path / "b"
    bundle.mkdir(parents=True)
    (bundle / "bundle.yml").write_text(yaml.safe_dump(data), encoding="utf-8")
    (bundle / "README.md").write_text("# x", encoding="utf-8")
    with pytest.raises(BundlerError):
        build_bundle(bundle, output_dir=tmp_path / "out")
    # The traversal target must not have been written outside out_dir.
    assert not (tmp_path / "evil-1.2.0.zip").exists()


def test_build_refuses_missing_readme(tmp_path: Path):
    bundle = tmp_path / "b"
    bundle.mkdir()
    (bundle / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    with pytest.raises(BundlerError, match="README.md"):
        build_bundle(bundle, output_dir=tmp_path / "out")


def test_asset_zip_starting_with_bundle_id_is_packaged(tmp_path: Path):
    # A non-artifact asset whose name merely starts with the bundle id (but is
    # not a semver-named build artifact) must still be included.
    bundle = _make_bundle(tmp_path / "b", extra_files={"demo-bundle-assets.zip": "data"})
    result = build_bundle(bundle, output_dir=tmp_path / "out")
    with zipfile.ZipFile(result.artifact_path) as archive:
        names = set(archive.namelist())
    assert "demo-bundle-assets.zip" in names


def test_prior_semver_artifact_is_excluded(tmp_path: Path):
    bundle = _make_bundle(tmp_path / "b", extra_files={"demo-bundle-0.9.0.zip": "old"})
    result = build_bundle(bundle, output_dir=bundle)
    with zipfile.ZipFile(result.artifact_path) as archive:
        names = set(archive.namelist())
    assert "demo-bundle-0.9.0.zip" not in names


def test_prior_artifact_with_prerelease_and_build_is_excluded(tmp_path: Path):
    # A semver artifact carrying both prerelease and build metadata must still
    # be recognized as a prior build artifact and excluded.
    bundle = _make_bundle(
        tmp_path / "b", extra_files={"demo-bundle-1.0.0-rc1+build5.zip": "old"}
    )
    result = build_bundle(bundle, output_dir=bundle)
    with zipfile.ZipFile(result.artifact_path) as archive:
        names = set(archive.namelist())
    assert "demo-bundle-1.0.0-rc1+build5.zip" not in names


@pytest.mark.skipif(
    os.name == "nt",
    reason="Windows filesystems do not carry Unix execute bits, so chmod(0o755) "
    "is a no-op and there is no executability to preserve.",
)
def test_executable_bit_preserved_in_artifact(tmp_path: Path):
    bundle = _make_bundle(tmp_path / "bundle")
    script = bundle / "scripts" / "hook.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    script.chmod(0o755)

    result = build_bundle(bundle, output_dir=tmp_path / "out")
    with zipfile.ZipFile(result.artifact_path) as archive:
        modes = {
            info.filename: (info.external_attr >> 16) & 0o777
            for info in archive.infolist()
        }
    # Executable source -> 0755; plain text files -> 0644.
    assert modes["scripts/hook.sh"] == 0o755
    assert modes["README.md"] == 0o644
