"""Tests for AuggieIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestAuggieIntegration(MarkdownIntegrationTests):
    KEY = "auggie"
    FOLDER = ".augment/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".augment/commands"
    CONTEXT_FILE = ".augment/rules/specify-rules.md"
