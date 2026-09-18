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
    source, status = cc.add_source(project, "sub/cat.json", policy="install-allowed", priority=50)

    assert status == "added"
    assert Path(source.url).is_absolute()
    assert Path(source.url) == catalog.resolve()


def test_remove_source_accepts_relative_local_path(tmp_path: Path, monkeypatch):
    """add_source stores a local path as an absolute url, so remove_source must
    accept the same relative path the caller added; otherwise `remove ./cat.json`
    cannot undo `add ./cat.json`."""
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    catalog = project / "sub" / "cat.json"
    catalog.parent.mkdir()
    catalog.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(project)

    cc.add_source(project, "sub/cat.json", policy="install-allowed", priority=50)
    # Removing with the same relative path must succeed (stored absolute).
    removed = cc.remove_source(project, "sub/cat.json")
    assert removed == "sub/cat.json"
    # And it is actually gone now.
    with pytest.raises(BundlerError, match="No project-scoped catalog source"):
        cc.remove_source(project, "sub/cat.json")


def test_remove_by_id_does_not_also_delete_canonical_url_match(tmp_path: Path, monkeypatch):
    """`remove <id>` must remove only the exact-id source, not also a different
    source whose url happens to equal the id's canonicalized path. (_canonicalize_url
    treats a bare id as a local path, so the canonical match is only a fallback when
    there is no exact id/url match.)"""
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    monkeypatch.chdir(project)
    # Source A: id "local", a remote url.
    cc.add_source(
        project, "https://example.com/a.json", source_id="local",
        policy="install-allowed", priority=10,
    )
    # Source B: a local path that canonicalizes to <cwd>/local, with a distinct id.
    cc.add_source(project, "local", source_id="bsource", policy="install-allowed", priority=20)

    removed = cc.remove_source(project, "local")
    assert removed == "local"
    ids = {c["id"] for c in cc._read(project)}
    assert "local" not in ids   # the exact-id source was removed
    assert "bsource" in ids     # the canonical-url source survives (not collateral)


def test_add_source_refuses_symlinked_specify_escape(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".specify").symlink_to(outside, target_is_directory=True)

    with pytest.raises(BundlerError, match="escapes the allowed root"):
        cc.add_source(project, "https://example.com/c.json", policy="install-allowed", priority=50)


@pytest.mark.parametrize("padding", ["", " \t"])
def test_add_source_rerun_surfaces_bad_stored_priority_as_bundlererror(tmp_path: Path, padding):
    """A hand-edited matching entry with a non-integer priority must surface a
    clean BundlerError during an idempotent-add comparison rather than leaking
    int()'s ValueError past the CLI's `except BundlerError` (#4505)."""
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text(
        "schema_version: '1.0'\n"
        "catalogs:\n"
        f"  - id: '{padding}mine{padding}'\n"
        f"    url: '{padding}https://example.com/c.json{padding}'\n"
        "    priority: not-a-number\n"
        "    install_policy: install-allowed\n",
        encoding="utf-8",
    )

    config_path = cc._config_path(project)
    original = config_path.read_bytes()
    modified_at = config_path.stat().st_mtime_ns
    with pytest.raises(BundlerError, match="non-integer priority"):
        cc.add_source(
            project, "https://example.com/c.json", source_id="mine",
            policy="install-allowed", priority=10,
        )
    assert config_path.read_bytes() == original
    assert config_path.stat().st_mtime_ns == modified_at


def test_add_source_rerun_with_string_priority_is_unchanged(tmp_path: Path):
    """A stored priority written as a numeric string is normalized like catalog
    parsing, so an otherwise-identical rerun is a no-op, not a false conflict."""
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text(
        "schema_version: '1.0'\n"
        "catalogs:\n"
        "  - id: mine\n"
        "    url: https://example.com/c.json\n"
        "    priority: '10'\n"
        "    install_policy: install-allowed\n",
        encoding="utf-8",
    )

    source, status = cc.add_source(
        project, "https://example.com/c.json", source_id="mine",
        policy="install-allowed", priority=10,
    )
    assert status == "unchanged"
    assert source.priority == 10


