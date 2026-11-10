"""Tests for NexoraIntegration (Nexora Code)."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from specify_cli.extensions import CORE_COMMAND_NAMES
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest
from specify_cli.integrations.nexora import ARGUMENT_HINTS, NexoraIntegration
from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

from .test_integration_base_skills import SkillsIntegrationTests

REPO_ROOT = Path(__file__).resolve().parents[2]

# Extension id → command stems; each becomes ``speckit-<ext>-<stem>/SKILL.md``.
BUNDLED_EXTENSION_COMMANDS = {
    "bug": ("assess", "fix", "test"),
    "assess": ("decide", "define", "intake", "research", "shape"),
}


def _skill_frontmatter(skill_file: Path) -> dict:
    content = skill_file.read_text(encoding="utf-8")
    return yaml.safe_load(content.split("---", 2)[1])


class TestNexoraIntegration(SkillsIntegrationTests):
    KEY = "nexora"
    FOLDER = ".nexora/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".nexora/skills"

    def test_options_include_skills_flag(self):
        """Override inherited test: Nexora has a single skills-only layout, so
        it declares neither ``--skills`` nor any other integration option."""
        i = get_integration(self.KEY)
        assert [o for o in i.options() if o.name == "--skills"] == []
        assert i.options() == []

    def test_requires_cli_is_false(self):
        """The editor extension needs no CLI; the npm CLI is optional."""
        i = get_integration(self.KEY)
        assert i.config["requires_cli"] is False

    def test_install_url_points_at_marketplace(self):
        i = get_integration(self.KEY)
        assert i.config["install_url"] == (
            "https://marketplace.visualstudio.com/items"
            "?itemName=nexora-intelligence.nexora-code"
        )

    def test_display_name(self):
        assert get_integration(self.KEY).config["name"] == "Nexora Code"

    def test_multi_install_safe(self):
        assert get_integration(self.KEY).multi_install_safe is True

    def test_invoke_separator_is_hyphen(self):
        i = get_integration(self.KEY)
        assert i.invoke_separator == "-"
        assert i.effective_invoke_separator() == "-"
        assert i.invoke_separator_for_mode(True) == "-"

    def test_build_command_invocation_uses_hyphen(self):
        i = get_integration(self.KEY)
        assert i.build_command_invocation("plan") == "/speckit-plan"
        assert i.build_command_invocation("bug.assess") == "/speckit-bug-assess"

    def test_build_exec_args_returns_none_without_cli(self):
        """No CLI dispatch: ``requires_cli`` is False so no argv is produced."""
        i = get_integration(self.KEY)
        assert i.build_exec_args("hello") is None
        assert i.build_exec_args("hello", model="x", output_json=True) is None

    def test_skills_dest(self, tmp_path):
        i = get_integration(self.KEY)
        assert i.skills_dest(tmp_path) == tmp_path / ".nexora" / "skills"

    def test_setup_creates_core_skill_files(self, tmp_path):
        i = get_integration(self.KEY)
        m = IntegrationManifest(self.KEY, tmp_path)
        i.setup(tmp_path, m, script_type="sh")
        for name in CORE_COMMAND_NAMES:
            skill = tmp_path / ".nexora" / "skills" / f"speckit-{name}" / "SKILL.md"
            assert skill.exists(), f"missing {skill}"
            assert _skill_frontmatter(skill)["name"] == f"speckit-{name}"

    def test_teardown_removes_skills_and_leaves_foreign_skill(self, tmp_path):
        i = get_integration(self.KEY)
        foreign = tmp_path / ".nexora" / "skills" / "my-own-skill" / "SKILL.md"
        foreign.parent.mkdir(parents=True)
        foreign.write_text("# mine\n", encoding="utf-8")

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.install(tmp_path, m)
        m.save()
        removed, skipped = i.uninstall(tmp_path, m)

        assert len(removed) == len(created)
        assert skipped == []
        assert not (tmp_path / ".nexora" / "skills" / "speckit-plan").exists()
        assert foreign.read_text(encoding="utf-8") == "# mine\n"


class TestNexoraInvocationStyle:
    """Nexora is a slash-skills agent; the shared helpers must agree."""

    def test_is_slash_skills_agent(self):
        from specify_cli._invocation_style import is_slash_skills_agent

        assert is_slash_skills_agent("nexora", True) is True
        # Conditional, like Claude Code, Antigravity and Alquimia: the
        # ``False`` branch never arises because ``SkillsIntegration``
        # persists ``ai_skills`` unconditionally.
        assert is_slash_skills_agent("nexora", False) is False

    def test_classified_as_a_conditional_slash_agent(self):
        from specify_cli._invocation_style import (
            ALWAYS_SLASH_AGENTS,
            CONDITIONAL_SLASH_AGENTS,
            DOLLAR_SKILLS_AGENTS,
            SKILL_COLON_AGENTS,
        )

        assert "nexora" in CONDITIONAL_SLASH_AGENTS
        assert "nexora" not in ALWAYS_SLASH_AGENTS
        assert "nexora" not in DOLLAR_SKILLS_AGENTS
        assert "nexora" not in SKILL_COLON_AGENTS

    def test_invocation_prefix_is_slash(self):
        from specify_cli._invocation_style import (
            get_invocation_prefix,
            is_dollar_skills_agent,
        )

        assert get_invocation_prefix("nexora", True) == "/"
        assert is_dollar_skills_agent("nexora", True) is False

    def test_ai_skills_is_always_persisted(self):
        i = get_integration("nexora")
        assert i.is_skills_mode() is True
        assert i.is_skills_mode({}, project_root=None) is True

    def test_hook_invocation_renders_the_hyphenated_form(self, tmp_path, monkeypatch):
        import specify_cli
        from specify_cli.extensions import HookExecutor

        monkeypatch.setattr(
            specify_cli,
            "load_init_options",
            lambda _root: {"ai": "nexora", "ai_skills": True},
        )

        rendered = HookExecutor(tmp_path)._render_hook_invocation("speckit.git.commit")

        assert rendered == "/speckit-git-commit"
        assert "/speckit." not in rendered


class TestNexoraArgumentHints:
    """Verify that argument-hint frontmatter is injected for Nexora skills."""

    def test_converge_has_no_argument_hint(self):
        """Converge should not advertise unsupported feature-name arguments."""
        assert "converge" not in ARGUMENT_HINTS

    def test_every_other_core_command_has_a_hint(self):
        assert set(ARGUMENT_HINTS) == set(CORE_COMMAND_NAMES) - {"converge"}
        assert all(hint.strip() for hint in ARGUMENT_HINTS.values())

    def test_all_skills_have_hints(self, tmp_path):
        """Every skill with a configured hint must contain an argument-hint line."""
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            stem = f.parent.name.removeprefix("speckit-")
            content = f.read_text(encoding="utf-8")
            if stem in ARGUMENT_HINTS:
                assert "argument-hint:" in content, (
                    f"{f.parent.name}/SKILL.md is missing argument-hint frontmatter"
                )
            else:
                assert "argument-hint:" not in content, (
                    f"{f.parent.name}/SKILL.md unexpectedly has argument-hint frontmatter"
                )

    def test_hints_match_expected_values(self, tmp_path):
        """Each skill's argument-hint must match the expected text."""
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        for f in skill_files:
            stem = f.parent.name.removeprefix("speckit-")
            expected_hint = ARGUMENT_HINTS.get(stem)
            content = f.read_text(encoding="utf-8")
            if expected_hint is None:
                assert "argument-hint:" not in content
            else:
                assert f'argument-hint: "{expected_hint}"' in content, (
                    f"{f.parent.name}/SKILL.md: expected hint '{expected_hint}' not found"
                )
                assert _skill_frontmatter(f)["argument-hint"] == expected_hint

    def test_hint_is_inside_frontmatter(self, tmp_path):
        """argument-hint must appear between the --- delimiters, not in the body."""
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        for f in (f for f in created if f.name == "SKILL.md"):
            content = f.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"No frontmatter in {f.parent.name}/SKILL.md"
            frontmatter, body = parts[1], parts[2]
            stem = f.parent.name.removeprefix("speckit-")
            if stem in ARGUMENT_HINTS:
                assert "argument-hint:" in frontmatter
                assert "argument-hint:" not in body
            else:
                assert "argument-hint:" not in content

    def test_hint_appears_after_description(self, tmp_path):
        """argument-hint must immediately follow the description scalar."""
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        for f in (f for f in created if f.name == "SKILL.md"):
            stem = f.parent.name.removeprefix("speckit-")
            if stem not in ARGUMENT_HINTS:
                continue
            lines = f.read_text(encoding="utf-8").splitlines()
            idx = next(
                (n for n, line in enumerate(lines) if line.startswith("description:")),
                None,
            )
            assert idx is not None, f"{f.parent.name}/SKILL.md: no description: line"
            # Skip folded continuation lines of a long description.
            idx += 1
            while idx < len(lines) and (lines[idx][:1] in (" ", "\t") or lines[idx] == ""):
                idx += 1
            assert lines[idx].startswith("argument-hint:"), (
                f"{f.parent.name}/SKILL.md: argument-hint does not follow description"
            )

    def test_inject_argument_hint_only_in_frontmatter(self):
        """inject_argument_hint must not modify description: lines in the body."""
        content = (
            "---\ndescription: My command\n---\n\ndescription: this is body text\n"
        )
        result = NexoraIntegration.inject_argument_hint(content, "Test hint")
        lines = result.splitlines()
        assert sum(1 for ln in lines if ln.startswith("argument-hint:")) == 1
        assert lines[1] == "description: My command"
        assert lines[2] == 'argument-hint: "Test hint"'
        assert result.endswith("description: this is body text\n")

    def test_inject_argument_hint_skips_if_already_present(self):
        content = (
            "---\n"
            "description: My command\n"
            'argument-hint: "Existing hint"\n'
            "---\n"
            "\n"
            "Body text\n"
        )
        result = NexoraIntegration.inject_argument_hint(content, "New hint")
        assert result == content

    def test_inject_argument_hint_escapes_quotes_and_backslashes(self):
        content = "---\nname: speckit-x\ndescription: d\n---\n\nBody\n"
        result = NexoraIntegration.inject_argument_hint(content, 'say "hi" \\ bye')
        parsed = yaml.safe_load(result.split("---", 2)[1])
        assert parsed["argument-hint"] == 'say "hi" \\ bye'

    def test_inject_argument_hint_without_description_is_a_no_op(self):
        content = "---\nname: speckit-x\n---\n\nBody\n"
        assert NexoraIntegration.inject_argument_hint(content, "hint") == content

    @pytest.mark.parametrize(
        "description",
        [
            # Folded by PyYAML across indented continuation lines.
            "A fairly long description that needs to wrap across multiple lines "
            "when dumped by PyYAML because it comfortably exceeds the width limit.",
            # Embedded paragraph break: PyYAML emits unindented blank lines.
            "First paragraph of a fairly long description that will need to wrap "
            "across multiple lines when dumped by PyYAML.\n\nSecond paragraph.",
        ],
    )
    def test_inject_argument_hint_survives_folded_description(self, description):
        frontmatter = {
            "name": "speckit-specify",
            "description": description,
            "compatibility": "Requires spec-kit project structure with .specify/ directory",
        }
        frontmatter_text = yaml.safe_dump(
            frontmatter, sort_keys=False, allow_unicode=True
        ).strip()
        content = f"---\n{frontmatter_text}\n---\n\nBody text\n"

        result = NexoraIntegration.inject_argument_hint(content, "Describe the feature")

        parsed = yaml.safe_load(result.split("---", 2)[1])
        assert parsed["argument-hint"] == "Describe the feature"
        assert parsed["description"] == description
        assert parsed["compatibility"] == frontmatter["compatibility"]

    def test_post_process_injects_hint_for_core_skill(self):
        i = get_integration("nexora")
        result = i.post_process_skill_content(
            "---\nname: speckit-plan\ndescription: Plan it\n---\n\nBody\n"
        )
        assert yaml.safe_load(result.split("---", 2)[1])["argument-hint"] == (
            ARGUMENT_HINTS["plan"]
        )

    def test_post_process_leaves_extension_skill_without_hint(self):
        i = get_integration("nexora")
        content = "---\nname: speckit-bug-assess\ndescription: Assess\n---\n\nBody\n"
        assert "argument-hint:" not in i.post_process_skill_content(content)

    def test_post_process_leaves_converge_without_hint(self):
        i = get_integration("nexora")
        content = "---\nname: speckit-converge\ndescription: Converge\n---\n\nBody\n"
        assert "argument-hint:" not in i.post_process_skill_content(content)

    def test_post_process_is_idempotent(self):
        i = get_integration("nexora")
        content = "---\nname: speckit-tasks\ndescription: Tasks\n---\n\nBody\n"
        once = i.post_process_skill_content(content)
        assert i.post_process_skill_content(once) == once

    def test_post_process_keeps_shared_hook_note(self):
        """The base class hook note must still be applied under the override."""
        i = get_integration("nexora")
        content = (
            "---\nname: speckit-specify\ndescription: Spec\n---\n\n"
            "- For each executable hook, output the following based on its flag:\n"
        )
        result = i.post_process_skill_content(content)
        assert "replace dots" in result
        assert "/speckit-git-commit" in result
        assert "$speckit-" not in result


