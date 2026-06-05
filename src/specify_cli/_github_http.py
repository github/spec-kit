"""Shared GitHub-authenticated HTTP helpers.

Used by both ExtensionCatalog and PresetCatalog to attach
GITHUB_TOKEN / GH_TOKEN credentials to requests targeting
GitHub-hosted domains, while preventing token leakage to
third-party hosts on redirects.
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
