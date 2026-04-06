"""Tests for ShaiIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestShaiIntegration(MarkdownIntegrationTests):
    KEY = "shai"
    FOLDER = ".shai/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".shai/commands"
    CONTEXT_FILE = "SHAI.md"
