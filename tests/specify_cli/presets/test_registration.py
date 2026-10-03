"""Registration and compatibility boundaries for ``specify preset``."""

from __future__ import annotations

from specify_cli.presets import _commands
from specify_cli.presets.catalog import catalog_app


def test_preset_commands_registered_once_in_stable_order():
    assert [command.name for command in _commands.preset_app.registered_commands] == [
        "list",
        "add",
        "remove",
        "update",
        "search",
        "script-chain",
        "resolve",
        "info",
        "set-priority",
        "enable",
        "disable",
    ]
    assert [group.name for group in _commands.preset_app.registered_groups] == [
        "catalog"
    ]


def test_catalog_commands_registered_once_in_stable_order():
    assert [command.name for command in catalog_app.registered_commands] == [
        "list",
        "add",
        "remove",
    ]


def test_legacy_add_import_resolves_to_extracted_handler():
    from specify_cli.presets.command_add import preset_add

    assert _commands.preset_add.__name__ == "preset_add"
    assert _commands.preset_add.__module__ == "specify_cli.presets._commands"
    assert callable(preset_add)
