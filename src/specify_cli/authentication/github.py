"""GitHub authentication provider."""

from __future__ import annotations

import os
import shutil
import subprocess
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


class GitHubCliAuthError(RuntimeError):
    """Raised when GitHub CLI cannot provide a configured credential."""


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
        credential_host = (
            "github.com" if request_host in _GITHUB_PUBLIC_HOSTS else request_host
        )
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
    def _acquire_via_gh_cli(hostname: str) -> str:
        """Run the fixed GitHub CLI token command for *hostname*."""
        resolved = shutil.which("gh")
        if not resolved or not os.path.isabs(resolved):
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                "GitHub CLI ('gh') was not found."
            )

        argv = [resolved, "auth", "token"]
        if hostname != "github.com":
            argv.extend(["--hostname", hostname])

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
