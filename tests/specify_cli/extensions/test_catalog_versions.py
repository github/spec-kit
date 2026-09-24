"""Regression coverage for exact releases in an extension catalog (#4719)."""

from __future__ import annotations

import hashlib
import zipfile
from io import BytesIO
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    CatalogEntry,
    ExtensionCatalog,
    ExtensionError,
    ExtensionManifest,
)


def _archive(tmp_path: Path, version: str, extension_id: str = "demo-history") -> Path:
    path = tmp_path / f"{extension_id}-{version}.zip"
    manifest = {
        "schema_version": "1.0",
        "extension": {
            "id": extension_id,
            "name": "Demo History",
            "version": version,
            "description": "Historical release test",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "commands": [
                {"name": "speckit.demo-history.hello", "file": "commands/hello.md"}
            ]
        },
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("extension.yml", yaml.safe_dump(manifest))
        archive.writestr("commands/hello.md", "---\ndescription: hello\n---\n\nhi\n")
    return path


def _entry(old_archive: Path) -> dict:
    return {
        "id": "demo-history",
        "name": "Demo History",
        "description": "Current description",
        "version": "0.5.1",
        "download_url": "https://example.com/demo-0.5.1.zip",
        "sha256": "a" * 64,
        "requires": {"speckit_version": ">=1.0.0"},
        "provides": {"commands": 3},
        "_catalog_name": "trusted",
        "_install_allowed": True,
        "releases": {
            "0.4.12": {
                "download_url": "https://example.com/demo-0.4.12.zip",
                "sha256": hashlib.sha256(old_archive.read_bytes()).hexdigest(),
                "requires": {"speckit_version": ">=0.1.0"},
            }
        },
    }


def _catalog(
    monkeypatch: pytest.MonkeyPatch, project: Path, entry: dict
) -> ExtensionCatalog:
    monkeypatch.setattr(
        ExtensionCatalog, "_get_merged_extensions", lambda self: [entry]
    )
    return ExtensionCatalog(project)


class _ArchiveResponse(BytesIO):
    def __init__(self, data: bytes, url: str):
        super().__init__(data)
        self.url = url

    def geturl(self):
        return self.url

    def getheader(self, _name):
        return "application/zip"


def test_legacy_entry_still_selects_its_current_release(tmp_path, monkeypatch):
    entry = {
        "id": "legacy",
        "version": "1.0.0",
        "download_url": "https://example.com/a.zip",
    }
    catalog = _catalog(monkeypatch, tmp_path, entry)

    assert catalog.get_extension_info("legacy") == entry
    assert catalog.get_extension_info("legacy", "1.0.0") == entry
    assert catalog.get_extension_info("legacy", "0.9.0") is None
    assert catalog.get_extension_versions("legacy") == ["1.0.0"]


def test_historical_release_selects_its_own_url_digest_and_requirements(
    tmp_path, monkeypatch
):
    entry = _entry(_archive(tmp_path, "0.4.12"))
    catalog = _catalog(monkeypatch, tmp_path, entry)

    current = catalog.get_extension_info("demo-history")
    old = catalog.get_extension_info("demo-history", "0.4.12")

    assert current["download_url"].endswith("0.5.1.zip")
    assert old["download_url"].endswith("0.4.12.zip")
    assert old["version"] == "0.4.12"
    assert old["sha256"] != current["sha256"]
    assert old["requires"] == {"speckit_version": ">=0.1.0"}
    assert "provides" not in old
    assert old["_catalog_name"] == "trusted"
    assert "releases" not in old
    assert catalog.get_extension_info("demo-history", "0.3.0") is None
    assert catalog.get_extension_versions("demo-history") == ["0.5.1", "0.4.12"]


def test_requested_version_does_not_fall_through_to_lower_priority_catalog(
    tmp_path, monkeypatch
):
    old_archive = _archive(tmp_path, "0.4.12")
    high = _entry(old_archive)
    high["releases"] = {}
    low = _entry(old_archive)
    catalog = ExtensionCatalog(tmp_path)
    sources = [
        CatalogEntry("https://example.com/high.json", "high", 1, True),
        CatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: sources)
    monkeypatch.setattr(
        catalog,
        "_fetch_single_catalog",
        lambda source, _force=False: {
            "schema_version": "1.0",
            "extensions": {"demo-history": high if source.name == "high" else low},
        },
    )

    assert catalog.get_extension_info("demo-history", "0.4.12") is None
    assert catalog.get_extension_versions("demo-history") == ["0.5.1"]


@pytest.mark.parametrize(
    "bad_history",
    [
        [],
        None,
        {
            "not-a-version": {
                "download_url": "https://example.com/a.zip",
                "sha256": "a" * 64,
            }
        },
        {"0.5.1": {"download_url": "https://example.com/a.zip", "sha256": "a" * 64}},
        {"0.4.12": {"download_url": "https://example.com/a.zip"}},
        {
            "0.4.12": {
                "download_url": "https://example.com/a.zip",
                "sha256": "a" * 64,
                "id": "other",
            }
        },
    ],
)
def test_malformed_history_is_rejected(tmp_path, monkeypatch, bad_history):
    entry = {"id": "demo-history", "version": "0.5.1", "releases": bad_history}
    catalog = _catalog(monkeypatch, tmp_path, entry)
    with pytest.raises(ExtensionError):
        catalog.get_extension_info("demo-history", "0.4.12")


def test_selected_release_download_uses_its_url_without_relookup(tmp_path, monkeypatch):
    archive = _archive(tmp_path, "0.4.12")
    entry = _entry(archive)
    catalog = _catalog(monkeypatch, tmp_path, entry)
    selected = catalog.get_extension_info("demo-history", "0.4.12")
    requested = []

    def open_url(url, **_kwargs):
        requested.append(url)
        return _ArchiveResponse(archive.read_bytes(), url)

    monkeypatch.setattr(catalog, "_open_url", open_url)
    monkeypatch.setattr(
        catalog,
        "get_extension_info",
        lambda *_args: pytest.fail("unexpected second lookup"),
    )
    downloaded = catalog.download_extension_info(
        selected, target_dir=tmp_path / "downloads"
    )

    assert requested == ["https://example.com/demo-0.4.12.zip"]
    assert downloaded.read_bytes() == archive.read_bytes()


def test_selected_discovery_release_cannot_be_downloaded(tmp_path, monkeypatch):
    entry = _entry(_archive(tmp_path, "0.4.12"))
    entry["_install_allowed"] = False
    catalog = _catalog(monkeypatch, tmp_path, entry)
    selected = catalog.get_extension_info("demo-history", "0.4.12")

    with pytest.raises(ExtensionError, match="discovery-only"):
        catalog.download_extension_info(selected)


def test_exact_cli_install_rejects_wrong_archive_before_writing(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    old_archive = _archive(tmp_path, "0.4.12")
    new_archive = _archive(tmp_path, "0.5.1")
    _catalog(monkeypatch, project, _entry(old_archive))
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        ExtensionCatalog, "download_extension_info", lambda self, _info: new_archive
    )

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "0.4.12"]
    )

    assert result.exit_code == 1
    assert "declares version 0.5.1, expected 0.4.12" in " ".join(result.output.split())
    assert not (
        project / ".specify" / "extensions" / "demo-history" / "extension.yml"
    ).exists()


