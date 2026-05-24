"""Goose integration — Block's open source AI agent."""

from ..base import YamlIntegration


class GooseIntegration(YamlIntegration):
    key = "goose"
    config = {
        "name": "Goose",
        "folder": ".goose/",
        "commands_subdir": "recipes",
        "install_url": "https://block.github.io/goose/docs/getting-started/installation",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".goose/recipes",
        "format": "yaml",
        "args": "{{ args | indent(2) }}",
        "extension": ".yaml",
    }
    context_file = "AGENTS.md"
