"""Cursor IDE integration."""

from ..base import MarkdownIntegration


class CursorAgentIntegration(MarkdownIntegration):
    key = "cursor-agent"
    config = {
        "name": "Cursor",
        "folder": ".cursor/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".cursor/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = ".cursor/rules/specify-rules.mdc"
