"""GitHub authentication provider."""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.error
from typing import TYPE_CHECKING

from .base import AuthProvider

if TYPE_CHECKING:
    from .config import AuthConfigEntry


_GITHUB_CLI_TIMEOUT_SECONDS = 10
_GITHUB_PUBLIC_HOSTS = frozenset({
    "github.com",
    "api.github.com",
    "raw.githubusercontent.com",
    "codeload.github.com",
})
_GITHUB_ENTERPRISE_SERVICE_PREFIXES = ("api.", "raw.", "codeload.")


class GitHubCliAuthError(urllib.error.URLError):
    """Raised when GitHub CLI cannot provide a configured credential."""

    def __str__(self) -> str:
        """Return the sanitized reason without URLError's wrapper."""
        return str(self.reason)


class GitHubAuth(AuthProvider):
    """GitHub authentication provider.

    Supports ``bearer`` for PATs, OAuth tokens, and GitHub App installation
    tokens, plus ``github-cli`` for credentials managed by GitHub CLI.
    """

    key = "github"
    supported_auth_schemes = ("bearer", "github-cli")

    def __init__(self) -> None:
        self._github_cli_cache: dict[str, tuple[bool, str]] = {}

    def auth_headers(self, token: str, auth_scheme: str) -> dict[str, str]:
        """Return ``Authorization: Bearer <token>``."""
        if auth_scheme not in self.supported_auth_schemes:
            raise ValueError(
                f"GitHubAuth does not support auth scheme {auth_scheme!r}"
            )
        return {"Authorization": f"Bearer {token}"}

    def resolve_token(
        self,
        entry: AuthConfigEntry,
        hostname: str | None = None,
    ) -> str | None:
        """Resolve configured tokens or acquire one from GitHub CLI."""
        if entry.auth != "github-cli":
            return super().resolve_token(entry, hostname)

        request_host = (hostname or entry.hosts[0]).lower()
        credential_host = self._credential_hostname(entry, request_host)
        cached = self._github_cli_cache.get(credential_host)
        if cached is not None:
            succeeded, value = cached
            if succeeded:
                return value
            raise GitHubCliAuthError(value)

        try:
            token = self._acquire_via_gh_cli(credential_host)
        except GitHubCliAuthError as exc:
            message = str(exc)
            self._github_cli_cache[credential_host] = (False, message)
            raise GitHubCliAuthError(message) from None

        self._github_cli_cache[credential_host] = (True, token)
        return token

    @staticmethod
    def _credential_hostname(entry: AuthConfigEntry, request_host: str) -> str:
        """Map a request host to the GitHub CLI login host."""
        if request_host in _GITHUB_PUBLIC_HOSTS:
            return "github.com"

        exact_hosts = {
            configured_host.lower()
            for configured_host in entry.hosts
            if "*" not in configured_host
        }
        for prefix in _GITHUB_ENTERPRISE_SERVICE_PREFIXES:
            if request_host.startswith(prefix):
                instance_host = request_host.removeprefix(prefix)
                if instance_host in exact_hosts:
                    return instance_host
        return request_host

    @staticmethod
    def _acquire_via_gh_cli(hostname: str) -> str:
        """Run the fixed GitHub CLI token command for *hostname*."""
        resolved = shutil.which("gh")
        if not resolved or not os.path.isabs(resolved):
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                "GitHub CLI ('gh') was not found."
            )

        argv = [resolved, "auth", "token", "--hostname", hostname]

        try:
            result = subprocess.run(  # noqa: S603
                argv,
                capture_output=True,
                text=True,
                timeout=_GITHUB_CLI_TIMEOUT_SECONDS,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                f"GitHub CLI timed out while requesting a token for {hostname!r}."
            ) from None
        except (OSError, UnicodeDecodeError):
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                f"GitHub CLI could not provide a token for {hostname!r}."
            ) from None

        if result.returncode != 0:
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                f"GitHub CLI could not provide a token for {hostname!r}. "
                f"Run 'gh auth login --hostname {hostname}'."
            )

        token = result.stdout.strip()
        if not token:
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                f"GitHub CLI returned an empty token for {hostname!r}. "
                f"Run 'gh auth login --hostname {hostname}'."
            )
        return token
