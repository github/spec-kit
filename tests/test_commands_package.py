"""Tests for the commands/ package structure."""
import importlib


def test_commands_package_importable():
    mod = importlib.import_module("specify_cli.commands")
    assert mod is not None


def test_commands_init_importable():
    mod = importlib.import_module("specify_cli.commands.init")
    assert hasattr(mod, "register")
    assert callable(mod.register)


def test_commands_stubs_importable():
    for name in ("integration", "preset", "extension", "workflow"):
        mod = importlib.import_module(f"specify_cli.commands.{name}")
        assert mod is not None


def test_agent_config_importable():
    from specify_cli._agent_config import (
        AGENT_CONFIG,
        AI_ASSISTANT_ALIASES,
        AI_ASSISTANT_HELP,
        DEFAULT_INIT_INTEGRATION,
        SCRIPT_TYPE_CHOICES,
    )
    assert isinstance(AGENT_CONFIG, dict)
    assert isinstance(AI_ASSISTANT_ALIASES, dict)
    assert isinstance(AI_ASSISTANT_HELP, str)
    assert DEFAULT_INIT_INTEGRATION == "copilot"
    assert "sh" in SCRIPT_TYPE_CHOICES


def test_agent_config_re_exported_from_init():
    from specify_cli import AGENT_CONFIG, AI_ASSISTANT_ALIASES, AI_ASSISTANT_HELP, SCRIPT_TYPE_CHOICES
    assert isinstance(AGENT_CONFIG, dict)
    assert "sh" in SCRIPT_TYPE_CHOICES


def test_init_command_registered():
    from specify_cli import app
    callback_names = [
        cmd.callback.__name__ for cmd in app.registered_commands if cmd.callback
    ]
    assert "init" in callback_names
