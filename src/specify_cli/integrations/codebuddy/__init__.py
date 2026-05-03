"""CodeBuddy CLI integration."""

from ..base import MarkdownIntegration


class CodebuddyIntegration(MarkdownIntegration):
    key = "codebuddy"
    config = {
        "name": "CodeBuddy",
        "folder": ".codebuddy/",
        "commands_subdir": "commands",
        "install_url": "https://www.codebuddy.ai/cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".codebuddy/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }
    context_file = "CODEBUDDY.md"
    multi_install_safe = True
