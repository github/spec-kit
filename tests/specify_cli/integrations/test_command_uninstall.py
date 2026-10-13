"""Tests for mirrored integration CLI behavior in test_command_uninstall.py."""

from __future__ import annotations

import json  # noqa: F401
import os  # noqa: F401
import shutil  # noqa: F401
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from specify_cli import app  # noqa: F401
from tests.conftest import strip_ansi  # noqa: F401
from tests.specify_cli.integrations._helpers import (
    _copy_project_template,  # noqa: F401
    _init_project,  # noqa: F401
    _integration_list_row_cells,  # noqa: F401
    _move_kilocode_install_to_legacy_layout,  # noqa: F401
    _run_in_project,  # noqa: F401
    _write_invalid_manifest,  # noqa: F401
    runner,  # noqa: F401
)

class TestIntegrationUninstall:
    def test_uninstall_requires_speckit_project(self, tmp_path):
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(app, ["integration", "uninstall"])
        finally:
            os.chdir(old_cwd)
        assert result.exit_code != 0
        assert "Not a Spec Kit project" in result.output

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
        assert ".claude/skills/speckit-plan/SKILL.md" in result.output

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
        script = project / ".specify" / "scripts" / "bash" / "check-prerequisites.sh"
        assert "/speckit.plan" in template.read_text(encoding="utf-8")
        assert "/speckit.plan" in script.read_text(encoding="utf-8")

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
        assert "/speckit-plan" in script.read_text(encoding="utf-8")

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
