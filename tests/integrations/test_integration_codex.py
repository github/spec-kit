"""Tests for CodexIntegration."""

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestCodexIntegration(SkillsIntegrationTests):
    KEY = "codex"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"
    CONTEXT_FILE = "AGENTS.md"


class TestCodexInitFlow:
    """--integration codex creates expected files."""

    def test_integration_codex_creates_skills(self, tmp_path):
        """--integration codex should create skills in .agents/skills."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--integration", "codex", "--ignore-agent-tools", "--script", "sh"])

        assert result.exit_code == 0, f"init --integration codex failed: {result.output}"
        assert (target / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_plan_skill_references_configured_context_files(self, tmp_path):
        """Plan skill should render all configured agent context files."""
        from specify_cli import _save_agent_context_config

        target = tmp_path / "test-proj"
        target.mkdir()
        _save_agent_context_config(
            target,
            {
                "context_file": "AGENTS.md",
                "context_files": ["AGENTS.md", "CLAUDE.md"],
                "context_markers": {
                    "start": "<!-- SPECKIT START -->",
                    "end": "<!-- SPECKIT END -->",
                },
            },
        )

        integration = get_integration("codex")
        manifest = IntegrationManifest("codex", target)
        integration.setup(target, manifest, script_type="sh")

        plan_skill = target / ".agents" / "skills" / "speckit-plan" / "SKILL.md"
        content = plan_skill.read_text(encoding="utf-8")
        assert "AGENTS.md, CLAUDE.md" in content
        assert "__CONTEXT_FILE__" not in content

    def test_plan_skill_ignores_context_files_when_agent_context_disabled(
        self, tmp_path
    ):
        """Disabled agent-context must not leak stale context_files into commands."""
        from specify_cli import _save_agent_context_config

        target = tmp_path / "test-proj"
        target.mkdir()
        registry = target / ".specify" / "extensions" / ".registry"
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(
            """
{
  "schema_version": "1.0",
  "extensions": {
    "agent-context": {
      "version": "1.0.0",
      "enabled": false
    }
  }
}
""".strip(),
            encoding="utf-8",
        )
        _save_agent_context_config(
            target,
            {
                "context_file": "AGENTS.md",
                "context_files": ["../outside.md", "CLAUDE.md"],
                "context_markers": {
                    "start": "<!-- SPECKIT START -->",
                    "end": "<!-- SPECKIT END -->",
                },
            },
        )

        integration = get_integration("codex")
        manifest = IntegrationManifest("codex", target)
        integration.setup(target, manifest, script_type="sh")

        plan_skill = target / ".agents" / "skills" / "speckit-plan" / "SKILL.md"
        content = plan_skill.read_text(encoding="utf-8")
        assert "AGENTS.md, CLAUDE.md" not in content
        assert "../outside.md" not in content
        assert "AGENTS.md" in content
        assert "__CONTEXT_FILE__" not in content


class TestCodexHookCommandNote:
    """Verify dot-to-hyphen normalization note is injected in hook sections.

    Hook commands in ``extensions.yml`` use dotted ids like
    ``speckit.git.commit`` but Codex skills are named with hyphens
    (``speckit-git-commit``). Without this note, Codex emits
    ``/speckit.git.commit``, which does not resolve.
    """

    def test_hook_note_injected_in_skills_with_hooks(self, tmp_path):
        """Skills that have hook sections should get the normalization note."""
        i = get_integration("codex")
        m = IntegrationManifest("codex", tmp_path)
        i.setup(tmp_path, m, script_type="sh")
        specify_skill = tmp_path / ".agents/skills/speckit-specify/SKILL.md"
        assert specify_skill.exists()
        content = specify_skill.read_text(encoding="utf-8")
        assert "replace dots" in content, (
            "speckit-specify should have dot-to-hyphen hook note"
        )

    def test_hook_note_not_in_skills_without_hooks(self):
        """Skills without hook sections should not get the note."""
        from specify_cli.integrations.codex import CodexIntegration

        content = "---\nname: test\ndescription: test\n---\n\nNo hooks here.\n"
        result = CodexIntegration._inject_hook_command_note(content)
        assert "replace dots" not in result

    def test_hook_note_idempotent(self):
        """Injecting the note twice should not duplicate it."""
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        once = CodexIntegration._inject_hook_command_note(content)
        twice = CodexIntegration._inject_hook_command_note(once)
        assert once == twice, "Hook note injection should be idempotent"

    def test_hook_note_fills_missing_repeated_instructions(self):
        """Already-noted hook sections should not suppress later sections."""
        from specify_cli.integrations.base import _HOOK_COMMAND_NOTE
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            f"{_HOOK_COMMAND_NOTE}"
            "- For each executable hook, output the following based on its flag:\n"
            "\n"
            "  - For each executable hook, output the following based on its flag:\n"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        assert result.count("replace dots (`.`) with hyphens") == 2

    def test_hook_note_not_suppressed_by_unrelated_phrase(self):
        """Unrelated text should not trip the hook-note idempotence guard."""
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            "This paragraph says replace dots in a different context.\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        assert "This paragraph says replace dots in a different context." in result
        assert result.count("replace dots (`.`) with hyphens") == 1

    def test_hook_note_preserves_indentation(self):
        """The injected note should match the indentation of the target line."""
        from specify_cli.integrations.codex import CodexIntegration

        content = (
            "---\nname: test\n---\n\n"
            "   - For each executable hook, output the following\n"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        lines = result.splitlines()
        note_line = [line for line in lines if "replace dots" in line][0]
        assert note_line.startswith("   "), "Note should preserve indentation"

    def test_hook_note_when_instruction_is_final_line_without_newline(self):
        """Note must not collapse onto the instruction line when the file
        ends without a trailing newline and the preceding line is not blank.
        """
        from specify_cli.integrations.codex import CodexIntegration

        # No blank line before the instruction and no trailing newline:
        # this is the case where the captured ``eol`` is empty and the
        # captured indent is also empty, so a missing line separator would
        # cause the note and instruction to collapse onto one line.
        content = (
            "---\nname: test\n---\n"
            "Body line\n"
            "- For each executable hook, output the following"
        )
        result = CodexIntegration._inject_hook_command_note(content)
        lines = result.splitlines()
        note_line_idx = next(
            i for i, line in enumerate(lines) if "replace dots" in line
        )
        instruction_line_idx = next(
            i for i, line in enumerate(lines)
            if line.lstrip().startswith("- For each executable hook")
        )
        assert note_line_idx < instruction_line_idx, (
            "Note must appear before the instruction"
        )
        assert "For each executable hook" not in lines[note_line_idx], (
            "Note and instruction must not be on the same line"
        )
