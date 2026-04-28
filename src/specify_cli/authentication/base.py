"""Abstract base class for authentication providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AuthProvider(ABC):
    """Abstract base class every authentication provider must implement.

    Subclasses must set the following class-level attribute:

    * ``key`` — unique provider identifier (e.g. ``"github"``, ``"azure-devops"``)

    And implement the following methods:

    * ``get_token()``    — resolve credentials from env vars / config
    * ``auth_headers()`` — provider-specific auth headers
    """

    key: str = ""
    """Unique provider identifier."""

    @abstractmethod
    def get_token(self) -> str | None:
        """Resolve credentials from environment variables or config.

        Returns the token string if available, or ``None`` if not configured.
        Implementations must strip surrounding whitespace and treat a
        whitespace-only value as absent.
        """

    @abstractmethod
    def auth_headers(self) -> dict[str, str]:
        """Return provider-specific authentication headers.

        Returns an empty dict if no credentials are available.
        """

    def is_configured(self) -> bool:
        """Return ``True`` if credentials are available for this provider."""
        return self.get_token() is not None
