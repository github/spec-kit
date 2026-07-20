"""Offline-first tests (Constitution Principle IV).

Assert that consume/author flows work with no network access: built-in catalogs
resolve offline, file:// catalogs resolve offline, and http(s) sources are
refused (never silently attempted) when network is disabled.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.catalog import CatalogSource, InstallPolicy, Scope
from specify_cli.bundler.services.adapters import make_catalog_fetcher
from specify_cli.bundler.services.catalog_stack import CatalogStack
from tests.bundler_helpers import catalog_entry_dict, write_catalog_file


def _src(source_id, url, priority=1, policy="install-allowed"):
    return CatalogSource(
        id=source_id, url=url, priority=priority,
        install_policy=InstallPolicy(policy), scope=Scope.PROJECT,
    )


def test_builtin_catalog_resolves_offline():
    fetcher = make_catalog_fetcher(allow_network=False)
    stack = CatalogStack([_src("default", "builtin://default")], fetcher)
    # Built-in default ships empty; search works without network and returns [].
    assert stack.search() == []


def test_builtin_community_catalog_resolves_from_packaged_snapshot_offline():
    fetcher = make_catalog_fetcher(allow_network=False)
    source = _src(
        "community",
        "builtin://community",
        priority=20,
        policy="discovery-only",
    )
    payload = fetcher(source)
    stack = CatalogStack([source], fetcher)

    assert isinstance(payload.get("bundles"), dict)
    assert all(
        result.source.id == "community" and not result.install_allowed
        for result in stack.search()
    )
    assert stack.sources[0].install_allowed is False


def test_file_catalog_resolves_offline(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    write_catalog_file(catalog_path, {"demo": catalog_entry_dict("demo")})
    fetcher = make_catalog_fetcher(allow_network=False)
    stack = CatalogStack([_src("local", str(catalog_path))], fetcher)
    resolved = stack.resolve("demo")
    assert resolved.entry.id == "demo"


def test_http_source_refused_when_offline():
    fetcher = make_catalog_fetcher(allow_network=False)
    stack = CatalogStack([_src("remote", "https://example.com/catalog.json")], fetcher)
    with pytest.raises(BundlerError, match="Network access disabled"):
        stack.resolve("anything")


def test_missing_file_catalog_errors_offline(tmp_path: Path):
    fetcher = make_catalog_fetcher(allow_network=False)
    stack = CatalogStack([_src("local", str(tmp_path / "nope.json"))], fetcher)
    with pytest.raises(BundlerError):
        stack.resolve("anything")


def test_file_url_catalog_resolves_offline(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    write_catalog_file(catalog_path, {"demo": catalog_entry_dict("demo")})
    fetcher = make_catalog_fetcher(allow_network=False)
    stack = CatalogStack([_src("local", catalog_path.as_uri())], fetcher)
    resolved = stack.resolve("demo")
    assert resolved.entry.id == "demo"


def test_plain_http_remote_rejected_before_network():
    # HTTPS is required for non-localhost catalogs; reject http:// up front.
    fetcher = make_catalog_fetcher(allow_network=True)
    stack = CatalogStack([_src("remote", "http://example.com/catalog.json")], fetcher)
    with pytest.raises(BundlerError, match="must use HTTPS"):
        stack.resolve("anything")


def test_remote_url_without_host_rejected():
    fetcher = make_catalog_fetcher(allow_network=True)
    stack = CatalogStack([_src("remote", "https:///catalog.json")], fetcher)
    with pytest.raises(BundlerError, match="valid URL with a host"):
        stack.resolve("anything")
