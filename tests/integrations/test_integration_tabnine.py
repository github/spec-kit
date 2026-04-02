"""Tests for TabnineIntegration."""

from .test_integration_base_toml import TomlIntegrationTests


class TestTabnineIntegration(TomlIntegrationTests):
    KEY = "tabnine"
    FOLDER = ".tabnine/agent/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".tabnine/agent/commands"
    CONTEXT_FILE = "TABNINE.md"