def test_exact_cli_install_rejects_wrong_archive_id_before_writing(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    old_archive = _archive(tmp_path, "0.4.12")
    wrong_id_archive = _archive(tmp_path, "0.4.12", "another-extension")
    _catalog(monkeypatch, project, _entry(old_archive))
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension_info",
        lambda self, _info: wrong_id_archive,
    )

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "0.4.12"]
    )

    assert result.exit_code == 1
    assert "declares ID 'another-extension', expected 'demo-history'" in " ".join(
        result.output.split()
    )
    assert not (project / ".specify" / "extensions" / "another-extension").exists()
    assert not (project / ".specify" / "extensions" / "demo-history").exists()


def test_exact_cli_install_rejects_wrong_historical_digest_before_writing(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    old_archive = _archive(tmp_path, "0.4.12")
    entry = _entry(old_archive)
    entry["releases"]["0.4.12"]["sha256"] = "0" * 64
    _catalog(monkeypatch, project, entry)
    monkeypatch.chdir(project)
    requested = []

    def open_url(self, url, **_kwargs):
        requested.append(url)
        return _ArchiveResponse(old_archive.read_bytes(), url)

    monkeypatch.setattr(ExtensionCatalog, "_open_url", open_url)

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "0.4.12"]
    )

    assert result.exit_code == 1
    assert requested == ["https://example.com/demo-0.4.12.zip"]
    assert "Integrity check failed for 'demo-history'" in " ".join(
        result.output.split()
    )
    assert not (project / ".specify" / "extensions" / "demo-history").exists()


