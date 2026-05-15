"""Tests for IflowIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestIflowIntegration(MarkdownIntegrationTests):
    KEY = "iflow"
    FOLDER = ".iflow/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".iflow/commands"
    CONTEXT_FILE = "IFLOW.md"
