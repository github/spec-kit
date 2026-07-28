"""Tests for LingmaIntegration."""

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestLingmaIntegration(SkillsIntegrationTests):
    KEY = "lingma"
    FOLDER = ".lingma/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".lingma/skills"

    def test_multi_install_safe(self):
        # Lingma writes only to its isolated, static root .lingma/skills,
        # disjoint from every other integration, so it must be co-install safe
        # (mirrors trae/zcode and the kiro-cli #3471 precedent).
        assert get_integration(self.KEY).multi_install_safe is True
