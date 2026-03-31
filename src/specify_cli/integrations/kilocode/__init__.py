"""Kilo Code integration."""

from ..base import MarkdownIntegration


class KilocodeIntegration(MarkdownIntegration):
    key = "kilocode"
    config = {
        "name": "Kilo Code",
        "folder": ".kilocode/",
        "commands_subdir": "workflows",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".kilocode/workflows",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = ".kilocode/rules/specify-rules.md"
