"""Tests for GooseIntegration."""

from .test_integration_base_yaml import YamlIntegrationTests


class TestGooseIntegration(YamlIntegrationTests):
    KEY = "goose"
    FOLDER = ".goose/"
    COMMANDS_SUBDIR = "recipes"
    REGISTRAR_DIR = ".goose/recipes"
    CONTEXT_FILE = "AGENTS.md"
