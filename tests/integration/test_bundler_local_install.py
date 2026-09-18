"""Tests for installing a bundle from a local artifact/path (T045).

The resolution-level tests are pure; the end-to-end test installs the bundled
``agent-context`` extension fully offline from a built ``.zip`` artifact,
proving the real in-process primitive dispatch (T044) works without a network.
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.bundler import BundlerError
from specify_cli.commands.bundle import _local_manifest_source
from tests.bundler_helpers import FakeInstaller, make_project, valid_manifest_dict, write_manifest


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


def test_local_source_zip_non_utf8_manifest_raises_bundler_error(tmp_path: Path):
    """Undecodable bundle.yml bytes inside a .zip must raise BundlerError.

    The manifest bytes are decoded as UTF-8 explicitly, matching
    ``yamlio.load_yaml``'s "Could not read ..." contract, instead of
    escaping as a raw ``UnicodeDecodeError``/``ReaderError`` traceback.
    """
    artifact = tmp_path / "demo.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", b"\xff\xfe bundle \xc3\x28\n")

    with pytest.raises(BundlerError, match="Could not read"):
        _local_manifest_source(str(artifact))


def test_local_source_zip_utf16_manifest_rejected_like_directory(tmp_path: Path):
    """A well-formed UTF-16 manifest must fail the same way in a .zip.

    ``yamlio.load_yaml`` decodes strictly as UTF-8, so a UTF-16 bundle.yml
    (the realistic PowerShell ``Out-File`` output) is rejected when read
    from a directory. Feeding the zip bytes straight to PyYAML would let
    its Reader honour the UTF-16 BOM and *accept* the same manifest,
    making zip and directory sources diverge.
    """
    artifact = tmp_path / "demo.zip"
    manifest_text = "bundle:\n  id: demo-bundle\n  version: 1.0.0\n"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", manifest_text.encode("utf-16"))

    with pytest.raises(BundlerError, match="Could not read"):
        _local_manifest_source(str(artifact))


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


def test_local_zip_uses_bounded_archive_open(tmp_path: Path):
    artifact = tmp_path / "too-many-entries.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", yaml.safe_dump(valid_manifest_dict()))
        for index in range(512):
            archive.writestr(f"assets/{index}.txt", "")

    with pytest.raises(BundlerError, match="too many entries"):
        _local_manifest_source(str(artifact))


def test_local_zip_wraps_malformed_manifest_yaml(tmp_path: Path):
    """A malformed bundle.yml inside a .zip must raise BundlerError.

    The zip branch parses YAML inline rather than through load_yaml(), so the
    raw yaml.YAMLError used to escape. It is neither a ValueError nor an
    OSError, so nothing upstream caught it.
    """
    artifact = tmp_path / "bad-manifest.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", "bundle: [unclosed\n  id: demo\n")

    with pytest.raises(BundlerError, match="Invalid YAML"):
        _local_manifest_source(str(artifact))


def test_malformed_manifest_yaml_fails_alike_for_every_local_source(tmp_path: Path):
    """`bundle install` reports malformed YAML the same way for all 3 sources.

    Directory and bundle.yml sources already exited 1 with an "Invalid YAML"
    message; the .zip source dumped a yaml.parser.ParserError traceback.
    """
    bad_yaml = "bundle: [unclosed\n  id: demo\n"

    directory = tmp_path / "dir-src"
    directory.mkdir()
    (directory / "bundle.yml").write_text(bad_yaml, encoding="utf-8")

    manifest_file = tmp_path / "standalone.yml"
    manifest_file.write_text(bad_yaml, encoding="utf-8")

    artifact = tmp_path / "artifact.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("bundle.yml", bad_yaml)

    runner = CliRunner()
    for source in (directory, manifest_file, artifact):
        result = runner.invoke(app, ["bundle", "install", str(source)])
        assert result.exit_code == 1, f"{source.name}: {result.output}"
        assert result.exception is None or isinstance(
            result.exception, SystemExit
        ), f"{source.name} leaked {type(result.exception).__name__}"
        assert "Invalid YAML" in result.output, f"{source.name}: {result.output}"


def test_invalid_local_manifest_is_rejected_before_project_init(
    tmp_path: Path,
    monkeypatch,
):
    bundle_dir = tmp_path / "invalid-bundle"
    data = valid_manifest_dict()
    data["bundle"]["author"] = ""
    write_manifest(bundle_dir, data)
    empty_cwd = tmp_path / "empty"
    empty_cwd.mkdir()
    monkeypatch.chdir(empty_cwd)

    runner = CliRunner()
    with patch("specify_cli.commands.bundle._run_init") as run_init:
        result = runner.invoke(
            app,
            ["bundle", "install", str(bundle_dir), "--offline"],
        )

    assert result.exit_code == 1
    assert "Missing required field: bundle.author" in result.output
    run_init.assert_not_called()


def test_incompatible_local_manifest_is_rejected_before_project_init(
    tmp_path: Path,
    monkeypatch,
):
    bundle_dir = tmp_path / "incompatible-bundle"
    data = valid_manifest_dict()
    data["requires"]["speckit_version"] = ">=999.0.0"
    write_manifest(bundle_dir, data)
    empty_cwd = tmp_path / "empty"
    empty_cwd.mkdir()
    monkeypatch.chdir(empty_cwd)

    runner = CliRunner()
    with patch("specify_cli.commands.bundle._run_init") as run_init:
        result = runner.invoke(
            app,
            ["bundle", "install", str(bundle_dir), "--offline"],
        )

    assert result.exit_code == 1
    assert "requires Spec Kit >=999.0.0" in result.output
    run_init.assert_not_called()


@pytest.mark.parametrize("source_kind", ["manifest", "directory", "zip"])
@pytest.mark.parametrize("bundle_version", ["1.2.0", "2.0.0"])
def test_local_install_refresh_updates_owned_components(
    tmp_path: Path, monkeypatch, source_kind: str, bundle_version: str,
):
    """Local upgrades refresh owned pins before advancing the bundle record."""
    from specify_cli.bundler.models.records import load_records, records_path

    project = make_project(tmp_path / "proj")
    monkeypatch.chdir(project)
    versions = {}

    class VersionedInstaller(FakeInstaller):
        def install(self, root, component):
            super().install(root, component)
            versions[(component.kind, component.id)] = component.version

        def refresh(self, root, component):
            assert load_records(root)[0].version == "1.2.0"
            super().refresh(root, component)
            versions[(component.kind, component.id)] = component.version

    installer = VersionedInstaller()
    monkeypatch.setattr(
        "specify_cli.bundler.services.adapters.DefaultPrimitiveInstaller",
        lambda **kwargs: installer,
    )
    data = valid_manifest_dict()
    manifest_path = write_manifest(tmp_path / "local bundle", data)
    runner = CliRunner()
    first = runner.invoke(app, ["bundle", "install", str(manifest_path), "--offline"])
    assert first.exit_code == 0, first.output
    original_record = records_path(project).read_bytes()
    original_versions = dict(versions)

    data["bundle"]["version"] = bundle_version
    data["provides"]["extensions"][0]["version"] = "2.0.0"
    data["provides"]["presets"][0]["version"] = "3.0.0"
    data["provides"]["workflows"][0]["version"] = "0.4.0"
    write_manifest(manifest_path.parent, data)
    if source_kind == "manifest":
        source = manifest_path
    elif source_kind == "directory":
        source = manifest_path.parent
    else:
        source = tmp_path / "local bundle.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.write(manifest_path, "bundle.yml")

    rejected = runner.invoke(app, ["bundle", "install", str(source), "--offline"])
    assert rejected.exit_code == 1, rejected.output
    assert records_path(project).read_bytes() == original_record
    assert versions == original_versions
    assert installer.refresh_calls == []

    refreshed = runner.invoke(
        app, ["bundle", "install", str(source), "--offline", "--refresh"],
    )
    assert refreshed.exit_code == 0, refreshed.output
    assert "--refresh" in rejected.output
    assert "4 refreshed" in refreshed.output
    expected = {
        ("extensions", "ext-a"): "2.0.0",
        ("presets", "preset-a"): "3.0.0",
        ("steps", "step-a"): None,
        ("workflows", "wf-a"): "0.4.0",
    }
    assert versions == expected
    assert set(installer.refresh_calls) == set(expected)
    record = load_records(project)[0]
    assert record.version == bundle_version
    assert {(c.kind, c.id): c.version for c in record.contributed_components} == expected


@pytest.mark.parametrize("source_kind", ["manifest", "directory", "zip"])
@pytest.mark.parametrize("bundle_version", ["1.2.0", "2.0.0"])
def test_local_refresh_catalog_extension_requires_network(
    tmp_path: Path, monkeypatch, source_kind: str, bundle_version: str,
):
    """Use the real installer; replace only catalog I/O with local artifacts."""
    from specify_cli.bundler.models.records import load_records, records_path
    from specify_cli.extensions import ExtensionCatalog

    project = make_project(tmp_path / "project")
    monkeypatch.chdir(project)
    monkeypatch.setattr("specify_cli.commands.bundle._bundle_overlaps", lambda *a, **kw: [])
    monkeypatch.setattr("specify_cli._assets._locate_bundled_extension", lambda cid: None)
    version = "1.0.0"
    downloads = []

    def download_extension(self, extension_id):
        downloads.append((extension_id, version))
        artifact = tmp_path / "extension.zip"
        extension = {
            "schema_version": "1.0",
            "extension": {
                "id": extension_id, "name": "Catalog extension",
                "version": version, "description": "Refresh regression",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"commands": [
                {"name": "speckit.catalog-ext.hello", "file": "commands/hello.md"},
            ]},
        }
        with zipfile.ZipFile(artifact, "w") as archive:
            archive.writestr("extension.yml", yaml.safe_dump(extension))
            archive.writestr("commands/hello.md", f"---\ndescription: Test\n---\n{version}\n")
        return artifact

    monkeypatch.setattr(
        ExtensionCatalog, "get_extension_info",
        lambda self, cid: {"id": cid, "version": version, "_install_allowed": True},
    )
    monkeypatch.setattr(ExtensionCatalog, "download_extension", download_extension)
    data = valid_manifest_dict(provides={"extensions": [{"id": "catalog-ext", "version": version}]})
    manifest_path = write_manifest(tmp_path / "local bundle", data)
    runner = CliRunner()
    first = runner.invoke(app, ["bundle", "install", str(manifest_path)])
    assert first.exit_code == 0, first.output
    installed_dir = project / ".specify" / "extensions" / "catalog-ext"
    payload = installed_dir / "commands" / "hello.md"
    original_payload = payload.read_bytes()
    original_manifest = (installed_dir / "extension.yml").read_bytes()
    original_record = records_path(project).read_bytes()

    version = "2.0.0"
    data["bundle"]["version"] = bundle_version
    data["provides"]["extensions"][0]["version"] = version
    write_manifest(manifest_path.parent, data)
    if source_kind == "manifest":
        source = manifest_path
    elif source_kind == "directory":
        source = manifest_path.parent
    else:
        source = tmp_path / "local bundle.zip"
        with zipfile.ZipFile(source, "w") as archive:
            archive.write(manifest_path, "bundle.yml")

    rejected = runner.invoke(app, ["bundle", "install", str(source), "--offline"])
    assert rejected.exit_code == 1, rejected.output
    assert "--refresh" in rejected.output
    assert downloads == [("catalog-ext", "1.0.0")]
    assert records_path(project).read_bytes() == original_record
    assert payload.read_bytes() == original_payload
    assert (installed_dir / "extension.yml").read_bytes() == original_manifest

    offline = runner.invoke(app, ["bundle", "install", str(source), "--refresh", "--offline"])
    assert offline.exit_code == 1, offline.output
    output = " ".join(offline.output.split())
    assert "catalog-ext" in output
    assert "refreshing this component requires network access" in output
    assert "re-run without --offline" in output
    assert "install it first" not in output
    assert downloads == [("catalog-ext", "1.0.0")]
    assert records_path(project).read_bytes() == original_record
    assert payload.read_bytes() == original_payload
    assert (installed_dir / "extension.yml").read_bytes() == original_manifest

    refreshed = runner.invoke(app, ["bundle", "install", str(source), "--refresh"])
    assert refreshed.exit_code == 0, refreshed.output
    assert "1 refreshed" in refreshed.output
    assert downloads == [("catalog-ext", "1.0.0"), ("catalog-ext", "2.0.0")]
    assert payload.read_text(encoding="utf-8").endswith("2.0.0\n")
    assert yaml.safe_load((installed_dir / "extension.yml").read_text(encoding="utf-8"))["extension"]["version"] == version
    record = load_records(project)[0]
    assert record.version == bundle_version
    assert record.contributed_components[0].version == version
