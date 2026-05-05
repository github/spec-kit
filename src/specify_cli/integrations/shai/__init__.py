"""SHAI CLI integration."""

from ..base import MarkdownIntegration


class ShaiIntegration(MarkdownIntegration):
    key = "shai"
    config = {
        "name": "SHAI",
        "folder": ".shai/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/ovh/shai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".shai/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "SHAI.md"
    multi_install_safe = True
