"""Authenticated HTTP helpers driven by ``~/.specify/auth.json``.

No credentials are sent unless the user has created ``auth.json``.
For each outbound URL the helper matches the hostname against
configured entries, resolves the token via the appropriate provider
class, and attaches auth headers.  Redirect safety is enforced:
the ``Authorization`` header is stripped when a redirect leaves the
entry's declared hosts.  On 401/403 the next matching entry is tried,
then unauthenticated.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from fnmatch import fnmatch
from urllib.parse import urlparse

from . import get_provider
from .config import AuthConfigEntry, find_entries_for_url, load_auth_config


_config_override: list[AuthConfigEntry] | None = None


def _load_config() -> list[AuthConfigEntry]:
    """Load auth config, using override if set (for testing)."""
    if _config_override is not None:
        return _config_override
    try:
        return load_auth_config()
    except (ValueError, OSError):
        return []


def _hostname_in_hosts(hostname: str, hosts: tuple[str, ...]) -> bool:
    """Return True if *hostname* matches any pattern in *hosts*."""
    hostname = hostname.lower()
    return any(p == hostname or fnmatch(hostname, p) for p in hosts)


class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Drop ``Authorization`` when a redirect leaves the entry's declared hosts."""

    def __init__(self, hosts: tuple[str, ...]) -> None:
        super().__init__()
        self._hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        original_auth = req.get_header("Authorization")
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            hostname = (urlparse(newurl).hostname or "").lower()
            if _hostname_in_hosts(hostname, self._hosts):
                if original_auth:
                    new_req.add_unredirected_header("Authorization", original_auth)
            else:
                new_req.headers.pop("Authorization", None)
                new_req.unredirected_hdrs.pop("Authorization", None)
        return new_req


def build_request(url: str, extra_headers: dict[str, str] | None = None) -> urllib.request.Request:
    """Build a :class:`~urllib.request.Request`, attaching auth when config matches.

    Uses the first matching entry from ``auth.json`` whose token resolves.
    Returns a plain request when no entry matches or the file doesn't exist.
    """
    headers: dict[str, str] = {}
    entries = find_entries_for_url(url, _load_config())
    for entry in entries:
        provider = get_provider(entry.provider)
        if provider is None:
            continue
        token = provider.resolve_token(entry)
        if token:
            headers.update(provider.auth_headers(token, entry.auth))
            break
    if extra_headers:
        headers.update(extra_headers)
    return urllib.request.Request(url, headers=headers)


def open_url(url: str, timeout: int = 10, extra_headers: dict[str, str] | None = None):
    """Open *url* with config-driven auth, redirect stripping, and fallthrough.

    1. Find ``auth.json`` entries whose hosts match the URL.
    2. For each entry, resolve the token and try the request.
    3. On 401/403 move to the next matching entry.
    4. After all entries exhausted (or none matched), try unauthenticated.
    5. Non-auth errors (404, 500, network) raise immediately.

    *extra_headers* (e.g. ``Accept``) are merged into every attempt.
    """
    entries = find_entries_for_url(url, _load_config())

    def _make_req(auth_headers: dict[str, str]) -> urllib.request.Request:
        merged = {**auth_headers}
        if extra_headers:
            merged.update(extra_headers)
        return urllib.request.Request(url, headers=merged)

    # Try each matching entry
    tried = 0
    for entry in entries:
        provider = get_provider(entry.provider)
        if provider is None:
            continue
        token = provider.resolve_token(entry)
        if not token:
            continue
        tried += 1

        req = _make_req(provider.auth_headers(token, entry.auth))
        opener = urllib.request.build_opener(_StripAuthOnRedirect(entry.hosts))
        try:
            return opener.open(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                continue  # try next entry
            raise

    # No entry worked (or none matched) — unauthenticated fallback
    req = _make_req({})
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
