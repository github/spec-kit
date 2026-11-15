"""Tests for DroidIntegration (Factory Droid CLI)."""

import json
import os
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
import yaml

from specify_cli.integrations import get_integration
from specify_cli.integrations.base import SkillsIntegration
from specify_cli.integrations.droid import DroidIntegration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _reset_droid_model_invocation():
    """``setup()`` stores ``--no-model-invocation`` on the process-wide Droid
    singleton; keep it from leaking between tests."""
    droid = get_integration("droid")
    droid._disable_model_invocation = False
    yield
    droid._disable_model_invocation = False


def _skill_frontmatter(skill_file: Path) -> dict:
    content = skill_file.read_text(encoding="utf-8")
    return yaml.safe_load(content.split("---", 2)[1])


class TestDroidIntegration(SkillsIntegrationTests):
    KEY = "droid"
    FOLDER = ".factory/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".factory/skills"

    def test_options_include_skills_flag(self):
        """Not applicable — Droid only supports the skills layout."""
        pytest.skip("Droid is always skills-based and does not expose a --skills option")

    def test_options_do_not_include_skills_flag(self):
        """Droid is always skills-based; no --skills option is exposed."""
        i = get_integration(self.KEY)
        assert i is not None
        opts = i.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 0, (
            "Droid is always skills-based and should not expose a --skills option"
        )

    def test_requires_cli_is_true(self):
        """Droid is a CLI tool; requires_cli must be True."""
        i = get_integration(self.KEY)
        assert i is not None
        assert i.config["requires_cli"] is True
        assert i.config["name"] == "Factory Droid"

    def test_multi_install_safe_is_true(self):
        """Droid uses an isolated .factory/ root — safe to install alongside others."""
        i = get_integration(self.KEY)
        assert i.multi_install_safe is True

    def test_is_slash_skills_agent(self):
        """Droid is an always-skills agent whose commands install as
        /speckit-<name>, so is_slash_skills_agent must report True — otherwise
        hook invocations and the init next-steps panel render the dotted
        /speckit.<name> form Droid never registers (mirrors grok/trae/zed/devin)."""
        from specify_cli._invocation_style import is_slash_skills_agent

        # True in BOTH the enabled and disabled cases: Droid is *always* slash,
        # not conditional. The disabled case is what distinguishes an
        # ALWAYS_SLASH agent from a CONDITIONAL_SLASH one (which would be False
        # when ai_skills is disabled).
        assert is_slash_skills_agent("droid", True) is True
        assert is_slash_skills_agent("droid", False) is True

    def test_install_url_points_to_factory(self):
        i = get_integration(self.KEY)
        url = i.config.get("install_url")
        assert url is not None
        host = (urlparse(url).hostname or "").lower()
        assert host == "factory.ai" or host.endswith(".factory.ai"), (
            f"install_url must point at the Factory domain, got: {url}"
        )


class TestDroidInitFlow:
    """--integration droid creates expected files."""

    def test_integration_droid_creates_skills(self, tmp_path):
        """--integration droid should create skills under .factory/skills."""
        from typer.testing import CliRunner

        from specify_cli import app

        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "droid",
                "--ignore-agent-tools",
                "--script",
                "sh",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"init --integration droid failed: {result.output}"
        assert (target / ".factory" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (target / ".factory" / "skills" / "speckit-specify" / "SKILL.md").exists()


class TestDroidBuildExecArgs:
    """Droid non-interactive execution argument building."""

    def test_default_argv_uses_exec_subcommand(self):
        """Default argv: ``droid exec <prompt> --output-format json``.

        No permission-bypass flag is auto-applied — operators who need it
        must pass it through ``SPECKIT_INTEGRATION_DROID_EXTRA_ARGS``.
        """
        i = get_integration("droid")
        args = i.build_exec_args("/speckit-specify some-feature")
        assert args == [
            "droid",
            "exec",
            "/speckit-specify some-feature",
            "--output-format",
            "json",
        ]
        assert "--skip-permissions-unsafe" not in args, (
            "Spec Kit must not auto-apply --skip-permissions-unsafe; "
            "it is a dangerous flag and operators must opt in explicitly"
        )

    def test_text_output_omits_format_flag(self):
        i = get_integration("droid")
        args = i.build_exec_args("/speckit-plan", output_json=False)
        assert args == [
            "droid",
            "exec",
            "/speckit-plan",
        ]
        assert "--skip-permissions-unsafe" not in args

    def test_model_is_appended(self):
        i = get_integration("droid")
        args = i.build_exec_args(
            "/speckit-specify", model="claude-opus-4-7", output_json=False
        )
        assert args == [
            "droid",
            "exec",
            "/speckit-specify",
            "--model",
            "claude-opus-4-7",
        ]
        assert "--skip-permissions-unsafe" not in args

    def test_extra_args_inserted_after_canonical_flags(self, monkeypatch):
        """Operator-injected extra args land after Spec Kit's canonical
        ``--model`` / ``--output-format`` flags so the canonical flags are
        always present in argv regardless of operator override."""
        from specify_cli.integrations import get_integration

        i = get_integration("droid")
        monkeypatch.setenv("SPECKIT_INTEGRATION_DROID_EXTRA_ARGS", "--foo bar")
        args = i.build_exec_args(
            "/speckit-plan", model="claude-sonnet", output_json=True
        )

        assert "--foo" in args
        assert "bar" in args
        assert args.index("bar") == args.index("--foo") + 1
        # Extra args land AFTER the canonical flags so the canonical flags
        # are always present in argv.
        assert args.index("--model") < args.index("--foo")
        assert args.index("--output-format") < args.index("--foo")
        assert args[args.index("--model") + 1] == "claude-sonnet"
        assert args[args.index("--output-format") + 1] == "json"

    def test_executable_override(self, monkeypatch):
        """``SPECKIT_INTEGRATION_DROID_EXECUTABLE`` overrides argv[0]."""
        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_DROID_EXECUTABLE", "/custom/droid"
        )
        i = get_integration("droid")
        args = i.build_exec_args("/speckit-plan", output_json=False)
        assert args[0] == "/custom/droid"
        # No dangerous permission-bypass flag should leak in via the override path.
        assert "--skip-permissions-unsafe" not in args

    def test_returns_none_when_requires_cli_is_false(self, monkeypatch):
        """When ``requires_cli`` is False, ``build_exec_args`` returns None."""
        i = get_integration("droid")
        monkeypatch.setitem(i.config, "requires_cli", False)
        assert i.build_exec_args("/speckit-plan") is None


