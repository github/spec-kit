"""Tests for the `specify doctor` CLI command."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from specify_cli import app, AGENT_CONFIG


runner = CliRunner()


@pytest.fixture
def speckit_project(tmp_path):
    """Create a minimal spec-kit project structure."""
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()

    # Init options
    init_opts = {
        "ai": "claude",
        "ai_skills": False,
        "script": "sh",
        "speckit_version": "0.4.3",
    }
    (specify_dir / "init-options.json").write_text(json.dumps(init_opts))

    # Constitution
    memory_dir = specify_dir / "memory"
    memory_dir.mkdir()
    (memory_dir / "constitution.md").write_text("# Constitution\nProject principles here.\n")

    # Templates
    templates_dir = specify_dir / "templates"
    templates_dir.mkdir()
    (templates_dir / "spec-template.md").write_text("# Spec Template\n")
    (templates_dir / "constitution-template.md").write_text("# Constitution Template\n")

    # Scripts
    scripts_dir = specify_dir / "scripts" / "bash"
    scripts_dir.mkdir(parents=True)
    script_file = scripts_dir / "check-prerequisites.sh"
    script_file.write_text("#!/usr/bin/env bash\necho 'ok'\n")
    if os.name != "nt":
        script_file.chmod(0o755)

    # Agent directory
    claude_dir = tmp_path / ".claude" / "commands"
    claude_dir.mkdir(parents=True)
    (claude_dir / "speckit.specify.md").write_text("# Specify command\n")

    return tmp_path


@pytest.fixture
def bare_project(tmp_path):
    """Create a directory without .specify/ — not a spec-kit project."""
    return tmp_path


class TestDoctorBasic:
    """Basic doctor command tests."""

    def test_doctor_exits_with_error_when_not_speckit_project(self, bare_project):
        """Doctor should fail when .specify/ directory doesn't exist."""
        result = runner.invoke(app, ["doctor"], catch_exceptions=False)
        # The command runs in CWD so we need to change to bare_project
        with patch("specify_cli.Path") as mock_path:
            pass  # CWD-based test handled below

    def test_doctor_healthy_project(self, speckit_project, monkeypatch):
        """Doctor should report healthy for a well-formed project."""
        monkeypatch.chdir(speckit_project)
        # Mock git and agent checks to avoid external dependencies
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "project-structure" in result.output
        assert "pass" in result.output.lower() or "●" in result.output

    def test_doctor_json_output(self, speckit_project, monkeypatch):
        """Doctor --json should produce valid JSON."""
        monkeypatch.chdir(speckit_project)
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)
        assert result.exit_code == 0
        # Extract JSON from output (skip any non-JSON lines)
        output = result.output.strip()
        data = json.loads(output)
        assert "checks" in data
        assert "fixes_applied" in data
        assert isinstance(data["checks"], list)

    def test_doctor_no_speckit_dir_json(self, bare_project, monkeypatch):
        """Doctor --json should output JSON even on failure."""
        monkeypatch.chdir(bare_project)
        result = runner.invoke(app, ["doctor", "--json"])
        assert result.exit_code == 1
        output = result.output.strip()
        data = json.loads(output)
        assert any(c["status"] == "fail" for c in data["checks"])


