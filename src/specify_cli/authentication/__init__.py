"""Authentication provider registry for multi-platform support.

Follows the same pattern as ``src/specify_cli/integrations/``.

Each provider is a self-contained module that handles credential resolution
and header construction for a specific platform (GitHub, Azure DevOps, etc.).
Built-in providers are instantiated and added to the global ``AUTH_REGISTRY``
by ``_register_builtins()``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import AuthProvider

# Maps provider key → AuthProvider instance.
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


def configured_providers() -> list[AuthProvider]:
    """Return all providers that currently have credentials configured."""
    return [p for p in AUTH_REGISTRY.values() if p.is_configured()]


# -- Register built-in providers -----------------------------------------


def _register_builtins() -> None:
    """Register all built-in authentication providers (alphabetical)."""
    # -- Imports (alphabetical) -------------------------------------------
    from .azure_devops import AzureDevOpsAuth
    from .github import GitHubAuth

    # -- Registration (alphabetical) --------------------------------------
    _register(AzureDevOpsAuth())
    _register(GitHubAuth())


_register_builtins()
