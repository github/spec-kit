"""Tests for LingmaIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestLingmaIntegration(SkillsIntegrationTests):
    KEY = "lingma"
    FOLDER = ".lingma/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".lingma/skills"
