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
        """--ai agy (without --ai-skills) should auto-promote to integration."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path / "test-proj"), "--ai", "agy"])

        assert "--integration agy" in result.output
