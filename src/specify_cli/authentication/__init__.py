"""Authentication provider registry for multi-platform support.

Credentials are **opt-in only**.  No authentication headers are sent unless
the user creates ``~/.specify/auth.json`` mapping hosts to providers.
Provider classes define *how* to authenticate (Bearer, Basic-PAT, etc.)
while the config file defines *where* and *with what credentials*.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import AuthProvider

# Maps provider key → AuthProvider class instance.
AUTH_REGISTRY: dict[str, AuthProvider] = {}


def _register(provider: AuthProvider) -> None:
    """Register a provider instance in the global registry.

    Raises ``ValueError`` for falsy keys and ``KeyError`` for duplicates.
    """
    key = provider.key
    if not key:
        raise ValueError("Cannot register provider with an empty key.")
    if key in AUTH_REGISTRY:
        raise KeyError(f"Provider with key {key!r} is already registered.")
    AUTH_REGISTRY[key] = provider


def get_provider(key: str) -> AuthProvider | None:
    """Return the provider for *key*, or ``None`` if not registered."""
    return AUTH_REGISTRY.get(key)


# -- Register built-in providers -----------------------------------------


def _register_builtins() -> None:
    """Register all built-in authentication providers (alphabetical)."""
    from .azure_devops import AzureDevOpsAuth
    from .github import GitHubAuth

    _register(AzureDevOpsAuth())
    _register(GitHubAuth())


_register_builtins()
