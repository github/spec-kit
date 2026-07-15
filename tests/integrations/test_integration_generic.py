"""Tests for GenericIntegration."""

import os

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations.base import MarkdownIntegration
from specify_cli.integrations.manifest import IntegrationManifest


class TestGenericIntegration:
    """Tests for GenericIntegration — requires --commands-dir option."""

    # -- Registration -----------------------------------------------------

    def test_registered(self):
        from specify_cli.integrations import INTEGRATION_REGISTRY
        assert "generic" in INTEGRATION_REGISTRY

    def test_is_markdown_integration(self):
        assert isinstance(get_integration("generic"), MarkdownIntegration)

    # -- Config -----------------------------------------------------------

    def test_config_folder_is_none(self):
        i = get_integration("generic")
        assert i.config["folder"] is None

    def test_config_requires_cli_false(self):
        i = get_integration("generic")
        assert i.config["requires_cli"] is False

    # -- Options ----------------------------------------------------------

    def test_options_include_commands_dir(self):
        i = get_integration("generic")
        opts = i.options()
        assert len(opts) == 1
        assert opts[0].name == "--commands-dir"
        assert opts[0].required is True
        assert opts[0].is_flag is False

    # -- Setup / teardown -------------------------------------------------

    def test_setup_requires_commands_dir(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        with pytest.raises(ValueError, match="--commands-dir is required"):
            i.setup(tmp_path, m, parsed_options={})

    def test_setup_requires_nonempty_commands_dir(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        with pytest.raises(ValueError, match="--commands-dir is required"):
            i.setup(tmp_path, m, parsed_options={"commands_dir": ""})

    def test_setup_writes_to_correct_directory(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".myagent/commands"},
        )
        expected_dir = tmp_path / ".myagent" / "commands"
        assert expected_dir.exists(), f"Expected directory {expected_dir} was not created"
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) > 0, "No command files were created"
        for f in cmd_files:
            assert f.resolve().parent == expected_dir.resolve(), (
                f"{f} is not under {expected_dir}"
            )

    def test_setup_creates_md_files(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) > 0
        for f in cmd_files:
            assert f.name.startswith("speckit.")
            assert f.name.endswith(".md")

    def test_templates_are_processed(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        cmd_files = [f for f in created if "scripts" not in f.parts]
        for f in cmd_files:
            content = f.read_text(encoding="utf-8")
            assert "{SCRIPT}" not in content, f"{f.name} has unprocessed {{SCRIPT}}"
            assert "__AGENT__" not in content, f"{f.name} has unprocessed __AGENT__"
            assert "{ARGS}" not in content, f"{f.name} has unprocessed {{ARGS}}"
            assert "__SPECKIT_COMMAND_" not in content, f"{f.name} has unprocessed __SPECKIT_COMMAND_*__"

    def test_all_files_tracked_in_manifest(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.setup(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        for f in created:
            rel = f.resolve().relative_to(tmp_path.resolve()).as_posix()
            assert rel in m.files, f"{rel} not tracked in manifest"

    def test_install_uninstall_roundtrip(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.install(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        assert len(created) > 0
        m.save()
        for f in created:
            assert f.exists()
        removed, skipped = i.uninstall(tmp_path, m)
        assert len(removed) == len(created)
        assert skipped == []

    def test_modified_file_survives_uninstall(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        created = i.install(
            tmp_path, m,
            parsed_options={"commands_dir": ".custom/cmds"},
        )
        m.save()
        modified = created[0]
        modified.write_text("user modified this", encoding="utf-8")
        removed, skipped = i.uninstall(tmp_path, m)
        assert modified.exists()
        assert modified in skipped

    def test_different_commands_dirs(self, tmp_path):
        """Generic should work with various user-specified paths."""
        for path in [".agent/commands", "tools/ai-cmds", ".custom/prompts"]:
            project = tmp_path / path.replace("/", "-")
            project.mkdir()
            i = get_integration("generic")
            m = IntegrationManifest("generic", project)
            created = i.setup(
                project, m,
                parsed_options={"commands_dir": path},
            )
            expected = project / path
            assert expected.is_dir(), f"Dir {expected} not created for {path}"
            cmd_files = [f for f in created if "scripts" not in f.parts]
            assert len(cmd_files) > 0

    # -- Context section ---------------------------------------------------

    def test_setup_does_not_write_context_section(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        for path in tmp_path.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert "<!-- SPECKIT START -->" not in text

    def test_plan_command_has_no_context_placeholder(self, tmp_path):
        """The core plan command must not carry a context-file placeholder —
        agent context files are owned by the opt-in agent-context extension."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        plan_file = tmp_path / ".custom" / "cmds" / "speckit.plan.md"
        assert plan_file.exists()
        content = plan_file.read_text(encoding="utf-8")
        assert "__CONTEXT_FILE__" not in content

    def test_plan_defines_quickstart_as_validation_guide(self, tmp_path):
        """The generated plan command should keep quickstart.md out of implementation scope."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        plan_file = tmp_path / ".custom" / "cmds" / "speckit.plan.md"
        assert plan_file.exists()
        content = plan_file.read_text(encoding="utf-8")

        assert "Create quickstart validation guide" in content
        assert "runnable validation scenarios" in content
        assert "Do not include full implementation code" in content
        assert "implementation details belong in `tasks.md` and the implementation phase" in content

    def test_implement_loads_constitution_context(self, tmp_path):
        """The generated implement command should load constitution governance context."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        implement_file = tmp_path / ".custom" / "cmds" / "speckit.implement.md"
        assert implement_file.exists()
        content = implement_file.read_text(encoding="utf-8")
        assert ".specify/memory/constitution.md" in content

    @pytest.mark.parametrize(
        "command_stem",
        [
            "analyze",
            "clarify",
            "converge",
            "implement",
            "plan",
            "checklist",
            "specify",
            "tasks",
            "taskstoissues",
        ],
    )
    def test_command_loads_constitution_context(self, tmp_path, command_stem):
        """Every command except constitution must reference constitution.md."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        cmd_file = tmp_path / ".custom" / "cmds" / f"speckit.{command_stem}.md"
        assert cmd_file.exists(), f"Command file missing: {cmd_file.name}"
        content = cmd_file.read_text(encoding="utf-8")
        assert "constitution.md" in content, (
            f"speckit.{command_stem}.md must reference constitution.md"
        )

    def test_constitution_command_exists(self, tmp_path):
        """The constitution command itself must exist but is not required to load itself."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        cmd_file = tmp_path / ".custom" / "cmds" / "speckit.constitution.md"
        assert cmd_file.exists()

    # -- CLI --------------------------------------------------------------

    def test_cli_generic_without_commands_dir_fails(self, tmp_path):
        """--integration generic without --integration-options should fail."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(tmp_path / "test-generic"), "--integration", "generic",
        ])
        # Generic requires --commands-dir via --integration-options
        assert result.exit_code != 0


    def test_complete_file_inventory_sh(self, tmp_path):
        """Every file produced by specify init --integration generic --integration-options=--commands-dir ... --script sh."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-generic-sh"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--integration-options=--commands-dir .myagent/commands",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file() and ".git" not in p.parts
        )
        expected = sorted([
            ".myagent/commands/speckit.analyze.md",
            ".myagent/commands/speckit.checklist.md",
            ".myagent/commands/speckit.clarify.md",
            ".myagent/commands/speckit.constitution.md",
            ".myagent/commands/speckit.converge.md",
            ".myagent/commands/speckit.implement.md",
            ".myagent/commands/speckit.plan.md",
            ".myagent/commands/speckit.specify.md",
            ".myagent/commands/speckit.tasks.md",
            ".myagent/commands/speckit.taskstoissues.md",
            ".specify/init-options.json",
            ".specify/integration.json",
            ".specify/integrations/generic.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/.constitution-template.json",
            ".specify/memory/constitution.md",
            ".specify/scripts/bash/check-prerequisites.sh",
            ".specify/scripts/bash/common.sh",
            ".specify/scripts/bash/create-new-feature.sh",
            ".specify/scripts/bash/setup-plan.sh",
            ".specify/scripts/bash/setup-tasks.sh",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
            ".specify/workflows/speckit/workflow.yml",
            ".specify/workflows/workflow-registry.json",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )

    def test_complete_file_inventory_ps(self, tmp_path):
        """Every file produced by specify init --integration generic --integration-options=--commands-dir ... --script ps."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-generic-ps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--integration-options=--commands-dir .myagent/commands",
                "--script", "ps",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file() and ".git" not in p.parts
        )
        expected = sorted([
            ".myagent/commands/speckit.analyze.md",
            ".myagent/commands/speckit.checklist.md",
            ".myagent/commands/speckit.clarify.md",
            ".myagent/commands/speckit.constitution.md",
            ".myagent/commands/speckit.converge.md",
            ".myagent/commands/speckit.implement.md",
            ".myagent/commands/speckit.plan.md",
            ".myagent/commands/speckit.specify.md",
            ".myagent/commands/speckit.tasks.md",
            ".myagent/commands/speckit.taskstoissues.md",
            ".specify/init-options.json",
            ".specify/integration.json",
            ".specify/integrations/generic.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/.constitution-template.json",
            ".specify/memory/constitution.md",
            ".specify/scripts/powershell/check-prerequisites.ps1",
            ".specify/scripts/powershell/common.ps1",
            ".specify/scripts/powershell/create-new-feature.ps1",
            ".specify/scripts/powershell/setup-plan.ps1",
            ".specify/scripts/powershell/setup-tasks.ps1",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
            ".specify/workflows/speckit/workflow.yml",
            ".specify/workflows/workflow-registry.json",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