def test_unqualified_cli_install_uses_current_release_with_history(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    old_archive = _archive(tmp_path, "0.4.12")
    current_archive = _archive(tmp_path, "0.5.1")
    entry = _entry(old_archive)
    entry["sha256"] = hashlib.sha256(current_archive.read_bytes()).hexdigest()
    _catalog(monkeypatch, project, entry)
    monkeypatch.chdir(project)
    requested = []

    def open_url(self, url, **_kwargs):
        requested.append(url)
        return _ArchiveResponse(current_archive.read_bytes(), url)

    monkeypatch.setattr(ExtensionCatalog, "_open_url", open_url)

    result = CliRunner().invoke(app, ["extension", "add", "demo-history"])

    assert result.exit_code == 0, result.output
    assert requested == ["https://example.com/demo-0.5.1.zip"]
    installed = yaml.safe_load(
        (
            project / ".specify" / "extensions" / "demo-history" / "extension.yml"
        ).read_text(encoding="utf-8")
    )
    assert installed["extension"]["version"] == "0.5.1"


def test_exact_cli_install_historical_release(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    old_archive = _archive(tmp_path, "0.4.12")
    _catalog(monkeypatch, project, _entry(old_archive))
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        ExtensionCatalog, "download_extension_info", lambda self, _info: old_archive
    )

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "0.4.12"]
    )

    assert result.exit_code == 0, result.output
    installed = yaml.safe_load(
        (
            project / ".specify" / "extensions" / "demo-history" / "extension.yml"
        ).read_text(encoding="utf-8")
    )
    assert installed["extension"]["version"] == "0.4.12"


def test_info_lists_versions_and_discovery_only_policy(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    entry = _entry(_archive(tmp_path, "0.4.12"))
    entry["_install_allowed"] = False
    _catalog(monkeypatch, project, entry)
    monkeypatch.chdir(project)

    result = CliRunner().invoke(
        app, ["extension", "info", "demo-history", "--versions"]
    )

    assert result.exit_code == 0, result.output
    assert "0.5.1 (current)" in result.output
    assert "0.4.12" in result.output
    assert "Discovery only" in result.output


def test_exact_cli_install_rejects_missing_version_in_winning_catalog(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    _catalog(monkeypatch, project, _entry(_archive(tmp_path, "0.4.12")))
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension_info",
        lambda *_args: pytest.fail("must not download a different version"),
    )

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "0.3.0"]
    )

    assert result.exit_code == 1
    assert "no catalog release for version 0.3.0" in " ".join(result.output.split())


def test_exact_cli_install_refuses_discovery_only_catalog(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    entry = _entry(_archive(tmp_path, "0.4.12"))
    entry["_install_allowed"] = False
    _catalog(monkeypatch, project, entry)
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        ExtensionCatalog,
        "download_extension_info",
        lambda *_args: pytest.fail("discovery-only catalogs must not download"),
    )

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "0.4.12"]
    )

    assert result.exit_code == 1
    assert "discovery-only" in result.output


def test_exact_cli_does_not_bypass_discovery_policy_via_bundled_copy(
    tmp_path, monkeypatch
):
    from specify_cli._assets import _locate_bundled_extension

    bundled = _locate_bundled_extension("agent-context")
    assert bundled is not None
    version = ExtensionManifest(bundled / "extension.yml").version
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    entry = {
        "id": "agent-context",
        "name": "Agent Context",
        "version": version,
        "bundled": True,
        "_catalog_name": "discovery",
        "_install_allowed": False,
    }
    _catalog(monkeypatch, project, entry)
    monkeypatch.chdir(project)

    result = CliRunner().invoke(
        app, ["extension", "add", "agent-context", "--version", version]
    )

    assert result.exit_code == 1
    assert "discovery-only" in result.output
    assert not (
        project / ".specify" / "extensions" / "agent-context" / "extension.yml"
    ).exists()


@pytest.mark.parametrize("matches_package", [True, False])
def test_exact_cli_bundled_version_must_match_packaged_manifest(
    tmp_path, monkeypatch, matches_package
):
    from specify_cli._assets import _locate_bundled_extension

    bundled = _locate_bundled_extension("agent-context")
    assert bundled is not None
    packaged_version = ExtensionManifest(bundled / "extension.yml").version
    requested_version = packaged_version if matches_package else "9999.0.0"
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    entry = {
        "id": "agent-context",
        "name": "Agent Context",
        "version": requested_version,
        "bundled": True,
        "_catalog_name": "trusted",
        "_install_allowed": True,
    }
    _catalog(monkeypatch, project, entry)
    monkeypatch.chdir(project)

    result = CliRunner().invoke(
        app, ["extension", "add", "agent-context", "--version", requested_version]
    )

    installed_manifest = (
        project / ".specify" / "extensions" / "agent-context" / "extension.yml"
    )
    if matches_package:
        assert result.exit_code == 0, result.output
        assert ExtensionManifest(installed_manifest).version == packaged_version
    else:
        assert result.exit_code == 1
        assert f"version {requested_version} is not shipped" in " ".join(
            result.output.split()
        )
        assert not installed_manifest.exists()
