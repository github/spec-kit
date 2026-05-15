"""iFlow CLI integration."""

from ..base import MarkdownIntegration


class IflowIntegration(MarkdownIntegration):
    key = "iflow"
    config = {
        "name": "iFlow CLI",
        "folder": ".iflow/",
        "commands_subdir": "commands",
        "install_url": "https://docs.iflow.cn/en/cli/quickstart",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".iflow/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "IFLOW.md"
    multi_install_safe = True