class TestDroidFrontmatter:
    """Every generated SKILL.md must carry Droid-specific frontmatter flags."""

    def test_skills_carry_user_invocable_true(self, tmp_path):
        i = get_integration("droid")
        m = IntegrationManifest("droid", tmp_path)
        i.setup(tmp_path, m, script_type="sh")

        skill_files = [
            f
            for f in (tmp_path / ".factory" / "skills").rglob("SKILL.md")
        ]
        assert skill_files, "expected at least one SKILL.md"
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            assert "user-invocable: true" in content, (
                f"{f} missing user-invocable: true"
            )

    def test_skills_carry_disable_model_invocation_false(self, tmp_path):
        i = get_integration("droid")
        m = IntegrationManifest("droid", tmp_path)
        i.setup(tmp_path, m, script_type="sh")

        skill_files = [
            f
            for f in (tmp_path / ".factory" / "skills").rglob("SKILL.md")
        ]
        assert skill_files, "expected at least one SKILL.md"
        for f in skill_files:
            content = f.read_text(encoding="utf-8")
            assert "disable-model-invocation: false" in content, (
                f"{f} missing disable-model-invocation: false"
            )

    def test_inject_frontmatter_flag_adds_key_when_absent(self):
        """Fresh content (key absent) gets the flag injected on its own line."""
        content = "---\nname: x\ndescription: y\n---\n\nBody.\n"
        result = DroidIntegration._inject_frontmatter_flag(content, "user-invocable")
        assert "user-invocable: true" in result
        # The injected key must sit on its own line, not glued to the closing ---.
        assert "\nuser-invocable: true\n---" in result, (
            "Injected key must be on its own line, not fused to closing ---"
        )

    def test_inject_frontmatter_flag_injects_custom_value(self):
        """The value parameter must be honored (used for disable-model-invocation: false)."""
        content = "---\nname: x\n---\n\nBody.\n"
        result = DroidIntegration._inject_frontmatter_flag(
            content, "disable-model-invocation", "false"
        )
        assert "disable-model-invocation: false" in result

    def test_inject_frontmatter_flag_no_trailing_newline(self):
        """Regression for the frontmatter-fusion P2 bug.

        When the closing ``---`` is the literal last line of the file with
        no trailing newline, the injected key must still land on its own
        line (not fused onto the closing delimiter). Previously this
        produced ``user-invocable: true---``, an unparseable YAML line.
        """
        content = "---\nname: x\ndescription: y\n---"
        result = DroidIntegration._inject_frontmatter_flag(content, "user-invocable")
        assert "user-invocable: true" in result
        # The injected key and the closing delimiter must NOT be fused.
        assert "user-invocable: true---" not in result, (
            "Injected key fused onto closing ---; no-trailing-newline regression"
        )
        # And the injected key must be on its own line.
        assert "\nuser-invocable: true\n---" in result

    def test_frontmatter_injection_is_idempotent(self):
        """Running the post-processor twice must not duplicate the flag."""
        content = "---\nname: x\n---\n\nBody.\n"
        once = DroidIntegration._inject_frontmatter_flag(content, "user-invocable")
        twice = DroidIntegration._inject_frontmatter_flag(once, "user-invocable")
        assert once == twice, "Frontmatter injection must be idempotent"
        # Belt-and-braces: the flag must appear exactly once.
        assert once.count("user-invocable: true") == 1


