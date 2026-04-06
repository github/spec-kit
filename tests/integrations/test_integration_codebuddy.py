"""Tests for CodebuddyIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestCodebuddyIntegration(MarkdownIntegrationTests):
    KEY = "codebuddy"
    FOLDER = ".codebuddy/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".codebuddy/commands"
    CONTEXT_FILE = "CODEBUDDY.md"
