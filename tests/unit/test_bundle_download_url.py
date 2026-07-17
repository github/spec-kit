"""Unit tests for malformed download-URL handling in bundle manifest resolution."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from specify_cli.bundler import BundlerError
from specify_cli.commands.bundle import _download_manifest, _require_https

_MALFORMED_URLS = [
    "https://[::1",  # unclosed IPv6 bracket
    "https://[not-an-ip]/bundle.yml",
]


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
