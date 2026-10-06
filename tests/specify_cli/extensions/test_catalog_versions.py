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
    ExtensionCatalogValidationError,
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
        ExtensionCatalog, "_get_merged_extensions",
        lambda self, *, extension_id=None: [entry]
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


@pytest.mark.parametrize("legacy", [False, True])
def test_deeply_nested_catalog_json_is_a_validation_error(
    tmp_path, monkeypatch, legacy
):
    source = CatalogEntry("https://example.com/deep.json", "deep", 1, True)
    catalog = ExtensionCatalog(tmp_path)
    payload = b"[" * 12000 + b"0" + b"]" * 12000
    monkeypatch.setattr(
        catalog,
        "_open_url",
        lambda *_args, **_kwargs: _ArchiveResponse(payload, source.url),
    )
    if legacy:
        monkeypatch.setattr(catalog, "get_catalog_url", lambda: source.url)

    with pytest.raises(ExtensionCatalogValidationError, match="nesting"):
        if legacy:
            catalog.fetch_catalog(force_refresh=True)
        else:
            catalog._fetch_single_catalog(source, force_refresh=True)


@pytest.mark.parametrize("legacy", [False, True])
def test_deeply_nested_cached_catalog_refetches(tmp_path, monkeypatch, legacy):
    catalog = ExtensionCatalog(tmp_path)
    url = catalog.DEFAULT_CATALOG_URL
    source = CatalogEntry(url, "default", 1, True)
    catalog.cache_file.parent.mkdir(parents=True, exist_ok=True)
    catalog.cache_file.write_bytes(b"[" * 12000 + b"0" + b"]" * 12000)
    monkeypatch.setattr(catalog, "is_cache_valid", lambda: True)
    monkeypatch.setattr(catalog, "get_catalog_url", lambda: url)
    monkeypatch.setattr(
        catalog,
        "_open_url",
        lambda *_args, **_kwargs: _ArchiveResponse(
            b'{"schema_version":"1.0","extensions":{}}', url
        ),
    )

    data = catalog.fetch_catalog() if legacy else catalog._fetch_single_catalog(source)
    assert data["extensions"] == {}


@pytest.mark.parametrize("legacy", [False, True])
def test_deeply_nested_cache_metadata_refetches(tmp_path, monkeypatch, legacy):
    catalog = ExtensionCatalog(tmp_path)
    url = catalog.DEFAULT_CATALOG_URL if legacy else "https://example.com/deep.json"
    source = CatalogEntry(url, "deep", 1, True)
    if legacy:
        cache_file = catalog.cache_file
        metadata_file = catalog.cache_metadata_file
        monkeypatch.setattr(catalog, "get_catalog_url", lambda: url)
    else:
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        cache_file = catalog.cache_dir / f"catalog-{url_hash}.json"
        metadata_file = catalog.cache_dir / f"catalog-{url_hash}-metadata.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(b'{"schema_version":"1.0","extensions":{}}')
    metadata_file.write_bytes(b"[" * 12000 + b"0" + b"]" * 12000)
    monkeypatch.setattr(
        catalog,
        "_open_url",
        lambda *_args, **_kwargs: _ArchiveResponse(
            b'{"schema_version":"1.0","extensions":{}}', url
        ),
    )

    data = catalog.fetch_catalog() if legacy else catalog._fetch_single_catalog(source)
    assert data["extensions"] == {}


def test_legacy_entry_still_selects_its_current_release(tmp_path, monkeypatch):
    entry = {
        "id": "legacy",
        "version": "1.0.0",
        "download_url": "https://example.com/a.zip",
    }
    catalog = _catalog(monkeypatch, tmp_path, entry)

    assert catalog.get_extension_info("legacy") == entry
    assert catalog.get_extension_info("legacy", "1.0.0") == entry
    assert catalog.get_extension_info("legacy", "v1.0") == entry
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