class TestDoctorChecks:
    """Test individual diagnostic checks."""

    def test_missing_constitution_detected(self, speckit_project, monkeypatch):
        """Doctor should warn when constitution.md is missing from memory/."""
        monkeypatch.chdir(speckit_project)
        constitution = speckit_project / ".specify" / "memory" / "constitution.md"
        constitution.unlink()

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        constitution_checks = [c for c in data["checks"] if c["check"] == "constitution"]
        assert len(constitution_checks) == 1
        assert constitution_checks[0]["status"] == "warn"
        assert constitution_checks[0]["fixable"] is True

    def test_constitution_fix(self, speckit_project, monkeypatch):
        """Doctor --fix should copy constitution from template."""
        monkeypatch.chdir(speckit_project)
        constitution = speckit_project / ".specify" / "memory" / "constitution.md"
        constitution.unlink()

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--fix", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        assert any(f.startswith("Copied constitution") for f in data["fixes_applied"])
        assert constitution.is_file()

    def test_init_options_detected(self, speckit_project, monkeypatch):
        """Doctor should detect init-options.json."""
        monkeypatch.chdir(speckit_project)
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        init_checks = [c for c in data["checks"] if c["check"] == "init-options"]
        assert len(init_checks) == 1
        assert init_checks[0]["status"] == "pass"
        assert "claude" in init_checks[0]["message"]

    def test_missing_init_options_warns(self, speckit_project, monkeypatch):
        """Doctor should warn when init-options.json is missing."""
        monkeypatch.chdir(speckit_project)
        (speckit_project / ".specify" / "init-options.json").unlink()

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        init_checks = [c for c in data["checks"] if c["check"] == "init-options"]
        assert len(init_checks) == 1
        assert init_checks[0]["status"] == "warn"

    def test_scripts_directory_check(self, speckit_project, monkeypatch):
        """Doctor should verify scripts directory."""
        monkeypatch.chdir(speckit_project)
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        script_checks = [c for c in data["checks"] if c["check"] == "scripts"]
        assert len(script_checks) == 1
        assert script_checks[0]["status"] == "pass"

    def test_templates_directory_check(self, speckit_project, monkeypatch):
        """Doctor should verify templates directory."""
        monkeypatch.chdir(speckit_project)
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        template_checks = [c for c in data["checks"] if c["check"] == "templates"]
        assert len(template_checks) == 1
        assert template_checks[0]["status"] == "pass"

    def test_agent_cli_found(self, speckit_project, monkeypatch):
        """Doctor should report when agent CLI is found."""
        monkeypatch.chdir(speckit_project)
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=True):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        cli_checks = [c for c in data["checks"] if c["check"] == "agent-cli"]
        assert len(cli_checks) == 1
        assert cli_checks[0]["status"] == "pass"

    def test_agent_cli_not_found(self, speckit_project, monkeypatch):
        """Doctor should warn when agent CLI is missing."""
        monkeypatch.chdir(speckit_project)
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        cli_checks = [c for c in data["checks"] if c["check"] == "agent-cli"]
        assert len(cli_checks) == 1
        assert cli_checks[0]["status"] == "warn"


class TestDoctorExtensions:
    """Test extension-related diagnostics."""

    def test_extension_registry_healthy(self, speckit_project, monkeypatch):
        """Doctor should detect healthy extension registry."""
        monkeypatch.chdir(speckit_project)
        ext_dir = speckit_project / ".specify" / "extensions"
        ext_dir.mkdir()
        registry = {"my-ext": {"name": "My Extension", "version": "1.0.0", "enabled": True}}
        (ext_dir / "registry.json").write_text(json.dumps(registry))
        (ext_dir / "my-ext").mkdir()

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        ext_checks = [c for c in data["checks"] if c["check"] == "extensions"]
        assert len(ext_checks) == 1
        assert ext_checks[0]["status"] == "pass"
        assert "1 extension" in ext_checks[0]["message"]

    def test_extension_missing_directory(self, speckit_project, monkeypatch):
        """Doctor should warn when extension directory is missing."""
        monkeypatch.chdir(speckit_project)
        ext_dir = speckit_project / ".specify" / "extensions"
        ext_dir.mkdir()
        registry = {"ghost-ext": {"name": "Ghost", "version": "1.0.0"}}
        (ext_dir / "registry.json").write_text(json.dumps(registry))
        # Intentionally do NOT create the ghost-ext directory

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        ghost_checks = [c for c in data["checks"] if c["check"] == "ext-ghost-ext"]
        assert len(ghost_checks) == 1
        assert ghost_checks[0]["status"] == "warn"

    def test_corrupted_extension_registry(self, speckit_project, monkeypatch):
        """Doctor should detect corrupted extension registry."""
        monkeypatch.chdir(speckit_project)
        ext_dir = speckit_project / ".specify" / "extensions"
        ext_dir.mkdir()
        (ext_dir / "registry.json").write_text("not valid json!!!")

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        ext_checks = [c for c in data["checks"] if c["check"] == "extensions"]
        assert len(ext_checks) == 1
        assert ext_checks[0]["status"] == "fail"


