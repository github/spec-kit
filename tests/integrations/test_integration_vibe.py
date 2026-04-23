"""Tests for VibeIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestVibeIntegration(SkillsIntegrationTests):
    KEY = "vibe"
    FOLDER = ".vibe/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".vibe/skills"
    CONTEXT_FILE = "AGENTS.md"