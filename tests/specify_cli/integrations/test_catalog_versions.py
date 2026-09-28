"""Versioned integration catalog metadata and exact-release lookup."""

from __future__ import annotations

import copy

import pytest

from tests.http_helpers import route_opener_open_through_urlopen  # noqa: F401

from specify_cli.integrations import (
    IntegrationCatalog,
    IntegrationCatalogEntry,
    IntegrationCatalogError,
    _catalog_shape_error,
)


CURRENT = {
    "id": "sample",
    "name": "Sample Agent",
    "author": "example",
    "version": "2.0.0",
    "description": "Current release",
    "repository": "https://example.com/current",
    "tags": ["current"],
    "requires": {"speckit_version": ">=1.0"},
    "download_url": "https://example.com/current.zip",
    "releases": {
        "1.0.0": {
            "description": "Historical release",
            "repository": "https://example.com/old",
            "tags": ["historical"],
            "requires": {"speckit_version": ">=0.7"},
        },
        "1.5.0": {"description": "Intermediate release"},
    },
}


def test_legacy_entry_keeps_current_fields_and_exact_lookup(tmp_path, monkeypatch):
    legacy = {key: value for key, value in CURRENT.items() if key != "releases"}
    monkeypatch.setattr(
        IntegrationCatalog,
        "_get_merged_integrations",
        lambda self: [legacy],
    )
    catalog = IntegrationCatalog(tmp_path)
    assert catalog.get_integration_info("sample") is legacy
    assert catalog.get_integration_info("sample", version="2.0.0") is legacy
    assert catalog.get_integration_info("sample", version="1.0.0") is None
    assert catalog.get_integration_versions("sample") == ["2.0.0"]


def test_missing_legacy_version_cannot_be_selected_as_empty_string(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        IntegrationCatalog,
        "_get_merged_integrations",
        lambda self: [{"id": "sample", "name": "Sample Agent", "version": ""}],
    )
    catalog = IntegrationCatalog(tmp_path)
    assert catalog.get_integration_info("sample")["name"] == "Sample Agent"
    assert catalog.get_integration_info("sample", version="") is None
    assert catalog.get_integration_versions("sample") == []


def test_exact_release_returns_selected_metadata_not_current(tmp_path, monkeypatch):
    entry = {**CURRENT, "_catalog_name": "primary", "_install_allowed": False}
    monkeypatch.setattr(
        IntegrationCatalog,
        "_get_merged_integrations",
        lambda self: [entry],
    )
    catalog = IntegrationCatalog(tmp_path)

    assert catalog.get_integration_info("sample") is entry
    selected = catalog.get_integration_info("sample", version="v1.0")
    assert selected == {
        "id": "sample",
        "name": "Sample Agent",
        "author": "example",
        "version": "1.0.0",
        "description": "Historical release",
        "repository": "https://example.com/old",
        "tags": ["historical"],
        "requires": {"speckit_version": ">=0.7"},
        "_catalog_name": "primary",
        "_install_allowed": False,
    }
    assert catalog.get_integration_info("sample", version="v2.0") is entry
    assert catalog.get_integration_versions("sample") == ["2.0.0", "1.5.0", "1.0.0"]
    assert "download_url" not in selected


