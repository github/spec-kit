"""Bitbucket authentication provider."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from .base import AuthProvider

if TYPE_CHECKING:
    from .config import AuthConfigEntry


class BitbucketAuth(AuthProvider):
    """Bitbucket authentication provider (Cloud and Data Center).

    Supports two auth schemes:

    * ``bearer`` — repository/project/workspace access tokens (Bitbucket
      Cloud) and HTTP access tokens (Bitbucket Data Center)
    * ``basic`` — username + secret, Base64-encoded as
      ``<username>:<secret>``. Used for Atlassian API tokens (username is
      the Atlassian account email).

    For the ``basic`` scheme the config entry's ``username`` field is
    required: :meth:`resolve_token` returns the combined
    ``<username>:<secret>`` credential, which :meth:`auth_headers` encodes
    verbatim. This keeps the ``AuthProvider`` interface unchanged (a single
    resolved token string flows from ``resolve_token`` to ``auth_headers``).
    """

    key = "bitbucket"
    supported_auth_schemes = ("bearer", "basic")

    def auth_headers(self, token: str, auth_scheme: str) -> dict[str, str]:
        """Build the ``Authorization`` header for the given scheme.

        For ``basic``, *token* must already be the full
        ``<username>:<secret>`` credential produced by :meth:`resolve_token`.
        """
        if auth_scheme == "bearer":
            return {"Authorization": f"Bearer {token}"}
        if auth_scheme == "basic":
            # Guard the internal contract: a bare secret here would silently
            # produce a well-formed header with an empty username and a 401.
            if ":" not in token:
                raise ValueError(
                    "BitbucketAuth 'basic' expects a '<username>:<secret>' "
                    "credential as produced by resolve_token()"
                )
            encoded = base64.b64encode(token.encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        raise ValueError(
            f"BitbucketAuth does not support auth scheme {auth_scheme!r}"
        )

    def resolve_token(self, entry: AuthConfigEntry) -> str | None:
        """Resolve the credential, combining ``username`` for ``basic``.

        Returns ``None`` when the secret is missing, or — for ``basic`` —
        when ``username`` is absent (config validation enforces it, but
        directly-constructed entries must not produce a malformed
        ``:<secret>`` credential).
        """
        secret = super().resolve_token(entry)
        if entry.auth != "basic":
            return secret
        username = (entry.username or "").strip()
        if not secret or not username:
            return None
        return f"{username}:{secret}"
