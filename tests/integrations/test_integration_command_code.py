"""Tests for CommandCodeIntegration — skills-based integration (Command Code)."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestCommandCodeIntegration(SkillsIntegrationTests):
    KEY = "command-code"
    FOLDER = ".commandcode/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".commandcode/skills"
