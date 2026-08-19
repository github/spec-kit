"""Tests for QodercliIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestQodercliIntegration(SkillsIntegrationTests):
    KEY = "qodercli"
    FOLDER = ".qoder/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".qoder/skills"
