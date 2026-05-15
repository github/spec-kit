"""Tests for JunieIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestJunieIntegration(MarkdownIntegrationTests):
    KEY = "junie"
    FOLDER = ".junie/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".junie/commands"
    CONTEXT_FILE = ".junie/AGENTS.md"
