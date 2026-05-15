"""Tests for KilocodeIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestKilocodeIntegration(MarkdownIntegrationTests):
    KEY = "kilocode"
    FOLDER = ".kilocode/"
    COMMANDS_SUBDIR = "workflows"
    REGISTRAR_DIR = ".kilocode/workflows"
    CONTEXT_FILE = ".kilocode/rules/specify-rules.md"
