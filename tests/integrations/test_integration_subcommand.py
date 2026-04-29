"""Tests for ``specify integration`` subcommand (list, install, uninstall, switch)."""

import json
import os

import pytest
from typer.testing import CliRunner

from specify_cli import app


runner = CliRunner()


def _init_project(tmp_path, integration="copilot"):
    """Helper: init a spec-kit project with the given integration."""
    project = tmp_path / "proj"
    project.mkdir()
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        result = runner.invoke(app, [
            "init", "--here",
            "--integration", integration,
            "--script", "sh",
            "--no-git",
            "--ignore-agent-tools",
        ], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)
    assert result.exit_code == 0, f"init failed: {result.output}"
    return project


def _run_in_project(project, args):
    """Run a CLI command from inside a generated project."""
    old_cwd = os.getcwd()
    try:
        os.chdir(project)
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def _write_invalid_manifest(project, key):
    manifest = project / ".specify" / "integrations" / f"{key}.manifest.json"
    manifest.write_bytes(b"\xff\xfe\x00")
    return manifest


def _integration_list_row_cells(output: str, key: str) -> list[str]:
    row = next(line for line in output.splitlines() if line.startswith(f"│ {key}"))
    return [cell.strip() for cell in row.split("│")[1:-1]]


# ── list ─────────────────────────────────────────────────────────────