def test_equivalent_version_spelling_preserves_advertised_release(
    tmp_path, monkeypatch
):
    entry = _entry(_archive(tmp_path, "0.4.12"))
    catalog = _catalog(monkeypatch, tmp_path, entry)

    assert catalog.get_extension_info("demo-history", "v0.5.1") == entry
    historical = catalog.get_extension_info("demo-history", "0.4.12.0")
    assert historical["version"] == "0.4.12"
    assert historical["download_url"] == entry["releases"]["0.4.12"]["download_url"]
    assert catalog.get_extension_info("demo-history", "not-a-version") is None


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


def test_targeted_lookup_rejects_malformed_higher_catalog_but_search_continues(
    tmp_path, monkeypatch,
):
    from specify_cli.extensions import ExtensionCatalogValidationError

    catalog = ExtensionCatalog(tmp_path)
    sources = [
        CatalogEntry("https://example.com/high.json", "high", 1, True),
        CatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: sources)

    def fetch(source, _force=False):
        if source.name == "high":
            catalog._validate_catalog_payload({"extensions": []}, source.url)
        return {
            "schema_version": "1.0",
            "extensions": {"demo-history": {"version": "1.0.0"}},
        }

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)

    with pytest.raises(ExtensionCatalogValidationError, match="Invalid catalog format"):
        catalog.get_extension_info("demo-history")
    assert catalog.search("demo-history")[0]["_catalog_name"] == "low"


def test_targeted_lookup_rejects_lower_match_when_higher_catalog_is_unreachable(
    tmp_path, monkeypatch,
):
    from specify_cli.extensions import ExtensionCatalogFetchError

    catalog = ExtensionCatalog(tmp_path)
    sources = [
        CatalogEntry("https://example.com/high.json", "high", 1, True),
        CatalogEntry("https://example.com/low.json", "low", 2, True),
    ]
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: sources)
    high_available = False

    def fetch(source, _force=False):
        if source.name == "high" and not high_available:
            raise ExtensionCatalogFetchError("high catalog is offline")
        return {
            "schema_version": "1.0",
            "extensions": {"demo-history": {"version": "1.0.0"}},
        }

    monkeypatch.setattr(catalog, "_fetch_single_catalog", fetch)
    with pytest.raises(ExtensionCatalogFetchError, match="offline"):
        catalog.get_extension_info("demo-history", "1.0.0")
    assert catalog.search("demo-history")[0]["_catalog_name"] == "low"
    high_available = True
    assert catalog.get_extension_info("demo-history")["_catalog_name"] == "high"


@pytest.mark.parametrize("second_lookup", ["lower_priority", "unavailable"])
def test_exact_cli_install_uses_first_resolved_catalog_snapshot(
    tmp_path, monkeypatch, second_lookup
):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    old_archive = _archive(tmp_path, "0.4.12")
    high = _entry(old_archive)
    low = _entry(old_archive)
    low["releases"]["0.4.12"]["download_url"] = "https://example.com/low.zip"
    fetches = []
    selected = []

    def merged(_self, *, extension_id=None):
        fetches.append(True)
        if len(fetches) == 1:
            return [high]
        if second_lookup == "unavailable":
            raise ExtensionError("winning catalog is unavailable")
        return [low]

    def download(_self, info):
        selected.append(info)
        return old_archive

    monkeypatch.setattr(ExtensionCatalog, "_get_merged_extensions", merged)
    monkeypatch.setattr(ExtensionCatalog, "download_extension_info", download)
    monkeypatch.chdir(project)

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "0.4.12"]
    )

    assert result.exit_code == 0, result.output
    assert len(fetches) == 1
    assert selected[0]["download_url"] == "https://example.com/demo-0.4.12.zip"


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
        {"0.5.1.0": {"download_url": "https://example.com/a.zip", "sha256": "a" * 64}},
        {"0.4.12": {"download_url": "https://example.com/a.zip"}},
        {
            "0.4.12": {
                "download_url": "https://example.com/a.zip",
                "sha256": "md5:" + "a" * 64,
            }
        },
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


