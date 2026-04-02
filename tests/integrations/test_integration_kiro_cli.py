"""Tests for KiroCliIntegration."""

import os

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestKiroCliIntegration(MarkdownIntegrationTests):
    KEY = "kiro-cli"
    FOLDER = ".kiro/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".kiro/prompts"
    CONTEXT_FILE = "AGENTS.md"


class TestKiroAlias:
    """--ai kiro alias normalizes to kiro-cli and auto-promotes."""

    def test_kiro_alias_normalized_to_kiro_cli(self, tmp_path):
        """--ai kiro should normalize to canonical kiro-cli and auto-promote."""
        from typer.testing import CliRunner
        from specify_cli import app

        target = tmp_path / "kiro-alias-proj"
        target.mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(target)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "kiro",
                "--ignore-agent-tools", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0
        assert (target / ".kiro" / "prompts" / "speckit.plan.md").exists()