class TestIntegrationList:
    def test_list_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_list_shows_installed(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "copilot" in result.output
        assert "installed" in result.output

    def test_list_shows_available_integrations(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        # Should show multiple integrations
        assert "claude" in result.output
        assert "gemini" in result.output

    def test_list_shows_multi_install_safe_status(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "Multi-install" in result.output
        assert "Safe" in result.output
        assert _integration_list_row_cells(result.output, "claude")[-1] == "yes"
        assert _integration_list_row_cells(result.output, "copilot")[-1] == "no"

    def test_list_rejects_newer_integration_state_schema(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        data = json.loads(int_json.read_text(encoding="utf-8"))
        data["integration_state_schema"] = 99
        int_json.write_text(json.dumps(data), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "list"])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        normalized = " ".join(result.output.split())
        assert "schema 99" in normalized
        assert "only supports schema 1" in normalized


# ── install ──────────────────────────────────────────────────────────


class TestIntegrationInstall:
    def test_install_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "install", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_install_unknown_integration(self, tmp_path):
        project = _init_project(tmp_path)
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "nonexistent"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_install_already_installed(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "copilot"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "already installed" in result.output
        normalized = " ".join(result.output.split())
        assert "specify integration upgrade copilot" in normalized
        assert "specify integration uninstall copilot" in normalized

    def test_install_different_when_one_exists(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "install", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Installed integrations: copilot" in result.output
        assert "Default integration: copilot" in result.output
        assert "--force" in result.output

    def test_install_multi_safe_integration(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "installed successfully" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["default_integration"] == "claude"
        assert data["integration_state_schema"] == 1
        assert data["installed_integrations"] == ["claude", "codex"]
        assert data["integration_settings"]["claude"]["invoke_separator"] == "-"
        assert data["integration_settings"]["codex"]["invoke_separator"] == "-"

        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_install_additional_preserves_shared_manifest(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        shared_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        before = set(json.loads(shared_manifest.read_text(encoding="utf-8"))["files"])
        assert before

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        after = set(json.loads(shared_manifest.read_text(encoding="utf-8"))["files"])
        assert before <= after

    def test_install_multi_safe_migrates_legacy_state(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        int_json.write_text(json.dumps({
            "integration": "claude",
            "version": "0.0.0",
        }), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads(int_json.read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["default_integration"] == "claude"
        assert data["installed_integrations"] == ["claude", "codex"]

    def test_install_multi_unsafe_requires_force(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Installed integrations: copilot" in result.output
        assert "multi-install safe" in result.output
        assert "--force" in result.output

    def test_install_multi_unsafe_allowed_with_force(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"
        assert data["installed_integrations"] == ["copilot", "claude"]

    def test_install_into_bare_project(self, tmp_path):
        """Install into a project with .specify/ but no integration."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "installed successfully" in result.output

        # integration.json written
        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"

        # Manifest created
        assert (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        # Claude uses skills directory (not commands)
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

    def test_install_bare_project_gets_shared_infra(self, tmp_path):
        """Installing into a bare project should create shared scripts and templates."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        # Shared infrastructure should be present
        assert (project / ".specify" / "scripts").is_dir()
        assert (project / ".specify" / "templates").is_dir()


# ── uninstall ────────────────────────────────────────────────────────


class TestIntegrationUninstall:
    def test_uninstall_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "uninstall"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_uninstall_no_integration(self, tmp_path):
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "No integration" in result.output

    def test_uninstall_removes_files(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        # Claude uses skills directory
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "uninstalled" in result.output

        # Command files removed
        assert not (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        # Manifest removed
        assert not (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        # integration.json removed
        assert not (project / ".specify" / "integration.json").exists()

    def test_uninstall_preserves_modified_files(self, tmp_path):
        """Full lifecycle: install → modify → uninstall → modified file kept."""
        project = _init_project(tmp_path, "claude")
        plan_file = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
        assert plan_file.exists()

        # Modify a file
        plan_file.write_text("# My custom plan command\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "preserved" in result.output

        # Modified file kept
        assert plan_file.exists()
        assert plan_file.read_text(encoding="utf-8") == "# My custom plan command\n"

    def test_uninstall_wrong_key(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_uninstall_invalid_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "manifest" in result.output
        assert "unreadable" in result.output

    def test_uninstall_non_default_preserves_default(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "uninstall", "codex",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert not (project / ".agents" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert data["installed_integrations"] == ["claude"]

    def test_uninstall_default_refreshes_templates_for_fallback(self, tmp_path):
        project = _init_project(tmp_path, "gemini")
        template = project / ".specify" / "templates" / "plan-template.md"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, ["integration", "uninstall", "gemini"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"
        assert "/speckit-plan" in template.read_text(encoding="utf-8")

    def test_uninstall_preserves_shared_infra(self, tmp_path):
        """Shared scripts and templates are not removed by integration uninstall."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "common.sh"
        assert shared_script.exists()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # Shared infrastructure preserved
        assert shared_script.exists()
        assert (project / ".specify" / "templates").is_dir()


class TestIntegrationUse:
    def test_use_installed_integration_sets_default(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, ["integration", "use", "codex"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "codex"
        assert data["default_integration"] == "codex"
        assert data["installed_integrations"] == ["claude", "codex"]

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "codex"
        assert opts["ai"] == "codex"

    def test_use_requires_installed_integration(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "use", "codex"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "not installed" in result.output

    def test_use_refreshes_shared_templates_between_command_styles(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        assert "/speckit-plan" in template.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "gemini",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            use_gemini = runner.invoke(app, ["integration", "use", "gemini"], catch_exceptions=False)
            assert use_gemini.exit_code == 0, use_gemini.output
            assert "/speckit.plan" in template.read_text(encoding="utf-8")

            use_claude = runner.invoke(app, ["integration", "use", "claude"], catch_exceptions=False)
            assert use_claude.exit_code == 0, use_claude.output
            assert "/speckit-plan" in template.read_text(encoding="utf-8")
        finally:
            os.chdir(old_cwd)

    def test_use_preserves_modified_templates_unless_forced(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        template.write_text("custom template with /speckit-plan\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "gemini",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            use_gemini = runner.invoke(app, ["integration", "use", "gemini"], catch_exceptions=False)
            assert use_gemini.exit_code == 0, use_gemini.output
            assert template.read_text(encoding="utf-8") == "custom template with /speckit-plan\n"

            force_use = runner.invoke(app, [
                "integration", "use", "gemini",
                "--force",
            ], catch_exceptions=False)
            assert force_use.exit_code == 0, force_use.output
        finally:
            os.chdir(old_cwd)

        updated = template.read_text(encoding="utf-8")
        assert "/speckit.plan" in updated
        assert "custom template" not in updated

    @pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks are unavailable")
    def test_use_does_not_persist_default_when_template_refresh_fails(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        int_json = project / ".specify" / "integration.json"
        init_options = project / ".specify" / "init-options.json"

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            before_state = json.loads(int_json.read_text(encoding="utf-8"))
            before_options = json.loads(init_options.read_text(encoding="utf-8"))

            outside = tmp_path / "outside-template.md"
            outside.write_text("# outside\n", encoding="utf-8")
            template = project / ".specify" / "templates" / "plan-template.md"
            template.unlink()
            os.symlink(outside, template)

            result = runner.invoke(app, [
                "integration", "use", "codex",
                "--force",
            ])
        finally:
            os.chdir(old_cwd)

        assert result.exit_code != 0
        assert "Failed to refresh shared templates" in result.output
        assert json.loads(int_json.read_text(encoding="utf-8")) == before_state
        assert json.loads(init_options.read_text(encoding="utf-8")) == before_options
        assert outside.read_text(encoding="utf-8") == "# outside\n"


# ── switch ───────────────────────────────────────────────────────────


class TestIntegrationSwitch:
    def test_switch_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "switch", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a spec-kit project" in result.output

    def test_switch_unknown_target(self, tmp_path):
        project = _init_project(tmp_path)
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "switch", "nonexistent"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Unknown integration" in result.output

    def test_switch_invalid_current_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "codex",
                "--script", "sh",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Could not read integration manifest" in result.output

    def test_switch_same_noop(self, tmp_path):
        project = _init_project(tmp_path, "copilot")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "switch", "copilot"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "already the default integration" in result.output

    def test_switch_same_force_refreshes_shared_templates(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        template = project / ".specify" / "templates" / "plan-template.md"
        template.write_text("# custom shared template\n", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "claude",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "managed shared templates refreshed" in result.output
        assert "/speckit-plan" in template.read_text(encoding="utf-8")

    def test_switch_installed_target_rejects_integration_options(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "switch", "codex",
                "--integration-options", "--bogus",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "--integration-options cannot be used" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["default_integration"] == "claude"

    def test_switch_between_integrations(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        # Verify claude files exist (claude uses skills)
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output
        assert "Switched to" in result.output

        # Old claude files removed
        assert not (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        # New copilot files created
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()

        # integration.json updated
        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

    def test_switch_migrates_extension_commands(self, tmp_path):
        """Switching should migrate extension commands to the new agent directory."""
        project = _init_project(tmp_path, "kimi")

        # Install the bundled git extension
        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        # Verify git extension skills exist for kimi
        kimi_git_feature = project / ".kimi" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert kimi_git_feature.exists(), "Git extension skill should exist for kimi"

        result = _run_in_project(project, [
            "integration", "switch", "opencode",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        # Git extension commands should exist for opencode
        opencode_git_feature = project / ".opencode" / "command" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Git extension command should exist for opencode"

        # Old kimi extension skills should be removed
        assert not kimi_git_feature.exists(), "Old kimi extension skill should be removed"

        # Extension registry should be updated
        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        registered_commands = registry["extensions"]["git"]["registered_commands"]
        assert "opencode" in registered_commands
        assert "kimi" not in registered_commands

        # Switch to claude
        result = _run_in_project(project, [
            "integration", "switch", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        # Git extension skills should exist for claude
        claude_git_feature = project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert claude_git_feature.exists(), "Git extension skill should exist for claude"

        # Old opencode extension commands should be removed
        assert not opencode_git_feature.exists(), "Old opencode extension command should be removed"

        # Extension registry should be updated
        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        registered_commands = registry["extensions"]["git"]["registered_commands"]
        assert "claude" in registered_commands
        assert "opencode" not in registered_commands

    def test_switch_migrates_copilot_skills_extension_commands(self, tmp_path):
        """Copilot --skills should receive extension skills, not .agent.md files."""
        project = _init_project(tmp_path, "opencode")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"

        result = _run_in_project(project, [
            "integration", "switch", "copilot",
            "--script", "sh",
            "--integration-options", "--skills",
        ])
        assert result.exit_code == 0, result.output

        copilot_git_feature = project / ".github" / "skills" / "speckit-git-feature" / "SKILL.md"
        copilot_agent_file = project / ".github" / "agents" / "speckit.git.feature.agent.md"
        assert copilot_git_feature.exists(), "Git extension skill should exist for Copilot skills mode"
        assert not copilot_agent_file.exists(), "Copilot skills mode should not create extension .agent.md files"

        # Verify Copilot-specific frontmatter: mode field should map from
        # skill name (speckit-git-feature) back to dot notation (speckit.git-feature)
        skill_content = copilot_git_feature.read_text(encoding="utf-8")
        assert "mode: speckit.git-feature" in skill_content, (
            "Copilot skill frontmatter should contain mode mapped from skill name"
        )

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert "speckit-git-feature" in git_meta["registered_skills"]
        assert "copilot" not in git_meta["registered_commands"]

        result = _run_in_project(project, [
            "integration", "switch", "opencode",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        opencode_git_feature = project / ".opencode" / "command" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Git extension command should exist for opencode"
        assert not copilot_git_feature.exists(), "Old Copilot extension skill should be removed"

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert git_meta["registered_skills"] == []
        assert "opencode" in git_meta["registered_commands"]
        assert "copilot" not in git_meta["registered_commands"]

    def test_switch_does_not_register_disabled_extensions(self, tmp_path):
        """Disabled extensions should stay disabled and should not migrate commands."""
        project = _init_project(tmp_path, "opencode")

        result = _run_in_project(project, ["extension", "add", "git"])
        assert result.exit_code == 0, f"extension add failed: {result.output}"
        result = _run_in_project(project, ["extension", "disable", "git"])
        assert result.exit_code == 0, result.output

        opencode_git_feature = project / ".opencode" / "command" / "speckit.git.feature.md"
        assert opencode_git_feature.exists(), "Disabled extension command remains until integration switch"

        result = _run_in_project(project, [
            "integration", "switch", "claude",
            "--script", "sh",
        ])
        assert result.exit_code == 0, result.output

        claude_git_feature = project / ".claude" / "skills" / "speckit-git-feature" / "SKILL.md"
        assert not claude_git_feature.exists(), "Disabled extension should not be registered for new agent"
        assert not opencode_git_feature.exists(), "Old disabled extension command should be removed on switch"

        registry = json.loads(
            (project / ".specify" / "extensions" / ".registry").read_text(encoding="utf-8")
        )
        git_meta = registry["extensions"]["git"]
        assert git_meta["enabled"] is False
        assert "claude" not in git_meta["registered_commands"]
        assert "opencode" not in git_meta["registered_commands"]

    def test_switch_preserves_shared_infra(self, tmp_path):
        """Switching preserves shared scripts, templates, and memory."""
        project = _init_project(tmp_path, "claude")
        shared_script = project / ".specify" / "scripts" / "bash" / "common.sh"
        assert shared_script.exists()
        shared_content = shared_script.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # Shared infra untouched
        assert shared_script.exists()
        assert shared_script.read_text(encoding="utf-8") == shared_content

    def test_switch_from_nothing(self, tmp_path):
        """Switch when no integration is installed should just install the target."""
        project = tmp_path / "bare"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "switch", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "Switched to" in result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "claude"

    def test_failed_switch_keeps_fallback_metadata_consistent(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "codex",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "switch", "generic",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "codex"
        assert data["installed_integrations"] == ["codex"]

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "codex"
        assert opts["ai"] == "codex"

        template = project / ".specify" / "templates" / "plan-template.md"
        assert "/speckit-plan" in template.read_text(encoding="utf-8")


class TestIntegrationUpgrade:
    def test_upgrade_invalid_manifest_reports_cli_error(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        _write_invalid_manifest(project, "claude")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "upgrade", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "manifest" in result.output
        assert "unreadable" in result.output

    def test_upgrade_non_default_keeps_default_template_invocations(self, tmp_path):
        project = _init_project(tmp_path, "gemini")
        template = project / ".specify" / "templates" / "plan-template.md"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            install = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert install.exit_code == 0, install.output

            result = runner.invoke(app, [
                "integration", "upgrade", "claude",
                "--script", "sh",
                "--force",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, result.output

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "gemini"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")


# ── Full lifecycle ───────────────────────────────────────────────────


class TestIntegrationLifecycle:
    def test_install_modify_uninstall_preserves_modified(self, tmp_path):
        """Full lifecycle: install → modify file → uninstall → verify modified file kept."""
        project = tmp_path / "lifecycle"
        project.mkdir()
        (project / ".specify").mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)

            # Install
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert result.exit_code == 0
            assert "installed successfully" in result.output

            # Claude uses skills directory
            plan_file = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
            assert plan_file.exists()

            # Modify one file
            plan_file.write_text("# user customization\n", encoding="utf-8")

            # Uninstall
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
            assert result.exit_code == 0
            assert "preserved" in result.output

            # Modified file kept
            assert plan_file.exists()
            assert plan_file.read_text(encoding="utf-8") == "# user customization\n"
        finally:
            os.chdir(old_cwd)


# ── Edge-case fixes ─────────────────────────────────────────────────


class TestScriptTypeValidation:
    def test_invalid_script_type_rejected(self, tmp_path):
        """--script with an invalid value should fail with a clear error."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "bash",
            ])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Invalid script type" in result.output

    def test_valid_script_types_accepted(self, tmp_path):
        """Both 'sh' and 'ps' should be accepted."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0


class TestParseIntegrationOptionsEqualsForm:
    def test_equals_form_parsed(self):
        """--commands-dir=./x should be parsed the same as --commands-dir ./x."""
        from specify_cli import _parse_integration_options
        from specify_cli.integrations import get_integration

        integration = get_integration("generic")
        assert integration is not None

        result_space = _parse_integration_options(integration, "--commands-dir ./mydir")
        result_equals = _parse_integration_options(integration, "--commands-dir=./mydir")
        assert result_space is not None
        assert result_equals is not None
        assert result_space["commands_dir"] == "./mydir"
        assert result_equals["commands_dir"] == "./mydir"


class TestUninstallNoManifestClearsInitOptions:
    def test_init_options_cleared_on_no_manifest_uninstall(self, tmp_path):
        """When no manifest exists, uninstall should still clear init-options.json."""
        project = tmp_path / "proj"
        project.mkdir()
        (project / ".specify").mkdir()

        # Write integration.json and init-options.json without a manifest
        int_json = project / ".specify" / "integration.json"
        int_json.write_text(json.dumps({"integration": "claude"}), encoding="utf-8")

        opts_json = project / ".specify" / "init-options.json"
        opts_json.write_text(json.dumps({
            "integration": "claude",
            "ai": "claude",
            "ai_skills": True,
            "script": "sh",
        }), encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall", "claude"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # init-options.json should have integration keys cleared
        opts = json.loads(opts_json.read_text(encoding="utf-8"))
        assert "integration" not in opts
        assert "ai" not in opts
        assert "ai_skills" not in opts
        # Non-integration keys preserved
        assert opts.get("script") == "sh"


class TestSwitchClearsMetadataAfterTeardown:
    def test_metadata_cleared_between_phases(self, tmp_path):
        """After a successful switch, metadata should reference the new integration."""
        project = _init_project(tmp_path, "claude")

        # Verify initial state
        int_json = project / ".specify" / "integration.json"
        assert json.loads(int_json.read_text(encoding="utf-8"))["integration"] == "claude"

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            # Switch to copilot — should succeed and update metadata
            result = runner.invoke(app, [
                "integration", "switch", "copilot",
                "--script", "sh",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0

        # integration.json should reference copilot, not claude
        data = json.loads(int_json.read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

        # init-options.json should reference copilot
        opts_json = project / ".specify" / "init-options.json"
        opts = json.loads(opts_json.read_text(encoding="utf-8"))
        assert opts.get("ai") == "copilot"
