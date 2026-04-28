"""Authenticated HTTP helpers using the auth provider registry.

Replaces the former ``_github_http`` module.  For any outbound request the
helper iterates configured providers in registry order, trying each one's
auth headers.  If the request fails with a 401 or 403 the next configured
provider is tried.  After all providers are exhausted the request is
retried without credentials.
"""

from __future__ import annotations

import urllib.error
import urllib.request

from . import configured_providers


def build_request(url: str, extra_headers: dict[str, str] | None = None) -> urllib.request.Request:
    """Build a :class:`~urllib.request.Request` with the first configured provider's auth.

    Attaches auth headers from the first configured provider (if any).
    *extra_headers* are added on top.
    """
    headers: dict[str, str] = {}
    providers = configured_providers()
    if providers:
        headers.update(providers[0].auth_headers())
    if extra_headers:
        headers.update(extra_headers)
    return urllib.request.Request(url, headers=headers)


def open_url(url: str, timeout: int = 10):
    """Open *url*, trying each configured provider's auth on failure.

    1. Try each configured provider's auth headers in registry order.
    2. If the request gets a 401 or 403, move to the next provider.
    3. If all providers fail (or none are configured), try unauthenticated.
    4. Any non-auth error is raised immediately.
    """
    providers = configured_providers()

    for provider in providers:
        headers = provider.auth_headers()
        req = urllib.request.Request(url, headers=headers)
        try:
            return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403) and provider is not providers[-1]:
                continue  # try next provider
            if exc.code in (401, 403):
                break  # last provider failed auth — fall through to unauth
            raise

    # No configured provider worked (or none existed) — try unauthenticated.
    req = urllib.request.Request(url)
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310
