"""Tests for ClaudeIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestClaudeIntegration(MarkdownIntegrationTests):
    KEY = "claude"
    FOLDER = ".claude/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".claude/commands"
    CONTEXT_FILE = "CLAUDE.md"
