"""Tests for KiroCliIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestKiroCliIntegration(MarkdownIntegrationTests):
    KEY = "kiro-cli"
    FOLDER = ".kiro/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".kiro/prompts"
    CONTEXT_FILE = "AGENTS.md"
