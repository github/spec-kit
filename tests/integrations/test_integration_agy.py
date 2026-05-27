"""Tests for AgyIntegration (Antigravity)."""

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestAgyIntegration(SkillsIntegrationTests):
    KEY = "agy"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"
    CONTEXT_FILE = "AGENTS.md"

    def test_options_include_skills_flag(self):
        """Override inherited test: AgyIntegration should not expose a --skills flag because .agents/ is its only layout."""
        i = get_integration(self.KEY)
        skills_opts = [o for o in i.options() if o.name == "--skills"]
        assert len(skills_opts) == 0

    def test_requires_cli_is_true(self):
        """agy is a CLI tool; requires_cli must be True."""
        i = get_integration(self.KEY)
        assert i.config["requires_cli"] is True

    def test_install_url_is_set(self):
        """install_url must point to the official installation page."""
        i = get_integration(self.KEY)
        assert i.config["install_url"] == "https://antigravity.google/"


class TestAgyAutoPromote:
    """--ai agy auto-promotes to integration path."""

    def test_ai_agy_without_ai_skills_auto_promotes(self, tmp_path):
        """--ai agy should work the same as --integration agy."""
        from typer.testing import CliRunner
        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--ai", "agy", "--no-git", "--script", "sh", "--ignore-agent-tools"])

        assert result.exit_code == 0, f"init --ai agy failed: {result.output}"
        assert (target / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_agy_setup_warning(self, tmp_path):
        """Agy integration should print a warning about v1.20.5 requirement during setup."""
        from typer.testing import CliRunner
        from specify_cli import app

        # Click >= 8.2 separates stdout and stderr natively
        runner = CliRunner()
        target = tmp_path / "test-proj2"
        result = runner.invoke(app, ["init", str(target), "--ai", "agy", "--no-git", "--script", "sh", "--ignore-agent-tools"])

        assert result.exit_code == 0
        assert "Warning: The .agents/ layout requires Antigravity v1.20.5 or newer" in result.stderr


class TestAgyBuildExecArgs:
    """agy non-interactive execution argument building."""

    def test_build_exec_args_returns_print_command(self):
        """build_exec_args should return ['agy', '--print', prompt]."""
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("describe my feature")
        assert result == ["agy", "--print", "describe my feature"]

    def test_build_exec_args_ignores_model(self):
        """agy does not support --model; model param must be ignored."""
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("my prompt", model="gemini-pro")
        assert result == ["agy", "--print", "my prompt"]

    def test_build_exec_args_ignores_output_json(self):
        """agy does not support JSON output; output_json param must be ignored."""
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("my prompt", output_json=False)
        assert result == ["agy", "--print", "my prompt"]


class TestAgyHookCommandNote:
    """Verify dot-to-hyphen normalization note is injected into hook sections."""

    def test_hook_note_injected_in_skills_with_hooks(self, tmp_path):
        """Skills with hook sections should contain the normalization note."""
        from specify_cli.integrations import get_integration
        from specify_cli.integrations.manifest import IntegrationManifest

        i = get_integration("agy")
        m = IntegrationManifest("agy", tmp_path)
        i.setup(tmp_path, m, script_type="sh")
        specify_skill = tmp_path / ".agents/skills/speckit-specify/SKILL.md"
        assert specify_skill.exists()
        content = specify_skill.read_text(encoding="utf-8")
        assert "replace dots" in content, (
            "speckit-specify should have dot-to-hyphen hook note"
        )

    def test_hook_note_not_in_skills_without_hooks(self):
        """Skills without hook sections should not get the note."""
        from specify_cli.integrations.agy import AgyIntegration

        content = "---\nname: test\ndescription: test\n---\n\nNo hooks here.\n"
        result = AgyIntegration._inject_hook_command_note(content)
        assert "replace dots" not in result

    def test_hook_note_idempotent(self):
        """Injecting the note twice must not duplicate it."""
        from specify_cli.integrations.agy import AgyIntegration

        content = (
            "---\nname: test\n---\n\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        once = AgyIntegration._inject_hook_command_note(content)
        twice = AgyIntegration._inject_hook_command_note(once)
        assert once == twice, "Hook note injection should be idempotent"

    def test_hook_note_preserves_indentation(self):
        """The injected note must match the indentation of the target line."""
        from specify_cli.integrations.agy import AgyIntegration

        content = (
            "---\nname: test\n---\n\n"
            "   - For each executable hook, output the following\n"
        )
        result = AgyIntegration._inject_hook_command_note(content)
        lines = result.splitlines()
        note_line = [l for l in lines if "replace dots" in l][0]
        assert note_line.startswith("   "), "Note should preserve indentation"