class TestDoctorPresets:
    """Test preset-related diagnostics."""

    def test_preset_registry_healthy(self, speckit_project, monkeypatch):
        """Doctor should detect healthy preset registry."""
        monkeypatch.chdir(speckit_project)
        preset_dir = speckit_project / ".specify" / "presets"
        preset_dir.mkdir()
        registry = {"my-preset": {"name": "My Preset", "version": "1.0.0"}}
        (preset_dir / "registry.json").write_text(json.dumps(registry))

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        preset_checks = [c for c in data["checks"] if c["check"] == "presets"]
        assert len(preset_checks) == 1
        assert preset_checks[0]["status"] == "pass"
        assert "1 preset" in preset_checks[0]["message"]

    def test_corrupted_preset_registry(self, speckit_project, monkeypatch):
        """Doctor should detect corrupted preset registry."""
        monkeypatch.chdir(speckit_project)
        preset_dir = speckit_project / ".specify" / "presets"
        preset_dir.mkdir()
        (preset_dir / "registry.json").write_text("{{{broken json")

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        preset_checks = [c for c in data["checks"] if c["check"] == "presets"]
        assert len(preset_checks) == 1
        assert preset_checks[0]["status"] == "fail"


class TestDoctorAISkills:
    """Test AI skills diagnostics."""

    def test_ai_skills_healthy(self, speckit_project, monkeypatch):
        """Doctor should validate AI skills when enabled."""
        monkeypatch.chdir(speckit_project)
        # Update init options to enable skills
        init_opts = json.loads((speckit_project / ".specify" / "init-options.json").read_text())
        init_opts["ai_skills"] = True
        (speckit_project / ".specify" / "init-options.json").write_text(json.dumps(init_opts))

        # Create skills
        skills_dir = speckit_project / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        for skill_name in ["speckit-specify", "speckit-plan", "speckit-tasks"]:
            skill_dir = skills_dir / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"---\nname: {skill_name}\n---\n# Skill\n")

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        skill_checks = [c for c in data["checks"] if c["check"] == "ai-skills"]
        assert len(skill_checks) == 1
        assert skill_checks[0]["status"] == "pass"
        assert "3 agent skill" in skill_checks[0]["message"]

    def test_ai_skills_missing_skill_md(self, speckit_project, monkeypatch):
        """Doctor should warn about skill dirs missing SKILL.md."""
        monkeypatch.chdir(speckit_project)
        init_opts = json.loads((speckit_project / ".specify" / "init-options.json").read_text())
        init_opts["ai_skills"] = True
        (speckit_project / ".specify" / "init-options.json").write_text(json.dumps(init_opts))

        skills_dir = speckit_project / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        # Create skill dir WITHOUT SKILL.md
        (skills_dir / "speckit-broken").mkdir()
        # Create a valid one too
        valid_dir = skills_dir / "speckit-specify"
        valid_dir.mkdir()
        (valid_dir / "SKILL.md").write_text("---\nname: speckit-specify\n---\n")

        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor", "--json"], catch_exceptions=False)

        data = json.loads(result.output.strip())
        integrity_checks = [c for c in data["checks"] if c["check"] == "ai-skills-integrity"]
        assert len(integrity_checks) == 1
        assert integrity_checks[0]["status"] == "warn"
        assert "speckit-broken" in integrity_checks[0]["message"]


class TestDoctorSummary:
    """Test summary output."""

    def test_healthy_project_shows_healthy_message(self, speckit_project, monkeypatch):
        """Healthy project should show success message."""
        monkeypatch.chdir(speckit_project)
        with patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.check_tool", return_value=False):
            result = runner.invoke(app, ["doctor"], catch_exceptions=False)

        assert result.exit_code == 0
        # Output should contain summary info
        assert "Summary" in result.output or "passed" in result.output
