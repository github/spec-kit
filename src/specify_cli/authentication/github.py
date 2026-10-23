"""GitHub authentication provider."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import TYPE_CHECKING
from urllib.error import URLError

from .base import AuthProvider

if TYPE_CHECKING:
    from .config import AuthConfigEntry


_GITHUB_CLI_TIMEOUT_SECONDS = 10


def _is_safe_cli_hostname(hostname: str) -> bool:
    """Return whether *hostname* is a shell-safe DNS hostname."""
    if not hostname or len(hostname) > 253 or not hostname.isascii():
        return False
    labels = hostname.split(".")
    return all(
        0 < len(label) <= 63
        and label[0].isalnum()
        and label[-1].isalnum()
        and all(char.isalnum() or char == "-" for char in label)
        for label in labels
    )


class GitHubCliAuthError(URLError):
    """Raised when GitHub CLI cannot provide a configured credential."""


class GitHubAuth(AuthProvider):
    """GitHub authentication provider."""

    key = "github"
    supported_auth_schemes = ("bearer", "github-cli")

    def __init__(self) -> None:
        self._github_cli_cache: dict[str, tuple[bool, str]] = {}

    def auth_headers(self, token: str, auth_scheme: str) -> dict[str, str]:
        """Return a bearer authorization header."""
        if auth_scheme not in self.supported_auth_schemes:
            raise ValueError(
                f"GitHubAuth does not support auth scheme {auth_scheme!r}"
            )
        return {"Authorization": "Bearer " + token}

    def resolve_token(self, entry: AuthConfigEntry) -> str | None:
        """Resolve a configured token or acquire one from GitHub CLI."""
        if entry.auth != "github-cli":
            return super().resolve_token(entry)

        credential_host = self._credential_hostname(entry)
        cached = self._github_cli_cache.get(credential_host)
        if cached is not None:
            succeeded, value = cached
            if succeeded:
                return value
            raise GitHubCliAuthError(value)

        try:
            token = self._acquire_via_gh_cli(credential_host)
        except GitHubCliAuthError as exc:
            message = str(exc.reason)
            self._github_cli_cache[credential_host] = (False, message)
            raise GitHubCliAuthError(message) from None

        self._github_cli_cache[credential_host] = (True, token)
        return token

    @staticmethod
    def _credential_hostname(entry: AuthConfigEntry) -> str:
        """Use the first configured host for GitHub CLI credential acquisition."""
        hostname = entry.hosts[0]
        if "*" in hostname:
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                "the first hostname in a github-cli entry must be an exact "
                "hostname, not a wildcard."
            )
        return hostname

    @staticmethod
    def _acquire_via_gh_cli(hostname: str) -> str:
        """Run the fixed GitHub CLI token command for *hostname*."""
        if not _is_safe_cli_hostname(hostname):
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                "the configured hostname is not valid for GitHub CLI authentication."
            )

        resolved = shutil.which("gh")
        if not resolved or not os.path.isabs(resolved):
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                "GitHub CLI ('gh') was not found."
            )

        try:
            result = subprocess.run(  # noqa: S603
                [resolved, "auth", "token", "--hostname", hostname],
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
        if "\r" in token or "\n" in token:
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                f"GitHub CLI returned a malformed token for {hostname!r}."
            )
        return token
