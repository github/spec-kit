"""
Unit tests for AI agent skills installation.

Tests cover:
- Skills directory resolution for different agents (_get_skills_dir)
- YAML frontmatter parsing and SKILL.md generation (install_ai_skills)
- Cleanup of duplicate command files when --ai-skills is used
- Missing templates directory handling
- Malformed template error handling
- CLI validation: --ai-skills requires --ai
"""

import re
import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from unittest.mock import patch

import specify_cli

from specify_cli import (
    _get_skills_dir,
    install_ai_skills,
    AGENT_SKILLS_DIR_OVERRIDES,
    DEFAULT_SKILLS_DIR,
    SKILL_DESCRIPTIONS,
    AGENT_CONFIG,
    app,
)


# ===== Fixtures =====

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock project directory."""
    proj_dir = temp_dir / "test-project"
    proj_dir.mkdir()
    return proj_dir


@pytest.fixture
def templates_dir(project_dir):
    """Create mock command templates in the project's agent commands directory.

    This simulates what download_and_extract_template() does: it places
    command .md files into project_path/<agent_folder>/commands/.
    install_ai_skills() now reads from here instead of from the repo
    source tree.
    """
    tpl_root = project_dir / ".claude" / "commands"
    tpl_root.mkdir(parents=True, exist_ok=True)

    # Template with valid YAML frontmatter
    (tpl_root / "specify.md").write_text(
        "---\n"
        "description: Create or update the feature specification.\n"
        "handoffs:\n"
        "  - label: Build Plan\n"
        "    agent: speckit.plan\n"
        "scripts:\n"
        "  sh: scripts/bash/create-new-feature.sh\n"
        "---\n"
        "\n"
        "# Specify Command\n"
        "\n"
        "Run this to create a spec.\n",
        encoding="utf-8",
    )

    # Template with minimal frontmatter
    (tpl_root / "plan.md").write_text(
        "---\n"
        "description: Generate implementation plan.\n"
        "---\n"
        "\n"
        "# Plan Command\n"
        "\n"
        "Plan body content.\n",
        encoding="utf-8",
    )

    # Template with no frontmatter
    (tpl_root / "tasks.md").write_text(
        "# Tasks Command\n"
        "\n"
        "Body without frontmatter.\n",
        encoding="utf-8",
    )

    # Template with empty YAML frontmatter (yaml.safe_load returns None)
    (tpl_root / "empty_fm.md").write_text(
        "---\n"
        "---\n"
        "\n"
        "# Empty Frontmatter Command\n"
        "\n"
        "Body with empty frontmatter.\n",
        encoding="utf-8",
    )

    return tpl_root


@pytest.fixture
def commands_dir_claude(project_dir):
    """Create a populated .claude/commands directory simulating template extraction."""
    cmd_dir = project_dir / ".claude" / "commands"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    for name in ["speckit.specify.md", "speckit.plan.md", "speckit.tasks.md"]:
        (cmd_dir / name).write_text(f"# {name}\nContent here\n")
    return cmd_dir


@pytest.fixture
def commands_dir_gemini(project_dir):
    """Create a populated .gemini/commands directory (TOML format)."""
    cmd_dir = project_dir / ".gemini" / "commands"
    cmd_dir.mkdir(parents=True)
    for name in ["speckit.specify.toml", "speckit.plan.toml", "speckit.tasks.toml"]:
        (cmd_dir / name).write_text(f'[command]\nname = "{name}"\n')
    return cmd_dir


# ===== _get_skills_dir Tests =====

class TestGetSkillsDir:
    """Test the _get_skills_dir() helper function."""

    def test_claude_skills_dir(self, project_dir):
        """Claude should use .claude/skills/."""
        result = _get_skills_dir(project_dir, "claude")
        assert result == project_dir / ".claude" / "skills"

    def test_gemini_skills_dir(self, project_dir):
        """Gemini should use .gemini/skills/."""
        result = _get_skills_dir(project_dir, "gemini")
        assert result == project_dir / ".gemini" / "skills"

    def test_copilot_skills_dir(self, project_dir):
        """Copilot should use .github/skills/."""
        result = _get_skills_dir(project_dir, "copilot")
        assert result == project_dir / ".github" / "skills"

    def test_codex_uses_override(self, project_dir):
        """Codex should use the AGENT_SKILLS_DIR_OVERRIDES value."""
        result = _get_skills_dir(project_dir, "codex")
        assert result == project_dir / ".agents" / "skills"

    def test_cursor_agent_skills_dir(self, project_dir):
        """Cursor should use .cursor/skills/."""
        result = _get_skills_dir(project_dir, "cursor-agent")
        assert result == project_dir / ".cursor" / "skills"

    def test_unknown_agent_uses_default(self, project_dir):
        """Unknown agents should fall back to DEFAULT_SKILLS_DIR."""
        result = _get_skills_dir(project_dir, "nonexistent-agent")
        assert result == project_dir / DEFAULT_SKILLS_DIR

    def test_all_configured_agents_resolve(self, project_dir):
        """Every agent in AGENT_CONFIG should resolve to a valid path."""
        for agent_key in AGENT_CONFIG:
            result = _get_skills_dir(project_dir, agent_key)
            assert result is not None
            assert str(result).startswith(str(project_dir))
            # Should always end with "skills"
            assert result.name == "skills"

    def test_override_takes_precedence_over_config(self, project_dir):
        """AGENT_SKILLS_DIR_OVERRIDES should take precedence over AGENT_CONFIG."""
        for agent_key in AGENT_SKILLS_DIR_OVERRIDES:
            result = _get_skills_dir(project_dir, agent_key)
            expected = project_dir / AGENT_SKILLS_DIR_OVERRIDES[agent_key]
            assert result == expected


# ===== install_ai_skills Tests =====

class TestInstallAiSkills:
    """Test SKILL.md generation and installation logic."""

    def test_skills_installed_with_correct_structure(self, project_dir, templates_dir):
        """Verify SKILL.md files have correct agentskills.io structure."""
        result = install_ai_skills(project_dir, "claude")

        assert result is True

        skills_dir = project_dir / ".claude" / "skills"
        assert skills_dir.exists()

        # Check that skill directories were created
        skill_dirs = sorted([d.name for d in skills_dir.iterdir() if d.is_dir()])
        assert "speckit-plan" in skill_dirs
        assert "speckit-specify" in skill_dirs
        assert "speckit-tasks" in skill_dirs
        assert "speckit-empty_fm" in skill_dirs

        # Verify SKILL.md content for speckit-specify
        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()

        # Check agentskills.io frontmatter
        assert content.startswith("---\n")
        assert "name: speckit-specify" in content
        assert "description:" in content
        assert "compatibility:" in content
        assert "metadata:" in content
        assert "author: github-spec-kit" in content
        assert "source: templates/commands/specify.md" in content

        # Check body content is included
        assert "# Speckit Specify Skill" in content
        assert "Run this to create a spec." in content

    def test_generated_skill_has_parseable_yaml(self, project_dir, templates_dir):
        """Generated SKILL.md should contain valid, parseable YAML frontmatter."""
        install_ai_skills(project_dir, "claude")

        skill_file = project_dir / ".claude" / "skills" / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()

        # Extract and parse frontmatter
        assert content.startswith("---\n")
        parts = content.split("---", 2)
        assert len(parts) >= 3
        parsed = yaml.safe_load(parts[1])
        assert isinstance(parsed, dict)
        assert "name" in parsed
        assert parsed["name"] == "speckit-specify"
        assert "description" in parsed

    def test_empty_yaml_frontmatter(self, project_dir, templates_dir):
        """Templates with empty YAML frontmatter (---\\n---) should not crash."""
        result = install_ai_skills(project_dir, "claude")

        assert result is True

        skill_file = project_dir / ".claude" / "skills" / "speckit-empty_fm" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "name: speckit-empty_fm" in content
        assert "Body with empty frontmatter." in content

    def test_enhanced_descriptions_used_when_available(self, project_dir, templates_dir):
        """SKILL_DESCRIPTIONS take precedence over template frontmatter descriptions."""
        install_ai_skills(project_dir, "claude")

        skill_file = project_dir / ".claude" / "skills" / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()

        # Parse the generated YAML to compare the description value
        # (yaml.safe_dump may wrap long strings across multiple lines)
        parts = content.split("---", 2)
        parsed = yaml.safe_load(parts[1])

        if "specify" in SKILL_DESCRIPTIONS:
            assert parsed["description"] == SKILL_DESCRIPTIONS["specify"]

    def test_template_without_frontmatter(self, project_dir, templates_dir):
        """Templates without YAML frontmatter should still produce valid skills."""
        install_ai_skills(project_dir, "claude")

        skill_file = project_dir / ".claude" / "skills" / "speckit-tasks" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()

        # Should still have valid SKILL.md structure
        assert "name: speckit-tasks" in content
        assert "Body without frontmatter." in content

    def test_missing_templates_directory(self, project_dir):
        """Returns False when no command templates exist anywhere."""
        # No .claude/commands/ exists, and __file__ fallback won't find anything
        fake_init = project_dir / "nonexistent" / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            result = install_ai_skills(project_dir, "claude")

        assert result is False

        # Skills directory should not exist
        skills_dir = project_dir / ".claude" / "skills"
        assert not skills_dir.exists()

    def test_empty_templates_directory(self, project_dir):
        """Returns False when commands directory has no .md files."""
        # Create empty .claude/commands/
        empty_cmds = project_dir / ".claude" / "commands"
        empty_cmds.mkdir(parents=True)

        # Block the __file__ fallback so it can't find real templates
        fake_init = project_dir / "nowhere" / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            result = install_ai_skills(project_dir, "claude")

        assert result is False

    def test_malformed_yaml_frontmatter(self, project_dir):
        """Malformed YAML in a template should be handled gracefully, not crash."""
        # Create .claude/commands/ with a broken template
        cmds_dir = project_dir / ".claude" / "commands"
        cmds_dir.mkdir(parents=True)

        (cmds_dir / "broken.md").write_text(
            "---\n"
            "description: [unclosed bracket\n"
            "  invalid: yaml: content: here\n"
            "---\n"
            "\n"
            "# Broken\n",
            encoding="utf-8",
        )

        # Should not raise — errors are caught per-file
        result = install_ai_skills(project_dir, "claude")

        # The broken template should be skipped but not crash the process
        assert result is False

    def test_additive_does_not_overwrite_other_files(self, project_dir, templates_dir):
        """Installing skills should not remove non-speckit files in the skills dir."""
        # Pre-create a custom skill
        custom_dir = project_dir / ".claude" / "skills" / "my-custom-skill"
        custom_dir.mkdir(parents=True)
        custom_file = custom_dir / "SKILL.md"
        custom_file.write_text("# My Custom Skill\n")

        install_ai_skills(project_dir, "claude")

        # Custom skill should still exist
        assert custom_file.exists()
        assert custom_file.read_text() == "# My Custom Skill\n"

    def test_return_value(self, project_dir, templates_dir):
        """install_ai_skills returns True when skills installed, False otherwise."""
        assert install_ai_skills(project_dir, "claude") is True

    def test_return_false_when_no_templates(self, project_dir):
        """install_ai_skills returns False when no templates found."""
        fake_init = project_dir / "missing" / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            assert install_ai_skills(project_dir, "claude") is False

    def test_non_md_commands_dir_falls_back(self, project_dir):
        """When extracted commands are .toml (e.g. gemini), fall back to repo templates."""
        # Simulate gemini template extraction: .gemini/commands/ with .toml files only
        cmds_dir = project_dir / ".gemini" / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "speckit.specify.toml").write_text('[command]\nname = "specify"\n')
        (cmds_dir / "speckit.plan.toml").write_text('[command]\nname = "plan"\n')

        # The __file__ fallback should find the real repo templates/commands/*.md
        result = install_ai_skills(project_dir, "gemini")

        assert result is True
        skills_dir = project_dir / ".gemini" / "skills"
        assert skills_dir.exists()
        # Should have installed skills from the fallback .md templates
        skill_dirs = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 1
        # .toml commands should be untouched
        assert (cmds_dir / "speckit.specify.toml").exists()

    @pytest.mark.parametrize("agent_key", [k for k in AGENT_CONFIG.keys() if k != "generic"])
    def test_skills_install_for_all_agents(self, temp_dir, agent_key):
        """install_ai_skills should produce skills for every configured agent."""
        proj = temp_dir / f"proj-{agent_key}"
        proj.mkdir()

        # Place .md templates in the agent's commands directory
        agent_folder = AGENT_CONFIG[agent_key]["folder"]
        cmds_dir = proj / agent_folder.rstrip("/") / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "specify.md").write_text(
            "---\ndescription: Test command\n---\n\n# Test\n\nBody.\n"
        )

        result = install_ai_skills(proj, agent_key)

        assert result is True
        skills_dir = _get_skills_dir(proj, agent_key)
        assert skills_dir.exists()
        skill_dirs = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        assert "speckit-specify" in skill_dirs
        assert (skills_dir / "speckit-specify" / "SKILL.md").exists()



class TestCommandCoexistence:
    """Verify install_ai_skills never touches command files.

    Cleanup of freshly-extracted commands for NEW projects is handled
    in init(), not in install_ai_skills().  These tests confirm that
    install_ai_skills leaves existing commands intact.
    """

    def test_existing_commands_preserved_claude(self, project_dir, templates_dir, commands_dir_claude):
        """install_ai_skills must NOT remove pre-existing .claude/commands files."""
        # Verify commands exist before
        assert len(list(commands_dir_claude.glob("speckit.*"))) == 3

        install_ai_skills(project_dir, "claude")

        # Commands must still be there — install_ai_skills never touches them
        remaining = list(commands_dir_claude.glob("speckit.*"))
        assert len(remaining) == 3

    def test_existing_commands_preserved_gemini(self, project_dir, templates_dir, commands_dir_gemini):
        """install_ai_skills must NOT remove pre-existing .gemini/commands files."""
        assert len(list(commands_dir_gemini.glob("speckit.*"))) == 3

        install_ai_skills(project_dir, "gemini")

        remaining = list(commands_dir_gemini.glob("speckit.*"))
        assert len(remaining) == 3

    def test_commands_dir_not_removed(self, project_dir, templates_dir, commands_dir_claude):
        """install_ai_skills must not remove the commands directory."""
        install_ai_skills(project_dir, "claude")

        assert commands_dir_claude.exists()

    def test_no_commands_dir_no_error(self, project_dir, templates_dir):
        """No error when installing skills — commands dir has templates and is preserved."""
        result = install_ai_skills(project_dir, "claude")

        # Should succeed since templates are in .claude/commands/ via fixture
        assert result is True


# ===== New-Project Command Skip Tests =====

class TestNewProjectCommandSkip:
    """Test that init() removes extracted commands for new projects only.

    These tests run init() end-to-end via CliRunner with
    download_and_extract_template patched to create local fixtures.
    """

    def _fake_extract(self, agent, project_path, **_kwargs):
        """Simulate template extraction: create agent commands dir."""
        agent_cfg = AGENT_CONFIG.get(agent, {})
        agent_folder = agent_cfg.get("folder", "")
        if agent_folder:
            cmds_dir = project_path / agent_folder.rstrip("/") / "commands"
            cmds_dir.mkdir(parents=True, exist_ok=True)
            (cmds_dir / "speckit.specify.md").write_text("# spec")

    def test_new_project_commands_removed_after_skills_succeed(self, tmp_path):
        """For new projects, commands should be removed when skills succeed."""
        from typer.testing import CliRunner

        runner = CliRunner()
        target = tmp_path / "new-proj"

        def fake_download(project_path, *args, **kwargs):
            self._fake_extract("claude", project_path)

        with patch("specify_cli.download_and_extract_template", side_effect=fake_download), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.install_ai_skills", return_value=True) as mock_skills, \
             patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.shutil.which", return_value="/usr/bin/git"):
            result = runner.invoke(app, ["init", str(target), "--ai", "claude", "--ai-skills", "--script", "sh", "--no-git"])

        # Skills should have been called
        mock_skills.assert_called_once()

        # Commands dir should have been removed after skills succeeded
        cmds_dir = target / ".claude" / "commands"
        assert not cmds_dir.exists()

    def test_commands_preserved_when_skills_fail(self, tmp_path):
        """If skills fail, commands should NOT be removed (safety net)."""
        from typer.testing import CliRunner

        runner = CliRunner()
        target = tmp_path / "fail-proj"

        def fake_download(project_path, *args, **kwargs):
            self._fake_extract("claude", project_path)

        with patch("specify_cli.download_and_extract_template", side_effect=fake_download), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.install_ai_skills", return_value=False), \
             patch("specify_cli.is_git_repo", return_value=False), \
             patch("specify_cli.shutil.which", return_value="/usr/bin/git"):
            result = runner.invoke(app, ["init", str(target), "--ai", "claude", "--ai-skills", "--script", "sh", "--no-git"])

        # Commands should still exist since skills failed
        cmds_dir = target / ".claude" / "commands"
        assert cmds_dir.exists()
        assert (cmds_dir / "speckit.specify.md").exists()

    def test_here_mode_commands_preserved(self, tmp_path, monkeypatch):
        """For --here on existing repos, commands must NOT be removed."""
        from typer.testing import CliRunner

        runner = CliRunner()
        # Create a mock existing project with commands already present
        target = tmp_path / "existing"
        target.mkdir()
        agent_folder = AGENT_CONFIG["claude"]["folder"]
        cmds_dir = target / agent_folder.rstrip("/") / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "speckit.specify.md").write_text("# spec")

        # --here uses CWD, so chdir into the target
        monkeypatch.chdir(target)

        def fake_download(project_path, *args, **kwargs):
            pass  # commands already exist, no need to re-create

        with patch("specify_cli.download_and_extract_template", side_effect=fake_download), \
             patch("specify_cli.ensure_executable_scripts"), \
             patch("specify_cli.ensure_constitution_from_template"), \
             patch("specify_cli.install_ai_skills", return_value=True), \
             patch("specify_cli.is_git_repo", return_value=True), \
             patch("specify_cli.shutil.which", return_value="/usr/bin/git"):
            result = runner.invoke(app, ["init", "--here", "--ai", "claude", "--ai-skills", "--script", "sh", "--no-git"])

        # Commands must remain for --here
        assert cmds_dir.exists()
        assert (cmds_dir / "speckit.specify.md").exists()


# ===== Skip-If-Exists Tests =====

class TestSkipIfExists:
    """Test that install_ai_skills does not overwrite existing SKILL.md files."""

    def test_existing_skill_not_overwritten(self, project_dir, templates_dir):
        """Pre-existing SKILL.md should not be replaced on re-run."""
        # Pre-create a custom SKILL.md for speckit-specify
        skill_dir = project_dir / ".claude" / "skills" / "speckit-specify"
        skill_dir.mkdir(parents=True)
        custom_content = "# My Custom Specify Skill\nUser-modified content\n"
        (skill_dir / "SKILL.md").write_text(custom_content)

        result = install_ai_skills(project_dir, "claude")

        # The custom SKILL.md should be untouched
        assert (skill_dir / "SKILL.md").read_text() == custom_content

        # But other skills should still be installed
        assert result is True
        assert (project_dir / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project_dir / ".claude" / "skills" / "speckit-tasks" / "SKILL.md").exists()

    def test_fresh_install_writes_all_skills(self, project_dir, templates_dir):
        """On first install (no pre-existing skills), all should be written."""
        result = install_ai_skills(project_dir, "claude")

        assert result is True
        skills_dir = project_dir / ".claude" / "skills"
        skill_dirs = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        # All 4 templates should produce skills (specify, plan, tasks, empty_fm)
        assert len(skill_dirs) == 4


# ===== SKILL_DESCRIPTIONS Coverage Tests =====

class TestSkillDescriptions:
    """Test SKILL_DESCRIPTIONS constants."""

    def test_all_known_commands_have_descriptions(self):
        """All standard spec-kit commands should have enhanced descriptions."""
        expected_commands = [
            "specify", "plan", "tasks", "implement", "analyze",
            "clarify", "constitution", "checklist", "taskstoissues",
        ]
        for cmd in expected_commands:
            assert cmd in SKILL_DESCRIPTIONS, f"Missing description for '{cmd}'"
            assert len(SKILL_DESCRIPTIONS[cmd]) > 20, f"Description for '{cmd}' is too short"


# ===== CLI Validation Tests =====

class TestCliValidation:
    """Test --ai-skills CLI flag validation."""

    def test_ai_skills_without_ai_fails(self):
        """--ai-skills without --ai should fail with exit code 1."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["init", "test-proj", "--ai-skills"])

        assert result.exit_code == 1
        assert "--ai-skills requires --ai" in result.output

    def test_ai_skills_without_ai_shows_usage(self):
        """Error message should include usage hint."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["init", "test-proj", "--ai-skills"])

        assert "Usage:" in result.output
        assert "--ai" in result.output

    def test_ai_skills_flag_appears_in_help(self):
        """--ai-skills should appear in init --help output."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["init", "--help"])

        plain = re.sub(r'\x1b\[[0-9;]*m', '', result.output)
        assert "--ai-skills" in plain
        assert "agent skills" in plain.lower()


