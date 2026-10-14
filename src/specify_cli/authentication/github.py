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
_GITHUB_SERVICE_PREFIXES = ("api.", "raw.", "codeload.")


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


class GitHubCliAuthError(RuntimeError):
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
            message = str(exc)
            self._github_cli_cache[credential_host] = (False, message)
            raise GitHubCliAuthError(message) from None

        self._github_cli_cache[credential_host] = (True, token)
        return token

    @staticmethod
    def _credential_hostname(entry: AuthConfigEntry) -> str:
        """Select the one GitHub CLI credential host represented by *entry*."""
        exact_hosts = {
            host.lower()
            for host in entry.hosts
            if "*" not in host
        }
        if exact_hosts & _GITHUB_PUBLIC_HOSTS:
            if any(host not in _GITHUB_PUBLIC_HOSTS for host in exact_hosts):
                raise GitHubCliAuthError(
                    "GitHub authentication failed for provider 'github': "
                    "a github-cli entry must describe one GitHub instance. "
                    "Use separate provider entries for github.com and GitHub Enterprise."
                )
            return "github.com"

        bare_hosts = {
            host
            for host in exact_hosts
            if not host.startswith(_GITHUB_SERVICE_PREFIXES)
        }
        if len(bare_hosts) != 1:
            raise GitHubCliAuthError(
                "GitHub authentication failed for provider 'github': "
                "a github-cli entry must list exactly one bare GitHub host."
            )
        return next(iter(bare_hosts))

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
        return token
