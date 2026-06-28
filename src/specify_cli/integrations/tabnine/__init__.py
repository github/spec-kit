"""Tabnine CLI integration."""

from ..base import TomlIntegration


class TabnineIntegration(TomlIntegration):
    key = "tabnine"
    config = {
        "name": "Tabnine CLI",
        "folder": ".tabnine/agent/",
        "commands_subdir": "commands",
        "install_url": "https://docs.tabnine.com/main/getting-started/tabnine-cli",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".tabnine/agent/commands",
        "format": "toml",
        "args": "{{args}}",
        "extension": ".toml",
    }
    context_file = "TABNINE.md"
    multi_install_safe = True
