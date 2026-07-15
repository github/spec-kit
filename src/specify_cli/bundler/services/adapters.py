"""Concrete adapters: catalog fetching and primitive installation.

These wire the bundler's injectable seams to the real environment:

* :func:`make_catalog_fetcher` returns an offline-first fetcher that reads
  built-in catalogs and local/pinned file URLs without network, and falls back
  to a timeout-bounded HTTP GET only for ``http(s)://`` sources.
* :class:`DefaultPrimitiveInstaller` dispatches component install/remove to the
  existing Spec Kit primitive machinery in-process.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import ParseResult, urlparse
from urllib.request import url2pathname

from .. import BundlerError
from ..lib.yamlio import loads_json
from ..models.catalog import CatalogSource
from ..models.manifest import ComponentRef

# Built-in catalog payloads ship empty by default; a host distribution can
# replace these with curated content. Keeping them here makes ``search``/``info``
# work fully offline against the default stack.
_BUILTIN_CATALOGS: dict[str, dict] = {
    "builtin://default": {
        "schema_version": "1.0",
        "catalog_url": "builtin://default",
        "bundles": {},
    },
    "builtin://community": {
        "schema_version": "1.0",
        "catalog_url": "builtin://community",
        "bundles": {},
    },
}

HTTP_TIMEOUT_SECONDS = 10

# Windows absolute paths like ``C:\catalog.json`` parse with a single-letter
# ``scheme`` under urlparse; treat them as local files rather than URLs.
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def _is_windows_drive_path(url: str) -> bool:
    return bool(_WINDOWS_DRIVE_RE.match(url))


def _file_url_to_path(parsed: ParseResult) -> Path:
    """Convert a ``file://`` URL to a local path.

    Uses ``url2pathname`` for percent-decoding and OS-correct separators, and
    preserves ``netloc`` so UNC paths (``file://server/share``) and Windows
    drive URLs (``file:///C:/x``) resolve correctly instead of dropping host
    or producing ``/C:/x``.
    """
    netloc = parsed.netloc
    if netloc and netloc.lower() != "localhost":
        # UNC share: file://server/share/... -> \\server\share\...
        return Path(url2pathname(f"//{netloc}{parsed.path}"))
    return Path(url2pathname(parsed.path))


def _validate_remote_url(source_id: str, url: str) -> None:
    """Restrict remote catalogs to HTTPS (HTTP only for localhost) with a host.

    Mirrors ``specify_cli.catalogs`` URL validation to avoid MITM/downgrade
    issues before any network call.
    """
    # A malformed authority (e.g. an unclosed IPv6 bracket ``https://[::1``)
    # makes urlparse / hostname access raise ValueError. This function's
    # contract is to raise BundlerError for a bad URL, so surface that as a
    # clean error rather than leaking a raw ValueError to the caller.
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
    except ValueError:
        raise BundlerError(
            f"Catalog '{source_id}' URL is malformed: {url}"
        ) from None
    is_localhost = hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
        raise BundlerError(
            f"Catalog '{source_id}' URL must use HTTPS (got {parsed.scheme}://). "
            "HTTP is only allowed for localhost."
        )
    # Check hostname, not netloc: netloc is truthy for host-less URLs like
    # "https://:8080" or "https://user@...", so requiring netloc would let
    # those through even though they carry no host. hostname is None in those
    # cases. Mirrors the fix in ``specify_cli.catalogs`` (#3210).
    if not hostname:
        raise BundlerError(
            f"Catalog '{source_id}' URL must be a valid URL with a host: {url}"
        )


def make_catalog_fetcher(*, allow_network: bool = True):
    """Return a fetcher callable suitable for :class:`CatalogStack`.

    When *allow_network* is False, ``http(s)://`` sources raise instead of
    touching the network (used by offline tests and ``--offline`` flows).
    """

    def fetch(source: CatalogSource) -> dict:
        url = source.url
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme == "builtin":
            payload = _BUILTIN_CATALOGS.get(url)
            if payload is None:
                raise BundlerError(f"Unknown built-in catalog '{url}'.")
            return payload

        if scheme == "file":
            path = _file_url_to_path(parsed)
            if not path.exists():
                raise BundlerError(f"Catalog file not found: {path}")
            return loads_json(path.read_text(encoding="utf-8"), origin=str(path))

        if scheme == "" or _is_windows_drive_path(url):
            path = Path(url)
            if not path.exists():
                raise BundlerError(f"Catalog file not found: {path}")
            return loads_json(path.read_text(encoding="utf-8"), origin=str(path))

        if scheme in ("http", "https"):
            if not allow_network:
                raise BundlerError(
                    f"Network access disabled; cannot fetch catalog '{source.id}' "
                    f"from {url}."
                )
            _validate_remote_url(source.id, url)
            return _http_get_json(source.id, url)

        raise BundlerError(f"Unsupported catalog URL scheme: {url}")

    return fetch


def _http_get_json(source_id: str, url: str) -> dict:
    """Fetch catalog JSON over HTTP(S) via the shared authenticated client.

    Routing through :func:`specify_cli.authentication.http.open_url` gives
    ``auth.json`` token support and strips the ``Authorization`` header when a
    redirect leaves the entry's trusted hosts or downgrades the scheme. We also
    reject any redirect that leaves HTTPS (the ``redirect_validator`` runs
    *before* each hop) and re-validate the final URL after redirects, so the
    HTTPS/host guarantee from ``_validate_remote_url`` is preserved end to end
    rather than only on the initial URL.
    """
    from ...authentication.http import open_url

    def _validate_redirect(_old_url: str, new_url: str) -> None:
        _validate_remote_url(source_id, new_url)

    try:
        with open_url(
            url,
            timeout=HTTP_TIMEOUT_SECONDS,
            redirect_validator=_validate_redirect,
        ) as response:
            final_url = response.geturl()
            _validate_remote_url(source_id, final_url)
            raw = response.read().decode("utf-8")
    except BundlerError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise BundlerError(f"Failed to fetch catalog from {url}: {exc}") from exc
    return loads_json(raw, origin=final_url)


class DefaultPrimitiveInstaller:
    """Dispatch component install/remove to existing primitive machinery.

    This adapter is intentionally thin: it owns no install logic of its own,
    delegating entirely to the per-primitive managers so the bundler honours
    Principle I (no duplicated primitive logic).

    *allow_network* mirrors the bundle command's ``--offline`` flag: when False,
    component kinds that can only be sourced from a remote catalog refuse rather
    than touching the network. Bundled presets/extensions still install offline.
    """

    def __init__(self, *, allow_network: bool = True) -> None:
        self._allow_network = allow_network

    def is_installed(self, project_root: Path, component: ComponentRef) -> bool:
        manager = self._manager_for(component, project_root)
        return manager.is_installed(component)

    def install(self, project_root: Path, component: ComponentRef) -> None:
        manager = self._manager_for(component, project_root)
        manager.install(component)

    def remove(self, project_root: Path, component: ComponentRef) -> None:
        manager = self._manager_for(component, project_root)
        manager.remove(component)

    def _manager_for(self, component: ComponentRef, project_root: Path):
        # Lazy import to avoid import cycles and keep startup cheap (Principle IV).
        from .primitives import primitive_manager

        return primitive_manager(
            component.kind, project_root, allow_network=self._allow_network
        )
