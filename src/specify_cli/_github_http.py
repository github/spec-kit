"""Shared GitHub-authenticated HTTP helpers.

Used by both ExtensionCatalog and PresetCatalog to attach
GITHUB_TOKEN / GH_TOKEN credentials to requests targeting
GitHub-hosted domains, while preventing token leakage to
third-party hosts on redirects.
"""

import os
import urllib.request
from urllib.parse import urlparse
from typing import Dict

# GitHub-owned hostnames that should receive the Authorization header.
# Includes codeload.github.com because GitHub archive URL downloads
# (e.g. /archive/refs/tags/<tag>.zip) redirect there and require auth
# for private repositories.
GITHUB_HOSTS = frozenset({
    "raw.githubusercontent.com",
    "github.com",
    "api.github.com",
    "codeload.github.com",
})


def build_github_request(url: str) -> urllib.request.Request:
    """Build a urllib Request, adding a GitHub auth header when available.

    Reads GITHUB_TOKEN or GH_TOKEN from the environment and attaches an
    ``Authorization: Bearer <value>`` header when the target hostname is one
    of the known GitHub-owned domains. Non-GitHub URLs are returned as plain
    requests so credentials are never leaked to third-party hosts.
    """
    headers: Dict[str, str] = {}
    if not url or not url.strip():
        raise ValueError("url must not be empty")
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"url must start with http:// or https://, got: {url!r}")
    if not parsed.hostname:
        raise ValueError(f"url must include a hostname, got: {url!r}")
    github_token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    gh_token = (os.environ.get("GH_TOKEN") or "").strip()
    token = github_token or gh_token or None
    hostname = parsed.hostname.lower()
    if token and hostname in GITHUB_HOSTS:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


class _StripAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """Redirect handler that drops the Authorization header when leaving GitHub.

    Prevents token leakage to CDNs or other third-party hosts that GitHub
    may redirect to (e.g. S3 for release asset downloads, objects.githubusercontent.com).
    Auth is preserved as long as the redirect target remains within GITHUB_HOSTS.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        original_auth = req.get_header("Authorization")
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            hostname = (urlparse(newurl).hostname or "").lower()
            if hostname in GITHUB_HOSTS:
                if original_auth:
                    new_req.add_unredirected_header("Authorization", original_auth)
            else:
                new_req.headers.pop("Authorization", None)
                new_req.unredirected_hdrs.pop("Authorization", None)
        return new_req


def open_github_url(url: str, timeout: int = 10):
    """Open a URL with GitHub auth, stripping the header on cross-host redirects.

    When the request carries an Authorization header, a custom redirect
    handler drops that header if the redirect target is not a GitHub-owned
    domain, preventing token leakage to CDNs or other third-party hosts
    that GitHub may redirect to (e.g. S3 for release asset downloads).
    """
    req = build_github_request(url)

    if not req.get_header("Authorization"):
        return urllib.request.urlopen(req, timeout=timeout)

    opener = urllib.request.build_opener(_StripAuthOnRedirect)
    return opener.open(req, timeout=timeout)
