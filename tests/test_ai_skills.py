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
def templates_dir(temp_dir):
    """Create a mock templates/commands directory with sample templates."""
    tpl_root = temp_dir / "templates" / "commands"
    tpl_root.mkdir(parents=True)

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
    cmd_dir.mkdir(parents=True)
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
    """Test agent-specific skills directory resolution."""

    def test_claude_skills_dir(self, project_dir):
        """Claude skills go to .claude/skills."""
        result = _get_skills_dir(project_dir, "claude")
        assert result == project_dir / ".claude" / "skills"

    def test_gemini_skills_dir(self, project_dir):
        """Gemini skills go to .gemini/skills."""
        result = _get_skills_dir(project_dir, "gemini")
        assert result == project_dir / ".gemini" / "skills"

    def test_copilot_skills_dir(self, project_dir):
        """Copilot skills go to .github/skills."""
        result = _get_skills_dir(project_dir, "copilot")
        assert result == project_dir / ".github" / "skills"

    def test_codex_uses_override(self, project_dir):
        """Codex should use the AGENT_SKILLS_DIR_OVERRIDES mapping (.agents/skills)."""
        result = _get_skills_dir(project_dir, "codex")
        assert result == project_dir / ".agents" / "skills"
        # Verify it's coming from the override, not AGENT_CONFIG
        assert "codex" in AGENT_SKILLS_DIR_OVERRIDES

    def test_cursor_agent_skills_dir(self, project_dir):
        """Cursor agent skills go to .cursor/skills."""
        result = _get_skills_dir(project_dir, "cursor-agent")
        assert result == project_dir / ".cursor" / "skills"

    def test_unknown_agent_uses_default(self, project_dir):
        """Unknown agents fall back to DEFAULT_SKILLS_DIR (.agents/skills)."""
        result = _get_skills_dir(project_dir, "totally-unknown-agent")
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
        # We need to make Path(__file__).parent.parent.parent resolve to temp root
        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
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
        # We need to make Path(__file__).parent.parent.parent resolve to temp root
        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
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
        """Templates with empty YAML frontmatter (---\n---) should not crash."""
        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            result = install_ai_skills(project_dir, "claude")

        assert result is True

        skill_file = project_dir / ".claude" / "skills" / "speckit-empty_fm" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "name: speckit-empty_fm" in content
        assert "Body with empty frontmatter." in content

    def test_enhanced_descriptions_used_when_available(self, project_dir, templates_dir):
        """SKILL_DESCRIPTIONS take precedence over template frontmatter descriptions."""

        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            install_ai_skills(project_dir, "claude")

        skill_file = project_dir / ".claude" / "skills" / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()

        # Should use the enhanced description from SKILL_DESCRIPTIONS, not the template one
        if "specify" in SKILL_DESCRIPTIONS:
            assert SKILL_DESCRIPTIONS["specify"] in content

    def test_template_without_frontmatter(self, project_dir, templates_dir):
        """Templates without YAML frontmatter should still produce valid skills."""


        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            install_ai_skills(project_dir, "claude")

        skill_file = project_dir / ".claude" / "skills" / "speckit-tasks" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()

        # Should still have valid SKILL.md structure
        assert "name: speckit-tasks" in content
        assert "Body without frontmatter." in content

    def test_missing_templates_directory(self, project_dir):
        """Returns False when templates/commands directory doesn't exist."""


        # Point to a non-existent directory
        fake_init = project_dir / "nonexistent" / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            result = install_ai_skills(project_dir, "claude")

        assert result is False

        # Skills directory should not exist
        skills_dir = project_dir / ".claude" / "skills"
        assert not skills_dir.exists()

    def test_empty_templates_directory(self, project_dir, temp_dir):
        """Returns False when templates/commands has no .md files."""


        # Create empty templates/commands
        empty_tpl = temp_dir / "empty_root" / "templates" / "commands"
        empty_tpl.mkdir(parents=True)
        fake_init = temp_dir / "empty_root" / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            result = install_ai_skills(project_dir, "claude")

        assert result is False

    def test_malformed_yaml_frontmatter(self, project_dir, temp_dir):
        """Malformed YAML in a template should be handled gracefully, not crash."""


        tpl_dir = temp_dir / "bad_root" / "templates" / "commands"
        tpl_dir.mkdir(parents=True)

        # Write a template with invalid YAML
        (tpl_dir / "broken.md").write_text(
            "---\n"
            "description: [unclosed bracket\n"
            "  invalid: yaml: content: here\n"
            "---\n"
            "\n"
            "# Broken\n",
            encoding="utf-8",
        )

        fake_init = temp_dir / "bad_root" / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
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

        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            install_ai_skills(project_dir, "claude")

        # Custom skill should still exist
        assert custom_file.exists()
        assert custom_file.read_text() == "# My Custom Skill\n"

    def test_return_value(self, project_dir, templates_dir):
        """install_ai_skills returns True when skills installed, False otherwise."""


        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            assert install_ai_skills(project_dir, "claude") is True

        # Second call to non-existent dir
        fake_init2 = project_dir / "missing" / "src" / "specify_cli" / "__init__.py"
        fake_init2.parent.mkdir(parents=True, exist_ok=True)
        fake_init2.touch()

        with patch.object(specify_cli, "__file__", str(fake_init2)):
            assert install_ai_skills(project_dir, "claude") is False


