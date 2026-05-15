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

    def test_context_file_is_agents_md(self):
        i = get_integration("generic")
        assert i.context_file == "AGENTS.md"

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

    def test_setup_upserts_context_section(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        if i.context_file:
            ctx_path = tmp_path / i.context_file
            assert ctx_path.exists()
            content = ctx_path.read_text(encoding="utf-8")
            assert "<!-- SPECKIT START -->" in content
            assert "<!-- SPECKIT END -->" in content

    def test_plan_references_correct_context_file(self, tmp_path):
        """The generated plan command must reference generic's context file."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        plan_file = tmp_path / ".custom" / "cmds" / "speckit.plan.md"
        assert plan_file.exists()
        content = plan_file.read_text(encoding="utf-8")
        assert i.context_file in content, (
            f"Plan command should reference {i.context_file!r}"
        )
        assert "__CONTEXT_FILE__" not in content

    def test_implement_loads_constitution_context(self, tmp_path):
        """The generated implement command should load constitution governance context."""
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        implement_file = tmp_path / ".custom" / "cmds" / "speckit.implement.md"
        assert implement_file.exists()
        content = implement_file.read_text(encoding="utf-8")
        assert ".specify/memory/constitution.md" in content

    # -- CLI --------------------------------------------------------------

    def test_cli_generic_without_commands_dir_fails(self, tmp_path):
        """--integration generic without --ai-commands-dir should fail."""
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", str(tmp_path / "test-generic"), "--integration", "generic",
            "--script", "sh", "--no-git",
        ])
        # Generic requires --commands-dir / --ai-commands-dir
        # The integration path validates via setup()
        assert result.exit_code != 0

    def test_init_options_includes_context_file(self, tmp_path):
        """init-options.json must include context_file for the generic integration."""
        import json
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "opts-generic"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--ai-commands-dir", ".myagent/commands",
                "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        opts = json.loads((project / ".specify" / "init-options.json").read_text())
        assert opts.get("context_file") == "AGENTS.md"

    def test_complete_file_inventory_sh(self, tmp_path):
        """Every file produced by specify init --integration generic --ai-commands-dir ... --script sh."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-generic-sh"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--ai-commands-dir", ".myagent/commands",
                "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        expected = sorted([
            "AGENTS.md",
            ".myagent/commands/speckit.agent.md",
            ".myagent/commands/speckit.analyze.md",
            ".myagent/commands/speckit.arch.md",
            ".myagent/commands/speckit.governance.md",
            ".myagent/commands/speckit.checklist.md",
            ".myagent/commands/speckit.clarify.md",
            ".myagent/commands/speckit.constitution.md",
            ".myagent/commands/speckit.implement.md",
            ".myagent/commands/speckit.plan.md",
            ".myagent/commands/speckit.specify.md",
            ".myagent/commands/speckit.tasks.md",
            ".myagent/commands/speckit.taskstoissues.md",
            ".specify/init-options.json",
            ".specify/integration.json",
            ".specify/integrations/generic.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/agent-governance.md",
            ".specify/memory/constitution.md",
            ".specify/scripts/bash/check-prerequisites.sh",
            ".specify/scripts/bash/common.sh",
            ".specify/scripts/bash/create-new-feature.sh",
            ".specify/scripts/bash/setup-arch.sh",
            ".specify/scripts/bash/setup-plan.sh",
            ".specify/scripts/bash/setup-tasks.sh",
            ".specify/templates/agent-governance-template.md",
            ".specify/templates/architecture-development-template.md",
            ".specify/templates/architecture-logical-template.md",
            ".specify/templates/architecture-physical-template.md",
            ".specify/templates/architecture-process-template.md",
            ".specify/templates/architecture-scenario-template.md",
            ".specify/templates/architecture-template.md",
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
        """Every file produced by specify init --integration generic --ai-commands-dir ... --script ps."""
        from typer.testing import CliRunner
        from specify_cli import app

        project = tmp_path / "inventory-generic-ps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "generic",
                "--ai-commands-dir", ".myagent/commands",
                "--script", "ps", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        actual = sorted(
            p.relative_to(project).as_posix()
            for p in project.rglob("*") if p.is_file()
        )
        expected = sorted([
            "AGENTS.md",
            ".myagent/commands/speckit.agent.md",
            ".myagent/commands/speckit.analyze.md",
            ".myagent/commands/speckit.arch.md",
            ".myagent/commands/speckit.governance.md",
            ".myagent/commands/speckit.checklist.md",
            ".myagent/commands/speckit.clarify.md",
            ".myagent/commands/speckit.constitution.md",
            ".myagent/commands/speckit.implement.md",
            ".myagent/commands/speckit.plan.md",
            ".myagent/commands/speckit.specify.md",
            ".myagent/commands/speckit.tasks.md",
            ".myagent/commands/speckit.taskstoissues.md",
            ".specify/init-options.json",
            ".specify/integration.json",
            ".specify/integrations/generic.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/agent-governance.md",
            ".specify/memory/constitution.md",
            ".specify/scripts/powershell/check-prerequisites.ps1",
            ".specify/scripts/powershell/common.ps1",
            ".specify/scripts/powershell/create-new-feature.ps1",
            ".specify/scripts/powershell/setup-arch.ps1",
            ".specify/scripts/powershell/setup-plan.ps1",
            ".specify/scripts/powershell/setup-tasks.ps1",
            ".specify/templates/agent-governance-template.md",
            ".specify/templates/architecture-development-template.md",
            ".specify/templates/architecture-logical-template.md",
            ".specify/templates/architecture-physical-template.md",
            ".specify/templates/architecture-process-template.md",
            ".specify/templates/architecture-scenario-template.md",
            ".specify/templates/architecture-template.md",
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
