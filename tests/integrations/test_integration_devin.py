"""Tests for DevinIntegration."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestDevinIntegration(SkillsIntegrationTests):
    KEY = "devin"
    FOLDER = ".devin/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".devin/skills"
    CONTEXT_FILE = "AGENTS.md"


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