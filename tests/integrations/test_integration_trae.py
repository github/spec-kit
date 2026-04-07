"""Tests for TraeIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestTraeIntegration(MarkdownIntegrationTests):
    KEY = "trae"
    FOLDER = ".trae/"
    COMMANDS_SUBDIR = "rules"
    REGISTRAR_DIR = ".trae/rules"
    CONTEXT_FILE = ".trae/rules/project_rules.md"
