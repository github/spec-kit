"""Tests for ZcodeIntegration — skills-based integration (Z.AI)."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestZcodeIntegration(SkillsIntegrationTests):
    KEY = "zcode"
    FOLDER = ".zcode/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".zcode/skills"
    CONTEXT_FILE = "ZCODE.md"
