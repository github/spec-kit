"""Trae IDE integration."""

from ..base import MarkdownIntegration


class TraeIntegration(MarkdownIntegration):
    key = "trae"
    config = {
        "name": "Trae",
        "folder": ".trae/",
        "commands_subdir": "rules",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".trae/rules",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = ".trae/rules/AGENTS.md"
