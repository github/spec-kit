"""Tests for WindsurfIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestWindsurfIntegration(MarkdownIntegrationTests):
    KEY = "windsurf"
    FOLDER = ".windsurf/"
    COMMANDS_SUBDIR = "workflows"
    REGISTRAR_DIR = ".windsurf/workflows"
    CONTEXT_FILE = ".windsurf/rules/specify-rules.md"
