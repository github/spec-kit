"""Unit tests for project catalog-config id derivation and url canonicalization."""
from __future__ import annotations

from pathlib import Path

from specify_cli.bundler.commands_impl import catalog_config as cc


def test_derive_id_incorporates_path_stem_for_same_host():
    # Two catalogs on the same host must not collide on the derived id.
    a = cc._derive_id("https://example.com/team-a.json")
    b = cc._derive_id("https://example.com/team-b.json")
    assert a == "example-team-a"
    assert b == "example-team-b"
    assert a != b


def test_derive_id_falls_back_to_host_when_no_path():
    assert cc._derive_id("https://example.com/") == "example"


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
