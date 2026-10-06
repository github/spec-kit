"""Tests for ``specify artifact`` command-group registration."""

from specify_cli.artifacts import _commands


def test_artifact_commands_registered_once_in_stable_order():
    assert [command.name for command in _commands.artifact_app.registered_commands] == [
        "list",
        "info",
        "lookup",
    ]
