"""Tests for DevinIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestDevinIntegration(SkillsIntegrationTests):
    KEY = "devin"
    FOLDER = ".devin/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".devin/skills"
    CONTEXT_FILE = "AGENTS.md"


class TestDevinBuildExecArgs:
    """Regression tests for DevinIntegration.build_exec_args.

    Devin's CLI has no --output-format flag, so build_exec_args must
    omit it regardless of the output_json argument. The integration
    must also remain dispatchable (must not return None, which is the
    codebase's IDE-only sentinel checked by CommandStep).
    """

    def test_returns_args_not_none_for_dispatch(self):
        """Devin is CLI-dispatchable; build_exec_args must not return None."""
        from specify_cli.integrations.devin import DevinIntegration

        impl = DevinIntegration()
        args = impl.build_exec_args("test prompt")
        assert args is not None, (
            "DevinIntegration.build_exec_args must not return None. "
            "None is the codebase sentinel for IDE-only integrations "
            "(see WindsurfIntegration); Devin is dispatchable via 'devin -p'."
        )
        assert args[:3] == ["devin", "-p", "test prompt"]

    def test_output_json_does_not_emit_output_format_flag(self):
        """Devin has no --output-format flag; output_json=True must not add it."""
        from specify_cli.integrations.devin import DevinIntegration

        impl = DevinIntegration()
        args_json = impl.build_exec_args("hello", output_json=True)
        args_text = impl.build_exec_args("hello", output_json=False)

        assert "--output-format" not in args_json
        assert "json" not in args_json[3:]
        # The two should be identical: output_json is documented as having
        # no effect on the command line for Devin (plain-text stdout).
        assert args_json == args_text

    def test_model_flag_passed_through(self):
        """--model is supported and should appear when provided."""
        from specify_cli.integrations.devin import DevinIntegration

        impl = DevinIntegration()
        args = impl.build_exec_args("hi", model="claude-sonnet-4")
        assert args == ["devin", "-p", "hi", "--model", "claude-sonnet-4"]


class TestDevinAutoPromote:
    """--ai devin auto-promotes to integration path."""

    def test_ai_devin_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai devin should work the same as --integration devin."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(
            app,
            ["init", str(target), "--ai", "devin", "--no-git", "--ignore-agent-tools", "--script", "sh"],
        )

        assert result.exit_code == 0, f"init --ai devin failed: {result.output}"
        assert (target / ".devin" / "skills" / "speckit-plan" / "SKILL.md").exists()