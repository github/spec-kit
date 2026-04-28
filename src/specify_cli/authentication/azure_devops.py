"""Azure DevOps authentication provider."""

from __future__ import annotations

import base64
import json as _json
import os
import subprocess
from typing import TYPE_CHECKING

from .base import AuthProvider

if TYPE_CHECKING:
    from .config import AuthConfigEntry

# Azure DevOps resource ID for OAuth / Azure AD token acquisition.
_ADO_RESOURCE_ID = "499b84ac-1321-427f-aa17-267ca6975798"


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
            token = payload.get("accessToken", "").strip()
            return token or None
        except (OSError, _json.JSONDecodeError, KeyError):
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
        body = (
            f"grant_type=client_credentials"
            f"&client_id={entry.client_id}"
            f"&client_secret={client_secret}"
            f"&scope={_ADO_RESOURCE_ID}/.default"
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                payload = _json.loads(resp.read().decode("utf-8"))
                token = payload.get("access_token", "").strip()
                return token or None
        except (urllib.error.URLError, OSError, _json.JSONDecodeError, KeyError):
            return None
