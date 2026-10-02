"""Tests for DshIntegration (DeepSeek Harness)."""

import json

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_skills import SkillsIntegrationTests


class TestDshIntegration(SkillsIntegrationTests):
    KEY = "dsh"
    FOLDER = ".dsh/"
    COMMANDS_SUBDIR = "skills"
    REGISTRAR_DIR = ".dsh/skills"

    def test_options_include_skills_flag(self):
        """Not applicable to DSH — DSH is always skills-based with no --skills flag."""
        pytest.skip("DSH is always skills-based and does not expose a --skills option")

    def test_options_do_not_include_skills_flag(self):
        """DSH is always skills-based; no --skills option is exposed."""
        i = get_integration(self.KEY)
        assert i is not None
        opts = i.options()
        skills_opts = [o for o in opts if o.name == "--skills"]
        assert len(skills_opts) == 0, (
            "DSH is always skills-based and should not expose a --skills option"
        )


class TestDshBuildExecArgs:
    """Regression tests for DshIntegration.build_exec_args.

    DSH's one-shot mode is ``dsh --profile headless "<task>"``. The CLI has
    no structured-output or model flag, so ``output_json``/``model`` must
    not add anything, and the integration must stay CLI-dispatchable
    (``None`` is the IDE-only sentinel checked by CommandStep).
    """

    def test_returns_args_not_none_for_dispatch(self):
        """DSH is CLI-dispatchable; build_exec_args must not return None."""
        from specify_cli.integrations.dsh import DshIntegration

        impl = DshIntegration()
        args = impl.build_exec_args("/speckit-specify build photo albums")
        assert args is not None, (
            "DshIntegration.build_exec_args must not return None. "
            "None is the codebase sentinel for IDE-only integrations; "
            "DSH is dispatchable via 'dsh --profile headless'."
        )
        assert args == [
            "dsh",
            "--profile",
            "headless",
            "/speckit-specify build photo albums",
        ]

    def test_output_json_and_model_do_not_change_command_line(self):
        """DSH has no --output-format/--model flags for the headless profile."""
        from specify_cli.integrations.dsh import DshIntegration

        impl = DshIntegration()
        base = impl.build_exec_args("hello")
        assert impl.build_exec_args("hello", output_json=True) == base
        assert impl.build_exec_args("hello", output_json=False) == base
        assert impl.build_exec_args("hello", model="deepseek-chat") == base

    def test_extra_args_precede_headless_task(self, monkeypatch):
        """Launcher options must appear before DSH's task positional."""
        from specify_cli.integrations.dsh import DshIntegration

        monkeypatch.setenv(
            "SPECKIT_INTEGRATION_DSH_EXTRA_ARGS", "--patch custom.yml"
        )

        assert DshIntegration().build_exec_args("/speckit-plan ship it") == [
            "dsh",
            "--profile",
            "headless",
            "--patch",
            "custom.yml",
            "/speckit-plan ship it",
        ]


class TestDshInitFlow:
    """--integration dsh creates expected files."""

    def test_integration_dsh_creates_skills(self, tmp_path):
        """--integration dsh should create skills in .dsh/skills."""
        runner = CliRunner()
        target = tmp_path / "test-proj"
        result = runner.invoke(
            app,
            ["init", str(target), "--integration", "dsh", "--ignore-agent-tools", "--script", "sh"],
        )

        assert result.exit_code == 0, f"init --integration dsh failed: {result.output}"
        assert (target / ".dsh" / "skills" / "speckit-plan" / "SKILL.md").exists()


