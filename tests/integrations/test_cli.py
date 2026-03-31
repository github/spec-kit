"""Tests for --integration flag on specify init (CLI-level)."""

import json
import os

import pytest


class TestInitIntegrationFlag:
    def test_integration_and_ai_mutually_exclusive(self):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", "test-project", "--ai", "claude", "--integration", "copilot",
        ])
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output

    def test_unknown_integration_rejected(self):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        result = runner.invoke(app, [
            "init", "test-project", "--integration", "nonexistent",
        ])
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_integration_copilot_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "int-test"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here", "--integration", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()
        assert (project / ".github" / "prompts" / "speckit.plan.prompt.md").exists()
        assert (project / ".specify" / "scripts" / "bash" / "common.sh").exists()

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"
        assert "scripts" in data
        assert "update-context" in data["scripts"]

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "copilot"

        assert (project / ".specify" / "integrations" / "copilot.manifest.json").exists()
        assert (project / ".specify" / "integrations" / "copilot" / "scripts" / "update-context.sh").exists()

        shared_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        assert shared_manifest.exists()

    def test_ai_copilot_auto_promotes(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        project = tmp_path / "promote-test"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            runner = CliRunner()
            result = runner.invoke(app, [
                "init", "--here", "--ai", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "--integration copilot" in result.output
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()

    def test_complete_file_inventory_sh(self, tmp_path):
        """Every file produced by --integration copilot --script sh."""
        from typer.testing import CliRunner
        from specify_cli import app
        project = tmp_path / "inventory-sh"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        actual = sorted(str(p.relative_to(project)) for p in project.rglob("*") if p.is_file())
        expected = sorted([
            ".github/agents/speckit.analyze.agent.md",
            ".github/agents/speckit.checklist.agent.md",
            ".github/agents/speckit.clarify.agent.md",
            ".github/agents/speckit.constitution.agent.md",
            ".github/agents/speckit.implement.agent.md",
            ".github/agents/speckit.plan.agent.md",
            ".github/agents/speckit.specify.agent.md",
            ".github/agents/speckit.tasks.agent.md",
            ".github/agents/speckit.taskstoissues.agent.md",
            ".github/prompts/speckit.analyze.prompt.md",
            ".github/prompts/speckit.checklist.prompt.md",
            ".github/prompts/speckit.clarify.prompt.md",
            ".github/prompts/speckit.constitution.prompt.md",
            ".github/prompts/speckit.implement.prompt.md",
            ".github/prompts/speckit.plan.prompt.md",
            ".github/prompts/speckit.specify.prompt.md",
            ".github/prompts/speckit.tasks.prompt.md",
            ".github/prompts/speckit.taskstoissues.prompt.md",
            ".vscode/settings.json",
            ".specify/integration.json",
            ".specify/init-options.json",
            ".specify/integrations/copilot.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/integrations/copilot/scripts/update-context.ps1",
            ".specify/integrations/copilot/scripts/update-context.sh",
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
            ".specify/memory/constitution.md",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )

    def test_complete_file_inventory_ps(self, tmp_path):
        """Every file produced by --integration copilot --script ps."""
        from typer.testing import CliRunner
        from specify_cli import app
        project = tmp_path / "inventory-ps"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = CliRunner().invoke(app, [
                "init", "--here", "--integration", "copilot", "--script", "ps", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        actual = sorted(str(p.relative_to(project)) for p in project.rglob("*") if p.is_file())
        expected = sorted([
            ".github/agents/speckit.analyze.agent.md",
            ".github/agents/speckit.checklist.agent.md",
            ".github/agents/speckit.clarify.agent.md",
            ".github/agents/speckit.constitution.agent.md",
            ".github/agents/speckit.implement.agent.md",
            ".github/agents/speckit.plan.agent.md",
            ".github/agents/speckit.specify.agent.md",
            ".github/agents/speckit.tasks.agent.md",
            ".github/agents/speckit.taskstoissues.agent.md",
            ".github/prompts/speckit.analyze.prompt.md",
            ".github/prompts/speckit.checklist.prompt.md",
            ".github/prompts/speckit.clarify.prompt.md",
            ".github/prompts/speckit.constitution.prompt.md",
            ".github/prompts/speckit.implement.prompt.md",
            ".github/prompts/speckit.plan.prompt.md",
            ".github/prompts/speckit.specify.prompt.md",
            ".github/prompts/speckit.tasks.prompt.md",
            ".github/prompts/speckit.taskstoissues.prompt.md",
            ".vscode/settings.json",
            ".specify/integration.json",
            ".specify/init-options.json",
            ".specify/integrations/copilot.manifest.json",
            ".specify/integrations/speckit.manifest.json",
            ".specify/integrations/copilot/scripts/update-context.ps1",
            ".specify/integrations/copilot/scripts/update-context.sh",
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
            ".specify/memory/constitution.md",
        ])
        assert actual == expected, (
            f"Missing: {sorted(set(expected) - set(actual))}\n"
            f"Extra: {sorted(set(actual) - set(expected))}"
        )
