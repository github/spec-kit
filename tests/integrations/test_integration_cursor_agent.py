"""Tests for CursorAgentIntegration."""

from pathlib import Path

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestCursorAgentIntegration(SkillsIntegrationTests):
    KEY = "cursor-agent"
    FOLDER = ".cursor/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".cursor/skills"
    CONTEXT_FILE = ".cursor/rules/specify-rules.mdc"


class TestCursorMdcFrontmatter:
    """Verify .mdc frontmatter handling in upsert/remove context section."""

    def _setup(self, tmp_path: Path):
        i = get_integration("cursor-agent")
        m = IntegrationManifest("cursor-agent", tmp_path)
        return i, m

    def test_new_mdc_gets_frontmatter(self, tmp_path):
        """A freshly created .mdc file includes alwaysApply: true."""
        i, m = self._setup(tmp_path)
        i.setup(tmp_path, m)
        ctx = (tmp_path / i.context_file).read_text(encoding="utf-8")
        assert ctx.startswith("---\n")
        assert "alwaysApply: true" in ctx

    def test_existing_mdc_without_frontmatter_gets_it(self, tmp_path):
        """An existing .mdc without frontmatter gets it added."""
        i, m = self._setup(tmp_path)
        ctx_path = tmp_path / i.context_file
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text("# User rules\n", encoding="utf-8")
        i.upsert_context_section(tmp_path)
        content = ctx_path.read_text(encoding="utf-8")
        assert content.lstrip().startswith("---")
        assert "alwaysApply: true" in content
        assert "# User rules" in content

    def test_existing_mdc_with_frontmatter_preserves_it(self, tmp_path):
        """An existing .mdc with custom frontmatter is preserved."""
        i, m = self._setup(tmp_path)
        ctx_path = tmp_path / i.context_file
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text(
            "---\nalwaysApply: true\ncustomKey: hello\n---\n\n# Rules\n",
            encoding="utf-8",
        )
        i.upsert_context_section(tmp_path)
        content = ctx_path.read_text(encoding="utf-8")
        assert "alwaysApply: true" in content
        assert "customKey: hello" in content
        assert "<!-- SPECKIT START -->" in content

    def test_existing_mdc_wrong_alwaysapply_fixed(self, tmp_path):
        """An .mdc with alwaysApply: false gets corrected."""
        i, m = self._setup(tmp_path)
        ctx_path = tmp_path / i.context_file
        ctx_path.parent.mkdir(parents=True, exist_ok=True)
        ctx_path.write_text(
            "---\nalwaysApply: false\n---\n\n# Rules\n",
            encoding="utf-8",
        )
        i.upsert_context_section(tmp_path)
        content = ctx_path.read_text(encoding="utf-8")
        assert "alwaysApply: true" in content
        assert "alwaysApply: false" not in content

    def test_upsert_idempotent_no_duplicate_frontmatter(self, tmp_path):
        """Repeated upserts don't duplicate frontmatter."""
        i, m = self._setup(tmp_path)
        i.upsert_context_section(tmp_path)
        i.upsert_context_section(tmp_path)
        content = (tmp_path / i.context_file).read_text(encoding="utf-8")
        assert content.count("alwaysApply") == 1

    def test_remove_deletes_mdc_with_only_frontmatter(self, tmp_path):
        """Removing the section from a Speckit-only .mdc deletes the file."""
        i, m = self._setup(tmp_path)
        i.upsert_context_section(tmp_path)
        ctx_path = tmp_path / i.context_file
        assert ctx_path.exists()
        i.remove_context_section(tmp_path)
        assert not ctx_path.exists()


class TestCursorAgentAutoPromote:
    """--ai cursor-agent auto-promotes to integration path."""

    def test_ai_cursor_agent_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai cursor-agent should work the same as --integration cursor-agent."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--ai", "cursor-agent", "--no-git", "--ignore-agent-tools", "--script", "sh"])

        assert result.exit_code == 0, f"init --ai cursor-agent failed: {result.output}"
        assert (target / ".cursor" / "skills" / "speckit-plan" / "SKILL.md").exists()

