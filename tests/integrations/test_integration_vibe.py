"""Tests for VibeIntegration."""

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestVibeIntegration(MarkdownIntegrationTests):
    KEY = "vibe"
    FOLDER = ".vibe/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".vibe/prompts"
    CONTEXT_FILE = ".vibe/agents/specify-agents.md"
