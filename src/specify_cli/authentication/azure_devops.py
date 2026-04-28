"""Azure DevOps authentication provider."""

from __future__ import annotations

import base64
import os

from .base import AuthProvider


class AzureDevOpsAuth(AuthProvider):
    """Azure DevOps authentication provider.

    Resolves credentials from ``AZURE_DEVOPS_PAT`` or ``ADO_TOKEN``
    environment variables, checking ``AZURE_DEVOPS_PAT`` first.

    Azure DevOps uses HTTP Basic Authentication with an empty username and the
    Personal Access Token (PAT) as the password.  The credentials are
    Base64-encoded in the form ``:<PAT>`` as required by the Azure DevOps REST
    API.
    """

    key = "azure-devops"

    def get_token(self) -> str | None:
        """Return the first non-empty PAT from AZURE_DEVOPS_PAT or ADO_TOKEN."""
        for env_var in ("AZURE_DEVOPS_PAT", "ADO_TOKEN"):
            candidate = os.environ.get(env_var)
            if candidate is not None:
                candidate = candidate.strip()
                if candidate:
                    return candidate
        return None

    def auth_headers(self) -> dict[str, str]:
        """Return Azure DevOps Basic auth headers, or an empty dict if not configured.

        Azure DevOps REST API requires Basic authentication where the password
        is the PAT and the username is left empty, encoded as ``:<PAT>`` in
        Base64.
        """
        token = self.get_token()
        if token:
            encoded = base64.b64encode(f":{token}".encode("ascii")).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        return {}