class TestParameterOrderingIssue:
    """Test fix for GitHub issue #1641: parameter ordering issues."""

    def test_ai_flag_consuming_here_flag(self):
        """--ai without value should not consume --here flag (issue #1641)."""
        from typer.testing import CliRunner

        runner = CliRunner()
        # This used to fail with "Must specify project name" because --here was consumed by --ai
        result = runner.invoke(app, ["init", "--ai-skills", "--ai", "--here"])

        assert result.exit_code == 1
        assert "Invalid value for --ai" in result.output
        assert "--here" in result.output  # Should mention the invalid value

    def test_ai_flag_consuming_ai_skills_flag(self):
        """--ai without value should not consume --ai-skills flag."""
        from typer.testing import CliRunner

        runner = CliRunner()
        # This should fail with helpful error about missing --ai value
        result = runner.invoke(app, ["init", "--here", "--ai", "--ai-skills"])

        assert result.exit_code == 1
        assert "Invalid value for --ai" in result.output
        assert "--ai-skills" in result.output  # Should mention the invalid value

    def test_error_message_provides_hint(self):
        """Error message should provide helpful hint about missing value."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["init", "--ai", "--here"])

        assert result.exit_code == 1
        assert "Hint:" in result.output or "hint" in result.output.lower()
        assert "forget to provide a value" in result.output.lower()

    def test_error_message_lists_available_agents(self):
        """Error message should list available agents."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["init", "--ai", "--here"])

        assert result.exit_code == 1
        # Should mention some known agents
        output_lower = result.output.lower()
        assert any(agent in output_lower for agent in ["claude", "copilot", "gemini"])

    def test_ai_commands_dir_consuming_flag(self):
        """--ai-commands-dir without value should not consume next flag."""
        from typer.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(app, ["init", "myproject", "--ai", "generic", "--ai-commands-dir", "--here"])

        assert result.exit_code == 1
        assert "Invalid value for --ai-commands-dir" in result.output
        assert "--here" in result.output
