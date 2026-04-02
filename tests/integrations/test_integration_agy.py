"""Tests for AgyIntegration (Antigravity)."""

from .test_integration_base_skills import SkillsIntegrationTests


class TestAgyIntegration(SkillsIntegrationTests):
    KEY = "agy"
    FOLDER = ".agent/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agent/skills"
    CONTEXT_FILE = "AGENTS.md"


class TestAgyAutoPromote:
    """--ai agy auto-promotes to integration path."""

    def test_ai_agy_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai agy should work the same as --integration agy."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--ai", "agy", "--no-git", "--script", "sh"])

        assert result.exit_code == 0, f"init --ai agy failed: {result.output}"
        assert (target / ".agent" / "skills" / "speckit-plan" / "SKILL.md").exists()
