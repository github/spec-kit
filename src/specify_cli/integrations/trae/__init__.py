"""Trae IDE integration."""

from ..base import MarkdownIntegration


class TraeIntegration(MarkdownIntegration):
    key = "trae"
    config = {
        "name": "Trae",
        "folder": ".trae/",
        "commands_subdir": "skills",
        "install_url": None,
        "requires_cli": False,
    }
    registrar_config = {
        "dir": ".trae/skills",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": "SKILL.md",
    }
    context_file = ".trae/rules/project_rules.md"
