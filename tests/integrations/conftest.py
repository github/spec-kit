"""Shared test helpers for integration tests."""

from specify_cli.integrations.base import MarkdownIntegration


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
    context_file = "STUB.md"
