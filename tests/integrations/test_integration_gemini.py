"""Tests for GeminiIntegration."""

from .test_integration_base_toml import TomlIntegrationTests


class TestGeminiIntegration(TomlIntegrationTests):
    KEY = "gemini"
    FOLDER = ".gemini/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".gemini/commands"
    CONTEXT_FILE = "GEMINI.md"
