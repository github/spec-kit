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

    def test_context_file_is_none(self):
        i = get_integration("generic")
        assert i.context_file is None

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

    # -- Scripts ----------------------------------------------------------

    def test_setup_installs_update_context_scripts(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        scripts_dir = tmp_path / ".specify" / "integrations" / "generic" / "scripts"
        assert scripts_dir.is_dir(), "Scripts directory not created for generic"
        assert (scripts_dir / "update-context.sh").exists()
        assert (scripts_dir / "update-context.ps1").exists()

    def test_scripts_tracked_in_manifest(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        script_rels = [k for k in m.files if "update-context" in k]
        assert len(script_rels) >= 2

    def test_sh_script_is_executable(self, tmp_path):
        i = get_integration("generic")
        m = IntegrationManifest("generic", tmp_path)
        i.setup(tmp_path, m, parsed_options={"commands_dir": ".custom/cmds"})
        sh = tmp_path / ".specify" / "integrations" / "generic" / "scripts" / "update-context.sh"
        assert os.access(sh, os.X_OK)

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
            ".myagent/commands/speckit.analyze.md",
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
            ".specify/integrations/generic/scripts/update-context.ps1",
            ".specify/integrations/generic/scripts/update-context.sh",
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/constitution.md",
            ".specify/scripts/bash/check-prerequisites.sh",
            ".specify/scripts/bash/common.sh",
            ".specify/scripts/bash/create-new-feature.sh",
            ".specify/scripts/bash/setup-plan.sh",
            ".specify/scripts/bash/update-agent-context.sh",
            ".specify/templates/agent-file-template.md",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
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
            ".myagent/commands/speckit.analyze.md",
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
            ".specify/integrations/generic/scripts/update-context.ps1",
            ".specify/integrations/generic/scripts/update-context.sh",
            ".specify/integrations/speckit.manifest.json",
            ".specify/memory/constitution.md",
            ".specify/scripts/powershell/check-prerequisites.ps1",
            ".specify/scripts/powershell/common.ps1",
            ".specify/scripts/powershell/create-new-feature.ps1",
            ".specify/scripts/powershell/setup-plan.ps1",
            ".specify/scripts/powershell/update-agent-context.ps1",
            ".specify/templates/agent-file-template.md",
            ".specify/templates/checklist-template.md",
            ".specify/templates/constitution-template.md",
            ".specify/templates/plan-template.md",
            ".specify/templates/spec-template.md",
            ".specify/templates/tasks-template.md",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
