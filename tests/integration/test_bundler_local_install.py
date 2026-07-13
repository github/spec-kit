"""Tests for installing a bundle from a local artifact/path (T045).

The resolution-level tests are pure; the end-to-end test installs the bundled
``agent-context`` extension fully offline from a built ``.zip`` artifact,
proving the real in-process primitive dispatch (T044) works without a network.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler import BundlerError
from specify_cli.commands.bundle import _local_manifest_source
from tests.bundler_helpers import make_project, valid_manifest_dict, write_manifest


def test_local_source_none_for_non_path():
    assert _local_manifest_source("some-catalog-bundle-id") is None


def test_local_source_from_directory(tmp_path: Path):
    write_manifest(tmp_path, valid_manifest_dict())
    manifest = _local_manifest_source(str(tmp_path))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_local_source_from_bundle_yml(tmp_path: Path):
    path = write_manifest(tmp_path, valid_manifest_dict())
    manifest = _local_manifest_source(str(path))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_local_source_from_zip_artifact(tmp_path: Path):
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    write_manifest(bundle_dir, valid_manifest_dict())
    (bundle_dir / "README.md").write_text("# demo\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["bundle", "build", "--path", str(bundle_dir)])
    assert result.exit_code == 0, result.output
    artifact = next(bundle_dir.glob("*.zip"))

    manifest = _local_manifest_source(str(artifact))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_local_source_rejects_unknown_file(tmp_path: Path):
    weird = tmp_path / "thing.txt"
    weird.write_text("nope", encoding="utf-8")
    with pytest.raises(BundlerError, match="not a recognised bundle source"):
        _local_manifest_source(str(weird))


def test_install_bundled_extension_from_zip_offline(tmp_path: Path):
    """End-to-end: build → install (offline, local .zip) → list → remove."""
    project = make_project(tmp_path / "proj")

    bundle_dir = tmp_path / "mini"
    bundle_dir.mkdir()
    (bundle_dir / "bundle.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "bundle": {
                    "id": "mini",
                    "name": "Mini",
                    "version": "1.0.0",
                    "role": "developer",
                    "description": "minimal",
                    "author": "tests",
                    "license": "MIT",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "extensions": [{"id": "agent-context", "version": "1.0.0"}]
                },
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "README.md").write_text("# Mini\n", encoding="utf-8")

    runner = CliRunner()
    previous = Path.cwd()
    os.chdir(project)
    try:
        build = runner.invoke(app, ["bundle", "build", "--path", str(bundle_dir)])
        assert build.exit_code == 0, build.output
        artifact = next(bundle_dir.glob("*.zip"))

        install = runner.invoke(app, ["bundle", "install", str(artifact), "--offline"])
        assert install.exit_code == 0, install.output

        from specify_cli.extensions import ExtensionManager

        assert ExtensionManager(project).registry.is_installed("agent-context")

        listing = runner.invoke(app, ["bundle", "list"])
        assert "mini" in listing.output

        remove = runner.invoke(app, ["bundle", "remove", "mini"])
        assert remove.exit_code == 0, remove.output
        assert not ExtensionManager(project).registry.is_installed("agent-context")
    finally:
        os.chdir(previous)


def test_download_manifest_rejects_file_url(tmp_path: Path):
    """A catalog ``file://`` download_url is rejected — catalog URLs are
    HTTPS-only, matching extensions/presets/workflows. Disk installs go through
    the positional path (see the local-source tests above), not download_url.
    """
    from types import SimpleNamespace

    from specify_cli.commands.bundle import _download_manifest

    manifest_path = write_manifest(tmp_path / "my bundles")
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="demo-bundle", download_url=manifest_path.as_uri())
    )

    with pytest.raises(BundlerError, match="bundle install"):
        _download_manifest(resolved, offline=True)


def test_download_manifest_rejects_bare_path(tmp_path: Path):
    """A bare filesystem path download_url is likewise rejected."""
    from types import SimpleNamespace

    from specify_cli.commands.bundle import _download_manifest

    manifest_path = write_manifest(tmp_path / "plain")
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="demo-bundle", download_url=str(manifest_path))
    )

    with pytest.raises(BundlerError, match="bundle install"):
        _download_manifest(resolved, offline=True)


def test_local_install_still_resolves_via_positional_path(tmp_path: Path):
    """The supported local route — a positional path, not a download_url —
    still resolves the manifest via _local_manifest_source."""
    manifest_path = write_manifest(tmp_path / "my bundles")
    manifest = _local_manifest_source(str(manifest_path))
    assert manifest is not None
    assert manifest.bundle.id == "demo-bundle"


def test_download_manifest_rejects_non_https_url_even_offline(tmp_path: Path):
    """A non-HTTPS download_url must report the HTTPS problem, not a misleading
    'Network access disabled', even under --offline (scheme is validated before
    the offline gate)."""
    from types import SimpleNamespace

    from specify_cli.commands.bundle import _download_manifest

    resolved = SimpleNamespace(
        entry=SimpleNamespace(
            id="demo-bundle", download_url="http://example.com/bundle.zip"
        )
    )
    with pytest.raises(BundlerError, match="HTTPS"):
        _download_manifest(resolved, offline=True)
