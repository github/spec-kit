"""Tests for QodercliIntegration."""

import pytest

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestQodercliIntegration(SkillsIntegrationTests):
    KEY = "qodercli"
    FOLDER = ".qoder/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".qoder/skills"

    def test_options_include_skills_flag(self):
        """Not applicable — Qoder IDE 1.24+ is always skills-based."""
        pytest.skip(
            "Qoder is always skills-based and does not expose a --skills option"
        )

    def test_options_do_not_include_skills_flag(self):
        """Qoder is always skills-based; no --skills option is exposed."""
        i = get_integration(self.KEY)
        assert i is not None
        opts = i.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 0, (
            "Qoder is always skills-based and should not expose a --skills option"
        )

    def test_requires_cli_is_true(self):
        """Qoder CLI is a CLI-based agent; requires_cli must remain True."""
        i = get_integration(self.KEY)
        assert i is not None
        assert i.config is not None
        assert i.config["requires_cli"] is True
        assert i.config["name"] == "Qoder CLI"
        assert i.multi_install_safe is True
