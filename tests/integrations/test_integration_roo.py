"""Tests for RooIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestRooIntegration(MarkdownIntegrationTests):
    KEY = "roo"
    FOLDER = ".roo/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".roo/commands"
    CONTEXT_FILE = ".roo/rules/specify-rules.md"
