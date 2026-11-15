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
            # Guard the internal contract: both halves must be present. A bare
            # secret, ":<secret>", or "<username>:" would otherwise become a
            # well-formed header with an empty user or secret and a 401.
            # partition() splits on the first colon only, so a secret that
            # itself contains ':' is preserved intact.
            username, sep, secret = token.partition(":")
            if not sep or not username or not secret:
                raise ValueError(
                    "BitbucketAuth 'basic' expects a '<username>:<secret>' "
                    "credential with both parts non-empty, as produced by "
                    "resolve_token()"
                )
            encoded = base64.b64encode(token.encode("utf-8")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        raise ValueError(
            f"BitbucketAuth does not support auth scheme {auth_scheme!r}"
        )

    def resolve_token(self, entry: AuthConfigEntry) -> str | None:
        """Resolve the credential, combining ``username`` for ``basic``.

        Returns ``None`` when the secret is missing, or — for ``basic`` —
        when ``username`` is absent or contains ``:``. Config validation
        already enforces both for ``auth.json`` entries, but a
        directly-constructed entry must not produce a malformed
        ``:<secret>`` credential or a ``user:name:<secret>`` one that the
        server would parse as user ``user`` (RFC 7617 §2).
        """
        secret = super().resolve_token(entry)
        if entry.auth != "basic":
            return secret
        username = (entry.username or "").strip()
        if not secret or not username or ":" in username:
            return None
        return f"{username}:{secret}"
