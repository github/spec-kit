"""Tests for CursorAgentIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestCursorAgentIntegration(MarkdownIntegrationTests):
    KEY = "cursor-agent"
    FOLDER = ".cursor/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".cursor/commands"
    CONTEXT_FILE = ".cursor/rules/specify-rules.mdc"
