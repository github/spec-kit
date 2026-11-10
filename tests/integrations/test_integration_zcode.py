"""Tests for ZcodeIntegration — skills-based integration (Z.AI)."""

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestZcodeIntegration(SkillsIntegrationTests):
    KEY = "zcode"
    FOLDER = ".zcode/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".zcode/skills"

    def test_build_exec_args_uses_prompt_flag(self):
        integration = get_integration("zcode")

        args = integration.build_exec_args(
            "$speckit-specify build a login page",
            output_json=False,
        )

        assert args == ["zcode", "-p", "$speckit-specify build a login page"]

    def test_build_exec_args_requests_json_output(self):
        integration = get_integration("zcode")

        args = integration.build_exec_args("$speckit-plan add OAuth", output_json=True)

        assert args == [
            "zcode",
            "-p",
            "$speckit-plan add OAuth",
            "--output-format",
            "json",
        ]

    def test_build_exec_args_omits_model_flag(self):
        """ZCode has no model flag; its strict parser rejects `--model` and exits 1."""
        integration = get_integration("zcode")

        args = integration.build_exec_args(
            "$speckit-specify build a login page",
            model="glm-5",
            output_json=False,
        )

        assert args == ["zcode", "-p", "$speckit-specify build a login page"]
        assert "--model" not in args
        assert "glm-5" not in args

    def test_build_exec_args_applies_extra_args(self, monkeypatch):
        monkeypatch.setenv("SPECKIT_INTEGRATION_ZCODE_EXTRA_ARGS", "--mode build")
        integration = get_integration("zcode")

        args = integration.build_exec_args(
            "check the build", model="glm-5", output_json=True
        )

        assert args == [
            "zcode",
            "-p",
            "check the build",
            "--mode",
            "build",
            "--output-format",
            "json",
        ]

class TestZcodeInvocation:
    """ZCode renders $speckit-* chat invocations (like Codex)."""

    def test_next_steps_show_dollar_skill_invocation(self, tmp_path):
        """ZCode next-steps guidance should display $speckit-* usage."""
        import os
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "zcode-next-steps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--integration", "zcode",
                "--ignore-agent-tools", "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert "$speckit-constitution" in result.output
        assert "/speckit.constitution" not in result.output
