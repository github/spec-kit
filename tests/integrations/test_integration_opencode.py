"""Tests for OpencodeIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestOpencodeIntegration(MarkdownIntegrationTests):
    KEY = "opencode"
    FOLDER = ".opencode/"
    COMMANDS_SUBDIR = "command"
    REGISTRAR_DIR = ".opencode/command"
    CONTEXT_FILE = "AGENTS.md"
