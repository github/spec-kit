"""Tests for the commands/ package structure."""
import importlib


def test_commands_package_importable():
    mod = importlib.import_module("specify_cli.commands")
    assert mod is not None


def test_commands_init_importable():
    mod = importlib.import_module("specify_cli.commands.init")
    assert hasattr(mod, "register")
    assert callable(mod.register)


def test_agent_config_importable():
    from specify_cli._agent_config import (
        AGENT_CONFIG,
        DEFAULT_INIT_INTEGRATION,
        SCRIPT_TYPE_CHOICES,
    )
    assert isinstance(AGENT_CONFIG, dict)
    assert DEFAULT_INIT_INTEGRATION == "copilot"
    assert "sh" in SCRIPT_TYPE_CHOICES


def test_script_type_choices_includes_python():
    from specify_cli._agent_config import SCRIPT_TYPE_CHOICES
    assert SCRIPT_TYPE_CHOICES.get("py") == "Python"
    # The three supported variants are sh, ps, and py.
    assert {"sh", "ps", "py"} <= set(SCRIPT_TYPE_CHOICES)


def test_workflow_init_valid_script_types_includes_python():
    from specify_cli.workflows.steps.init import VALID_SCRIPT_TYPES
    assert "py" in VALID_SCRIPT_TYPES
    # Negative: an unknown variant is not accepted.
    assert "rb" not in VALID_SCRIPT_TYPES


def test_agent_config_re_exported_from_init():
    from specify_cli import AGENT_CONFIG, SCRIPT_TYPE_CHOICES
    assert isinstance(AGENT_CONFIG, dict)
    assert "sh" in SCRIPT_TYPE_CHOICES


def test_init_command_registered():
    from specify_cli import app
    callback_names = [
        cmd.callback.__name__ for cmd in app.registered_commands if cmd.callback
    ]
    assert "init" in callback_names
