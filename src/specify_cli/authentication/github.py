"""GitHub authentication provider."""

from __future__ import annotations

import os

from .base import AuthProvider


class GitHubAuth(AuthProvider):
    """GitHub authentication provider.

    Resolves credentials from ``GH_TOKEN`` or ``GITHUB_TOKEN`` environment
    variables, checking ``GH_TOKEN`` first (matching the GitHub CLI convention
    and the existing ``_fetch_latest_release_tag()`` behaviour).
    """

    key = "github"

    def get_token(self) -> str | None:
        """Return the first non-empty token from GH_TOKEN or GITHUB_TOKEN."""
        for env_var in ("GH_TOKEN", "GITHUB_TOKEN"):
            candidate = os.environ.get(env_var)
            if candidate is not None:
                candidate = candidate.strip()
                if candidate:
                    return candidate
        return None

    def auth_headers(self) -> dict[str, str]:
        """Return GitHub Bearer token headers, or an empty dict if not configured."""
        token = self.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
