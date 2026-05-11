"""Abstract base class for authentication providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import AuthConfigEntry


class AuthProvider(ABC):
    """Abstract base class every authentication provider must implement.

    Subclasses must set:

    * ``key`` — unique provider identifier (e.g. ``"github"``, ``"azure-devops"``)
    * ``supported_auth_schemes`` — tuple of auth scheme strings this provider handles

    And implement:

    * ``auth_headers(token, auth_scheme)`` — build headers from a resolved token
    * ``resolve_token(entry)`` — obtain the token for a config entry
    """

    key: str = ""
    """Unique provider identifier."""

    supported_auth_schemes: tuple[str, ...] = ()
    """Auth schemes this provider supports (e.g. ``("bearer",)``)."""

    @abstractmethod
    def auth_headers(self, token: str, auth_scheme: str) -> dict[str, str]:
        """Build authentication headers for *token* using *auth_scheme*.

        Must return a dict with at least an ``Authorization`` key.
        """

    def resolve_token(self, entry: AuthConfigEntry) -> str | None:
        """Resolve the token for *entry*.

        Default implementation reads from ``entry.token`` directly
        or from the environment variable named by ``entry.token_env``.
        Override for schemes that acquire tokens dynamically
        (e.g. ``azure-cli``, ``azure-ad``).
        """
        import os

        if entry.token:
            return entry.token.strip() or None
        if entry.token_env:
            val = os.environ.get(entry.token_env)
            if val is not None:
                val = val.strip()
                if val:
                    return val
        return None
