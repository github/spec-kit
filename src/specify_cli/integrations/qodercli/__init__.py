"""Qoder CLI integration."""

from ..base import MarkdownIntegration


class QodercliIntegration(MarkdownIntegration):
    key = "qodercli"
    config = {
        "name": "Qoder CLI",
        "folder": ".qoder/",
        "commands_subdir": "commands",
        "install_url": "https://qoder.com/cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".qoder/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "QODER.md"
    multi_install_safe = True
