"""Kilo Code integration."""

from ..base import MarkdownIntegration


class KilocodeIntegration(MarkdownIntegration):
    key = "kilocode"
    config = {
        "name": "Kilo Code",
        "folder": ".kilo/",
        "commands_subdir": "commands",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".kilo/commands",
        "legacy_dir": ".kilocode/workflows",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    multi_install_safe = True