def test_historical_release_accepts_prefixed_digest(tmp_path, monkeypatch):
    archive = _archive(tmp_path, "0.4.12")
    entry = _entry(archive)
    digest = entry["releases"]["0.4.12"]["sha256"]
    entry["releases"]["0.4.12"]["sha256"] = f" SHA256: {digest.upper()} "
    catalog = _catalog(monkeypatch, tmp_path, entry)
    selected = catalog.get_extension_info("demo-history", "0.4.12")

    monkeypatch.setattr(
        catalog,
        "_open_url",
        lambda url, **_kwargs: _ArchiveResponse(archive.read_bytes(), url),
    )
    downloaded = catalog.download_extension_info(
        selected, target_dir=tmp_path / "downloads"
    )

    assert selected["sha256"] == f" SHA256: {digest.upper()} "
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


def test_exact_cli_install_reports_invalid_legacy_catalog_version(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    archive = _archive(tmp_path, "0.4.12")
    entry = _entry(archive)
    entry["version"] = "legacy-current"
    del entry["releases"]
    _catalog(monkeypatch, project, entry)
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        ExtensionCatalog, "download_extension_info", lambda self, _info: archive
    )

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", "legacy-current"]
    )

    assert result.exit_code == 1
    assert "Validation Error" in result.output
    assert "declares version 0.4.12, expected legacy-current" in " ".join(
        result.output.split()
    )
    assert not (project / ".specify" / "extensions" / "demo-history").exists()


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


@pytest.mark.parametrize("requested_version", ["0.4.12", "v0.4.12"])
def test_exact_cli_install_historical_release(tmp_path, monkeypatch, requested_version):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    old_archive = _archive(tmp_path, "0.4.12")
    _catalog(monkeypatch, project, _entry(old_archive))
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        ExtensionCatalog, "download_extension_info", lambda self, _info: old_archive
    )

    result = CliRunner().invoke(
        app, ["extension", "add", "demo-history", "--version", requested_version]
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


def test_info_versions_uses_first_resolved_catalog_snapshot(tmp_path, monkeypatch):
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    high = _entry(_archive(tmp_path, "0.4.12"))
    low = _entry(_archive(tmp_path, "0.4.12"))
    low["version"] = "0.8.0"
    fetches = []

    def merged(_self, *, extension_id=None):
        fetches.append(True)
        return [high if len(fetches) == 1 else low]

    monkeypatch.setattr(ExtensionCatalog, "_get_merged_extensions", merged)
    monkeypatch.chdir(project)

    result = CliRunner().invoke(
        app, ["extension", "info", "demo-history", "--versions"]
    )

    assert result.exit_code == 0, result.output
    assert len(fetches) == 1
    assert "0.5.1 (current)" in result.output
    assert "0.8.0" not in result.output


def test_info_versions_preserves_catalog_failure(tmp_path, monkeypatch):
    from specify_cli.extensions import _commands

    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    monkeypatch.chdir(project)
    monkeypatch.setattr(
        _commands,
        "_resolve_catalog_extension",
        lambda *_args: (None, ExtensionError("catalog fetch failed")),
    )

    result = CliRunner().invoke(
        app, ["extension", "info", "demo-history", "--versions"]
    )

    assert result.exit_code == 1
    assert "Could not query extension catalog: catalog fetch failed" in " ".join(
        result.output.split()
    )
    assert "No catalog versions found" not in result.output


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


@pytest.mark.parametrize("version_case", ["exact", "equivalent", "mismatch"])
def test_exact_cli_bundled_version_must_match_packaged_manifest(
    tmp_path, monkeypatch, version_case
):
    from specify_cli._assets import _locate_bundled_extension

    bundled = _locate_bundled_extension("agent-context")
    assert bundled is not None
    packaged_version = ExtensionManifest(bundled / "extension.yml").version
    requested_version = {
        "exact": packaged_version,
        "equivalent": f"v{packaged_version}",
        "mismatch": "9999.0.0",
    }[version_case]
    project = tmp_path / "project"
    (project / ".specify").mkdir(parents=True)
    entry = {
        "id": "agent-context",
        "name": "Agent Context",
        "version": requested_version
        if version_case == "mismatch"
        else packaged_version,
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
    if version_case != "mismatch":
        assert result.exit_code == 0, result.output
        assert ExtensionManifest(installed_manifest).version == packaged_version
    else:
        assert result.exit_code == 1
        assert f"version {requested_version} is not shipped" in " ".join(
            result.output.split()
        )
        assert not installed_manifest.exists()
