"""Unit tests for catalog-fetch adapters (auth + redirect safety)."""
from __future__ import annotations

import pytest

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
        self._final_url = final_url

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def geturl(self) -> str:
        return self._final_url

    def read(self) -> bytes:
        return self._body


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
