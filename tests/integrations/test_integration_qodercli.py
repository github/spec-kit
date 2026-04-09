"""Tests for QodercliIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestQodercliIntegration(MarkdownIntegrationTests):
    KEY = "qodercli"
    FOLDER = ".qoder/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".qoder/commands"
    CONTEXT_FILE = "QODER.md"
