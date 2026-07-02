"""Shared test helpers for integration tests."""

import pytest

from specify_cli.integrations.base import MarkdownIntegration


@pytest.fixture(autouse=True)
def _isolate_integration_home(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Keep integration tests from reading or writing the real user home."""
    home = tmp_path / "home"
    for path in (home, home / ".cache", home / ".config", home / ".local" / "share"):
        path.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(home / ".local" / "share"))


class StubIntegration(MarkdownIntegration):
    """Minimal concrete integration for testing."""

    key = "stub"
    config = {
        "name": "Stub Agent",
        "folder": ".stub/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".stub/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
