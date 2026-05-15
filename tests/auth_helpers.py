"""Shared test helpers for authentication config injection."""

from __future__ import annotations

from specify_cli.authentication.config import AuthConfigEntry


def make_github_auth_entry(token_env: str = "GH_TOKEN") -> AuthConfigEntry:
    """Build a GitHub ``AuthConfigEntry`` for testing."""
    return AuthConfigEntry(
        hosts=("github.com", "api.github.com", "raw.githubusercontent.com", "codeload.github.com"),
        provider="github",
        auth="bearer",
        token_env=token_env,
    )


def inject_github_config(monkeypatch, token_env: str = "GH_TOKEN") -> None:
    """Inject a GitHub auth.json config entry into the auth HTTP module."""
    from specify_cli.authentication import http as _auth_http
    monkeypatch.setattr(_auth_http, "_config_override", [make_github_auth_entry(token_env)])
