"""Tests for GrokIntegration."""

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestGrokIntegration(SkillsIntegrationTests):
    KEY = "grok"
    FOLDER = ".grok/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".grok/skills"

    def test_options_include_skills_flag(self):
        """Not applicable — Grok Build is always skills-based."""
        pytest.skip("Grok Build is always skills-based and does not expose a --skills option")

    def test_options_do_not_include_skills_flag(self):
        i = get_integration(self.KEY)
        assert i is not None
        opts = i.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 0

    def test_requires_cli_is_true(self):
        i = get_integration(self.KEY)
        assert i is not None
        assert i.config["requires_cli"] is True
        assert i.config["name"] == "Grok Build"
        assert i.multi_install_safe is True


class TestGrokInitFlow:
    """--integration grok creates expected files."""

    def test_integration_grok_creates_skills(self, tmp_path):
        """--integration grok should create skills in .grok/skills."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "grok",
                "--ignore-agent-tools",
                "--script",
                "sh",
            ],
        )

        assert result.exit_code == 0, f"init --integration grok failed: {result.output}"
        assert (target / ".grok" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (target / ".grok" / "skills" / "speckit-specify" / "SKILL.md").exists()

    def test_plan_skill_has_no_context_placeholder(self, tmp_path):
        """Core skills must not carry a context-file placeholder."""
        target = tmp_path / "test-proj"
        target.mkdir()

        integration = get_integration("grok")
        manifest = IntegrationManifest("grok", target)
        integration.setup(target, manifest, script_type="sh")

        plan_skill = target / ".grok" / "skills" / "speckit-plan" / "SKILL.md"
        content = plan_skill.read_text(encoding="utf-8")
        assert "__CONTEXT_FILE__" not in content

    def test_build_exec_args_uses_headless_prompt_flag(self):
        integration = get_integration("grok")
        args = integration.build_exec_args("hello", model="grok-build", output_json=True)
        assert args is not None
        assert args[0] == "grok" or args[0].endswith("/grok")
        assert "-p" in args
        assert "hello" in args
        assert "--model" in args
        assert "grok-build" in args
        assert "--output-format" in args
        assert "json" in args
