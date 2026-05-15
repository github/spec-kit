"""Tests for BobIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestBobIntegration(MarkdownIntegrationTests):
    KEY = "bob"
    FOLDER = ".bob/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".bob/commands"
    CONTEXT_FILE = "AGENTS.md"
