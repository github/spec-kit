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
from fnmatch import fnmatch
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
_MAX_RELEASE_METADATA_BYTES = 5 * 1024 * 1024


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


def _host_matches(hostname: str, patterns: tuple[str, ...]) -> bool:
    """Return True when *hostname* matches a pattern (exact or ``*.suffix``)."""
    hostname = hostname.lower()
    return any(p == hostname or fnmatch(hostname, p) for p in patterns)


def resolve_github_release_asset_api_url(
    download_url: str,
    open_url_fn: Callable,
    timeout: int = 60,
    github_hosts: tuple[str, ...] = (),
    redirect_validator: Callable[[str, str], None] | None = None,
    max_metadata_bytes: int = _MAX_RELEASE_METADATA_BYTES,
) -> Optional[str]:
    """Resolve a GitHub release browser-download URL to its REST API asset URL.

    Works for public ``github.com`` and for GitHub Enterprise Server (GHES)
    hosts. A host is treated as GHES when it matches one of *github_hosts*
    (exact hostname or ``*.suffix``) — supply the hosts the user has trusted
    under a ``github`` provider in ``auth.json``. This allowlist is the
    security gate: unlisted hosts never receive GHES API treatment, so a
    malicious catalog cannot induce an API request to an arbitrary host.

    For a public URL the API base is ``https://api.github.com``; for a GHES
    host it is ``{scheme}://{host[:port]}/api/v3``. Returns the API asset URL
    (downloadable with ``Accept: application/octet-stream`` + a token), the
    input unchanged if it is already an API asset URL, or ``None`` when the
    URL is not a resolvable GitHub release download or the lookup fails.

    Args:
        download_url: The URL to resolve.
        open_url_fn: A callable compatible with
            ``specify_cli.authentication.http.open_url`` used for the
            authenticated release-metadata lookup.
        timeout: Per-request timeout in seconds.
        github_hosts: Host patterns to treat as GitHub Enterprise Server.
        redirect_validator: Optional policy applied to metadata redirects.
        max_metadata_bytes: Maximum release-metadata response size.
    """
    import json
    import urllib.error

    from specify_cli._download_security import read_response_limited

    parsed = urlparse(download_url)
    hostname = (parsed.hostname or "").lower()
    parts = [unquote(part) for part in parsed.path.strip("/").split("/")]

    is_ghes = (
        bool(hostname)
        and hostname not in GITHUB_HOSTS
        and _host_matches(hostname, github_hosts)
    )

    def _is_asset_path(segments: list[str]) -> bool:
        return (
            len(segments) >= 6
            and segments[:1] == ["repos"]
            and segments[3:5] == ["releases", "assets"]
        )

    # Already a REST API asset URL — use it directly. Pure passthrough induces
    # no new request: the caller fetches this same URL regardless, so it is
    # gated on path shape alone rather than the GHES allowlist. The token stays
    # independently gated by auth.json in the download helper, and only the
    # resolving path below (which issues a tag-lookup request) needs the
    # allowlist as its anti-SSRF gate.
    if hostname == "api.github.com" and _is_asset_path(parts):
        return download_url
    if hostname and parts[:2] == ["api", "v3"] and _is_asset_path(parts[2:]):
        return download_url

    # Determine the REST API base for browser release-download URLs.
    if hostname == "github.com":
        api_base = "https://api.github.com"
    elif is_ghes:
        # ``parsed.port`` raises ValueError on a malformed port (e.g.
        # ``host:notaport``); the function's contract is to return None for
        # anything it can't resolve, not to raise.
        try:
            port = parsed.port
        except ValueError:
            return None
        authority = hostname if port is None else f"{hostname}:{port}"
        api_base = f"{parsed.scheme}://{authority}/api/v3"
    else:
        return None

    # Expecting /<owner>/<repo>/releases/download/<tag>/<asset>
    if len(parts) < 6 or parts[2:4] != ["releases", "download"]:
        return None

    owner, repo, tag = parts[0], parts[1], parts[4]
    asset_name = "/".join(parts[5:])
    encoded_tag = quote(tag, safe="")
    release_url = f"{api_base}/repos/{owner}/{repo}/releases/tags/{encoded_tag}"

    try:
        open_kwargs = {"timeout": timeout}
        if redirect_validator is not None:
            open_kwargs["redirect_validator"] = redirect_validator
        with open_url_fn(release_url, **open_kwargs) as response:
            release_data = json.loads(
                read_response_limited(
                    response,
                    max_bytes=max_metadata_bytes,
                    label=f"GitHub release metadata {release_url}",
                )
            )
    except (
        urllib.error.URLError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return None

    if not isinstance(release_data, dict):
        return None
    assets = release_data.get("assets", [])
    if not isinstance(assets, list):
        return None
    for asset in assets:
        if (
            isinstance(asset, dict)
            and asset.get("name") == asset_name
            and asset.get("url")
        ):
            return str(asset["url"])

    return None
