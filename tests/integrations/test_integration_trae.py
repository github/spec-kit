"""Tests for TraeIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestTraeIntegration(SkillsIntegrationTests):
    KEY = "trae"
    FOLDER = ".trae/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".trae/skills"
    CONTEXT_FILE = ".trae/rules/project_rules.md"
