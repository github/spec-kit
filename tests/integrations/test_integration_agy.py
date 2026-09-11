"""Tests for AgyIntegration (Antigravity)."""

from specify_cli.integrations import get_integration

from .test_integration_base_skills import SkillsIntegrationTests


class TestAgyIntegration(SkillsIntegrationTests):
    KEY = "agy"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"

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


class TestAgyInitFlow:
    """--integration agy creates expected files."""

    def test_integration_agy_creates_skills(self, tmp_path):
        """--integration agy should create skills directory."""
        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(app, ["init", str(target), "--integration", "agy", "--script", "sh", "--ignore-agent-tools"])

        assert result.exit_code == 0, f"init --integration agy failed: {result.output}"
        assert (target / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_agy_setup_warning(self, tmp_path):
        """Agy integration should print a warning about v1.20.5 requirement during setup."""
        from typer.testing import CliRunner

        from specify_cli import app

        # Click >= 8.2 separates stdout and stderr natively
        runner = CliRunner()
        target = tmp_path / "test-proj2"
        result = runner.invoke(app, ["init", str(target), "--integration", "agy", "--script", "sh", "--ignore-agent-tools"])

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

    def test_build_exec_args_honors_model(self):
        """agy >=1.20 supports --model; it must be prepended before --print."""
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("my prompt", model="gemini-pro")
        assert result == ["agy", "--model", "gemini-pro", "--print", "my prompt"]

    def test_build_exec_args_no_model_flag_when_model_is_none(self):
        """When model is None, no --model flag should appear in the args."""
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("my prompt", model=None)
        assert "--model" not in result

    def test_build_exec_args_ignores_output_json(self):
        """agy does not support JSON output; output_json param must be ignored."""
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("my prompt", output_json=False)
        assert result == ["agy", "--print", "my prompt"]

    def test_build_exec_args_extra_args_before_print(self, monkeypatch):
        """SPECKIT_INTEGRATION_AGY_EXTRA_ARGS must be inserted BEFORE --print.

        agy treats every token after --print as part of the prompt string,
        not as CLI flags.  Appending flags after --print (the previous
        behaviour) caused them to be silently absorbed into the prompt.

        See issue #4480.
        """
        from specify_cli.integrations import get_integration
        monkeypatch.setenv("SPECKIT_INTEGRATION_AGY_EXTRA_ARGS", "--verbose")
        i = get_integration("agy")
        result = i.build_exec_args("my prompt")
        # --verbose must appear before --print
        assert result.index("--verbose") < result.index("--print")
        assert result == ["agy", "--verbose", "--print", "my prompt"]

    def test_build_exec_args_add_dir_for_workspace(self, tmp_path):
        """--add-dir <project_root> must be injected before --print when project_root is given.

        Without --add-dir, agy cannot locate .agents/skills/ and reports
        'no active workspace', ignoring installed Spec Kit skills entirely.

        See issue #4480.
        """
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("my prompt", project_root=tmp_path)
        assert "--add-dir" in result
        add_dir_idx = result.index("--add-dir")
        print_idx = result.index("--print")
        assert add_dir_idx < print_idx, "--add-dir must come before --print"
        assert result[add_dir_idx + 1] == str(tmp_path)

    def test_build_exec_args_relative_project_root(self):
        """Relative project_root must be resolved to an absolute path.
        
        Passing a relative path to --add-dir breaks agy when the subprocess
        also changes cwd to that same relative path.
        """
        from pathlib import Path

        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        rel_path = Path("my_relative_dir")
        result = i.build_exec_args("my prompt", project_root=rel_path)
        assert "--add-dir" in result
        add_dir_idx = result.index("--add-dir")
        assert result[add_dir_idx + 1] == str(rel_path.resolve())

    def test_build_exec_args_no_add_dir_when_project_root_is_none(self):
        """When project_root is None, --add-dir must not appear."""
        from specify_cli.integrations import get_integration
        i = get_integration("agy")
        result = i.build_exec_args("my prompt", project_root=None)
        assert "--add-dir" not in result

    def test_build_exec_args_combined_flag_order(self, monkeypatch, tmp_path):
        """When model, project_root, and EXTRA_ARGS are all set, order must be:
        agy --model <m> --add-dir <d> <extra-args> --print <prompt>.
        """
        from specify_cli.integrations import get_integration
        monkeypatch.setenv("SPECKIT_INTEGRATION_AGY_EXTRA_ARGS", "--dangerously-skip-permissions")
        i = get_integration("agy")
        result = i.build_exec_args("hello", model="claude-3", project_root=tmp_path)
        assert result[0] == "agy"
        assert "--model" in result
        assert "--add-dir" in result
        assert "--dangerously-skip-permissions" in result
        print_idx = result.index("--print")
        for flag in ("--model", "--add-dir", "--dangerously-skip-permissions"):
            assert result.index(flag) < print_idx, f"{flag} must appear before --print"
        assert result[-1] == "hello"

    def test_build_exec_args_honors_executable_override(self, monkeypatch):
        from specify_cli.integrations import get_integration
        monkeypatch.setenv("SPECKIT_INTEGRATION_AGY_EXECUTABLE", "/custom/agy")
        i = get_integration("agy")
        assert i.build_exec_args("my prompt")[0] == "/custom/agy"

    def test_dispatch_command_forwards_project_root_as_add_dir(self, tmp_path):
        """dispatch_command must pass project_root to build_exec_args so --add-dir is included."""
        from unittest.mock import MagicMock, patch

        from specify_cli.integrations import get_integration

        i = get_integration("agy")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("specify_cli.integrations.base.shutil.which", return_value="agy"), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            result = i.dispatch_command("speckit.plan", stream=False, project_root=tmp_path)

        assert result["exit_code"] == 0
        argv = mock_run.call_args[0][0]
        assert "--add-dir" in argv
        assert argv[argv.index("--add-dir") + 1] == str(tmp_path)



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
        note_line = [ln for ln in lines if "replace dots" in ln][0]
        assert note_line.startswith("   "), "Note should preserve indentation"
