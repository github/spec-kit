"""Tests for QwenIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestQwenIntegration(MarkdownIntegrationTests):
    KEY = "qwen"
    FOLDER = ".qwen/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".qwen/commands"
    CONTEXT_FILE = "QWEN.md"
