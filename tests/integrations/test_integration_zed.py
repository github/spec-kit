"""Tests for ZedIntegration."""

import json

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestZedIntegration(SkillsIntegrationTests):
    KEY = "zed"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"
    CONTEXT_FILE = "AGENTS.md"

    def test_options_include_skills_flag(self):
        """Zed is always skills-based; no --skills option needed."""
        i = get_integration(self.KEY)
        skills_opts = [o for o in i.options() if o.name == "--skills"]
        assert len(skills_opts) == 0, (
            "Zed is always skills-based and should not expose a --skills option"
        )

    def test_requires_cli_is_false(self):
        """Zed is IDE-based; requires_cli must remain False."""
        i = get_integration(self.KEY)
        assert i is not None
        assert i.config is not None
        assert i.config["requires_cli"] is False


class TestZedHookInvocations:
    """Zed hook messages should reference slash-invokable skills."""

    def test_hooks_render_skill_invocation(self, tmp_path):
        from specify_cli.extensions import HookExecutor

        project = tmp_path / "zed-hooks"
        project.mkdir()
        init_options = project / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "zed", "ai_skills": True}))

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

        assert "Executing: `/speckit-plan`" in message
        assert "EXECUTE_COMMAND: speckit.plan" in message
        assert "EXECUTE_COMMAND_INVOCATION: /speckit-plan" in message

    def test_init_persists_ai_skills_for_zed(self, tmp_path, monkeypatch):
        """specify init --integration zed must persist ai_skills: true,
        so HookExecutor renders slash-skill invocations without manual
        init-options manipulation."""
        from typer.testing import CliRunner

        from specify_cli import app
        from specify_cli.extensions import HookExecutor

        project = tmp_path / "zed-init-test"
        project.mkdir()
        monkeypatch.chdir(project)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--here",
                "--integration",
                "zed",
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
        assert opts.get("ai") == "zed"
        assert opts.get("ai_skills") is True, (
            f"init must persist ai_skills=true for Zed, got: {opts.get('ai_skills')}"
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
            "Hook rendering must produce /speckit-plan for Zed without hint injection\n"
            f"Got message: {message}"
        )
        assert "EXECUTE_COMMAND_INVOCATION: /speckit-plan" in message
