"""Qwen Code integration."""

from ..base import MarkdownIntegration


class QwenIntegration(MarkdownIntegration):
    key = "qwen"
    config = {
        "name": "Qwen Code",
        "folder": ".qwen/",
        "commands_subdir": "commands",
        "install_url": "https://github.com/QwenLM/qwen-code",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".qwen/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "QWEN.md"
