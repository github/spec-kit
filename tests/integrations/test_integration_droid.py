"""Tests for DroidIntegration (Factory Droid CLI)."""

from urllib.parse import urlparse

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.droid import DroidIntegration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


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
