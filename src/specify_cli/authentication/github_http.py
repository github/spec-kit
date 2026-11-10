"""GitHub-specific HTTP request helpers for the authentication domain.

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
from ipaddress import ip_address
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
_GHE_COM_SUFFIX = ".ghe.com"
_GHE_COM_API_PREFIX = "api."
_MAX_RELEASE_METADATA_BYTES = 5 * 1024 * 1024


def _has_valid_percent_escapes(value: str) -> bool:
    """Return whether every percent sign in *value* starts a percent escape."""
    hex_digits = "0123456789abcdefABCDEF"
    for index, character in enumerate(value):
        if character == "%" and (
            index + 2 >= len(value)
            or value[index + 1] not in hex_digits
            or value[index + 2] not in hex_digits
        ):
            return False
    return True


def _has_valid_asset_url_spelling(value: str) -> bool:
    """Return whether an asset URL uses an unambiguous raw spelling."""
    return (
        not any(
            ord(character) <= 0x20 or ord(character) == 0x7F
            for character in value
        )
        and not any(delimiter in value for delimiter in ("?", "#", ";"))
        and _has_valid_percent_escapes(value)
    )


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
        ValueError: If ``url`` includes a malformed explicit port.
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
    # Accessing ``port`` validates any explicit port before request construction.
    parsed.port
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


def _ghe_com_api_hostname(web_hostname: str) -> str | None:
    """Return the paired GHE.com API hostname for a tenant web hostname."""
    if (
        web_hostname == "ghe.com"
        or web_hostname.startswith(_GHE_COM_API_PREFIX)
        or not web_hostname.endswith(_GHE_COM_SUFFIX)
    ):
        return None
    return f"{_GHE_COM_API_PREFIX}{web_hostname}"


def _ghe_com_web_hostname(api_hostname: str) -> str | None:
    """Return the paired GHE.com web hostname for a tenant API hostname."""
    if not api_hostname.startswith(_GHE_COM_API_PREFIX):
        return None
    web_hostname = api_hostname.removeprefix(_GHE_COM_API_PREFIX)
    if web_hostname == "ghe.com" or not web_hostname.endswith(_GHE_COM_SUFFIX):
        return None
    return web_hostname


def resolve_github_release_asset_api_url(
    download_url: str,
    open_url_fn: Callable,
    timeout: int = 60,
    github_hosts: tuple[str, ...] = (),
    redirect_validator: Callable[[str, str], None] | None = None,
    max_metadata_bytes: int = _MAX_RELEASE_METADATA_BYTES,
) -> Optional[str]:
    """Resolve a GitHub release browser-download URL to its REST API asset URL.

    Works for public ``github.com``, GitHub Enterprise Cloud with data
    residency (GHE.com), and GitHub Enterprise Server (GHES). Enterprise hosts
    must match *github_hosts* (exact hostname or ``*.suffix``), which should be
    the hosts the user trusted under a ``github`` provider in ``auth.json``.
    GHE.com additionally requires both the tenant web hostname and its paired
    ``api.`` hostname to be trusted.

    Public GitHub uses ``https://api.github.com``; a GHE.com tenant
    ``tenant.ghe.com`` uses ``https://api.tenant.ghe.com``; GHES uses
    ``{scheme}://{host[:port]}/api/v3``. Returns the API asset URL
    (downloadable with ``Accept: application/octet-stream`` + a token), the
    input unchanged if it is already a recognized API asset URL, or ``None``
    when the URL is not a resolvable GitHub release download or the lookup
    fails.

    Args:
        download_url: The URL to resolve.
        open_url_fn: A callable compatible with
            :func:`specify_cli.authentication.http.open_url` used for the
            authenticated release-metadata lookup.
        timeout: Per-request timeout in seconds.
        github_hosts: Host patterns trusted as GitHub Enterprise deployments.
        redirect_validator: Optional policy applied to metadata redirects.
        max_metadata_bytes: Maximum release-metadata response size.
    """
    import json
    import urllib.error

    from .._download_security import read_response_limited

    # Accessing ``.hostname`` (like ``.port`` below) raises ValueError on a
    # malformed authority, e.g. an invalid bracketed IPv6 host
    # ``https://[not-an-ip]/...``. The function's contract is to return None for
    # anything it can't resolve, not to raise, so guard the read. ``download_url``
    # is server-controlled here (a catalog ``download_url`` payload), so a
    # malformed value must not leak a raw traceback past the caller.
    try:
        parsed = urlparse(download_url)
        hostname = (parsed.hostname or "").lower()
        parsed_port = parsed.port
    except ValueError:
        return None
    parts = [unquote(part) for part in parsed.path.strip("/").split("/")]

    ghe_com_api_hostname = _ghe_com_api_hostname(hostname)
    is_ghe_com = (
        ghe_com_api_hostname is not None
        and parsed.scheme == "https"
        and parsed_port in (None, 443)
        and _host_matches(hostname, github_hosts)
        and _host_matches(ghe_com_api_hostname, github_hosts)
    )
    is_ghes = (
        bool(hostname)
        and hostname not in GITHUB_HOSTS
        and not hostname.endswith(_GHE_COM_SUFFIX)
        and _host_matches(hostname, github_hosts)
    )

    def _is_asset_path(segments: list[str]) -> bool:
        return (
            len(segments) >= 6
            and segments[:1] == ["repos"]
            and segments[3:5] == ["releases", "assets"]
        )

    def _is_exact_raw_asset_path(path: str) -> bool:
        segments = path.split("/")
        return (
            len(segments) == 7
            and segments[:2] == ["", "repos"]
            and bool(segments[2])
            and bool(segments[3])
            and segments[4:6] == ["releases", "assets"]
            and segments[-1].isascii()
            and segments[-1].isdigit()
        )

    # Already a REST API asset URL — use it directly. Existing GitHub.com and
    # GHES passthrough behavior remains path-gated because it induces no new
    # request; the caller would fetch the same URL regardless. GHE.com is new
    # here and uses its stricter tenant-pair trust check below.
    if hostname == "api.github.com" and _is_asset_path(parts):
        return download_url
    if (
        hostname
        and not hostname.endswith(_GHE_COM_SUFFIX)
        and parts[:2] == ["api", "v3"]
        and _is_asset_path(parts[2:])
    ):
        return download_url
    ghe_com_web_hostname = _ghe_com_web_hostname(hostname)
    if (
        ghe_com_web_hostname is not None
        and _has_valid_asset_url_spelling(download_url)
        and parsed.scheme == "https"
        and parsed_port in (None, 443)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and not parsed.params
        and _host_matches(hostname, github_hosts)
        and _host_matches(ghe_com_web_hostname, github_hosts)
        and _is_exact_raw_asset_path(parsed.path)
    ):
        return download_url

    # Browser download URLs must be usable HTTP(S) URLs before they can cause
    # a metadata request. Direct API-asset passthrough above intentionally
    # retains its existing path-only behavior.
    if parsed.scheme not in {"http", "https"}:
        return None

    # Determine the REST API base for browser release-download URLs.
    if hostname == "github.com":
        api_base = "https://api.github.com"
        expected_asset_prefix = ["", "repos"]
    elif is_ghe_com:
        api_base = f"https://{ghe_com_api_hostname}"
        expected_asset_prefix = ["", "repos"]
    elif is_ghes:
        # ``urlparse().hostname`` removes IPv6 brackets. Restore them when
        # constructing an authority so the derived API base remains a URL.
        authority_host = f"[{hostname}]" if ":" in hostname else hostname
        authority = (
            authority_host if parsed_port is None else f"{authority_host}:{parsed_port}"
        )
        api_base = f"{parsed.scheme}://{authority}/api/v3"
        expected_asset_prefix = ["", "api", "v3", "repos"]
    else:
        return None

    # Expecting /<owner>/<repo>/releases/download/<tag>/<asset>
    if len(parts) < 6 or parts[2:4] != ["releases", "download"]:
        return None

    owner, repo = parts[0], parts[1]
    tag = "/".join(parts[4:-1])
    asset_name = parts[-1]
    encoded_tag = quote(tag, safe="")
    release_url = f"{api_base}/repos/{owner}/{repo}/releases/tags/{encoded_tag}"

    def _is_expected_asset_url(asset_url: object) -> bool:
        """Return whether metadata names this release's exact API asset endpoint."""
        if not isinstance(asset_url, str):
            return False
        # ``urlparse`` tolerates some raw spellings (for example whitespace)
        # even though the original metadata value is returned to the caller.
        # Reject those spellings before parsing rather than normalizing them.
        if not _has_valid_asset_url_spelling(asset_url):
            return False
        try:
            asset_parsed = urlparse(asset_url)
            asset_host = asset_parsed.hostname
            asset_port = asset_parsed.port
            api_parsed = urlparse(api_base)
            api_host = api_parsed.hostname
            api_port = api_parsed.port
        except ValueError:
            return False

        if (
            asset_parsed.scheme not in {"http", "https"}
            or not asset_host
            or asset_parsed.username is not None
            or asset_parsed.password is not None
            or asset_parsed.query
            or asset_parsed.fragment
            or asset_parsed.params
        ):
            return False

        def _origin(parsed_url, host: str, port: int | None) -> tuple[str, str, int]:
            default_port = 443 if parsed_url.scheme == "https" else 80
            try:
                normalized_host = ip_address(host).compressed
            except ValueError:
                normalized_host = host.lower()
            return (
                parsed_url.scheme,
                normalized_host,
                default_port if port is None else port,
            )

        if _origin(asset_parsed, asset_host, asset_port) != _origin(
            api_parsed, api_host or "", api_port
        ):
            return False

        asset_parts = asset_parsed.path.split("/")
        owner_index = len(expected_asset_prefix)
        return (
            len(asset_parts) == owner_index + 5
            and asset_parts[:owner_index] == expected_asset_prefix
            and unquote(asset_parts[owner_index]).casefold() == owner.casefold()
            and unquote(asset_parts[owner_index + 1]).casefold() == repo.casefold()
            and asset_parts[owner_index + 2:owner_index + 4] == ["releases", "assets"]
            and asset_parts[-1].isascii()
            and asset_parts[-1].isdigit()
        )

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
        if isinstance(asset, dict) and asset.get("name") == asset_name:
            asset_url = asset.get("url")
            if _is_expected_asset_url(asset_url):
                return asset_url

    return None
