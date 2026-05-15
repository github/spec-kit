"""Amp CLI integration."""

from ..base import MarkdownIntegration


class AmpIntegration(MarkdownIntegration):
    key = "amp"
    config = {
        "name": "Amp",
        "folder": ".agents/",
        "commands_subdir": "commands",
        "install_url": "https://ampcode.com/manual#install",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".agents/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "AGENTS.md"
