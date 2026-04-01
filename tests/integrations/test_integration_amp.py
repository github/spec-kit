"""Tests for AmpIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestAmpIntegration(MarkdownIntegrationTests):
    KEY = "amp"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".agents/commands"
    CONTEXT_FILE = "AGENTS.md"
