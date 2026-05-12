"""GitHub API helpers used by :func:`infrakit_cli.cli.version` to look up the
latest released CLI version.

These helpers used to drive the per-agent template-zip download flow as well,
which has since been removed in favour of bundling templates inside the wheel.
The version check is the only remaining caller.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import httpx

# httpx client + SSL context shared by anyone calling the GitHub API.
# ``verify=True`` uses the system trust store via the ``truststore`` package
# (installed as a dependency); this is the right default for corporate
# environments with custom certificate authorities.
ssl_context = True
client = httpx.Client(verify=ssl_context)


def _github_token(cli_token: Optional[str] = None) -> Optional[str]:
    """Return a sanitised GitHub token, or ``None`` if no token is configured.

    Resolution order: the explicit ``cli_token`` argument wins over the
    ``GH_TOKEN`` environment variable, which in turn wins over ``GITHUB_TOKEN``.
    Whitespace is stripped; empty strings become ``None``.
    """
    return (
        (cli_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()
    ) or None


def _github_auth_headers(cli_token: Optional[str] = None) -> dict:
    """Return ``{"Authorization": "Bearer <token>"}`` if a token is available.

    When no token is available, returns ``{}`` so the caller's request goes out
    unauthenticated (subject to GitHub's low anonymous rate limit).
    """
    token = _github_token(cli_token)
    return {"Authorization": f"Bearer {token}"} if token else {}


def _parse_rate_limit_headers(headers: httpx.Headers) -> dict:
    """Extract GitHub rate-limit headers into a typed dict for diagnostics."""
    info = {}

    if "X-RateLimit-Limit" in headers:
        info["limit"] = headers.get("X-RateLimit-Limit")
    if "X-RateLimit-Remaining" in headers:
        info["remaining"] = headers.get("X-RateLimit-Remaining")
    if "X-RateLimit-Reset" in headers:
        reset_epoch = int(headers.get("X-RateLimit-Reset", "0"))
        if reset_epoch:
            reset_time = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
            info["reset_epoch"] = reset_epoch
            info["reset_time"] = reset_time
            info["reset_local"] = reset_time.astimezone()

    if "Retry-After" in headers:
        retry_after = headers.get("Retry-After")
        try:
            info["retry_after_seconds"] = int(retry_after)
        except ValueError:
            info["retry_after"] = retry_after

    return info


def _format_rate_limit_error(status_code: int, headers: httpx.Headers, url: str) -> str:
    """Format a user-friendly multi-line error message for rate-limited responses."""
    rate_info = _parse_rate_limit_headers(headers)

    lines = [f"GitHub API returned status {status_code} for {url}", ""]

    if rate_info:
        lines.append("[bold]Rate Limit Information:[/bold]")
        if "limit" in rate_info:
            lines.append(f"  • Rate Limit: {rate_info['limit']} requests/hour")
        if "remaining" in rate_info:
            lines.append(f"  • Remaining: {rate_info['remaining']}")
        if "reset_local" in rate_info:
            reset_str = rate_info["reset_local"].strftime("%Y-%m-%d %H:%M:%S %Z")
            lines.append(f"  • Resets at: {reset_str}")
        if "retry_after_seconds" in rate_info:
            lines.append(f"  • Retry after: {rate_info['retry_after_seconds']} seconds")
        lines.append("")

    lines.append("[bold]Troubleshooting Tips:[/bold]")
    lines.append(
        "  • If you're on a shared CI or corporate environment, you may be rate-limited."
    )
    lines.append(
        "  • Consider using a GitHub token via the GH_TOKEN/GITHUB_TOKEN environment variable"
    )
    lines.append("    to increase rate limits.")
    lines.append(
        "  • Authenticated requests have a limit of 5,000/hour vs 60/hour for unauthenticated."
    )

    return "\n".join(lines)