# ===== Command Coexistence Tests =====

class TestCommandCoexistence:
    """Verify install_ai_skills never touches command files.

    Cleanup of freshly-extracted commands for NEW projects is handled
    in init(), not in install_ai_skills().  These tests confirm that
    install_ai_skills leaves existing commands intact.
    """

    def test_existing_commands_preserved_claude(self, project_dir, templates_dir, commands_dir_claude):
        """install_ai_skills must NOT remove pre-existing .claude/commands files."""


        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        # Verify commands exist before
        assert len(list(commands_dir_claude.glob("speckit.*"))) == 3

        with patch.object(specify_cli, "__file__", str(fake_init)):
            install_ai_skills(project_dir, "claude")

        # Commands must still be there — install_ai_skills never touches them
        remaining = list(commands_dir_claude.glob("speckit.*"))
        assert len(remaining) == 3

    def test_existing_commands_preserved_gemini(self, project_dir, templates_dir, commands_dir_gemini):
        """install_ai_skills must NOT remove pre-existing .gemini/commands files."""


        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        assert len(list(commands_dir_gemini.glob("speckit.*"))) == 3

        with patch.object(specify_cli, "__file__", str(fake_init)):
            install_ai_skills(project_dir, "gemini")

        remaining = list(commands_dir_gemini.glob("speckit.*"))
        assert len(remaining) == 3

    def test_commands_dir_not_removed(self, project_dir, templates_dir, commands_dir_claude):
        """install_ai_skills must not remove the commands directory."""


        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            install_ai_skills(project_dir, "claude")

        assert commands_dir_claude.exists()

    def test_no_commands_dir_no_error(self, project_dir, templates_dir):
        """No error when agent has no commands directory at all."""


        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        # No .claude/commands directory exists
        with patch.object(specify_cli, "__file__", str(fake_init)):
            result = install_ai_skills(project_dir, "claude")

        # Should still succeed
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
        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        # Pre-create a custom SKILL.md for speckit-specify
        skill_dir = project_dir / ".claude" / "skills" / "speckit-specify"
        skill_dir.mkdir(parents=True)
        custom_content = "# My Custom Specify Skill\nUser-modified content\n"
        (skill_dir / "SKILL.md").write_text(custom_content)

        with patch.object(specify_cli, "__file__", str(fake_init)):
            result = install_ai_skills(project_dir, "claude")

        # The custom SKILL.md should be untouched
        assert (skill_dir / "SKILL.md").read_text() == custom_content

        # But other skills should still be installed
        assert result is True
        assert (project_dir / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project_dir / ".claude" / "skills" / "speckit-tasks" / "SKILL.md").exists()

    def test_fresh_install_writes_all_skills(self, project_dir, templates_dir):
        """On first install (no pre-existing skills), all should be written."""
        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
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

        assert "--ai-skills" in result.output
        assert "agent skills" in result.output.lower()
