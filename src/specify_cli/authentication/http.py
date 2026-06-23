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
from typing import Callable
from urllib.parse import urlparse

from .._download_security import is_https_or_localhost_http
from . import get_provider
from .config import AuthConfigEntry, _default_config_path, find_entries_for_url, load_auth_config


_config_override: list[AuthConfigEntry] | None = None
_config_cache: list[AuthConfigEntry] | None = None  # None = not yet loaded


def _load_config() -> list[AuthConfigEntry]:
    """Load auth config, using override if set (for testing).

    The result is cached per-process so ``auth.json`` is read at most once,
    and any warning about a malformed file fires only once.
    """
    global _config_cache
    if _config_override is not None:
        return _config_override
    if _config_cache is not None:
        return _config_cache
    try:
        _config_cache = load_auth_config()
    except (ValueError, OSError) as exc:
        import warnings
        config_path = _default_config_path()
        warnings.warn(
            f"Failed to load {config_path}: {exc}. "
            "All requests will be unauthenticated.",
            UserWarning,
            stacklevel=2,
        )
        _config_cache = []
    return _config_cache


def _hostname_in_hosts(hostname: str, hosts: tuple[str, ...]) -> bool:
    """Return True if *hostname* matches any pattern in *hosts*."""
    hostname = hostname.lower()
    return any(p == hostname or fnmatch(hostname, p) for p in hosts)


RedirectValidator = Callable[[str, str], None]


def _validate_strict_redirect(_old_url: str, new_url: str) -> None:
    if not is_https_or_localhost_http(new_url):
        raise urllib.error.URLError(
            "unsafe redirect: target must use HTTPS with a hostname, "
            "or HTTP for localhost (127.0.0.1, ::1)"
        )


class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Redirect handler that guards every redirect it is installed for.

    1. Run any caller-provided redirect validator.
    2. Reject redirects that are not HTTPS with a hostname, except HTTP to
       localhost / 127.0.0.1 / ::1 (the exact hosts allowed by
       ``is_https_or_localhost_http``).
    3. Drop ``Authorization`` when a redirect leaves trusted hosts or downgrades.
    """

    def __init__(
        self,
        hosts: tuple[str, ...],
        redirect_validator: RedirectValidator | None = None,
    ) -> None:
        super().__init__()
        self._hosts = hosts
        self._redirect_validator = redirect_validator

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if self._redirect_validator is not None:
            self._redirect_validator(req.full_url, newurl)
        _validate_strict_redirect(req.full_url, newurl)

        original_auth = (
            req.get_header("Authorization")
            or req.unredirected_hdrs.get("Authorization")
        )
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            old_scheme = urlparse(req.full_url).scheme
            new_parsed = urlparse(newurl)
            hostname = (new_parsed.hostname or "").lower()
            is_https_downgrade = old_scheme == "https" and new_parsed.scheme != "https"
            if _hostname_in_hosts(hostname, self._hosts) and not is_https_downgrade:
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
    if extra_headers:
        # Strip Authorization from extra_headers to prevent bypass
        headers.update({k: v for k, v in extra_headers.items() if k.lower() != "authorization"})
    # Auth headers applied last — cannot be overridden by extra_headers
    entries = find_entries_for_url(url, _load_config())
    for entry in entries:
        provider = get_provider(entry.provider)
        if provider is None:
            continue
        token = provider.resolve_token(entry)
        if token:
            headers.update(provider.auth_headers(token, entry.auth))
            break
    return urllib.request.Request(url, headers=headers)


def github_provider_hosts() -> tuple[str, ...]:
    """Return host patterns from every ``github`` provider entry in ``auth.json``.

    Used to classify which hosts are GitHub Enterprise Server instances when
    resolving release-asset download URLs. Returns an empty tuple when no
    ``auth.json`` exists or it contains no ``github`` entries.
    """
    hosts: list[str] = []
    for entry in _load_config():
        if entry.provider == "github":
            hosts.extend(entry.hosts)
    return tuple(hosts)


def open_url(
    url: str,
    timeout: int = 10,
    extra_headers: dict[str, str] | None = None,
    redirect_validator: RedirectValidator | None = None,
    strict_redirects: bool = False,
):
    """Open *url* with config-driven auth, redirect stripping, and fallthrough.

    1. Find ``auth.json`` entries whose hosts match the URL.
    2. For each entry, resolve the token and try the request.
    3. On 401/403 move to the next matching entry.
    4. After all entries exhausted (or none matched), try unauthenticated.
    5. Non-auth errors (404, 500, network) raise immediately.

    *extra_headers* (e.g. ``Accept``) are merged into every attempt.
    *redirect_validator*, when provided, is called with ``(old_url, new_url)``
    before following each redirect and may raise to reject the redirect.

    Redirect scheme safety: every authenticated attempt goes through
    ``_StripAuthOnRedirect``, which always rejects redirects to non-HTTPS
    URLs (except HTTP to localhost / 127.0.0.1 / ::1, the hosts allowed by
    ``is_https_or_localhost_http``). The unauthenticated fallback installs the
    same handler when *strict_redirects* is true or *redirect_validator* is
    supplied; without either, it follows redirects without that handler.
    """
    entries = find_entries_for_url(url, _load_config())

    effective_redirect_validator = redirect_validator
    use_redirect_handler = strict_redirects or effective_redirect_validator is not None

    def _make_req(auth_headers: dict[str, str]) -> urllib.request.Request:
        merged = {}
        if extra_headers:
            # Strip Authorization from extra_headers to prevent bypass
            merged.update({k: v for k, v in extra_headers.items() if k.lower() != "authorization"})
        # Auth headers applied last — cannot be overridden by extra_headers
        merged.update(auth_headers)
        return urllib.request.Request(url, headers=merged)

    # Try each matching entry
    for entry in entries:
        provider = get_provider(entry.provider)
        if provider is None:
            continue
        token = provider.resolve_token(entry)
        if not token:
            continue

        req = _make_req(provider.auth_headers(token, entry.auth))
        opener = urllib.request.build_opener(_StripAuthOnRedirect(entry.hosts, effective_redirect_validator))
        try:
            return opener.open(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                exc.close()
                continue  # try next entry
            raise

    # No entry worked (or none matched) — unauthenticated fallback
    req = _make_req({})
    if use_redirect_handler:
        # No auth is attached on this path, so the handler's host list is empty:
        # here it runs redirect validation only, not auth stripping.
        opener = urllib.request.build_opener(_StripAuthOnRedirect((), effective_redirect_validator))
        return opener.open(req, timeout=timeout)
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
