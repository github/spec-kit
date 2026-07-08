"""Tests for BobIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestBobIntegration(SkillsIntegrationTests):
    KEY = "bob"
    FOLDER = ".bob/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".bob/skills"
