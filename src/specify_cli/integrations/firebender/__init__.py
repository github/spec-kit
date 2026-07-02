"""Firebender IDE integration.

Firebender (https://firebender.com/) is an AI coding agent for Android Studio
and IntelliJ. It reads project-local custom slash commands from
``.firebender/commands/*.mdc`` and project rules from ``.firebender/rules/*.mdc``,
so Spec Kit installs its command templates as ``.mdc`` command files. The managed
context section (when used) is owned by the ``agent-context`` extension.
"""

from ..base import MarkdownIntegration


class FirebenderIntegration(MarkdownIntegration):
    key = "firebender"
    config = {
        "name": "Firebender",
        "folder": ".firebender/",
        "commands_subdir": "commands",
        "install_url": "https://firebender.com/",
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".firebender/commands",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".mdc",
    }
    multi_install_safe = True

    def command_filename(self, template_name: str) -> str:
        """Firebender reads custom slash commands from ``.firebender/commands/*.mdc``."""
        return f"speckit.{template_name}.mdc"
