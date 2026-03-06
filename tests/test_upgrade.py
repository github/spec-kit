"""Tests for minispec upgrade command."""

import json
from pathlib import Path

import pytest
from click.exceptions import Exit

from minispec_cli import (
    _apply_upgrade,
    _classify_upgrade_file,
    _detect_project_config,
    _diff_files,
)


class TestDetectProjectConfig:
    def test_detects_claude_sh(self, tmp_path):
        (tmp_path / ".claude" / "commands").mkdir(parents=True)
        (tmp_path / ".claude" / "commands" / "minispec.design.md").write_text("cmd")
        (tmp_path / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        agent, script = _detect_project_config(tmp_path)
        assert agent == "claude"
        assert script == "sh"

    def test_detects_copilot_ps(self, tmp_path):
        (tmp_path / ".github" / "agents").mkdir(parents=True)
        (tmp_path / ".github" / "agents" / "minispec.design.agent.md").write_text("cmd")
        (tmp_path / ".minispec" / "scripts" / "powershell").mkdir(parents=True)
        agent, script = _detect_project_config(tmp_path)
        assert agent == "copilot"
        assert script == "ps"

    def test_detects_cursor(self, tmp_path):
        (tmp_path / ".cursor" / "commands").mkdir(parents=True)
        (tmp_path / ".cursor" / "commands" / "minispec.design.md").write_text("cmd")
        (tmp_path / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        agent, script = _detect_project_config(tmp_path)
        assert agent == "cursor-agent"
        assert script == "sh"

    def test_no_agent_found(self, tmp_path):
        (tmp_path / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        with pytest.raises(Exit):
            _detect_project_config(tmp_path)

    def test_no_script_found(self, tmp_path):
        (tmp_path / ".claude" / "commands").mkdir(parents=True)
        (tmp_path / ".claude" / "commands" / "minispec.design.md").write_text("cmd")
        (tmp_path / ".minispec").mkdir(parents=True)
        with pytest.raises(Exit):
            _detect_project_config(tmp_path)

    def test_no_minispec_dir(self, tmp_path):
        with pytest.raises(Exit):
            _detect_project_config(tmp_path)


class TestClassifyUpgradeFile:
    def test_scripts_are_overwrite(self):
        assert _classify_upgrade_file(".minispec/scripts/bash/common.sh") == "overwrite"
        assert _classify_upgrade_file(".minispec/scripts/powershell/setup-plan.ps1") == "overwrite"

    def test_templates_are_overwrite(self):
        assert _classify_upgrade_file(".minispec/templates/design-template.md") == "overwrite"
        assert _classify_upgrade_file(".minispec/templates/knowledge/module-template.md") == "overwrite"

    def test_hooks_are_overwrite(self):
        assert _classify_upgrade_file(".minispec/hooks/scripts/claude-protect-main.sh") == "overwrite"
        assert _classify_upgrade_file(".minispec/hooks/hooks.yaml") == "overwrite"
        assert _classify_upgrade_file(".minispec/hooks/adapters/claude-code.json") == "overwrite"

    def test_settings_json_are_merge(self):
        assert _classify_upgrade_file(".claude/settings.json") == "merge"
        assert _classify_upgrade_file(".vscode/settings.json") == "merge"

    def test_agent_commands_are_prompt(self):
        assert _classify_upgrade_file(".claude/commands/minispec.design.md") == "prompt"
        assert _classify_upgrade_file(".cursor/commands/minispec.tasks.md") == "prompt"
        assert _classify_upgrade_file(".github/agents/minispec.next.agent.md") == "prompt"

    def test_constitution_is_skip(self):
        assert _classify_upgrade_file(".minispec/memory/constitution.md") == "skip"

    def test_unknown_files_are_overwrite(self):
        assert _classify_upgrade_file("GEMINI.md") == "overwrite"


class TestDiffFiles:
    def test_identical_files_returns_none(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("hello\nworld\n")
        b.write_text("hello\nworld\n")
        assert _diff_files(a, b) is None

    def test_different_files_returns_diff(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("line1\nline2\n")
        b.write_text("line1\nchanged\n")
        result = _diff_files(a, b)
        assert result is not None
        assert "-line2" in result
        assert "+changed" in result

    def test_new_file_returns_diff(self, tmp_path):
        a = tmp_path / "a.md"  # doesn't exist
        b = tmp_path / "b.md"
        b.write_text("new content\n")
        result = _diff_files(a, b)
        assert result is not None
        assert "+new content" in result


class TestApplyUpgrade:
    def _setup_project(self, tmp_path):
        """Create a minimal existing MiniSpec project."""
        project = tmp_path / "project"
        project.mkdir()
        (project / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        (project / ".minispec" / "templates").mkdir(parents=True)
        (project / ".minispec" / "memory").mkdir(parents=True)
        (project / ".minispec" / "memory" / "constitution.md").write_text("my principles")
        (project / ".claude" / "commands").mkdir(parents=True)
        (project / ".claude" / "commands" / "minispec.design.md").write_text("old design prompt")
        (project / ".claude" / "settings.json").write_text(json.dumps({"user_key": True}))
        return project

    def _setup_template(self, tmp_path):
        """Create a minimal extracted template."""
        template = tmp_path / "template"
        template.mkdir()
        (template / ".minispec" / "scripts" / "bash").mkdir(parents=True)
        (template / ".minispec" / "scripts" / "bash" / "common.sh").write_text("#!/bin/bash\n# new")
        (template / ".minispec" / "templates").mkdir(parents=True)
        (template / ".minispec" / "templates" / "design-template.md").write_text("# new template")
        (template / ".minispec" / "memory").mkdir(parents=True)
        (template / ".minispec" / "memory" / "constitution.md").write_text("new constitution")
        (template / ".claude" / "commands").mkdir(parents=True)
        (template / ".claude" / "commands" / "minispec.design.md").write_text("new design prompt")
        (template / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"new": True}}))
        return template

    def test_overwrites_scripts(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        results = _apply_upgrade(project, template, force=True)
        assert (project / ".minispec" / "scripts" / "bash" / "common.sh").read_text() == "#!/bin/bash\n# new"
        assert any(r[1] == "created" for r in results if "common.sh" in r[0])

    def test_preserves_constitution(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        _apply_upgrade(project, template, force=True)
        assert (project / ".minispec" / "memory" / "constitution.md").read_text() == "my principles"

    def test_merges_settings_json(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        _apply_upgrade(project, template, force=True)
        with open(project / ".claude" / "settings.json") as f:
            data = json.load(f)
        assert data["user_key"] is True
        assert data["hooks"]["new"] is True

    def test_force_overwrites_commands(self, tmp_path):
        project = self._setup_project(tmp_path)
        template = self._setup_template(tmp_path)
        results = _apply_upgrade(project, template, force=True)
        assert (project / ".claude" / "commands" / "minispec.design.md").read_text() == "new design prompt"
        assert any(r[1] == "overwritten (auto)" for r in results if "minispec.design.md" in r[0])
