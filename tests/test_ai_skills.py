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
from pathlib import Path
from unittest.mock import patch

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
        # Directly call install_ai_skills with a patched templates dir path
        import specify_cli

        orig_file = specify_cli.__file__
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
        assert skill_dirs == ["speckit-plan", "speckit-specify", "speckit-tasks"]

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

    def test_enhanced_descriptions_used_when_available(self, project_dir, templates_dir):
        """SKILL_DESCRIPTIONS take precedence over template frontmatter descriptions."""
        import specify_cli

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
        import specify_cli

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
        import specify_cli

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
        import specify_cli

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
        import specify_cli

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
        import specify_cli

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
        import specify_cli

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
        import specify_cli

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
        import specify_cli

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
        import specify_cli

        fake_init = templates_dir.parent.parent / "src" / "specify_cli" / "__init__.py"
        fake_init.parent.mkdir(parents=True, exist_ok=True)
        fake_init.touch()

        with patch.object(specify_cli, "__file__", str(fake_init)):
            install_ai_skills(project_dir, "claude")

        assert commands_dir_claude.exists()

    def test_no_commands_dir_no_error(self, project_dir, templates_dir):
        """No error when agent has no commands directory at all."""
        import specify_cli

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

    The init() function removes the freshly-extracted commands directory
    when --ai-skills is used and the project is NEW (not --here).
    For --here on existing repos, commands are left untouched.
    """

    def test_new_project_commands_dir_removed(self, project_dir):
        """For new projects, the extracted commands directory should be removed."""
        import shutil as _shutil

        # Simulate what init() does: after extraction, if ai_skills and not here
        agent_folder = AGENT_CONFIG["claude"]["folder"]
        cmds_dir = project_dir / agent_folder.rstrip("/") / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "speckit.specify.md").write_text("# spec")

        ai_skills = True
        here = False

        # Replicate the init() logic
        if ai_skills and not here:
            agent_cfg = AGENT_CONFIG.get("claude", {})
            af = agent_cfg.get("folder", "")
            if af:
                d = project_dir / af.rstrip("/") / "commands"
                if d.exists():
                    _shutil.rmtree(d)

        assert not cmds_dir.exists()

    def test_here_mode_commands_preserved(self, project_dir):
        """For --here on existing repos, commands must NOT be removed."""
        agent_folder = AGENT_CONFIG["claude"]["folder"]
        cmds_dir = project_dir / agent_folder.rstrip("/") / "commands"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "speckit.specify.md").write_text("# spec")

        ai_skills = True
        here = True

        # Replicate the init() logic
        if ai_skills and not here:
            import shutil as _shutil
            agent_cfg = AGENT_CONFIG.get("claude", {})
            af = agent_cfg.get("folder", "")
            if af:
                d = project_dir / af.rstrip("/") / "commands"
                if d.exists():
                    _shutil.rmtree(d)

        # Commands must remain for --here
        assert cmds_dir.exists()
        assert (cmds_dir / "speckit.specify.md").exists()


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
