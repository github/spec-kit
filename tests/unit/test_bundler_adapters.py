"""Unit tests for catalog-fetch adapters (auth + redirect safety)."""
from __future__ import annotations

import io
import urllib.error
import urllib.request
import warnings
from typing import Self

import pytest

from specify_cli.authentication.http import _StripAuthOnRedirect
from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.catalog import CatalogSource, InstallPolicy
from specify_cli.bundler.services import adapters


def _source(url: str) -> CatalogSource:
    return CatalogSource(
        id="team",
        url=url,
        priority=10,
        install_policy=InstallPolicy.INSTALL_ALLOWED,
    )


class _FakeResponse:
    def __init__(self, body: bytes, final_url: str) -> None:
        self._body = body
        self._offset = 0
        self._final_url = final_url

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def geturl(self) -> str:
        return self._final_url

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._body) - self._offset
        start = self._offset
        self._offset = min(len(self._body), self._offset + size)
        return self._body[start:self._offset]


def test_http_fetch_uses_shared_client_and_rejects_redirect_downgrade(monkeypatch):
    captured: dict = {}

    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        captured["url"] = url
        captured["validator"] = redirect_validator
        return _FakeResponse(b'{"schema_version": "1.0"}', url)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    fetcher = adapters.make_catalog_fetcher(allow_network=True)
    result = fetcher(_source("https://example.com/c.json"))
    assert result == {"schema_version": "1.0"}
    assert captured["url"] == "https://example.com/c.json"

    # The validator handed to open_url must reject an HTTP downgrade redirect.
    validator = captured["validator"]
    assert validator is not None
    with pytest.raises(BundlerError, match="must use HTTPS"):
        validator("https://example.com/c.json", "http://evil.example/c.json")
    # And a same-scheme HTTPS redirect is allowed (no raise).
    validator("https://example.com/c.json", "https://cdn.example/c.json")


def test_http_fetch_rejects_non_https_final_url(monkeypatch):
    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        # Simulate a response whose final URL silently downgraded to HTTP.
        return _FakeResponse(b"{}", "http://evil.example/c.json")

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    fetcher = adapters.make_catalog_fetcher(allow_network=True)
    with pytest.raises(BundlerError, match="must use HTTPS"):
        fetcher(_source("https://example.com/c.json"))


def test_http_fetch_bounds_catalog_response(monkeypatch):
    body = b'{"schema_version":"1.0","bundles":{}}'

    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        return _FakeResponse(body, url)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)
    monkeypatch.setattr(adapters, "MAX_JSON_CATALOG_BYTES", len(body) - 1)

    fetcher = adapters.make_catalog_fetcher(allow_network=True)
    with pytest.raises(BundlerError, match="exceeds maximum size"):
        fetcher(_source("https://example.com/c.json"))


def test_http_get_json_marks_connection_error_unavailable(monkeypatch):
    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        raise urllib.error.URLError("name resolution failed")

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    with pytest.raises(adapters._CatalogUnavailable):
        adapters._http_get_json("team", "https://example.com/c.json")


def test_http_get_json_marks_server_error_unavailable(monkeypatch):
    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        raise urllib.error.HTTPError(url, 503, "Service Unavailable", {}, None)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    with pytest.raises(adapters._CatalogUnavailable, match="503"):
        adapters._http_get_json("team", "https://example.com/c.json")


def test_http_get_json_preserves_client_error_as_bundler_error(monkeypatch):
    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    with pytest.raises(BundlerError, match="404") as excinfo:
        adapters._http_get_json("team", "https://example.com/c.json")
    assert not isinstance(excinfo.value, adapters._CatalogUnavailable)


def test_http_get_json_preserves_malformed_json(monkeypatch):
    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        return _FakeResponse(b"not json", url)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    with pytest.raises(BundlerError) as excinfo:
        adapters._http_get_json("team", "https://example.com/c.json")
    assert not isinstance(excinfo.value, adapters._CatalogUnavailable)


def test_http_get_json_preserves_invalid_utf8(monkeypatch):
    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        return _FakeResponse(b"\xff\xfe", url)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

    with pytest.raises(BundlerError, match="not valid UTF-8") as excinfo:
        adapters._http_get_json("team", "https://example.com/c.json")
    assert not isinstance(excinfo.value, adapters._CatalogUnavailable)


def test_http_get_json_preserves_oversized_response(monkeypatch):
    body = b'{"schema_version":"1.0","bundles":{}}'

    def fake_open_url(url, timeout=10, extra_headers=None, redirect_validator=None):
        return _FakeResponse(body, url)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)
    monkeypatch.setattr(adapters, "MAX_JSON_CATALOG_BYTES", len(body) - 1)

    with pytest.raises(BundlerError) as excinfo:
        adapters._http_get_json("team", "https://example.com/c.json")
    assert not isinstance(excinfo.value, adapters._CatalogUnavailable)


