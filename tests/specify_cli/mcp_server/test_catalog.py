"""Tests for the explicit MCP command inventory."""

import pytest

from specify_cli.mcp_server.catalog import (
    CommandAdapterError,
    describe_command,
    list_commands,
)


def test_inventory_contains_only_version():
    inventory = list_commands()

    assert [command.command for command in inventory.commands] == ["version"]


def test_describe_version_returns_stable_capabilities():
    description = describe_command("version")

    assert description.command == "version"
    assert description.arguments == []
    assert description.read_only is True
    assert description.json_output is True


def test_describe_rejects_unsupported_command():
    with pytest.raises(CommandAdapterError) as captured:
        describe_command("artifact.list")

    assert captured.value.payload() == {
        "error": {
            "code": "unavailable_command",
            "message": (
                "Command 'artifact.list' is not available through the experimental "
                "Spec Kit MCP server."
            ),
            "details": {
                "command": "artifact.list",
                "available_commands": ["version"],
            },
        }
    }
