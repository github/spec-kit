"""Tests for CodexIntegration."""

from pathlib import Path

from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestCodexIntegration(SkillsIntegrationTests):
    KEY = "codex"
    FOLDER = ".agents/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".agents/skills"

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

    def test_plan_skill_has_no_context_placeholder(self, tmp_path):
        """The core plan skill must not carry a context-file placeholder —
        agent context files are owned by the opt-in agent-context extension."""
        target = tmp_path / "test-proj"
        target.mkdir()

        integration = get_integration("codex")
        manifest = IntegrationManifest("codex", target)
        integration.setup(target, manifest, script_type="sh")

        plan_skill = target / ".agents" / "skills" / "speckit-plan" / "SKILL.md"
        content = plan_skill.read_text(encoding="utf-8")
        assert "__CONTEXT_FILE__" not in content

    def test_plan_skill_ignores_extension_config(self, tmp_path):
        """The extension config must not influence rendered commands: the CLI
        no longer reads any context-file metadata when rendering."""
        import yaml

        target = tmp_path / "test-proj"
        target.mkdir()
        ext_cfg = (
            target
            / ".specify"
            / "extensions"
            / "agent-context"
            / "agent-context-config.yml"
        )
        ext_cfg.parent.mkdir(parents=True, exist_ok=True)
        ext_cfg.write_text(
            yaml.safe_dump(
                {
                    "context_file": "FROM_CONFIG.md",
                    "context_files": ["FROM_CONFIG.md", "ALSO_CONFIG.md"],
                }
            ),
            encoding="utf-8",
        )

        integration = get_integration("codex")
        manifest = IntegrationManifest("codex", target)
        integration.setup(target, manifest, script_type="sh")

        plan_skill = target / ".agents" / "skills" / "speckit-plan" / "SKILL.md"
        content = plan_skill.read_text(encoding="utf-8")
        assert "FROM_CONFIG.md" not in content
        assert "ALSO_CONFIG.md" not in content
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
        assert "constructing command invocations" in content
        assert "constructing slash commands" not in content

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


class TestCodexNoModelInvocationOption:
    """``--integration-options="--no-model-invocation"`` opts core skills out of implicit invocation (#2654)."""

    @staticmethod
    def _policy(skill_dir):
        import yaml

        return yaml.safe_load((skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8"))

    def test_options_include_no_model_invocation_flag(self):
        opts = get_integration("codex").options()
        matching = [o for o in opts if o.name == "--no-model-invocation"]
        assert len(matching) == 1
        assert matching[0].is_flag is True
        assert matching[0].default is False

    def test_setup_with_option_writes_policy_for_core_skills(self, tmp_path):
        i = get_integration("codex")
        m = IntegrationManifest("codex", tmp_path)
        created = i.setup(
            tmp_path, m, parsed_options={"no_model_invocation": True}, script_type="sh"
        )
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            assert self._policy(f.parent) == {"policy": {"allow_implicit_invocation": False}}, f.parent.name
        yamls = [f for f in created if f.name == "openai.yaml"]
        assert len(yamls) == len(skill_files)
        assert all(
            y.relative_to(tmp_path).as_posix() in m.files for y in yamls
        )

    def test_setup_without_option_writes_no_policy(self, tmp_path):
        i = get_integration("codex")
        created = i.setup(tmp_path, IntegrationManifest("codex", tmp_path), script_type="sh")
        assert not [f for f in created if f.name == "openai.yaml"]
        assert not list((tmp_path / ".agents" / "skills").glob("*/agents"))

    def test_extension_named_skill_dirs_are_not_core(self):
        i = get_integration("codex")
        assert i._is_core_command_skill_dir("speckit-plan")
        assert not i._is_core_command_skill_dir("speckit-git-feature")
        assert not i._is_core_command_skill_dir("plan")

    def test_cli_rejects_value_for_flag(self, tmp_path):
        import os

        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "codex-bad-option"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(
                app,
                ["init", "--here", "--integration", "codex", "--integration-options",
                 "--no-model-invocation=yes", "--script", "sh", "--ignore-agent-tools"],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "does not accept a value" in result.output
        assert not (project / ".agents" / "skills").exists()

    def test_option_persists_across_upgrade_and_clearing_removes_policy(self, tmp_path):
        import json

        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        project = _init_project(tmp_path, "codex", "--no-model-invocation")
        skills_dir = project / ".agents" / "skills"
        policies = sorted(skills_dir.glob("*/agents/openai.yaml"))
        assert len(policies) > 0
        state = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert state["integration_settings"]["codex"]["parsed_options"] == {"no_model_invocation": True}

        result = _run_in_project(project, ["integration", "upgrade", "codex", "--force"])
        assert result.exit_code == 0, result.output
        assert sorted(skills_dir.glob("*/agents/openai.yaml")) == policies

        result = _run_in_project(
            project,
            ["integration", "upgrade", "codex", "--force", "--integration-options", ""],
        )
        assert result.exit_code == 0, result.output
        assert not list(skills_dir.glob("*/agents/openai.yaml"))
        manifest = (project / ".specify" / "integrations" / "codex.manifest.json").read_text(encoding="utf-8")
        assert "openai.yaml" not in manifest

    def test_extension_skills_have_no_policy_after_upgrade(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        project = _init_project(tmp_path, "codex", "--no-model-invocation")
        result = _run_in_project(
            project, ["extension", "add", "--dev", str(REPO_ROOT / "extensions" / "git")]
        )
        assert result.exit_code == 0, result.output
        result = _run_in_project(project, ["integration", "upgrade", "codex", "--force"])
        assert result.exit_code == 0, result.output
        skills_dir = project / ".agents" / "skills"
        git_skills = sorted(skills_dir.glob("speckit-git-*/SKILL.md"))
        assert git_skills, "git extension skills were not generated"
        for f in git_skills:
            assert not (f.parent / "agents").exists(), f.parent.name
        assert (skills_dir / "speckit-specify" / "agents" / "openai.yaml").exists()

    def test_existing_openai_yaml_keys_are_preserved(self, tmp_path):
        import yaml

        existing = tmp_path / ".agents" / "skills" / "speckit-plan" / "agents" / "openai.yaml"
        existing.parent.mkdir(parents=True)
        existing.write_text("interface:\n  display_name: Plan\n", encoding="utf-8")
        i = get_integration("codex")
        i.setup(
            tmp_path,
            IntegrationManifest("codex", tmp_path),
            parsed_options={"no_model_invocation": True},
            script_type="sh",
        )
        data = yaml.safe_load(existing.read_text(encoding="utf-8"))
        assert data == {
            "interface": {"display_name": "Plan"},
            "policy": {"allow_implicit_invocation": False},
        }
