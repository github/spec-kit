"""Unit tests for malformed download-URL handling in bundle manifest resolution."""
from __future__ import annotations

import hashlib
import io
from types import SimpleNamespace

import pytest
import yaml

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.catalog import CatalogEntry
from specify_cli.commands import bundle as bundle_commands
from specify_cli.commands.bundle import _download_manifest, _require_https
from tests.bundler_helpers import catalog_entry_dict, valid_manifest_dict

_MALFORMED_URLS = [
    "https://[::1",  # unclosed IPv6 bracket
    "https://[not-an-ip]/bundle.yml",
    "https://example.com:notaport/bundle.yml",
    "https://example.com:70000/bundle.yml",
]


class _Response(io.BytesIO):
    def __init__(self, body: bytes, url: str) -> None:
        super().__init__(body)
        self._url = url

    def geturl(self) -> str:
        return self._url


def _resolved_entry(**overrides) -> SimpleNamespace:
    entry = CatalogEntry.from_dict(
        catalog_entry_dict(
            "demo-bundle",
            download_url="https://example.com/demo-bundle.yml",
            **overrides,
        )
    )
    return SimpleNamespace(entry=entry)


def _patch_download(monkeypatch, body: bytes) -> None:
    def fake_open_url(
        url,
        timeout=10,
        extra_headers=None,
        redirect_validator=None,
    ):
        return _Response(body, url)

    monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)


@pytest.mark.parametrize("url", _MALFORMED_URLS)
def test_download_manifest_rejects_malformed_url_cleanly(url):
    """A malformed download_url must raise BundlerError, not a raw ValueError.

    ``urlparse`` raises ``ValueError`` on a malformed authority (e.g. an
    unclosed IPv6 bracket). The bundle CLI commands only catch BundlerError, so
    a raw ValueError would escape as an uncaught traceback. Sibling of the
    guarded ``_validate_remote_url`` (adapters) and the merged #3576 fix.
    """
    resolved = SimpleNamespace(
        entry=SimpleNamespace(id="mybundle", download_url=url)
    )
    with pytest.raises(BundlerError):
        _download_manifest(resolved, offline=True)


@pytest.mark.parametrize("url", _MALFORMED_URLS)
def test_require_https_rejects_malformed_url_cleanly(url):
    """``_require_https`` must also surface BundlerError on a malformed authority.

    On older Python versions the ValueError is raised at ``.hostname`` access
    rather than at ``urlparse``, so guarding both keeps the contract across the
    CI Python matrix.
    """
    with pytest.raises(BundlerError):
        _require_https("bundle 'x'", url)


def test_download_manifest_bounds_remote_artifact(monkeypatch):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    _patch_download(monkeypatch, body)
    monkeypatch.setattr(bundle_commands, "MAX_DOWNLOAD_BYTES", len(body) - 1)

    with pytest.raises(BundlerError, match="exceeds maximum size"):
        _download_manifest(_resolved_entry(), offline=False)


def test_download_manifest_accepts_matching_sha256(monkeypatch):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    digest = hashlib.sha256(body).hexdigest()
    _patch_download(monkeypatch, body)

    manifest = _download_manifest(
        _resolved_entry(sha256=f"sha256:{digest}"),
        offline=False,
    )

    assert manifest.bundle.id == "demo-bundle"


def test_download_manifest_accepts_legacy_entry_without_sha256(monkeypatch):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    _patch_download(monkeypatch, body)
    resolved = SimpleNamespace(
        entry=SimpleNamespace(
            id="demo-bundle",
            version="1.2.0",
            download_url="https://example.com/demo-bundle.yml",
        )
    )

    manifest = _download_manifest(resolved, offline=False)

    assert manifest.bundle.version == "1.2.0"


@pytest.mark.parametrize("declared", ["0" * 64, "not-a-sha256"])
def test_download_manifest_rejects_bad_sha256(monkeypatch, declared):
    body = yaml.safe_dump(valid_manifest_dict()).encode()
    _patch_download(monkeypatch, body)

    with pytest.raises(BundlerError, match="sha256|Integrity check"):
        _download_manifest(
            _resolved_entry(sha256=declared),
            offline=False,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("id", "other-bundle", "id mismatch"),
        ("version", "9.9.9", "version mismatch"),
    ],
)
def test_download_manifest_rejects_catalog_identity_mismatch(
    monkeypatch,
    field,
    value,
    message,
):
    data = valid_manifest_dict()
    data["bundle"][field] = value
    _patch_download(monkeypatch, yaml.safe_dump(data).encode())

    with pytest.raises(BundlerError, match=message):
        _download_manifest(_resolved_entry(), offline=False)


def test_download_manifest_rejects_invalid_structure(monkeypatch):
    data = valid_manifest_dict()
    data["bundle"]["author"] = ""
    _patch_download(monkeypatch, yaml.safe_dump(data).encode())

    with pytest.raises(BundlerError, match="invalid bundle manifest"):
        _download_manifest(_resolved_entry(), offline=False)
