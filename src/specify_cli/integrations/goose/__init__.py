"""Goose integration — open source AI agent (Agentic AI Foundation)."""

from ..base import YamlIntegration


class GooseIntegration(YamlIntegration):
    key = "goose"
    config = {
        "name": "Goose",
        "folder": ".goose/",
        "commands_subdir": "recipes",
        "install_url": "https://goose-docs.ai/docs/getting-started/installation",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".goose/recipes",
        "format": "yaml",
        "args": "{{args}}",
        "extension": ".yaml",
    }
