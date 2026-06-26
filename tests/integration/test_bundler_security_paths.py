"""Security tests: path-traversal / symlink confinement (Constitution Principle V).

These assert the bundler refuses to read or write outside an allowed root, so a
malicious manifest or artifact path cannot escape the project/bundle directory.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.lib.yamlio import ensure_within, is_safe_relpath


def test_ensure_within_allows_child(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    child = root / "sub" / "file.txt"
    assert ensure_within(root, child) == child.resolve()


def test_ensure_within_rejects_parent_traversal(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    escape = root / ".." / "secret.txt"
    with pytest.raises(BundlerError, match="escapes"):
        ensure_within(root, escape)


def test_ensure_within_rejects_absolute_outside(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    with pytest.raises(BundlerError):
        ensure_within(root, Path("/etc/passwd"))


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_ensure_within_rejects_symlink_escape(tmp_path: Path):
    root = tmp_path / "bundle"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "link.txt"
    link.symlink_to(outside)
    with pytest.raises(BundlerError, match="escapes"):
        ensure_within(root, link)


@pytest.mark.parametrize("rel,safe", [
    ("a/b.txt", True),
    ("./a.txt", True),
    ("../escape", False),
    ("a/../../escape", False),
    ("/abs", False),
    ("C:/abs", False),
    ("C:\\abs", False),
    ("\\\\server\\share", False),
    ("", False),
])
def test_is_safe_relpath(rel, safe):
    assert is_safe_relpath(rel) is safe


def test_build_skips_symlinks(tmp_path: Path):
    """Packager must not follow symlinks out of the bundle dir."""
    import yaml

    from specify_cli.bundler.services.packager import build_bundle
    from tests.bundler_helpers import valid_manifest_dict

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "bundle.yml").write_text(
        yaml.safe_dump(valid_manifest_dict()), encoding="utf-8"
    )
    (bundle / "README.md").write_text("# Demo", encoding="utf-8")

    if os.name != "nt":
        secret = tmp_path / "secret.txt"
        secret.write_text("top secret", encoding="utf-8")
        (bundle / "leak.txt").symlink_to(secret)

    result = build_bundle(bundle, output_dir=tmp_path / "out")
    import zipfile

    with zipfile.ZipFile(result.artifact_path) as archive:
        names = archive.namelist()
    assert "leak.txt" not in names
    assert "bundle.yml" in names


def test_load_records_refuses_symlinked_specify_escape(tmp_path: Path):
    # Reading bundle-records.json must honour the same confinement as writes:
    # a symlinked .specify pointing outside project_root is refused.
    from specify_cli.bundler.models.records import load_records

    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bundle-records.json").write_text(
        '{"schema_version": "1.0", "bundles": []}', encoding="utf-8"
    )
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    with pytest.raises(BundlerError, match="escapes the allowed root"):
        load_records(project)


def test_active_integration_refuses_symlinked_specify_escape(tmp_path: Path):
    # Reading the integration marker must not follow a .specify symlink that
    # resolves outside project_root; an escape is treated as "not determinable".
    from specify_cli.bundler.lib.project import active_integration

    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "integration.json").write_text(
        '{"integration": "leaked"}', encoding="utf-8"
    )
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    assert active_integration(project) is None


def test_read_catalog_config_refuses_symlinked_specify_escape(tmp_path: Path):
    from specify_cli.bundler.commands_impl import catalog_config as cc

    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bundle-catalogs.yml").write_text(
        "schema_version: '1.0'\ncatalogs: []\n", encoding="utf-8"
    )
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    with pytest.raises(BundlerError, match="escapes the allowed root"):
        cc._read(project)


def test_load_source_stack_refuses_symlinked_specify_dir(tmp_path: Path):
    from specify_cli.bundler.models.catalog import load_source_stack

    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bundle-catalogs.yml").write_text("catalogs: []\n", encoding="utf-8")
    try:
        (project / ".specify").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    with pytest.raises(BundlerError, match="escapes the allowed root"):
        load_source_stack(project)


def test_find_project_root_ignores_symlinked_specify(tmp_path: Path):
    from specify_cli.bundler.lib.project import find_project_root

    real = tmp_path / "real-specify"
    real.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    # A symlinked .specify must not be accepted as a project root.
    assert find_project_root(project) is None


def test_find_project_root_override_errors_on_symlinked_specify(tmp_path: Path, monkeypatch):
    """The SPECIFY_INIT_DIR override path refuses a symlinked .specify too,
    matching the cwd loop path (regression: the override returned early and
    skipped the symlink guard)."""
    from specify_cli.bundler.lib.project import find_project_root

    real = tmp_path / "real-specify"
    real.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / ".specify").symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    monkeypatch.setenv("SPECIFY_INIT_DIR", str(project))
    with pytest.raises(BundlerError, match="symlinked \\.specify"):
        find_project_root(None)
