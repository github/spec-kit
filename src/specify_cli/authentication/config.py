"""Authentication configuration loader.

Reads ``~/.specify/auth.json`` to determine which hosts receive credentials
and which provider/auth-scheme to use.  No credentials are sent without
an explicit opt-in via this file.
"""

from __future__ import annotations

import json
import stat
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class AuthConfigEntry:
    """A single provider entry from ``auth.json``."""

    hosts: tuple[str, ...]
    provider: str
    auth: str
    token: str | None = None
    token_env: str | None = None
    # Azure AD service-principal fields
    tenant_id: str | None = None
    client_id: str | None = None
    client_secret_env: str | None = None


_VALID_AUTH_SCHEMES = frozenset({
    "bearer",
    "basic-pat",
    "azure-cli",
    "azure-ad",
})


def _default_config_path() -> Path:
    """Return ``~/.specify/auth.json``."""
    return Path.home() / ".specify" / "auth.json"


def load_auth_config(
    path: Path | None = None,
) -> list[AuthConfigEntry]:
    """Load and validate ``auth.json``, returning configured entries.

    Returns an empty list when the file does not exist — this means
    all HTTP requests will be unauthenticated (opt-in model).

    Raises ``ValueError`` on schema violations so misconfigurations
    surface immediately rather than silently degrading to no-auth.
    """
    config_path = path or _default_config_path()

    if not config_path.is_file():
        return []

    # Warn (but don't fail) if the file is world-readable.
    try:
        mode = config_path.stat().st_mode
        if mode & (stat.S_IRGRP | stat.S_IROTH):
            import warnings

            warnings.warn(
                f"{config_path} is readable by group/others. "
                "Consider restricting with: chmod 600 "
                f"{config_path}",
                UserWarning,
                stacklevel=2,
            )
    except OSError:
        pass  # stat failed — skip permission check

    raw = json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError(f"auth.json must be a JSON object, got {type(raw).__name__}")

    providers_raw = raw.get("providers")
    if not isinstance(providers_raw, list):
        raise ValueError("auth.json must contain a 'providers' array")

    entries: list[AuthConfigEntry] = []
    for i, entry_raw in enumerate(providers_raw):
        if not isinstance(entry_raw, dict):
            raise ValueError(f"providers[{i}]: must be a JSON object")

        hosts = entry_raw.get("hosts")
        if not isinstance(hosts, list) or not hosts:
            raise ValueError(f"providers[{i}]: 'hosts' must be a non-empty array")
        if not all(isinstance(h, str) and h.strip() for h in hosts):
            raise ValueError(f"providers[{i}]: each host must be a non-empty string")
        # Normalize hosts: strip whitespace and lowercase
        hosts = [h.strip().lower() for h in hosts]

        provider = entry_raw.get("provider", "")
        if not isinstance(provider, str) or not provider:
            raise ValueError(f"providers[{i}]: 'provider' must be a non-empty string")

        auth = entry_raw.get("auth", "")
        if not isinstance(auth, str) or not auth:
            raise ValueError(f"providers[{i}]: 'auth' must be a non-empty string")
        if auth not in _VALID_AUTH_SCHEMES:
            raise ValueError(
                f"providers[{i}]: unsupported auth scheme {auth!r}; "
                f"valid: {sorted(_VALID_AUTH_SCHEMES)}"
            )

        token = entry_raw.get("token")
        token_env = entry_raw.get("token_env")

        # Validate token/token_env types
        if token is not None and (not isinstance(token, str) or not token.strip()):
            raise ValueError(f"providers[{i}]: 'token' must be a non-empty string")
        if token_env is not None and (not isinstance(token_env, str) or not token_env.strip()):
            raise ValueError(f"providers[{i}]: 'token_env' must be a non-empty string")

        # Validate provider+scheme compatibility
        from . import get_provider as _get_provider
        _prov = _get_provider(provider)
        if _prov is None:
            from . import AUTH_REGISTRY
            raise ValueError(
                f"providers[{i}]: unknown provider {provider!r}; "
                f"registered: {sorted(AUTH_REGISTRY.keys())}"
            )
        if auth not in _prov.supported_auth_schemes:
            raise ValueError(
                f"providers[{i}]: provider {provider!r} does not support "
                f"auth scheme {auth!r}; supported: {list(_prov.supported_auth_schemes)}"
            )

        # Validate token source based on auth scheme
        if auth in ("bearer", "basic-pat"):
            if not token and not token_env:
                raise ValueError(
                    f"providers[{i}]: auth={auth!r} requires 'token' or 'token_env'"
                )
        elif auth == "azure-ad":
            tenant_id = entry_raw.get("tenant_id")
            client_id = entry_raw.get("client_id")
            client_secret_env = entry_raw.get("client_secret_env")
            if not all([tenant_id, client_id, client_secret_env]):
                raise ValueError(
                    f"providers[{i}]: auth='azure-ad' requires "
                    "'tenant_id', 'client_id', and 'client_secret_env'"
                )
            for field_name, field_val in [
                ("tenant_id", tenant_id),
                ("client_id", client_id),
                ("client_secret_env", client_secret_env),
            ]:
                if not isinstance(field_val, str) or not field_val.strip():
                    raise ValueError(
                        f"providers[{i}]: '{field_name}' must be a non-empty string"
                    )
        # azure-cli needs no extra fields

        entries.append(
            AuthConfigEntry(
                hosts=tuple(hosts),
                provider=provider,
                auth=auth,
                token=token,
                token_env=token_env,
                tenant_id=entry_raw.get("tenant_id"),
                client_id=entry_raw.get("client_id"),
                client_secret_env=entry_raw.get("client_secret_env"),
            )
        )

    return entries


def find_entries_for_url(
    url: str, entries: list[AuthConfigEntry]
) -> list[AuthConfigEntry]:
    """Return entries whose ``hosts`` match the hostname of *url*."""
    hostname = (urlparse(url).hostname or "").lower()
    if not hostname:
        return []
    return [
        e
        for e in entries
        if any(
            pattern == hostname or fnmatch(hostname, pattern)
            for pattern in e.hosts
        )
    ]
