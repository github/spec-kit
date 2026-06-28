"""Auggie CLI integration."""

from ..base import MarkdownIntegration


class AuggieIntegration(MarkdownIntegration):
    key = "auggie"
    config = {
        "name": "Auggie CLI",
        "folder": ".augment/",
        "commands_subdir": "commands",
        "install_url": "https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".augment/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = ".augment/rules/specify-rules.md"
    multi_install_safe = True
