"""Azure DevOps authentication provider."""

from __future__ import annotations

import base64
import json as _json
import os
import subprocess
from typing import TYPE_CHECKING

from .._download_security import MAX_JSON_METADATA_BYTES, read_response_limited
from .base import AuthProvider

if TYPE_CHECKING:
    from .config import AuthConfigEntry

# Azure DevOps resource ID for OAuth / Azure AD token acquisition.
_ADO_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798"


class _TokenResponseTooLarge(Exception):
    """Raised when an Azure AD token response exceeds the bounded read limit."""


def _extract_token(payload: object, key: str) -> str | None:
    """Return a normalized token from a JSON object, or None for other shapes."""
    if not isinstance(payload, dict):
        return None
    token = payload.get(key)
    if not isinstance(token, str):
        return None
    return token.strip() or None


class AzureDevOpsAuth(AuthProvider):
    """Azure DevOps authentication provider.

    Supports four auth schemes:

    * ``basic-pat`` — PAT with empty username, Base64-encoded as ``:<PAT>``
    * ``bearer`` — pre-acquired OAuth / Azure AD token
    * ``azure-cli`` — acquires a token via ``az account get-access-token``
    * ``azure-ad`` — acquires a token via OAuth2 client credentials flow
    """

    key = "azure-devops"
    supported_auth_schemes = ("basic-pat", "bearer", "azure-cli", "azure-ad")

    def auth_headers(self, token: str, auth_scheme: str) -> dict[str, str]:
        """Build the ``Authorization`` header for the given scheme."""
        if auth_scheme == "basic-pat":
            encoded = base64.b64encode(f":{token}".encode("ascii")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        if auth_scheme in ("bearer", "azure-cli", "azure-ad"):
            return {"Authorization": f"Bearer {token}"}
        raise ValueError(
            f"AzureDevOpsAuth does not support auth scheme {auth_scheme!r}"
        )

    def resolve_token(self, entry: AuthConfigEntry) -> str | None:
        """Resolve token, with special handling for azure-cli and azure-ad."""
        if entry.auth == "azure-cli":
            return self._acquire_via_az_cli()
        if entry.auth == "azure-ad":
            return self._acquire_via_client_credentials(entry)
        return super().resolve_token(entry)

    # -- Token acquisition ------------------------------------------------

    @staticmethod
    def _acquire_via_az_cli() -> str | None:
        """Run ``az account get-access-token`` and return the access token."""
        try:
            result = subprocess.run(  # noqa: S603, S607
                [
                    "az",
                    "account",
                    "get-access-token",
                    "--resource",
                    _ADO_RESOURCE_ID,
                    "--output",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                return None
            payload = _json.loads(result.stdout)
            return _extract_token(payload, "accessToken")
        except (
            OSError,
            subprocess.TimeoutExpired,
            _json.JSONDecodeError,
            UnicodeDecodeError,
            KeyError,
        ):
            # UnicodeDecodeError: text=True decodes az stdout with the locale
            # encoding, which raises (not a JSONDecodeError) if the output isn't
            # decodable — this helper's contract is to return None on any
            # failure, never to propagate.
            return None

    @staticmethod
    def _acquire_via_client_credentials(entry: AuthConfigEntry) -> str | None:
        """Acquire a token via OAuth2 client credentials flow."""
        import urllib.error
        import urllib.request

        if not entry.tenant_id or not entry.client_id or not entry.client_secret_env:
            return None
        client_secret = os.environ.get(entry.client_secret_env, "").strip()
        if not client_secret:
            return None

        url = (
            f"https://login.microsoftonline.com/{entry.tenant_id}"
            "/oauth2/v2.0/token"
        )
        from urllib.parse import urlencode
        body = urlencode({
            "grant_type": "client_credentials",
            "client_id": entry.client_id,
            "client_secret": client_secret,
            "scope": f"{_ADO_RESOURCE_ID}/.default",
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            from specify_cli.authentication.http import _StripAuthOnRedirect

            def reject_token_redirect(_old_url: str, new_url: str) -> None:
                # A 307/308 redirect preserves this POST body, including the
                # client_secret. Refuse every redirect so credentials cannot
                # leave the fixed Microsoft token endpoint.
                raise urllib.error.URLError(
                    f"Azure AD token request must not be redirected to {new_url}"
                )

            opener = urllib.request.build_opener(
                _StripAuthOnRedirect((), reject_token_redirect)
            )
            with opener.open(req, timeout=30) as resp:  # noqa: S310
                payload = _json.loads(
                    read_response_limited(
                        resp,
                        max_bytes=MAX_JSON_METADATA_BYTES,
                        error_type=_TokenResponseTooLarge,
                        label="Azure DevOps token response",
                    ).decode("utf-8")
                )
                return _extract_token(payload, "access_token")
        except (
            urllib.error.URLError,
            OSError,
            _json.JSONDecodeError,
            UnicodeDecodeError,
            _TokenResponseTooLarge,
        ):
            # Network failure, malformed JSON, or an oversized response — fall
            # through to the next strategy. Unrelated programming errors (other
            # ValueErrors, KeyErrors) intentionally propagate so they surface.
            return None