class TestDshNextSteps:
    """CLI output tests for DSH next-steps display."""

    def test_init_next_steps_show_dsh_skill_guidance(self, tmp_path):
        """init --integration dsh should guide users to .dsh/skills and /speckit-*."""
        runner = CliRunner()
        target = tmp_path / "dsh-next-steps"
        result = runner.invoke(
            app,
            [
                "init",
                str(target),
                "--integration",
                "dsh",
                "--ignore-agent-tools",
                "--script",
                "sh",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"init --integration dsh failed: {result.output}"
        assert "Start DSH" in result.output, (
            f"Expected DSH start guidance in next steps but got:\n{result.output}"
        )
        assert "dsh web" in result.output, (
            f"Expected the 'dsh web' launch command in next steps but got:\n{result.output}"
        )
        assert ".dsh/skills" in result.output, (
            f"Expected .dsh/skills install path in next steps but got:\n{result.output}"
        )
        assert "/speckit-plan" in result.output, (
            f"Expected /speckit-plan in next steps but got:\n{result.output}"
        )
        assert "/speckit.plan" not in result.output, (
            f"Should not show /speckit.plan for DSH skills mode:\n{result.output}"
        )


class TestDshSkillCompatibility:
    """DSH-specific invariants the generated skills must satisfy.

    The DSH filesystem skill provider discovers one-level-deep
    ``<name>/SKILL.md`` bundles and parses the frontmatter as an open YAML
    object, requiring a kebab-case ``name`` and a ``description``; extra
    keys (``compatibility``, ``metadata``) are tolerated. These tests pin
    the properties DSH relies on so a template change cannot silently
    break discovery.
    """

    def _setup_skills(self, tmp_path):
        integration = get_integration("dsh")
        manifest = IntegrationManifest("dsh", tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")
        return tmp_path / ".dsh" / "skills"

    def test_skill_names_are_kebab_case(self, tmp_path):
        import re

        skills_dir = self._setup_skills(tmp_path)
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert skill_dirs, "no skill directories were created"
        for skill_dir in skill_dirs:
            assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", skill_dir.name), (
                f"skill directory {skill_dir.name!r} is not kebab-case; "
                "DSH rejects non-kebab-case skill names"
            )

    def test_skill_frontmatter_has_name_and_description(self, tmp_path):
        import yaml

        skills_dir = self._setup_skills(tmp_path)
        for skill_dir in sorted(skills_dir.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"missing SKILL.md in {skill_dir}"
            content = skill_file.read_text(encoding="utf-8")
            assert content.startswith("---\n"), f"{skill_file} missing frontmatter"
            lines = content.splitlines(keepends=True)
            close = next(
                i for i in range(1, len(lines)) if lines[i].rstrip() == "---"
            )
            frontmatter = yaml.safe_load("".join(lines[1:close]))
            assert isinstance(frontmatter, dict)
            # DSH requires a non-empty name matching the bundle directory and
            # a non-empty description for its model-facing skill catalog.
            assert frontmatter.get("name") == skill_dir.name
            assert isinstance(frontmatter.get("description"), str)
            assert frontmatter["description"].strip()

    def test_skill_definition_is_one_level_deep(self, tmp_path):
        """DSH discovery only recognizes <root>/<name>/SKILL.md — the
        SKILL.md file must sit directly inside a single skill directory,
        not in nested subdirectories."""
        skills_dir = self._setup_skills(tmp_path)
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            assert (skill_dir / "SKILL.md").is_file()


class TestDshMultiInstallSafe:
    """DSH confines itself to an isolated ``.dsh/`` root that no other
    integration touches, so it must be declared multi-install safe."""

    def test_multi_install_safe_is_true(self):
        integration = get_integration("dsh")
        assert integration.multi_install_safe is True

    def test_dsh_root_does_not_overlap_other_safe_integrations(self):
        from pathlib import PurePosixPath

        from specify_cli.integrations import INTEGRATION_REGISTRY

        dsh_root = PurePosixPath(".dsh")
        for key, integration in INTEGRATION_REGISTRY.items():
            if key == "dsh" or not integration.multi_install_safe:
                continue
            folder = (integration.config or {}).get("folder")
            if not folder:
                continue
            other = PurePosixPath(str(folder).rstrip("/"))
            for left, right in ((dsh_root, other), (other, dsh_root)):
                try:
                    left.relative_to(right)
                except ValueError:
                    continue
                raise AssertionError(
                    f"dsh agent root .dsh overlaps multi-install-safe "
                    f"integration {key!r} root {other}"
                )


class TestDshHookInvocations:
    """DSH is in ALWAYS_SLASH_AGENTS: hook messages and init output must
    reference slash-invokable skills regardless of the persisted ai_skills
    flag, because the DSH Web GUI invokes skills as ``/speckit-<command>``."""

    def test_hooks_render_skill_invocation(self, tmp_path):
        from specify_cli.extensions import HookExecutor

        project = tmp_path / "dsh-hooks"
        project.mkdir()
        init_options = project / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "dsh", "ai_skills": False}))

        hook_executor = HookExecutor(project)
        message = hook_executor.format_hook_message(
            "before_plan",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.plan",
                    "optional": False,
                },
            ],
        )

        assert "EXECUTE_COMMAND_INVOCATION: /speckit-plan" in message

    def test_init_persists_ai_skills_for_dsh(self, tmp_path, monkeypatch):
        """specify init --integration dsh must persist ai_skills: true,
        so HookExecutor renders slash-skill invocations."""
        from specify_cli.extensions import HookExecutor

        project = tmp_path / "dsh-init-test"
        project.mkdir()
        monkeypatch.chdir(project)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--here",
                "--integration",
                "dsh",
                "--script",
                "sh",
                "--ignore-agent-tools",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, f"init failed: {result.output}"

        opts_path = project / ".specify" / "init-options.json"
        assert opts_path.exists()
        opts = json.loads(opts_path.read_text(encoding="utf-8"))
        assert opts.get("ai") == "dsh"
        assert opts.get("ai_skills") is True, (
            f"init must persist ai_skills=true for DSH, got: {opts.get('ai_skills')}"
        )

        hook_executor = HookExecutor(project)
        message = hook_executor.format_hook_message(
            "before_plan",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.plan",
                    "optional": False,
                },
            ],
        )
        assert "Executing: `/speckit-plan`" in message, (
            "Hook rendering must produce /speckit-plan for DSH"
        )
        assert "EXECUTE_COMMAND_INVOCATION: /speckit-plan" in message
