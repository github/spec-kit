"""Tests for GrokIntegration."""

import json

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
            catch_exceptions=False,
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
        assert "--always-approve" in args
        assert "--model" in args
        assert "grok-build" in args
        assert "--output-format" in args
        assert "json" in args


class TestGrokNextSteps:
    """CLI output tests for Grok next-steps display."""

    def test_init_next_steps_show_grok_skill_guidance(self, tmp_path):
        """init --integration grok should guide users to .grok/skills and /speckit-*."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "grok-next-steps"
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
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"init --integration grok failed: {result.output}"
        assert "Start Grok Build" in result.output, (
            f"Expected Grok start guidance in next steps but got:\n{result.output}"
        )
        assert ".grok/skills" in result.output, (
            f"Expected .grok/skills install path in next steps but got:\n{result.output}"
        )
        assert "/speckit-plan" in result.output, (
            f"Expected /speckit-plan in next steps but got:\n{result.output}"
        )
        assert "/speckit.plan" not in result.output, (
            f"Should not show /speckit.plan for Grok skills mode:\n{result.output}"
        )


class TestGrokInitOptions:
    """Init-options persistence for always-skills Grok."""

    def test_init_persists_ai_skills_for_grok(self, tmp_path, monkeypatch):
        """specify init --integration grok must persist ai_skills: true,
        so HookExecutor renders slash-skill invocations without manual
        init-options manipulation.
        """
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.extensions import HookExecutor

        project = tmp_path / "grok-init-test"
        project.mkdir()
        monkeypatch.chdir(project)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--here",
                "--integration",
                "grok",
                "--script",
                "sh",
                "--ignore-agent-tools",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"init failed: {result.output}"

        opts_path = project / ".specify" / "init-options.json"
        assert opts_path.exists()
        opts = json.loads(opts_path.read_text(encoding="utf-8"))
        assert opts.get("ai") == "grok"
        assert opts.get("ai_skills") is True, (
            f"init must persist ai_skills=true for Grok, got: {opts.get('ai_skills')}"
        )

        hook_executor = HookExecutor(project)
        message = hook_executor.format_hook_message(
            "before_plan",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.plan",
                    "optional": False,
                }
            ],
        )
        assert "Executing: `/speckit-plan`" in message, (
            "Hook rendering must produce /speckit-plan for Grok without hint injection"
        )
        assert "EXECUTE_COMMAND_INVOCATION: /speckit-plan" in message