class TestNexoraHookCommandNote:
    def test_hook_note_injected_in_skills_with_hooks(self, tmp_path):
        """Skills with hook sections carry the note and valid manifest hashes."""
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", tmp_path)
        created = i.setup(tmp_path, m, script_type="sh")
        specify_skill = tmp_path / ".nexora/skills/speckit-specify/SKILL.md"
        assert specify_skill.exists()
        content = specify_skill.read_text(encoding="utf-8")
        assert "replace dots" in content
        rel_key = ".nexora/skills/speckit-specify/SKILL.md"
        assert rel_key in m.files
        assert m.files[rel_key] == hashlib.sha256(specify_skill.read_bytes()).hexdigest()
        assert m.check_modified() == []
        assert len(created) > 0

    def test_hook_note_not_in_skills_without_hooks(self):
        content = "---\nname: test\ndescription: test\n---\n\nNo hooks here.\n"
        assert "replace dots" not in NexoraIntegration._inject_hook_command_note(content)


class TestNexoraInitFlow:
    """``specify init --integration nexora`` and ``integration status``."""

    def test_init_creates_skills_without_agent_tool_check(self, tmp_path):
        """No CLI is required, so init succeeds without --ignore-agent-tools."""
        from typer.testing import CliRunner

        from specify_cli import app

        target = tmp_path / "nexora-proj"
        result = CliRunner().invoke(
            app,
            ["init", str(target), "--integration", "nexora", "--script", "sh"],
        )

        assert result.exit_code == 0, f"init --integration nexora failed: {result.output}"
        assert (target / ".nexora" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert "/speckit." not in result.output
        assert "/speckit-specify" in result.output

    def test_init_records_nexora_as_default_with_skills(self, tmp_path):
        project = _init_project(tmp_path, "nexora")
        opts = json.loads(
            (project / ".specify" / "init-options.json").read_text(encoding="utf-8")
        )
        assert opts["ai"] == "nexora"
        assert opts["ai_skills"] is True
        assert (project / ".specify" / "integrations" / "nexora.manifest.json").exists()

    def test_integration_status_reports_nexora(self, tmp_path):
        project = _init_project(tmp_path, "nexora")

        result = _run_in_project(project, ["integration", "status"])

        assert result.exit_code == 0, result.output
        assert "Integration status: OK" in result.output
        assert "Default integration: nexora" in result.output
        assert "Installed integrations: nexora" in result.output
        assert "Modified managed files: 0" in result.output
        assert "Missing managed files: 0" in result.output

    def test_integration_status_json_reports_nexora(self, tmp_path):
        project = _init_project(tmp_path, "nexora")

        result = _run_in_project(project, ["integration", "status", "--json"])

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["status"] == "ok"
        assert payload["default_integration"] == "nexora"
        assert payload["installed_integrations"] == ["nexora"]
        assert payload["multi_install_safe"] is True

    def test_integration_status_flags_modified_skill(self, tmp_path):
        project = _init_project(tmp_path, "nexora")
        plan = project / ".nexora" / "skills" / "speckit-plan" / "SKILL.md"
        plan.write_text("# user customization\n", encoding="utf-8")

        result = _run_in_project(project, ["integration", "status", "--json"])

        payload = json.loads(result.output)
        assert payload["status"] != "ok"
        assert ".nexora/skills/speckit-plan/SKILL.md" in json.dumps(payload)


class TestNexoraExtensions:
    """Bundled ``bug`` and ``assess`` extensions render Nexora skills."""

    @pytest.mark.parametrize(
        ("extension_id", "commands"), sorted(BUNDLED_EXTENSION_COMMANDS.items())
    )
    def test_extension_add_writes_hyphenated_skills(self, tmp_path, extension_id, commands):
        project = _init_project(tmp_path, "nexora")

        result = _run_in_project(
            project,
            ["extension", "add", "--dev", str(REPO_ROOT / "extensions" / extension_id)],
        )

        assert result.exit_code == 0, result.output
        skills_dir = project / ".nexora" / "skills"
        for command in commands:
            skill = skills_dir / f"speckit-{extension_id}-{command}" / "SKILL.md"
            assert skill.exists(), f"missing {skill}"
            content = skill.read_text(encoding="utf-8")
            fm = _skill_frontmatter(skill)
            assert fm["name"] == f"speckit-{extension_id}-{command}"
            assert fm["description"]
            assert fm["metadata"]["source"] == (
                f"{extension_id}:commands/speckit.{extension_id}.{command}.md"
            )
            assert "argument-hint:" not in content
            # Command references in the body must use the hyphenated skill
            # form; only ``metadata.source`` may keep the dotted template name.
            body = content.split("---", 2)[2]
            assert "/speckit." not in body
            assert "{ARGS}" not in body
        # No dotted-name directories or stray command files were written.
        assert not (project / ".nexora" / "commands").exists()
        assert not list(skills_dir.glob("speckit.*"))

    def test_extension_remove_deletes_its_skills_only(self, tmp_path):
        project = _init_project(tmp_path, "nexora")
        add = _run_in_project(
            project, ["extension", "add", "--dev", str(REPO_ROOT / "extensions" / "bug")]
        )
        assert add.exit_code == 0, add.output
        skills_dir = project / ".nexora" / "skills"
        assert (skills_dir / "speckit-bug-assess" / "SKILL.md").exists()

        result = _run_in_project(project, ["extension", "remove", "bug", "--force"])

        assert result.exit_code == 0, result.output
        for command in BUNDLED_EXTENSION_COMMANDS["bug"]:
            assert not (skills_dir / f"speckit-bug-{command}").exists()
        assert (skills_dir / "speckit-plan" / "SKILL.md").exists()


class TestNexoraMultiInstall:
    """Nexora installs alongside another multi-install-safe skills agent."""

    def test_install_alongside_claude(self, tmp_path):
        project = _init_project(tmp_path, "claude")

        result = _run_in_project(
            project, ["integration", "install", "nexora", "--script", "sh"]
        )

        assert result.exit_code == 0, result.output
        assert "installed successfully" in result.output
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".nexora" / "skills" / "speckit-plan" / "SKILL.md").exists()

        status = _run_in_project(project, ["integration", "status", "--json"])
        assert status.exit_code == 0, status.output
        payload = json.loads(status.output)
        assert payload["status"] == "ok"
        assert payload["default_integration"] == "claude"
        assert sorted(payload["installed_integrations"]) == ["claude", "nexora"]

    def test_uninstall_nexora_leaves_claude_intact(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        install = _run_in_project(
            project, ["integration", "install", "nexora", "--script", "sh"]
        )
        assert install.exit_code == 0, install.output

        result = _run_in_project(project, ["integration", "uninstall", "nexora"])

        assert result.exit_code == 0, result.output
        assert not (project / ".nexora" / "skills" / "speckit-plan").exists()
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        status = _run_in_project(project, ["integration", "status", "--json"])
        payload = json.loads(status.output)
        assert payload["installed_integrations"] == ["claude"]


def _symlink_or_skip(link: Path, target: Path, *, target_is_directory: bool = False) -> None:
    """Create *link* -> *target*, skipping when the platform cannot symlink."""
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


class TestNexoraSymlinkContainment:
    """Regression for the PR #5316 review finding: a symlink planted under
    ``.nexora/skills`` before setup must never let the inherited skill writer
    create or overwrite a file outside the project. The containment error is
    raised before any directory is created or bytes are written."""

    @staticmethod
    def _project(tmp_path: Path) -> Path:
        project = tmp_path / "proj"
        project.mkdir()
        return project

    def test_setup_refuses_skill_file_symlink_outside_project(self, tmp_path):
        project = self._project(tmp_path)
        outside = tmp_path / "outside" / "victim.md"
        outside.parent.mkdir()
        outside.write_text("outside content\n", encoding="utf-8")
        planted = project / ".nexora" / "skills" / "speckit-specify" / "SKILL.md"
        planted.parent.mkdir(parents=True)
        _symlink_or_skip(planted, outside)
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", project.resolve())

        with pytest.raises(ValueError, match="escapes project root"):
            i.setup(project, m, script_type="sh")

        assert outside.read_text(encoding="utf-8") == "outside content\n"
        assert planted.is_symlink()
        assert planted.resolve() == outside.resolve()
        assert not any(key.endswith("speckit-specify/SKILL.md") for key in m.files)

    def test_setup_refuses_skill_dir_symlink_outside_project(self, tmp_path):
        project = self._project(tmp_path)
        outside_dir = tmp_path / "outside-skill"
        outside_dir.mkdir()
        (outside_dir / "SKILL.md").write_text("outside content\n", encoding="utf-8")
        skills = project / ".nexora" / "skills"
        skills.mkdir(parents=True)
        _symlink_or_skip(skills / "speckit-specify", outside_dir, target_is_directory=True)
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", project.resolve())

        with pytest.raises(ValueError, match="escapes project root"):
            i.setup(project, m, script_type="sh")

        assert (outside_dir / "SKILL.md").read_text(encoding="utf-8") == "outside content\n"
        assert sorted(p.name for p in outside_dir.iterdir()) == ["SKILL.md"]

    def test_setup_refuses_skills_root_symlink_outside_project(self, tmp_path):
        project = self._project(tmp_path)
        outside_dir = tmp_path / "outside-skills"
        outside_dir.mkdir()
        (project / ".nexora").mkdir()
        _symlink_or_skip(project / ".nexora" / "skills", outside_dir, target_is_directory=True)
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", project.resolve())

        with pytest.raises(ValueError, match="escapes project root"):
            i.setup(project, m, script_type="sh")

        assert list(outside_dir.iterdir()) == []

    def test_setup_allows_symlinked_skill_dir_inside_project(self, tmp_path):
        """Links that stay inside the project are still honoured."""
        project = self._project(tmp_path)
        real = project / "shared-skills" / "speckit-specify"
        real.mkdir(parents=True)
        skills = project / ".nexora" / "skills"
        skills.mkdir(parents=True)
        _symlink_or_skip(skills / "speckit-specify", real, target_is_directory=True)
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", project.resolve())

        created = i.setup(project, m, script_type="sh")

        assert (real / "SKILL.md").exists()
        assert any(p.name == "SKILL.md" and p.parent.name == "speckit-specify" for p in created)
        assert m.check_modified() == []

    def test_setup_replaces_inside_symlinked_skill_file_instead_of_following(self, tmp_path):
        """An inside-project link at SKILL.md is replaced by a regular file;
        its former target is left untouched."""
        project = self._project(tmp_path)
        target = project / "elsewhere.md"
        target.write_text("keep\n", encoding="utf-8")
        planted = project / ".nexora" / "skills" / "speckit-specify" / "SKILL.md"
        planted.parent.mkdir(parents=True)
        _symlink_or_skip(planted, target)
        i = get_integration("nexora")
        m = IntegrationManifest("nexora", project.resolve())

        i.setup(project, m, script_type="sh")

        assert not planted.is_symlink()
        assert planted.read_text(encoding="utf-8").startswith("---\nname: \"speckit-specify\"")
        assert target.read_text(encoding="utf-8") == "keep\n"
        assert ".nexora/skills/speckit-specify/SKILL.md" in m.files
