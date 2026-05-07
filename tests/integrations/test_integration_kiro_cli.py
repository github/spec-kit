"""Tests for KiroCliIntegration."""

import os

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestKiroCliIntegration(MarkdownIntegrationTests):
    KEY = "kiro-cli"
    FOLDER = ".kiro/"
    COMMANDS_SUBDIR = "prompts"
    REGISTRAR_DIR = ".kiro/prompts"
    CONTEXT_FILE = "AGENTS.md"

    def test_registrar_config(self):
        """Override base assertion: kiro-cli uses a prose fallback for args
        because Kiro CLI file-based prompts do not natively substitute
        ``$ARGUMENTS`` (see issue #1926 / kirodotdev/Kiro#4141)."""
        i = get_integration(self.KEY)
        assert i.registrar_config["dir"] == self.REGISTRAR_DIR
        assert i.registrar_config["format"] == "markdown"
        assert i.registrar_config["args"] != "$ARGUMENTS"
        assert i.registrar_config["args"]
        assert i.registrar_config["extension"] == ".md"

    def test_rendered_prompts_do_not_contain_raw_arguments(self, tmp_path):
        """Rendered Kiro prompt files must NOT contain the raw ``$ARGUMENTS``
        token — Kiro CLI does not substitute it, so the literal would reach
        the model and break the prompt (issue #1926)."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        prompts_dir = tmp_path / self.REGISTRAR_DIR
        rendered = list(prompts_dir.glob("*.md"))
        assert rendered, "expected at least one rendered prompt file"

        offenders = [
            p.name for p in rendered if "$ARGUMENTS" in p.read_text(encoding="utf-8")
        ]
        assert offenders == [], (
            f"these rendered prompts still contain the raw $ARGUMENTS token: {offenders}"
        )

    def test_rendered_prompts_contain_kiro_arg_placeholder(self, tmp_path):
        """The chosen kiro-cli args fallback string must end up in at least
        one rendered prompt (proves substitution actually fired, not just
        that $ARGUMENTS was removed)."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        expected = integration.registrar_config["args"]
        prompts_dir = tmp_path / self.REGISTRAR_DIR
        contents = "\n".join(
            p.read_text(encoding="utf-8") for p in prompts_dir.glob("*.md")
        )
        assert expected in contents, (
            f"none of the rendered prompts contain the configured args fallback "
            f"({expected!r})"
        )


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