@pytest.mark.parametrize(
    "url",
    [
        "https://[::1",
        "https://example.com:notaport/catalog.json",
        "https://example.com:70000/catalog.json",
    ],
)
def test_fetch_rejects_malformed_source_url_cleanly(url):
    fetcher = adapters.make_catalog_fetcher(allow_network=True)
    with pytest.raises(BundlerError, match="URL is malformed"):
        fetcher(_source(url))


@pytest.mark.parametrize("use_file_url", [False, True], ids=["path", "file-url"])
def test_local_catalog_decode_errors_are_wrapped(tmp_path, use_file_url):
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(b"\xff\xfe")
    url = catalog_path.as_uri() if use_file_url else str(catalog_path)

    fetcher = adapters.make_catalog_fetcher(allow_network=False)

    with pytest.raises(BundlerError, match="Could not read"):
        fetcher(_source(url))


_SNAPSHOT_BODY = (
    '{"schema_version":"1.0","bundles":{"packaged":{'
    '"id":"packaged","name":"Packaged","version":"1.0.0",'
    '"role":"developer","description":"Packaged catalog entry.",'
    '"author":"Spec Kit","license":"MIT","download_url":"",'
    '"requires":{"speckit_version":">=0.1.0"},'
    '"provides":{},"verified":false}}}'
)


def _write_snapshot(tmp_path, filename):
    path = tmp_path / "bundles" / filename
    path.parent.mkdir(exist_ok=True)
    path.write_text(_SNAPSHOT_BODY, encoding="utf-8")
    return path


_BUILTIN_CASES = [
    pytest.param(
        "builtin://default",
        "catalog.json",
        adapters.FIRSTPARTY_CATALOG_URL,
        id="default",
    ),
    pytest.param(
        "builtin://community",
        "catalog.community.json",
        adapters.COMMUNITY_CATALOG_URL,
        id="community",
    ),
]


@pytest.mark.parametrize("builtin_id, snapshot_name, expected_url", _BUILTIN_CASES)
def test_builtin_catalog_fetches_repository_catalog_online(
    monkeypatch, builtin_id, snapshot_name, expected_url
):
    captured: dict = {}

    def fake_http_get_json(source_id, url):
        captured["source_id"] = source_id
        captured["url"] = url
        return {"schema_version": "1.0", "bundles": {}}

    monkeypatch.setattr(adapters, "_http_get_json", fake_http_get_json)

    fetcher = adapters.make_catalog_fetcher(allow_network=True)
    result = fetcher(_source(builtin_id))

    assert result["bundles"] == {}
    assert captured == {"source_id": "team", "url": expected_url}


@pytest.mark.parametrize("builtin_id, snapshot_name, expected_url", _BUILTIN_CASES)
def test_builtin_catalog_falls_back_to_snapshot_on_availability_error(
    monkeypatch, tmp_path, builtin_id, snapshot_name, expected_url
):
    _write_snapshot(tmp_path, snapshot_name)
    monkeypatch.setattr(adapters, "_locate_core_pack", lambda: tmp_path)

    def fail_http_get_json(source_id, url):
        raise adapters._CatalogUnavailable("repository unavailable")

    monkeypatch.setattr(adapters, "_http_get_json", fail_http_get_json)

    fetcher = adapters.make_catalog_fetcher(allow_network=True)
    with pytest.warns(UserWarning, match="packaged snapshot"):
        result = fetcher(_source(builtin_id))

    assert "packaged" in result["bundles"]


@pytest.mark.parametrize("builtin_id, snapshot_name, expected_url", _BUILTIN_CASES)
def test_builtin_catalog_validation_error_is_not_masked_by_snapshot(
    monkeypatch, tmp_path, builtin_id, snapshot_name, expected_url
):
    _write_snapshot(tmp_path, snapshot_name)
    monkeypatch.setattr(adapters, "_locate_core_pack", lambda: tmp_path)

    def fail_http_get_json(source_id, url):
        raise BundlerError("Invalid catalog payload")

    monkeypatch.setattr(adapters, "_http_get_json", fail_http_get_json)
    monkeypatch.setattr(
        adapters,
        "_load_packaged_catalog",
        lambda filename: pytest.fail(
            "snapshot must not be used for validation errors"
        ),
    )

    fetcher = adapters.make_catalog_fetcher(allow_network=True)
    with pytest.raises(BundlerError, match="Invalid catalog payload"):
        fetcher(_source(builtin_id))


@pytest.mark.parametrize("builtin_id, snapshot_name, expected_url", _BUILTIN_CASES)
def test_builtin_catalog_uses_core_pack_snapshot_offline_quietly(
    monkeypatch, tmp_path, builtin_id, snapshot_name, expected_url
):
    _write_snapshot(tmp_path, snapshot_name)
    monkeypatch.setattr(adapters, "_locate_core_pack", lambda: tmp_path)

    fetcher = adapters.make_catalog_fetcher(allow_network=False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = fetcher(_source(builtin_id))

    assert "packaged" in result["bundles"]
    assert not [w for w in caught if "snapshot" in str(w.message)]


@pytest.mark.parametrize("status_code", [408, 429, 500])
def test_builtin_community_catalog_falls_back_for_transient_http_failures(
    monkeypatch, tmp_path, status_code
):
    catalog_path = tmp_path / "bundles" / "catalog.community.json"
    catalog_path.parent.mkdir()
    catalog_path.write_text(
        '{"schema_version":"1.0","bundles":{}}', encoding="utf-8"
    )
    monkeypatch.setattr(adapters, "_locate_core_pack", lambda: tmp_path)

    def fail(url, timeout=10, extra_headers=None, redirect_validator=None):
        raise urllib.error.HTTPError(url, status_code, "transient", {}, None)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fail)
    fetcher = adapters.make_catalog_fetcher(allow_network=True)

    assert fetcher(_source("builtin://community")) == {
        "schema_version": "1.0",
        "bundles": {},
    }


