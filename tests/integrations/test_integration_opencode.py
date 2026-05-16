"""Tests for OpencodeIntegration."""

import os

import yaml

import warnings

from specify_cli.agents import CommandRegistrar
from specify_cli.integrations import get_integration
from specify_cli.integrations.manifest import IntegrationManifest

from .test_integration_base_markdown import MarkdownIntegrationTests


class TestOpencodeIntegration(MarkdownIntegrationTests):
    KEY = "opencode"
    FOLDER = ".opencode/"
    COMMANDS_SUBDIR = "commands"
    REGISTRAR_DIR = ".opencode/commands"
    CONTEXT_FILE = "AGENTS.md"

    def test_build_exec_args_uses_run_command_dispatch(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit.specify build a login page",
            output_json=False,
        )

        assert args == [
            "opencode",
            "run",
            "--command",
            "speckit.specify",
            "build a login page",
        ]
        assert "-p" not in args
        assert "--output-format" not in args

    def test_build_exec_args_maps_model_and_json_flags(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args(
            "/speckit.plan add OAuth",
            model="anthropic/claude-sonnet-4",
            output_json=True,
        )

        assert args == [
            "opencode",
            "run",
            "--command",
            "speckit.plan",
            "-m",
            "anthropic/claude-sonnet-4",
            "--format",
            "json",
            "add OAuth",
        ]

    def test_build_exec_args_keeps_plain_prompt_dispatch(self):
        integration = get_integration(self.KEY)

        args = integration.build_exec_args("explain this repository", output_json=False)

        assert args == ["opencode", "run", "explain this repository"]

    def test_registrar_config_has_legacy_dir(self):
        integration = get_integration(self.KEY)
        assert integration.registrar_config["legacy_dir"] == ".opencode/command"

    def test_legacy_dir_extension_registration(self, tmp_path):
        """Extensions register in legacy .opencode/command/ with a warning."""
        # Seed a legacy project with only .opencode/command/
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)
        (legacy_dir / "speckit.specify.md").write_text("# existing", encoding="utf-8")

        # Create a source command file for the registrar
        src_dir = tmp_path / "_ext_src"
        src_dir.mkdir()
        (src_dir / "myext.md").write_text(
            "---\ndescription: test\n---\n# ext command", encoding="utf-8",
        )

        registrar = CommandRegistrar()
        commands = [{"name": "speckit.myext", "file": "myext.md"}]

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = registrar.register_commands_for_all_agents(
                commands, "test-ext", src_dir, tmp_path,
            )

        # Should have registered in the legacy directory
        assert "opencode" in results
        assert (legacy_dir / "speckit.myext.md").exists()
        # Canonical directory should NOT have been created
        assert not (tmp_path / ".opencode" / "commands").exists()
        # Should have emitted a deprecation warning
        opencode_warnings = [
            w for w in caught
            if "legacy" in str(w.message) and "opencode" in str(w.message)
        ]
        assert len(opencode_warnings) == 1, (
            f"Expected exactly 1 legacy-dir warning, got {len(opencode_warnings)}"
        )
        assert "specify integration upgrade" in str(opencode_warnings[0].message)

    def test_legacy_dir_unregister(self, tmp_path):
        """Unregister finds commands in legacy .opencode/command/ dir."""
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)
        cmd_file = legacy_dir / "speckit.myext.md"
        cmd_file.write_text("# ext command", encoding="utf-8")

        registrar = CommandRegistrar()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            registrar.unregister_commands(
                {"opencode": ["speckit.myext"]}, tmp_path,
            )

        assert not cmd_file.exists()

    def test_unregister_cleans_legacy_when_both_dirs_exist(self, tmp_path):
        """Unregister removes files from legacy dir even when canonical exists."""
        # Set up both canonical and legacy dirs
        canonical_dir = tmp_path / ".opencode" / "commands"
        canonical_dir.mkdir(parents=True)
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)

        # Place a command file in the legacy dir (orphaned after upgrade)
        legacy_cmd = legacy_dir / "speckit.myext.md"
        legacy_cmd.write_text("# orphaned ext command", encoding="utf-8")
        # Place the same command in the canonical dir (current)
        canonical_cmd = canonical_dir / "speckit.myext.md"
        canonical_cmd.write_text("# ext command", encoding="utf-8")

        registrar = CommandRegistrar()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            registrar.unregister_commands(
                {"opencode": ["speckit.myext"]}, tmp_path,
            )

        # Both files should be removed
        assert not canonical_cmd.exists(), (
            "Command file in canonical dir should be removed"
        )
        assert not legacy_cmd.exists(), (
            "Orphaned command file in legacy dir should also be removed"
        )

    def test_canonical_dir_preferred_over_legacy(self, tmp_path):
        """When both dirs exist, canonical .opencode/commands/ is used."""
        legacy_dir = tmp_path / ".opencode" / "command"
        legacy_dir.mkdir(parents=True)
        canonical_dir = tmp_path / ".opencode" / "commands"
        canonical_dir.mkdir(parents=True)
        (canonical_dir / "speckit.specify.md").write_text("# cmd", encoding="utf-8")

        # Create a source command file for the registrar
        src_dir = tmp_path / "_ext_src"
        src_dir.mkdir()
        (src_dir / "myext.md").write_text(
            "---\ndescription: test\n---\n# ext command", encoding="utf-8",
        )

        registrar = CommandRegistrar()
        commands = [{"name": "speckit.myext", "file": "myext.md"}]

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = registrar.register_commands_for_all_agents(
                commands, "test-ext", src_dir, tmp_path,
            )

        # Should register in canonical dir, not legacy
        assert "opencode" in results
        assert (canonical_dir / "speckit.myext.md").exists()
        assert not (legacy_dir / "speckit.myext.md").exists()
        # No legacy warning when canonical dir exists
        opencode_warnings = [
            w for w in caught
            if "legacy" in str(w.message) and "opencode" in str(w.message)
        ]
        assert len(opencode_warnings) == 0

    def test_setup_writes_to_canonical_dir(self, tmp_path):
        """New installs always write to .opencode/commands/ (plural)."""
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest)

        canonical = tmp_path / ".opencode" / "commands"
        legacy = tmp_path / ".opencode" / "command"
        assert canonical.is_dir()
        assert not legacy.exists()
        assert any(canonical.glob("speckit.*.md"))


