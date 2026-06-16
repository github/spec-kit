"""Shared GitHub HTTP request helpers.

Provides ``build_github_request()`` for attaching GITHUB_TOKEN / GH_TOKEN
credentials to requests targeting GitHub-hosted domains, and
``resolve_github_release_asset_api_url()`` — used by extensions, presets,
and workflow URL resolution — to translate browser release-download URLs
into GitHub REST API asset URLs. Authenticated downloads themselves go
through the config-driven helpers in :mod:`specify_cli.authentication.http`.
"""

import os
import urllib.request
from typing import Callable, Dict, Optional
from urllib.parse import quote, unquote, urlparse

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

    Raises:
        ValueError: If ``url`` is empty or whitespace-only.
        ValueError: If ``url`` does not use the ``http`` or ``https`` scheme.
        ValueError: If ``url`` does not include a hostname.
    """
    headers: Dict[str, str] = {}
    url = url.strip()
    if not url:
        raise ValueError("url must not be empty")
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


def resolve_github_release_asset_api_url(
    download_url: str,
    open_url_fn: Callable,
    timeout: int = 60,
) -> Optional[str]:
    """Resolve a GitHub browser release URL to its REST API asset URL.

    For private or SSO-protected repositories, browser release download
    URLs (``https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>``)
    redirect to an HTML/SSO page instead of delivering the file.  This
    helper resolves such a URL to the matching GitHub REST API asset URL
    (``https://api.github.com/repos/…/releases/assets/<id>``), which can
    then be downloaded with ``Accept: application/octet-stream`` and an
    auth token to retrieve the actual file payload.

    If *download_url* is already a REST API asset URL, it is returned
    as-is.  Non-GitHub URLs and GitHub URLs that are not release-download
    URLs return ``None``.  If the API lookup fails (e.g. network error or
    asset not found), ``None`` is returned so callers can fall back to the
    original URL.

    Args:
        download_url: The URL to resolve.
        open_url_fn: A callable compatible with
            ``specify_cli.authentication.http.open_url`` used to make the
            authenticated API request.
        timeout: Per-request timeout in seconds.

    Returns:
        The resolved REST API asset URL, or ``None`` if resolution is not
        applicable or fails.
    """
    import json
    import urllib.error

    parsed = urlparse(download_url)
    parts = [unquote(part) for part in parsed.path.strip("/").split("/")]

    # Already a REST API asset URL — use it directly
    if (
        parsed.hostname == "api.github.com"
        and len(parts) >= 6
        and parts[:1] == ["repos"]
        and parts[3:5] == ["releases", "assets"]
    ):
        return download_url

    # Only handle github.com browser release download URLs
    if parsed.hostname != "github.com":
        return None

    # Expecting /<owner>/<repo>/releases/download/<tag>/<asset>
    if len(parts) < 6 or parts[2:4] != ["releases", "download"]:
        return None

    owner, repo, tag = parts[0], parts[1], parts[4]
    asset_name = "/".join(parts[5:])
    encoded_tag = quote(tag, safe="")
    release_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{encoded_tag}"

    try:
        with open_url_fn(release_url, timeout=timeout) as response:
            release_data = json.loads(response.read())
    except (urllib.error.URLError, json.JSONDecodeError):
        return None

    for asset in release_data.get("assets", []):
        if asset.get("name") == asset_name and asset.get("url"):
            return str(asset["url"])

    return None
