"""Tests for CodexIntegration."""

import os
import stat
from pathlib import Path

import pytest

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


class TestCodexNoModelInvocationOwnership:
    """``agents/openai.yaml`` handling must never destroy user configuration (#2654)."""

    PLAN_REL = ".agents/skills/speckit-plan/agents/openai.yaml"
    POLICY = {"allow_implicit_invocation": False}

    @staticmethod
    def _setup(project, enabled=True, manifest=None):
        manifest = manifest or IntegrationManifest("codex", project)
        get_integration("codex").setup(
            project,
            manifest,
            parsed_options={"no_model_invocation": True} if enabled else None,
            script_type="sh",
        )
        return manifest

    @staticmethod
    def _init(project, *options):
        from tests.specify_cli.integrations._helpers import _run_in_project

        args = ["init", "--here", "--force", "--integration", "codex",
                "--script", "sh", "--ignore-agent-tools"]
        if options:
            args += ["--integration-options", " ".join(options)]
        result = _run_in_project(project, args)
        assert result.exit_code == 0, result.output
        return result

    @staticmethod
    def _manifest(project):
        return IntegrationManifest.load("codex", project)

    @staticmethod
    def _yaml(path):
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def _seed(self, project, content=b"interface:\n  display_name: Plan\n"):
        path = project / self.PLAN_REL
        path.parent.mkdir(parents=True)
        path.write_bytes(content)
        return path

    def _other_policies(self, project):
        return [
            p for p in (project / ".agents" / "skills").glob("*/agents/openai.yaml")
            if p.relative_to(project).as_posix() != self.PLAN_REL
        ]

    @pytest.mark.parametrize(
        "content",
        [
            b"interface: [unclosed\n",
            b"- not\n- a mapping\n",
            b"policy: not-a-mapping\n",
            b"\xff\xfe\x00 invalid utf-8\n",
        ],
        ids=["invalid-yaml", "list-root", "scalar-policy", "invalid-utf8"],
    )
    def test_unusable_existing_file_aborts_without_overwriting(self, tmp_path, content):
        path = self._seed(tmp_path, content)
        with pytest.raises(ValueError, match="speckit-plan/agents/openai.yaml"):
            self._setup(tmp_path)
        assert path.read_bytes() == content
        assert self._other_policies(tmp_path) == []
        assert not list((tmp_path / ".agents" / "skills").glob("*/SKILL.md"))

    def test_unreadable_existing_file_aborts_without_overwriting(self, tmp_path, monkeypatch):
        path = self._seed(tmp_path)
        original = path.read_bytes()
        real_read_text = Path.read_text

        def read_text(self, *args, **kwargs):
            if self.name == "openai.yaml":
                raise PermissionError("denied")
            return real_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_text)
        with pytest.raises(ValueError, match="speckit-plan/agents/openai.yaml"):
            self._setup(tmp_path)
        monkeypatch.undo()
        assert path.read_bytes() == original

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    @pytest.mark.parametrize("linked", ["file", "agents-dir"])
    def test_symlink_outside_project_is_not_written(self, tmp_path, linked):
        project = tmp_path / "proj"
        outside = tmp_path / "outside"
        outside.mkdir()
        external = outside / "openai.yaml"
        external.write_bytes(b"interface:\n  display_name: External\n")
        agents_dir = project / ".agents" / "skills" / "speckit-plan" / "agents"
        if linked == "file":
            agents_dir.mkdir(parents=True)
            (agents_dir / "openai.yaml").symlink_to(external)
        else:
            agents_dir.parent.mkdir(parents=True)
            agents_dir.symlink_to(outside, target_is_directory=True)
        with pytest.raises(ValueError, match="symlink"):
            self._setup(project)
        assert external.read_bytes() == b"interface:\n  display_name: External\n"

    def test_existing_user_file_is_partial_and_keeps_its_keys(self, tmp_path):
        path = self._seed(tmp_path)
        manifest = self._setup(tmp_path)
        assert self._yaml(path) == {
            "interface": {"display_name": "Plan"},
            "policy": self.POLICY,
        }
        assert manifest.ownership_modes[self.PLAN_REL] == "partial"
        generated = self._other_policies(tmp_path)[0].relative_to(tmp_path).as_posix()
        assert manifest.ownership_modes[generated] == "whole"

    def test_user_file_already_disabling_implicit_invocation_is_not_claimed(self, tmp_path):
        content = b"policy:\n  allow_implicit_invocation: false\n"
        path = self._seed(tmp_path, content)
        manifest = self._setup(tmp_path)
        assert self.PLAN_REL not in manifest.files
        get_integration("codex").teardown(tmp_path, manifest)
        assert path.read_bytes() == content

    def test_teardown_removes_only_the_managed_policy_from_user_file(self, tmp_path):
        path = self._seed(tmp_path)
        manifest = self._setup(tmp_path)
        get_integration("codex").teardown(tmp_path, manifest)
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self._other_policies(tmp_path) == []

    def test_user_file_survives_upgrade_option_clearing_and_uninstall(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _run_in_project

        path = self._seed(tmp_path)
        self._init(tmp_path, "--no-model-invocation")
        assert self._manifest(tmp_path).ownership_modes[self.PLAN_REL] == "partial"

        result = _run_in_project(tmp_path, ["integration", "upgrade", "codex", "--force"])
        assert result.exit_code == 0, result.output
        assert self._manifest(tmp_path).ownership_modes[self.PLAN_REL] == "partial"
        assert self._yaml(path)["policy"] == self.POLICY

        result = _run_in_project(
            tmp_path, ["integration", "upgrade", "codex", "--force", "--integration-options", ""]
        )
        assert result.exit_code == 0, result.output
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self._other_policies(tmp_path) == []
        assert not [k for k in self._manifest(tmp_path).files if k.endswith("openai.yaml")]

        result = _run_in_project(
            tmp_path,
            ["integration", "upgrade", "codex", "--force",
             "--integration-options", "--no-model-invocation"],
        )
        assert result.exit_code == 0, result.output
        assert self._yaml(path)["policy"] == self.POLICY

        result = _run_in_project(tmp_path, ["integration", "uninstall", "codex"])
        assert result.exit_code == 0, result.output
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self._other_policies(tmp_path) == []

    def test_reinit_without_option_reconciles_previous_policies(self, tmp_path):
        path = self._seed(tmp_path)
        self._init(tmp_path, "--no-model-invocation")
        assert self._other_policies(tmp_path)

        self._init(tmp_path)
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self._other_policies(tmp_path) == []
        assert not list((tmp_path / ".agents" / "skills").glob("speckit-specify/agents"))
        assert not [k for k in self._manifest(tmp_path).files if k.endswith("openai.yaml")]

    def test_clearing_option_keeps_user_edits_to_a_generated_file(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _run_in_project

        self._init(tmp_path, "--no-model-invocation")
        path = tmp_path / self.PLAN_REL
        assert self._manifest(tmp_path).ownership_modes[self.PLAN_REL] == "whole"
        path.write_text(
            "interface:\n  display_name: Plan\npolicy:\n  allow_implicit_invocation: false\n",
            encoding="utf-8",
        )

        result = _run_in_project(
            tmp_path, ["integration", "upgrade", "codex", "--force", "--integration-options", ""]
        )
        assert result.exit_code == 0, result.output
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self._other_policies(tmp_path) == []

    def test_teardown_does_not_report_cleaned_user_file_as_preserved(self, tmp_path):
        path = self._seed(tmp_path)
        manifest = self._setup(tmp_path)
        _, skipped = get_integration("codex").teardown(tmp_path, manifest)
        assert path.resolve() not in [p.resolve() for p in skipped]

    def test_setup_accepts_unresolved_project_root(self, tmp_path):
        if not hasattr(os, "symlink"):
            pytest.skip("symlinks are unavailable")
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real, target_is_directory=True)
        manifest = self._setup(link)
        assert self._yaml(real / self.PLAN_REL) == {"policy": self.POLICY}
        assert self.PLAN_REL in manifest.files

    @pytest.mark.parametrize(
        "edited",
        [b"interface: [half-edited\n", b"\xff\xfe\x00 invalid utf-8\n"],
        ids=["invalid-yaml", "invalid-utf8"],
    )
    def test_clearing_option_keeps_unparseable_edit_of_generated_file(self, tmp_path, edited):
        from tests.specify_cli.integrations._helpers import _run_in_project

        self._init(tmp_path, "--no-model-invocation")
        path = tmp_path / self.PLAN_REL
        path.write_bytes(edited)

        result = _run_in_project(
            tmp_path, ["integration", "upgrade", "codex", "--force", "--integration-options", ""]
        )
        assert result.exit_code == 0, result.output
        assert path.read_bytes() == edited
        assert self._other_policies(tmp_path) == []
        # Upgrade's resync re-hashes the edit, so it must not stay ``whole``.
        assert self._manifest(tmp_path).ownership_modes[self.PLAN_REL] == "partial"

        result = _run_in_project(
            tmp_path, ["integration", "upgrade", "codex", "--force", "--integration-options", ""]
        )
        assert result.exit_code == 0, result.output
        assert path.read_bytes() == edited
        assert self._manifest(tmp_path).ownership_modes[self.PLAN_REL] == "partial"

        result = _run_in_project(tmp_path, ["integration", "uninstall", "codex"])
        assert result.exit_code == 0, result.output
        assert path.read_bytes() == edited

    def test_clearing_option_deletes_generated_file_after_cosmetic_change(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _run_in_project

        self._init(tmp_path, "--no-model-invocation")
        path = tmp_path / self.PLAN_REL
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") + b"# note\r\n")

        result = _run_in_project(tmp_path, ["integration", "upgrade", "codex", "--force"])
        assert result.exit_code == 0, result.output
        assert self._manifest(tmp_path).ownership_modes[self.PLAN_REL] == "whole"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") + b"# note\r\n")

        self._init(tmp_path)
        assert not path.exists()
        assert self._other_policies(tmp_path) == []

    def test_teardown_strips_policy_from_edited_generated_file(self, tmp_path):
        manifest = self._setup(tmp_path)
        path = tmp_path / self.PLAN_REL
        path.write_text(
            "interface:\n  display_name: Plan\npolicy:\n  allow_implicit_invocation: false\n",
            encoding="utf-8",
        )
        get_integration("codex").teardown(tmp_path, manifest)
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self._other_policies(tmp_path) == []

    def test_teardown_deletes_generated_file_after_cosmetic_change(self, tmp_path):
        manifest = self._setup(tmp_path)
        path = tmp_path / self.PLAN_REL
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n") + b"# note\r\n")
        get_integration("codex").teardown(tmp_path, manifest)
        assert not path.exists()

    def test_user_file_whose_policy_cannot_be_removed_stays_tracked(self, tmp_path):
        path = self._seed(tmp_path)
        self._setup(tmp_path).save()
        broken = path.read_bytes() + b"interface: [broken\n"
        path.write_bytes(broken)
        manifest = self._setup(tmp_path, enabled=False)
        assert path.read_bytes() == broken
        assert manifest.ownership_modes[self.PLAN_REL] == "partial"

    @pytest.mark.skipif(
        os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        reason="needs POSIX permissions enforced for the current user",
    )
    def test_clearing_option_keeps_unreadable_edit_of_generated_file(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _run_in_project

        self._init(tmp_path, "--no-model-invocation")
        path = tmp_path / self.PLAN_REL
        edited = b"interface:\n  display_name: Plan\npolicy:\n  allow_implicit_invocation: false\n"
        path.write_bytes(edited)
        path.chmod(0)
        try:
            result = _run_in_project(
                tmp_path, ["integration", "upgrade", "codex", "--force", "--integration-options", ""]
            )
        finally:
            path.chmod(0o644)
        assert result.exit_code == 0, result.output
        assert path.read_bytes() == edited
        assert self.PLAN_REL in self._manifest(tmp_path).files
        assert self._other_policies(tmp_path) == []

        self._init(tmp_path)
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self.PLAN_REL not in self._manifest(tmp_path).files

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_teardown_preserves_generated_file_under_symlinked_agents_dir(self, tmp_path):
        manifest = self._setup(tmp_path)
        agents_dir = (tmp_path / self.PLAN_REL).parent
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "openai.yaml").write_bytes((agents_dir / "openai.yaml").read_bytes())
        (agents_dir / "openai.yaml").unlink()
        agents_dir.rmdir()
        agents_dir.symlink_to(elsewhere, target_is_directory=True)
        content = (elsewhere / "openai.yaml").read_bytes()

        get_integration("codex").teardown(tmp_path, manifest)
        assert (elsewhere / "openai.yaml").read_bytes() == content
        assert agents_dir.is_symlink()
        assert self._other_policies(tmp_path) == []

    def test_policy_the_user_sets_after_clearing_is_never_claimed(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _run_in_project

        def upgrade(options):
            result = _run_in_project(
                tmp_path, ["integration", "upgrade", "codex", "--force", "--integration-options", options]
            )
            assert result.exit_code == 0, result.output

        self._init(tmp_path, "--no-model-invocation")
        path = tmp_path / self.PLAN_REL
        path.write_text(
            "interface:\n  display_name: Plan\npolicy:\n  allow_implicit_invocation: false\n",
            encoding="utf-8",
        )
        upgrade("")
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}
        assert self.PLAN_REL not in self._manifest(tmp_path).files

        user_owned = "interface:\n  display_name: Plan\npolicy:\n  allow_implicit_invocation: false\n"
        path.write_text(user_owned, encoding="utf-8")
        upgrade("--no-model-invocation")
        assert self.PLAN_REL not in self._manifest(tmp_path).files
        upgrade("")
        assert path.read_text(encoding="utf-8") == user_owned

    def test_generated_file_that_cannot_be_deleted_stays_tracked_for_retry(self, tmp_path, monkeypatch):
        self._setup(tmp_path).save()
        path = tmp_path / self.PLAN_REL
        real_unlink = Path.unlink

        def unlink(self, *args, **kwargs):
            if self.resolve() == path.resolve():
                raise PermissionError("locked")
            return real_unlink(self, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", unlink)
        manifest = self._setup(tmp_path, enabled=False)
        monkeypatch.undo()
        assert path.exists()
        assert manifest.ownership_modes[self.PLAN_REL] == "whole"
        assert self._other_policies(tmp_path) == []
        manifest.save()

        manifest = self._setup(tmp_path, enabled=False)
        assert not path.exists()
        assert self.PLAN_REL not in manifest.files

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_skills_dir_inside_project_is_rejected_before_writing(self, tmp_path):
        shared = tmp_path / "shared-skills"
        shared.mkdir()
        (tmp_path / ".agents").mkdir()
        (tmp_path / ".agents" / "skills").symlink_to(shared, target_is_directory=True)

        with pytest.raises(ValueError, match="--no-model-invocation.*symlink"):
            self._setup(tmp_path)
        assert not list(shared.rglob("*"))

        manifest = self._setup(tmp_path, enabled=False)
        assert list(shared.glob("*/SKILL.md"))
        assert not [k for k in manifest.files if k.endswith("openai.yaml")]

    @pytest.mark.skipif(
        os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        reason="needs POSIX permissions enforced for the current user",
    )
    def test_generated_file_unreadable_at_cleanup_is_deleted_on_retry(self, tmp_path):
        self._setup(tmp_path).save()
        path = tmp_path / self.PLAN_REL
        path.chmod(0)
        try:
            manifest = self._setup(tmp_path, enabled=False)
        finally:
            path.chmod(0o644)
        assert manifest.ownership_modes[self.PLAN_REL] == "whole"
        manifest.save()

        self._setup(tmp_path, enabled=False)
        assert not path.exists()
        assert not path.parent.exists()

    def test_cleaned_edit_of_a_former_core_policy_survives_upgrade(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _run_in_project

        self._init(tmp_path)
        rel = ".agents/skills/speckit-retired/agents/openai.yaml"
        path = tmp_path / rel
        path.parent.mkdir(parents=True)
        path.write_text(
            "interface:\n  display_name: Retired\npolicy:\n  allow_implicit_invocation: false\n",
            encoding="utf-8",
        )
        manifest = self._manifest(tmp_path)
        manifest._files[rel] = "0" * 64
        manifest._ownership_modes[rel] = "whole"
        manifest.save()

        result = _run_in_project(tmp_path, ["integration", "upgrade", "codex", "--force"])
        assert result.exit_code == 0, result.output
        assert self._yaml(path) == {"interface": {"display_name": "Retired"}}
        # Once the policy is gone the file is the user's, not tracked.
        assert rel not in self._manifest(tmp_path).files

        user_owned = "interface:\n  display_name: Retired\npolicy:\n  allow_implicit_invocation: false\n"
        path.write_text(user_owned, encoding="utf-8")
        result = _run_in_project(tmp_path, ["integration", "upgrade", "codex", "--force"])
        assert result.exit_code == 0, result.output
        result = _run_in_project(tmp_path, ["integration", "uninstall", "codex"])
        assert result.exit_code == 0, result.output
        assert path.read_text(encoding="utf-8") == user_owned

    def test_directory_at_policy_path_is_not_kept_tracked(self, tmp_path):
        self._setup(tmp_path).save()
        path = tmp_path / self.PLAN_REL
        path.unlink()
        path.mkdir()
        manifest = self._setup(tmp_path, enabled=False)
        assert path.is_dir()
        assert self.PLAN_REL not in manifest.files

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_symlinked_skill_dir_is_rejected_before_writing(self, tmp_path):
        shared = tmp_path / "shared-plan"
        shared.mkdir()
        skills = tmp_path / ".agents" / "skills"
        skills.mkdir(parents=True)
        (skills / "speckit-plan").symlink_to(shared, target_is_directory=True)

        with pytest.raises(ValueError, match="--no-model-invocation.*symlink"):
            self._setup(tmp_path)
        assert not list(skills.glob("*/SKILL.md"))
        assert not list(shared.iterdir())

    def test_round_trip_keeps_values_yaml_1_1_would_reinterpret(self, tmp_path):
        content = (
            "interface:\n"
            "  display_name: On\n"
            "  short_description: no\n"
            "  default_prompt: 1:30\n"
            "  brand_color: '0o12'\n"
            "  icon_small: =\n"
            "custom:\n"
            "  count: 010\n"
            "  big: 1_000\n"
            "  ratio: 1e3\n"
            "  when: 2026-01-01\n"
            "  enabled: yes\n"
        )
        path = self._seed(tmp_path, content.encode("utf-8"))
        manifest = self._setup(tmp_path)
        # The strings are written quoted, so YAML 1.1 readers see them too.
        assert self._yaml(path)["interface"]["display_name"] == "On"
        assert self._yaml(path)["custom"]["enabled"] == "yes"

        import yaml
        from specify_cli.integrations.codex import _Yaml12Loader

        original = yaml.load(content, Loader=_Yaml12Loader)
        assert original["interface"]["display_name"] == "On"
        written = path.read_text(encoding="utf-8")
        assert yaml.load(written, Loader=_Yaml12Loader) == {**original, "policy": self.POLICY}
        assert "count: 010\n" in written and "ratio: 1e3\n" in written

        get_integration("codex").teardown(tmp_path, manifest)
        assert yaml.load(path.read_text(encoding="utf-8"), Loader=_Yaml12Loader) == original

    def test_round_trip_keeps_the_text_of_numbers(self, tmp_path):
        content = (
            b"interface:\n  display_name: 1.10\n  short_description: 007\n"
            b"  brand_color: 0x1F\n  default_prompt: +1\n"
            b"dependencies:\n  tools:\n  - type: mcp\n    value: docs\n"
            b"    oauth:\n      callbackPort: 8080\n"
        )
        path = self._seed(tmp_path, content)
        manifest = self._setup(tmp_path)
        assert path.read_bytes().startswith(content)
        get_integration("codex").teardown(tmp_path, manifest)
        assert path.read_bytes() == content

    def test_tracked_file_already_holding_the_policy_is_not_rewritten(self, tmp_path):
        path = self._seed(tmp_path)
        self._setup(tmp_path).save()
        commented = b"# my note\n" + path.read_bytes()
        path.write_bytes(commented)
        manifest = self._setup(tmp_path)
        assert path.read_bytes() == commented
        assert manifest.ownership_modes[self.PLAN_REL] == "partial"

    @pytest.mark.skipif(
        os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        reason="needs POSIX permissions enforced for the current user",
    )
    def test_read_only_user_file_is_not_replaced(self, tmp_path):
        path = self._seed(tmp_path)
        original = path.read_bytes()
        path.chmod(0o444)
        try:
            with pytest.raises(PermissionError):
                self._setup(tmp_path)
            assert path.read_bytes() == original
        finally:
            path.chmod(0o644)

    def test_generated_file_with_a_non_boolean_policy_is_not_deleted(self, tmp_path):
        manifest = self._setup(tmp_path)
        path = tmp_path / self.PLAN_REL
        edited = b"policy:\n  allow_implicit_invocation: 0  # keep off\n"
        path.write_bytes(edited)
        get_integration("codex").teardown(tmp_path, manifest)
        assert path.read_bytes() == edited

    def test_teardown_warns_when_a_user_file_keeps_the_policy(self, tmp_path, caplog):
        path = self._seed(tmp_path)
        manifest = self._setup(tmp_path)
        broken = path.read_bytes() + b"interface: [broken\n"
        path.write_bytes(broken)
        with caplog.at_level("WARNING", logger="specify_cli.integrations.codex"):
            get_integration("codex").teardown(tmp_path, manifest)
        assert path.read_bytes() == broken
        assert "remove it by hand" in caplog.text

    @pytest.mark.parametrize(
        "content",
        [
            b"interface: invalid\n",
            b"dependencies: invalid\n",
            b"dependencies:\n  tools: invalid\n",
            b"dependencies:\n  tools:\n    - not-a-mapping\n",
            b"dependencies:\n  tools:\n    - type: mcp\n      oauth: 8080\n",
            b"policy:\n  products: codex\n",
        ],
        ids=["interface", "dependencies", "tools", "tool-item", "oauth", "products"],
    )
    def test_file_codex_would_ignore_aborts_without_overwriting(self, tmp_path, content):
        path = self._seed(tmp_path, content)
        with pytest.raises(ValueError, match="speckit-plan/agents/openai.yaml.*Codex would ignore"):
            self._setup(tmp_path)
        assert path.read_bytes() == content
        assert not list((tmp_path / ".agents" / "skills").glob("*/SKILL.md"))

    def test_file_with_every_supported_field_is_accepted(self, tmp_path):
        content = (
            b"interface:\n  display_name: Plan\n  short_description: Plans\n"
            b"dependencies:\n  tools:\n    - type: mcp\n      value: docs\n"
            b"      oauth:\n        callbackPort: 8080\n"
            b"policy:\n  products: [codex]\n"
        )
        path = self._seed(tmp_path, content)
        self._setup(tmp_path)
        assert self._yaml(path)["policy"] == {"products": ["codex"], **self.POLICY}
        assert self._yaml(path)["dependencies"]["tools"][0]["oauth"] == {"callbackPort": 8080}

    @staticmethod
    def _fail_policy_writes(monkeypatch):
        """Simulate a write that fails part-way, for in-place and staged writes."""
        real_write_bytes = Path.write_bytes
        real_replace = os.replace

        def write_bytes(self, data):
            if self.name == "openai.yaml" and self.exists():
                real_write_bytes(self, data[:5])
                raise OSError("disk full")
            return real_write_bytes(self, data)

        def replace(src, dst, *args, **kwargs):
            if Path(dst).name == "openai.yaml":
                raise OSError("disk full")
            return real_replace(src, dst, *args, **kwargs)

        monkeypatch.setattr(Path, "write_bytes", write_bytes)
        monkeypatch.setattr(os, "replace", replace)

    def test_failed_write_at_setup_leaves_user_file_intact(self, tmp_path, monkeypatch):
        path = self._seed(tmp_path)
        original = path.read_bytes()
        self._fail_policy_writes(monkeypatch)
        with pytest.raises(OSError, match="disk full"):
            self._setup(tmp_path)
        monkeypatch.undo()
        assert path.read_bytes() == original
        assert [p.name for p in path.parent.iterdir()] == ["openai.yaml"]

    def test_failed_write_at_cleanup_leaves_user_file_intact_and_tracked(self, tmp_path, monkeypatch):
        path = self._seed(tmp_path)
        self._setup(tmp_path).save()
        with_policy = path.read_bytes()
        self._fail_policy_writes(monkeypatch)
        manifest = self._setup(tmp_path, enabled=False)
        monkeypatch.undo()
        assert path.read_bytes() == with_policy
        assert manifest.ownership_modes[self.PLAN_REL] == "partial"
        assert [p.name for p in path.parent.iterdir()] == ["openai.yaml"]

        manifest.save()
        self._setup(tmp_path, enabled=False)
        assert self._yaml(path) == {"interface": {"display_name": "Plan"}}

    @pytest.mark.skipif(os.name == "nt", reason="needs POSIX file modes")
    def test_rewritten_user_file_keeps_its_mode(self, tmp_path):
        path = self._seed(tmp_path)
        path.chmod(0o640)
        manifest = self._setup(tmp_path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o640
        get_integration("codex").teardown(tmp_path, manifest)
        assert stat.S_IMODE(path.stat().st_mode) == 0o640

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_policy_behind_dangling_agents_symlink_stays_tracked(self, tmp_path):
        self._setup(tmp_path).save()
        path = tmp_path / self.PLAN_REL
        generated = path.read_bytes()
        agents_dir = path.parent
        path.unlink()
        agents_dir.rmdir()
        agents_dir.symlink_to(tmp_path / "missing", target_is_directory=True)

        manifest = self._setup(tmp_path, enabled=False)
        assert manifest.ownership_modes[self.PLAN_REL] == "whole"
        manifest.save()

        agents_dir.unlink()
        agents_dir.mkdir()
        path.write_bytes(generated)
        manifest = self._setup(tmp_path, enabled=False)
        assert not path.exists()
        assert self.PLAN_REL not in manifest.files

    @pytest.mark.parametrize(
        "blocker",
        [".agents/skills/speckit-plan/agents", ".agents/skills/speckit-plan"],
        ids=["agents-file", "skill-dir-file"],
    )
    def test_non_directory_on_policy_path_is_rejected_before_writing(self, tmp_path, blocker):
        (tmp_path / blocker).parent.mkdir(parents=True)
        (tmp_path / blocker).write_bytes(b"not a directory\n")
        with pytest.raises(ValueError, match=f"{blocker} is not a directory"):
            self._setup(tmp_path)
        assert not list((tmp_path / ".agents" / "skills").glob("*/SKILL.md"))
        assert (tmp_path / blocker).read_bytes() == b"not a directory\n"

    def test_stale_cleanup_never_deletes_policy_files(self):
        exclusions = get_integration("codex").stale_cleanup_exclusions()
        assert self.PLAN_REL in exclusions
        assert ".agents/skills/speckit-specify/agents/openai.yaml" in exclusions


@pytest.mark.filterwarnings("ignore:Cannot compose command 'speckit.wrap-test':UserWarning")
class TestCodexNoModelInvocationPresets:
    """Preset overrides rewrite ``SKILL.md`` without running ``setup()`` (#2654)."""

    SKILL = ".agents/skills/speckit-specify"

    @staticmethod
    def _add_and_remove_self_test_preset(project):
        from tests.specify_cli.integrations._helpers import _run_in_project

        skill_md = project / TestCodexNoModelInvocationPresets.SKILL / "SKILL.md"
        result = _run_in_project(
            project, ["preset", "add", "--dev", str(REPO_ROOT / "presets" / "self-test")]
        )
        assert result.exit_code == 0, result.output
        overridden = "preset:self-test" in skill_md.read_text(encoding="utf-8")
        policy_while_overridden = sorted((skill_md.parent).rglob("openai.yaml"))
        result = _run_in_project(project, ["preset", "remove", "self-test"])
        assert result.exit_code == 0, result.output
        assert "preset:self-test" not in skill_md.read_text(encoding="utf-8")
        return overridden, policy_while_overridden

    def test_policy_survives_preset_override_and_removal(self, tmp_path):
        import yaml

        from tests.specify_cli.integrations._helpers import _init_project

        project = _init_project(tmp_path, "codex", "--no-model-invocation")
        policy = project / self.SKILL / "agents" / "openai.yaml"
        before = policy.read_bytes()
        overridden, during = self._add_and_remove_self_test_preset(project)
        assert overridden
        assert during == [policy]
        assert policy.read_bytes() == before
        assert yaml.safe_load(before) == {"policy": {"allow_implicit_invocation": False}}

    def test_preset_override_adds_no_policy_without_option(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _init_project

        project = _init_project(tmp_path, "codex")
        overridden, during = self._add_and_remove_self_test_preset(project)
        assert overridden
        assert during == []
        assert not (project / self.SKILL / "agents").exists()


class TestCodexManifestInternals:
    """Pins the manifest internals the Codex policy cleanup depends on.

    The public manifest API cannot record a prior hash without re-reading the
    file, and has no public path validator, so the Codex package uses
    ``IntegrationManifest._files`` and ``_validate_record_path``. A change to
    either should fail here rather than silently in cleanup.
    """

    REL = ".agents/skills/speckit-plan/agents/openai.yaml"

    def test_retained_entry_is_public_and_survives_save_and_load(self, tmp_path):
        codex = get_integration("codex")
        manifest = IntegrationManifest("codex", tmp_path)
        codex._retain(manifest, self.REL, "0" * 64, "partial")
        assert manifest.files == {self.REL: "0" * 64}
        assert manifest.ownership_modes == {self.REL: "partial"}

        manifest.save()
        loaded = IntegrationManifest.load("codex", tmp_path)
        assert loaded.files == {self.REL: "0" * 64}
        assert loaded.ownership_modes == {self.REL: "partial"}

    def test_uninstall_honours_retained_entries(self, tmp_path):
        import hashlib

        codex = get_integration("codex")
        kept = tmp_path / ".agents/skills/speckit-specify/agents/openai.yaml"
        removed = tmp_path / self.REL
        for path in (kept, removed):
            path.parent.mkdir(parents=True)
            path.write_bytes(b"policy:\n  allow_implicit_invocation: false\n")
        digest = hashlib.sha256(removed.read_bytes()).hexdigest()
        manifest = IntegrationManifest("codex", tmp_path)
        codex._retain(manifest, kept.relative_to(tmp_path).as_posix(), digest, "partial")
        codex._retain(manifest, self.REL, digest, "whole")

        manifest.uninstall(tmp_path, remove_manifest=False)
        assert kept.exists()
        assert not removed.exists()

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_validate_record_path_accepts_missing_file_and_rejects_symlinked_ancestor(self, tmp_path):
        from specify_cli.integrations.manifest import _validate_record_path

        assert _validate_record_path(Path(self.REL), tmp_path) == tmp_path / self.REL

        real = tmp_path / "elsewhere"
        real.mkdir()
        (tmp_path / ".agents").symlink_to(real, target_is_directory=True)
        with pytest.raises(ValueError):
            _validate_record_path(Path(self.REL), tmp_path)