class TestOpencodeSkillsMode:
    KEY = "opencode"

    def test_skills_option_declared(self):
        integration = get_integration(self.KEY)
        opts = integration.options()
        names = [o.name for o in opts]
        assert "--skills" in names
        skills_opt = next(o for o in opts if o.name == "--skills")
        assert skills_opt.is_flag is True
        assert skills_opt.default is False

    def test_skills_mode_creates_skill_md_files(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        created = integration.setup(tmp_path, manifest, parsed_options={"skills": True}, script_type="sh")

        skill_files = [p for p in created if p.name == "SKILL.md"]
        assert skill_files

        skills_dir = tmp_path / ".opencode" / "skills"
        assert skills_dir.is_dir()

        specify_skill = skills_dir / "speckit-specify" / "SKILL.md"
        assert specify_skill.exists()

    def test_skills_mode_does_not_create_md_command_files(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, parsed_options={"skills": True}, script_type="sh")

        command_dir = tmp_path / ".opencode" / "commands"
        md_files = list(command_dir.glob("*.md")) if command_dir.exists() else []
        assert md_files == []

    def test_skills_mode_frontmatter(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, parsed_options={"skills": True}, script_type="sh")

        skill_path = tmp_path / ".opencode" / "skills" / "speckit-plan" / "SKILL.md"
        assert skill_path.exists()

        content = skill_path.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        parsed = yaml.safe_load(parts[1])

        assert parsed["name"] == "speckit-plan"
        assert "description" in parsed
        assert "compatibility" in parsed
        assert parsed["metadata"]["author"] == "github-spec-kit"

    def test_default_mode_unchanged(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")

        command_dir = tmp_path / ".opencode" / "commands"
        assert command_dir.is_dir()
        md_files = list(command_dir.glob("speckit.*.md"))
        assert md_files

    def test_effective_invoke_separator_skills_mode(self):
        integration = get_integration(self.KEY)
        assert integration.effective_invoke_separator({"skills": True}) == "-"

    def test_effective_invoke_separator_default_mode(self):
        integration = get_integration(self.KEY)
        assert integration.effective_invoke_separator({}) == "."

    def test_skills_mode_flag_set_on_instance(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, parsed_options={"skills": True}, script_type="sh")
        assert integration._skills_mode is True

    def test_skills_mode_resets_on_default_setup(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, parsed_options={"skills": True}, script_type="sh")
        assert integration._skills_mode is True

        manifest2 = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest2, script_type="sh")
        assert integration._skills_mode is False

    def test_init_cli_with_skills_option(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "opencode-skills"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "opencode",
                "--integration-options", "--skills",
                "--script", "sh", "--no-git", "--ignore-agent-tools",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert result.exit_code == 0, f"init failed: {result.output}"
        skills_dir = project / ".opencode" / "skills"
        assert skills_dir.is_dir(), "Skills directory was not created"
        plan_skill = skills_dir / "speckit-plan" / "SKILL.md"
        assert plan_skill.exists(), "speckit-plan/SKILL.md not found"

        import json
        init_opts = json.loads((project / ".specify" / "init-options.json").read_text())
        assert init_opts.get("ai_skills") is True

        commands_dir = project / ".opencode" / "commands"
        if commands_dir.exists():
            assert not list(commands_dir.glob("*.md"))

    def test_build_command_invocation_skills_mode(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, parsed_options={"skills": True}, script_type="sh")

        assert integration.build_command_invocation("speckit.plan", "add OAuth") == "/speckit-plan add OAuth"
        assert integration.build_command_invocation("speckit.specify", "") == "/speckit-specify"

    def test_build_command_invocation_default_mode(self, tmp_path):
        integration = get_integration(self.KEY)
        manifest = IntegrationManifest(self.KEY, tmp_path)
        integration.setup(tmp_path, manifest, script_type="sh")
        assert integration.build_command_invocation("speckit.plan", "add OAuth") == "/speckit.plan add OAuth"

    def test_dispatch_command_uses_dotted_invocation_for_non_skills_project(self, tmp_path):
        from unittest import mock

        integration = get_integration(self.KEY)
        integration._skills_mode = False  # no prior skills setup

        project = tmp_path / "regular-project"
        project.mkdir()
        (project / ".opencode").mkdir()

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            integration.dispatch_command(
                "speckit.plan", "test args", project_root=project, stream=False,
            )

        called_args = mock_run.call_args[0][0]
        assert "--command" in called_args
        assert called_args[called_args.index("--command") + 1] == "speckit.plan"
        # singleton _skills_mode is not mutated by dispatch
        assert integration._skills_mode is False

    def test_dispatch_command_uses_hyphenated_invocation_for_skills_project(self, tmp_path):
        from unittest import mock

        integration = get_integration(self.KEY)
        integration._skills_mode = False  # start without skills

        project = tmp_path / "skills-project"
        skills_dir = project / ".opencode" / "skills" / "speckit-plan"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# skill", encoding="utf-8")

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(returncode=0)
            integration.dispatch_command(
                "speckit.plan", "test args", project_root=project, stream=False,
            )

        called_args = mock_run.call_args[0][0]
        assert "--command" in called_args
        assert called_args[called_args.index("--command") + 1] == "speckit-plan"
        # singleton _skills_mode is not mutated by dispatch
        assert integration._skills_mode is False
