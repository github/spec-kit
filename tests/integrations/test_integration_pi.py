"""Tests for PiIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestPiIntegration(MarkdownIntegrationTests):
    KEY = "pi"
    FOLDER = ".pi/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".pi/prompts"
    CONTEXT_FILE = "AGENTS.md"
