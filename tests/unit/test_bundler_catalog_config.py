"""Unit tests for project catalog-config id derivation and url canonicalization."""
from __future__ import annotations

from pathlib import Path

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.commands_impl import catalog_config as cc


def test_derive_id_incorporates_path_stem_for_same_host():
    # Two catalogs on the same host must not collide on the derived id.
    a = cc._derive_id("https://example.com/team-a.json")
    b = cc._derive_id("https://example.com/team-b.json")
    assert a == "example-com-team-a"
    assert b == "example-com-team-b"
    assert a != b


def test_derive_id_distinguishes_tlds():
    # Different TLDs sharing a second-level label must not collide.
    com = cc._derive_id("https://example.com/team-a.json")
    net = cc._derive_id("https://example.net/team-a.json")
    assert com == "example-com-team-a"
    assert net == "example-net-team-a"
    assert com != net


def test_derive_id_falls_back_to_host_when_no_path():
    assert cc._derive_id("https://example.com/") == "example-com"


def test_derive_id_for_local_path_uses_stem():
    assert cc._derive_id("./catalogs/my-catalog.json") == "my-catalog"


def test_canonicalize_makes_relative_local_path_absolute(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "local.json").write_text("{}", encoding="utf-8")

    result = cc._canonicalize_url("local.json")

    assert Path(result).is_absolute()
    assert Path(result) == (tmp_path / "local.json").resolve()


def test_canonicalize_leaves_remote_urls_untouched():
    for url in (
        "https://example.com/c.json",
        "http://localhost:8080/c.json",
        "file:///tmp/c.json",
        "builtin://default",
    ):
        assert cc._canonicalize_url(url) == url


def test_add_source_persists_absolute_local_path(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    catalog = project / "sub" / "cat.json"
    catalog.parent.mkdir()
    catalog.write_text("{}", encoding="utf-8")

    monkeypatch.chdir(project)
    source = cc.add_source(project, "sub/cat.json", policy="install-allowed", priority=50)

    assert Path(source.url).is_absolute()
    assert Path(source.url) == catalog.resolve()


def test_add_source_refuses_symlinked_specify_escape(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    with pytest.raises(BundlerError, match="escapes the allowed root"):
        cc.add_source(project, "https://example.com/c.json", policy="install-allowed", priority=50)


def test_read_rejects_non_list_catalogs(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text(
        "schema_version: '1.0'\ncatalogs: not-a-list\n", encoding="utf-8"
    )

    with pytest.raises(BundlerError, match="'catalogs' must be a list"):
        cc._read(project)


def test_read_rejects_non_mapping_catalog_entry(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text(
        "schema_version: '1.0'\ncatalogs:\n  - just-a-string\n", encoding="utf-8"
    )

    with pytest.raises(BundlerError, match="each catalog entry must be a mapping"):
        cc._read(project)


def test_read_rejects_non_mapping_top_level(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text("- a\n- b\n", encoding="utf-8")

    with pytest.raises(BundlerError, match="expected a mapping at the top level"):
        cc._read(project)


def test_read_rejects_unknown_schema_version(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text(
        "schema_version: '2.0'\ncatalogs: []\n", encoding="utf-8"
    )

    with pytest.raises(BundlerError, match="Unsupported catalog config schema version"):
        cc._read(project)


def test_read_accepts_forward_compatible_minor_schema(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text(
        "schema_version: '1.5'\ncatalogs: []\n", encoding="utf-8"
    )
    assert cc._read(project) == []


def test_read_tolerates_missing_schema_version(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text("catalogs: []\n", encoding="utf-8")
    assert cc._read(project) == []


def test_read_returns_empty_for_missing_or_empty_config(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    assert cc._read(project) == []

    cc._config_path(project).write_text("schema_version: '1.0'\n", encoding="utf-8")
    assert cc._read(project) == []


def test_slug_lowercases_for_deterministic_ids():
    # Mixed-case local filenames must derive the same id regardless of case so
    # the case-sensitive duplicate check cannot admit logical duplicates.
    assert cc._slug("Team-A") == "team-a"
    assert cc._derive_id("./catalogs/Team-A.json") == "team-a"
    assert cc._derive_id("https://Example.com/Team-A.json") == "example-com-team-a"


def test_derive_id_handles_ipv6_literal():
    # An IPv6 host must not be truncated at the first colon.
    derived = cc._derive_id("https://[2001:db8::1]/catalog.json")
    assert derived == "2001-db8--1-catalog"


def test_derive_id_ignores_credentials_and_port():
    assert cc._derive_id("https://user:pw@example.com:8443/c.json") == "example-com-c"


def test_add_source_rejects_unsupported_scheme(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(BundlerError, match="Unsupported catalog url scheme"):
        cc.add_source(project, "ssh://host/catalog.json", policy="install-allowed", priority=50)


def test_add_source_allows_local_path_with_colon(tmp_path: Path, monkeypatch):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    monkeypatch.chdir(project)
    # A relative path containing ':' but no '://' is still a local path.
    source = cc.add_source(project, "weird:name.json", policy="install-allowed", priority=50)
    assert source.url.endswith("weird:name.json") or "weird" in source.url