class TestDroidCommandInvocation:
    """Skills agents use the hyphenated ``/speckit-<name>`` slash form."""

    def test_build_command_invocation_uses_hyphenated_skill_name(self):
        i = get_integration("droid")
        assert i.build_command_invocation("speckit.plan", "feature-x") == (
            "/speckit-plan feature-x"
        )
        assert i.build_command_invocation("plan") == "/speckit-plan"


class TestDroidNoModelInvocationOption:
    """``--integration-options="--no-model-invocation"`` opts out of model invocation (#2654)."""

    def test_options_include_no_model_invocation_flag(self):
        opts = get_integration("droid").options()
        matching = [o for o in opts if o.name == "--no-model-invocation"]
        assert len(matching) == 1
        assert matching[0].is_flag is True
        # Opt-in: skills stay model-invocable unless the flag is passed.
        assert matching[0].default is False

    def test_setup_with_option_sets_disable_model_invocation_true(self, tmp_path):
        i = get_integration("droid")
        m = IntegrationManifest("droid", tmp_path)
        created = i.setup(
            tmp_path, m, parsed_options={"no_model_invocation": True}, script_type="sh"
        )
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            fm = _skill_frontmatter(f)
            assert fm["disable-model-invocation"] is True, f.parent.name
            assert fm["user-invocable"] is True, f.parent.name
            assert f.read_text(encoding="utf-8").count("disable-model-invocation:") == 1

    def test_post_process_follows_option_from_setup(self, tmp_path):
        """Preset overrides of core commands re-registered in the same run as
        ``setup()`` (init, upgrade) get the same value."""
        i = get_integration("droid")
        i.setup(
            tmp_path,
            IntegrationManifest("droid", tmp_path),
            parsed_options={"no_model_invocation": True},
            script_type="sh",
        )
        result = i.post_process_skill_content("---\nname: speckit-plan\n---\n\nBody\n")
        assert "disable-model-invocation: true" in result
        assert "disable-model-invocation: false" not in result

    def test_extension_skills_stay_model_invocable(self, tmp_path):
        """Mandatory extension hooks rely on the model invoking the hook skill,
        so the option never applies to extension commands."""
        i = get_integration("droid")
        i.setup(
            tmp_path,
            IntegrationManifest("droid", tmp_path),
            parsed_options={"no_model_invocation": True},
            script_type="sh",
        )
        result = i.post_process_skill_content(
            "---\nname: speckit-git-feature\n---\n\nBody\n"
        )
        assert "disable-model-invocation: false" in result
        assert "disable-model-invocation: true" not in result

    def test_option_requires_speckit_prefixed_core_name(self, tmp_path):
        """A skill merely named like a core stem is not a core command skill."""
        i = get_integration("droid")
        i.setup(
            tmp_path,
            IntegrationManifest("droid", tmp_path),
            parsed_options={"no_model_invocation": True},
            script_type="sh",
        )
        result = i.post_process_skill_content("---\nname: tasks\n---\n\nBody\n")
        assert "disable-model-invocation: false" in result

    def test_failed_setup_does_not_leave_option_set(self, tmp_path):
        i = get_integration("droid")
        with patch.object(SkillsIntegration, "setup", side_effect=RuntimeError("boom")):
            with pytest.raises(RuntimeError):
                i.setup(
                    tmp_path,
                    IntegrationManifest("droid", tmp_path),
                    parsed_options={"no_model_invocation": True},
                    script_type="sh",
                )
        result = i.post_process_skill_content("---\nname: speckit-plan\n---\n\nBody\n")
        assert "disable-model-invocation: false" in result

    def test_setup_without_option_resets_to_false(self, tmp_path):
        i = get_integration("droid")
        first = tmp_path / "first"
        first.mkdir()
        i.setup(
            first,
            IntegrationManifest("droid", first),
            parsed_options={"no_model_invocation": True},
            script_type="sh",
        )
        second = tmp_path / "second"
        second.mkdir()
        created = i.setup(second, IntegrationManifest("droid", second), script_type="sh")
        skill_files = [f for f in created if f.name == "SKILL.md"]
        assert len(skill_files) > 0
        for f in skill_files:
            assert _skill_frontmatter(f)["disable-model-invocation"] is False, f.parent.name
        result = i.post_process_skill_content("---\nname: speckit-plan\n---\n\nBody\n")
        assert "disable-model-invocation: false" in result

    def test_cli_rejects_value_for_flag(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "droid-bad-option"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(
                app,
                [
                    "init",
                    "--here",
                    "--integration",
                    "droid",
                    "--integration-options",
                    "--no-model-invocation=yes",
                    "--script",
                    "sh",
                    "--ignore-agent-tools",
                ],
                catch_exceptions=False,
            )
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "does not accept a value" in result.output
        assert not (project / ".factory" / "skills").exists()

    def test_option_persists_across_upgrade_and_can_be_cleared(self, tmp_path):
        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        project = _init_project(tmp_path, "droid", "--no-model-invocation")
        skills_dir = project / ".factory" / "skills"
        skill_files = sorted(skills_dir.glob("*/SKILL.md"))
        assert len(skill_files) > 0
        for f in skill_files:
            assert _skill_frontmatter(f)["disable-model-invocation"] is True, f.parent.name

        state = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        settings = state["integration_settings"]["droid"]
        assert settings["raw_options"] == "--no-model-invocation"
        assert settings["parsed_options"] == {"no_model_invocation": True}

        # A later ``specify integration upgrade`` is a new process: drop the
        # in-memory value so only the persisted options can supply it.
        get_integration("droid")._disable_model_invocation = False
        result = _run_in_project(project, ["integration", "upgrade", "droid", "--force"])
        assert result.exit_code == 0, result.output
        for f in skill_files:
            assert _skill_frontmatter(f)["disable-model-invocation"] is True, f.parent.name

        # Passing replacement options (here: none) clears it.
        result = _run_in_project(
            project,
            ["integration", "upgrade", "droid", "--force", "--integration-options", ""],
        )
        assert result.exit_code == 0, result.output
        for f in skill_files:
            assert _skill_frontmatter(f)["disable-model-invocation"] is False, f.parent.name
        state = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert "parsed_options" not in state["integration_settings"]["droid"]

    def test_upgrade_reapplies_option_to_preset_overrides(self, tmp_path):
        """``preset add`` runs without ``setup()`` (documented limitation);
        ``integration upgrade droid --force`` reapplies the option to the
        core-command skills a preset overrides."""
        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        project = _init_project(tmp_path, "droid", "--no-model-invocation")
        skill_file = project / ".factory" / "skills" / "speckit-plan" / "SKILL.md"
        assert _skill_frontmatter(skill_file)["disable-model-invocation"] is True

        get_integration("droid")._disable_model_invocation = False
        result = _run_in_project(
            project, ["preset", "add", "--dev", str(REPO_ROOT / "presets" / "lean")]
        )
        assert result.exit_code == 0, result.output
        fm = _skill_frontmatter(skill_file)
        assert fm["metadata"]["source"] == "preset:lean"
        # Documented in docs/integrations/droid.md; update the docs if
        # preset commands start honouring the option.
        assert fm["disable-model-invocation"] is False

        # The docs say ``--force`` is needed here: preset add modified
        # installed skill files, so a plain upgrade refuses.
        result = _run_in_project(project, ["integration", "upgrade", "droid"])
        assert result.exit_code != 0
        assert "modified since installation" in result.output
        assert _skill_frontmatter(skill_file)["disable-model-invocation"] is False

        get_integration("droid")._disable_model_invocation = False
        result = _run_in_project(project, ["integration", "upgrade", "droid", "--force"])
        assert result.exit_code == 0, result.output
        fm = _skill_frontmatter(skill_file)
        assert fm["metadata"]["source"] == "preset:lean"
        assert fm["disable-model-invocation"] is True

    def test_extension_hook_skills_stay_model_invocable_after_upgrade(self, tmp_path):
        """``integration upgrade`` re-registers extension skills in the same
        process as ``setup()``; they must keep ``false`` so mandatory hooks
        (e.g. ``speckit.git.feature``) can still be invoked by the model."""
        from tests.specify_cli.integrations._helpers import _init_project, _run_in_project

        project = _init_project(tmp_path, "droid", "--no-model-invocation")
        result = _run_in_project(
            project, ["extension", "add", "--dev", str(REPO_ROOT / "extensions" / "git")]
        )
        assert result.exit_code == 0, result.output
        get_integration("droid")._disable_model_invocation = False
        result = _run_in_project(project, ["integration", "upgrade", "droid", "--force"])
        assert result.exit_code == 0, result.output

        skills_dir = project / ".factory" / "skills"
        git_skills = sorted(skills_dir.glob("speckit-git-*/SKILL.md"))
        assert git_skills, "git extension skills were not generated"
        for f in git_skills:
            assert _skill_frontmatter(f)["disable-model-invocation"] is False, f.parent.name
        assert _skill_frontmatter(skills_dir / "speckit-specify" / "SKILL.md")[
            "disable-model-invocation"
        ] is True