def test_missing_version_does_not_fall_back_to_lower_priority(tmp_path, monkeypatch):
    winning = {**CURRENT, "_catalog_name": "primary", "_install_allowed": False}
    lower = {
        **CURRENT,
        "_catalog_name": "secondary",
        "_install_allowed": True,
        "releases": {"0.9.0": {"description": "Lower-priority version"}},
    }
    monkeypatch.setattr(
        IntegrationCatalog,
        "_get_merged_integrations",
        lambda self: [winning, lower],
    )
    catalog = IntegrationCatalog(tmp_path)
    assert catalog.get_integration_info("sample", version="0.9.0") is None
    assert catalog.get_integration_info("sample", version="bad version") is None
    assert catalog.get_integration_info("missing", version="2.0.0") is None
    assert catalog.get_integration_versions("missing") == []


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"releases": []}, "releases"),
        ({"releases": {"1.0.0": []}}, "object"),
        ({"releases": {"not-a-version": {}}}, "version"),
        ({"version": "not-a-version"}, "current version"),
        ({"version": None}, "current version"),
        ({"releases": {"2.0.0": {}}}, "repeats"),
        ({"releases": {"v2.0": {}}}, "repeats"),
        ({"releases": {"1.0.0": {}, "v1.0": {}}}, "repeats"),
        ({"releases": {"1.0.0": {"version": "0.9"}}}, "reserved"),
        ({"releases": {"1.0.0": {"id": "different"}}}, "reserved"),
        ({"releases": {"1.0.0": {"_install_allowed": True}}}, "reserved"),
        ({"releases": {"1.0.0": {"releases": {}}}}, "reserved"),
        ({"releases": {"1.0.0": {"tags": "cli"}}}, "tags"),
        ({"releases": {"1.0.0": {"tags": [42]}}}, "tags"),
        ({"releases": {"1.0.0": {"requires": []}}}, "requires"),
        ({"releases": {"1.0.0": {"description": 42}}}, "description"),
        (
            {"releases": {"1.0.0": {"download_url": "https://example.com/a.zip"}}},
            "unsupported",
        ),
        ({"id": "different"}, "inconsistent id"),
        ({"releases": {"": {}}}, "version key"),
        ({"releases": {"1.0.0": {"repository": None}}}, "repository"),
        ({"releases": {"1.0.0": {"_catalog_name": "other"}}}, "reserved"),
    ],
)
def test_rejects_malformed_release_history(change, reason):
    entry = copy.deepcopy(CURRENT)
    entry.update(change)
    payload = {"schema_version": "1.0", "integrations": {"sample": entry}}
    assert reason in _catalog_shape_error(payload)


def test_invalid_release_history_is_rejected_on_fetch_and_not_cached(
    tmp_path, monkeypatch
):
    catalog = IntegrationCatalog(tmp_path)
    source = IntegrationCatalogEntry(
        url="https://example.com/catalog.json",
        name="custom",
        priority=1,
        install_allowed=True,
    )
    from tests.specify_cli.integrations.test_catalog import TestCatalogFetch

    TestCatalogFetch()._patch_urlopen(
        monkeypatch,
        {
            "schema_version": "1.0",
            "integrations": {"sample": {**CURRENT, "releases": {"v2.0": {}}}},
        },
    )
    with pytest.raises(IntegrationCatalogError, match="repeats"):
        catalog._fetch_single_catalog(source)
    assert not list(catalog.cache_dir.glob("catalog-*.json"))


def test_poisoned_release_cache_is_refetched(tmp_path, monkeypatch):
    source = IntegrationCatalogEntry(
        url="https://example.com/catalog.json",
        name="custom",
        priority=1,
        install_allowed=True,
    )
    from tests.specify_cli.integrations.test_catalog import TestCatalogFetch

    TestCatalogFetch()._patch_urlopen(
        monkeypatch,
        {"schema_version": "1.0", "integrations": {"sample": CURRENT}},
    )
    catalog = IntegrationCatalog(tmp_path)
    catalog._fetch_single_catalog(source)
    cache_file = next(
        file
        for file in catalog.cache_dir.glob("catalog-*.json")
        if not file.name.endswith("-metadata.json")
    )
    cache_file.write_text(
        '{"schema_version":"1.0","integrations":{"sample":'
        '{"version":"2.0.0","releases":{"2.0.0":{}}}}}',
        encoding="utf-8",
    )
    assert catalog._fetch_single_catalog(source)["integrations"]["sample"] == CURRENT


def test_source_priority_and_current_search_are_unchanged(tmp_path, monkeypatch):
    primary = IntegrationCatalogEntry(
        url="https://example.com/primary.json",
        name="primary",
        priority=1,
        install_allowed=False,
    )
    secondary = IntegrationCatalogEntry(
        url="https://example.com/secondary.json",
        name="secondary",
        priority=2,
        install_allowed=True,
    )
    catalog = IntegrationCatalog(tmp_path)
    monkeypatch.setattr(catalog, "get_active_catalogs", lambda: [primary, secondary])
    monkeypatch.setattr(
        catalog,
        "_fetch_single_catalog",
        lambda source, force_refresh=False: {
            "integrations": {
                "sample": CURRENT
                if source.name == "primary"
                else {
                    "version": "3.0.0",
                    "releases": {"0.9.0": {"description": "Only in secondary"}},
                }
            }
        },
    )
    assert [item["version"] for item in catalog.search()] == ["2.0.0"]
    assert catalog.get_integration_info("sample", version="0.9.0") is None
    assert (
        catalog.get_integration_info("sample", version="1.0.0")["_install_allowed"]
        is False
    )