def test_builtin_community_catalog_falls_back_for_transport_errors(monkeypatch, tmp_path):
    catalog_path = tmp_path / "bundles" / "catalog.community.json"
    catalog_path.parent.mkdir()
    catalog_path.write_text(
        '{"schema_version":"1.0","bundles":{}}', encoding="utf-8"
    )
    monkeypatch.setattr(adapters, "_locate_core_pack", lambda: tmp_path)

    def fail(url, timeout=10, extra_headers=None, redirect_validator=None):
        raise urllib.error.URLError("network unreachable")

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fail)
    fetcher = adapters.make_catalog_fetcher(allow_network=True)

    assert fetcher(_source("builtin://community")) == {
        "schema_version": "1.0",
        "bundles": {},
    }


@pytest.mark.parametrize(
    "target",
    [
        # Remote-to-loopback redirect (accepted by URL validation, rejected by
        # the strict redirect policy).
        "https://localhost/internal/catalog.json",
        # Malformed redirect target (unterminated IPv6 bracket).
        "https://[::1/internal/catalog.json",
    ],
)
def test_builtin_community_catalog_does_not_fall_back_for_redirect_policy_errors(
    monkeypatch, tmp_path, target
):
    """A redirect the shared client rejects as a policy violation must surface
    as a hard error even though ``RedirectPolicyError`` subclasses ``URLError``.

    The fake ``open_url`` runs the real ``_StripAuthOnRedirect`` handler, so the
    production classification is exercised instead of injecting the exception.
    A snapshot is present to prove the fallback is not taken.
    """
    catalog_path = tmp_path / "bundles" / "catalog.community.json"
    catalog_path.parent.mkdir()
    catalog_path.write_text(
        '{"schema_version":"1.0","bundles":{}}', encoding="utf-8"
    )
    monkeypatch.setattr(adapters, "_locate_core_pack", lambda: tmp_path)

    def redirect_into_policy_violation(
        url, timeout=10, extra_headers=None, redirect_validator=None
    ):
        handler = _StripAuthOnRedirect((), redirect_validator)
        handler.redirect_request(
            urllib.request.Request(url),
            io.BytesIO(b""),
            302,
            "Found",
            {},
            target,
        )
        raise AssertionError("redirect should have been rejected")

    monkeypatch.setattr(
        "specify_cli.authentication.http.open_url", redirect_into_policy_violation
    )
    fetcher = adapters.make_catalog_fetcher(allow_network=True)

    with pytest.raises(BundlerError, match="Failed to fetch catalog") as excinfo:
        fetcher(_source("builtin://community"))
    assert not isinstance(excinfo.value, adapters._CatalogUnavailable)


@pytest.mark.parametrize(
    "url",
    [
        "https://:8080",          # port only, no host
        "https://:0",
        "https://user@",          # userinfo only, no host
        "https://user:pw@",
        "https://:8080/catalog.json",
    ],
)
def test_validate_remote_url_rejects_host_less_urls(url):
    """A URL with a truthy netloc but no host (``https://:8080``,
    ``https://user@``) must be rejected.

    ``urlparse`` gives these a non-empty ``netloc`` but ``hostname is None``,
    so a ``netloc`` check would wrongly accept them. This mirrors the fix in
    ``specify_cli.catalogs`` (#3210), which the docstring says this validator
    mirrors."""
    with pytest.raises(BundlerError, match="valid URL with a host"):
        adapters._validate_remote_url("team", url)


def test_validate_remote_url_accepts_normal_https_url():
    # Sanity: a real host with a port still passes.
    adapters._validate_remote_url("team", "https://example.com:8080/c.json")


@pytest.mark.parametrize(
    "url",
    [
        "https://[::1",  # unclosed IPv6 bracket
        "https://[not-an-ip]/c.json",
    ],
)
def test_validate_remote_url_rejects_malformed_url_cleanly(url):
    """A malformed URL must raise BundlerError, not a raw ValueError.

    ``urlparse``/``hostname`` raise ``ValueError`` on a malformed authority
    (e.g. an unclosed IPv6 bracket). The validator's contract is to raise
    BundlerError for any bad URL, so the raw ValueError must not escape to the
    caller. Bundler sibling of #3369."""
    with pytest.raises(BundlerError):
        adapters._validate_remote_url("team", url)
