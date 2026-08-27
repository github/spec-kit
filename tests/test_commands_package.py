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


def test_resolve_default_init_integration_unset(monkeypatch):
    from specify_cli._agent_config import (
        DEFAULT_INIT_INTEGRATION,
        DEFAULT_INIT_INTEGRATION_ENV_VAR,
        resolve_default_init_integration,
    )
    monkeypatch.delenv(DEFAULT_INIT_INTEGRATION_ENV_VAR, raising=False)
    assert resolve_default_init_integration() == DEFAULT_INIT_INTEGRATION


def test_resolve_default_init_integration_valid_override(monkeypatch):
    from specify_cli._agent_config import (
        DEFAULT_INIT_INTEGRATION_ENV_VAR,
        resolve_default_init_integration,
    )
    monkeypatch.setenv(DEFAULT_INIT_INTEGRATION_ENV_VAR, "gemini")
    assert resolve_default_init_integration() == "gemini"


def test_resolve_default_init_integration_whitespace_trimmed(monkeypatch):
    from specify_cli._agent_config import (
        DEFAULT_INIT_INTEGRATION_ENV_VAR,
        resolve_default_init_integration,
    )
    monkeypatch.setenv(DEFAULT_INIT_INTEGRATION_ENV_VAR, "  gemini  ")
    assert resolve_default_init_integration() == "gemini"


def test_resolve_default_init_integration_invalid_warns_and_falls_back(
    monkeypatch, capsys
):
    from specify_cli._agent_config import (
        DEFAULT_INIT_INTEGRATION,
        DEFAULT_INIT_INTEGRATION_ENV_VAR,
        resolve_default_init_integration,
    )
    monkeypatch.setenv(DEFAULT_INIT_INTEGRATION_ENV_VAR, "not-a-real-agent")
    assert resolve_default_init_integration() == DEFAULT_INIT_INTEGRATION
    captured = capsys.readouterr()
    assert "not-a-real-agent" in captured.err
    assert DEFAULT_INIT_INTEGRATION_ENV_VAR in captured.err


def test_resolve_default_init_integration_re_exported_from_init():
    from specify_cli import resolve_default_init_integration
    assert callable(resolve_default_init_integration)