def test_add_source_same_url_without_id_preserves_custom_id(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    original_source, first_status = cc.add_source(
        project,
        "https://example.com/c.json",
        source_id="custom",
        policy="install-allowed",
        priority=10,
    )

    source, status = cc.add_source(
        project,
        "https://example.com/c.json",
        policy="install-allowed",
        priority=10,
    )

    assert first_status == "added"
    assert status == "unchanged"
    assert source.id == original_source.id == "custom"
    assert len(cc._read(project)) == 1


@pytest.mark.parametrize("id_padding", ["", " \t"])
@pytest.mark.parametrize("url_padding", ["", " \t"])
@pytest.mark.parametrize("source_id,url,outcome", [
    ("local", "https://example.com/c.json", "unchanged"),
    ("local", "https://example.com/other.json", "conflict"),
    ("other", "https://example.com/c.json", "conflict"),
    ("other", "https://example.com/other.json", "added"),
])
def test_add_source_normalizes_stored_identity(
    tmp_path: Path, id_padding, url_padding, source_id, url, outcome
):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    existing = {
        "id": f"{id_padding}local{id_padding}",
        "url": f"{url_padding}https://example.com/c.json{url_padding}",
        "priority": 10,
        "install_policy": "install-allowed",
    }
    cc._write(project, [existing])
    config_path = cc._config_path(project)
    original = config_path.read_bytes()
    modified_at = config_path.stat().st_mtime_ns

    if outcome == "conflict":
        with pytest.raises(BundlerError, match="different settings"):
            cc.add_source(project, url, source_id=source_id, policy="install-allowed", priority=10)
    else:
        source, status = cc.add_source(
            project, url, source_id=source_id, policy="install-allowed", priority=10,
        )
        assert status == outcome
        assert source.id == source_id
        assert source.url == url
        assert source.priority == 10
        assert source.install_allowed

    entries = cc._read(project)
    assert entries[0] == existing
    assert len(entries) == (2 if outcome == "added" else 1)
    if outcome != "added":
        assert config_path.read_bytes() == original
        assert config_path.stat().st_mtime_ns == modified_at


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


@pytest.mark.parametrize("body", ["[]\n", "false\n", "0\n", "''\n", "null\n", "~\n"])
def test_read_rejects_falsy_non_mapping_top_level(tmp_path: Path, body: str):
    # A FALSY non-mapping top level ([], false, 0, '') OR an explicit null
    # (null/~) must raise like a truthy one. safe_load coerces these to
    # None/{}, so load_yaml distinguishes them from a truly empty document —
    # staying consistent with models/catalog._merge_config.
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    cc._config_path(project).write_text(body, encoding="utf-8")

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
    source, _ = cc.add_source(project, "weird:name.json", policy="install-allowed", priority=50)
    assert source.url.endswith("weird:name.json") or "weird" in source.url


def test_add_source_rejects_plain_http_for_non_localhost(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(BundlerError, match="HTTPS"):
        cc.add_source(project, "http://example.com/catalog.json", policy="install-allowed", priority=50)


def test_add_source_allows_http_for_localhost(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    source, _ = cc.add_source(project, "http://localhost:8080/c.json", policy="install-allowed", priority=50)
    assert source.url == "http://localhost:8080/c.json"


def test_add_source_rejects_host_less_remote_urls(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    for url in ("https://:8080", "https://user@"):
        with pytest.raises(BundlerError, match="host"):
            cc.add_source(project, url, policy="install-allowed", priority=50)


def test_add_source_wraps_invalid_ipv6_as_bundler_error(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(BundlerError, match="Invalid catalog url"):
        cc.add_source(project, "https://[::1/c.json", policy="install-allowed", priority=50)


def test_add_source_wraps_bracketed_non_ip_host_as_bundler_error(tmp_path: Path):
    # A bracketed-but-invalid IPv6 authority (e.g. "https://[not-an-ip]/c.json")
    # parses cleanly under urlparse() on Python < 3.14 and only raises ValueError
    # lazily on the first .hostname access; the raise moved eager into urlparse()
    # in 3.14. add_source must surface its own BundlerError on every supported
    # version, never leak a raw ValueError past the CLI's `except BundlerError`.
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(BundlerError, match="Invalid catalog url"):
        cc.add_source(project, "https://[not-an-ip]/c.json", policy="install-allowed", priority=50)


def test_add_source_wraps_lazy_hostname_valueerror(tmp_path: Path, monkeypatch):
    # Simulate the Python < 3.14 shape explicitly (independent of the running
    # interpreter): urlparse() succeeds but .hostname raises ValueError lazily.
    # This is the exact path the fix guards; it fails with a raw ValueError if
    # .hostname is read outside the try/except.
    from urllib.parse import urlparse as _real_urlparse

    class _LazyHostnameRaiser:
        def __init__(self, parsed):
            self._parsed = parsed

        @property
        def hostname(self):
            raise ValueError("simulated lazy IPv6 hostname failure")

        def __getattr__(self, name):
            return getattr(self._parsed, name)

    def _fake_urlparse(url, *args, **kwargs):
        return _LazyHostnameRaiser(_real_urlparse(url, *args, **kwargs))

    monkeypatch.setattr(cc, "urlparse", _fake_urlparse)

    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(BundlerError, match="Invalid catalog url"):
        cc.add_source(project, "https://example.com/c.json", policy="install-allowed", priority=50)


def test_remove_source_does_not_crash_on_invalid_ipv6(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".specify").mkdir(parents=True)
    with pytest.raises(BundlerError, match="No project-scoped catalog source"):
        cc.remove_source(project, "https://[::1/c.json")
