"""
Unit tests for extension skill auto-registration.

Tests cover:
- SKILL.md generation when --ai-skills was used during init
- No skills created when ai_skills not active
- SKILL.md content correctness
- Existing user-modified skills not overwritten
- Skill cleanup on extension removal
- Registry metadata includes registered_skills
"""

import json
import pytest
import tempfile
import shutil
import yaml
from pathlib import Path

from specify_cli.extensions import (
    ExtensionManifest,
    ExtensionManager,
    ExtensionError,
)


# ===== Helpers =====

def _create_init_options(project_root: Path, ai: str = "claude", ai_skills: bool = True):
    """Write a .specify/init-options.json file."""
    opts_dir = project_root / ".specify"
    opts_dir.mkdir(parents=True, exist_ok=True)
    opts_file = opts_dir / "init-options.json"
    opts_file.write_text(json.dumps({
        "ai": ai,
        "ai_skills": ai_skills,
        "script": "sh",
    }))


def _create_skills_dir(project_root: Path, ai: str = "claude") -> Path:
    """Create and return the expected skills directory for the given agent."""
    # Match the logic in _get_skills_dir() from specify_cli
    from specify_cli import AGENT_CONFIG, AGENT_SKILLS_DIR_OVERRIDES, DEFAULT_SKILLS_DIR

    if ai in AGENT_SKILLS_DIR_OVERRIDES:
        skills_dir = project_root / AGENT_SKILLS_DIR_OVERRIDES[ai]
    else:
        agent_config = AGENT_CONFIG.get(ai, {})
        agent_folder = agent_config.get("folder", "")
        if agent_folder:
            skills_dir = project_root / agent_folder.rstrip("/") / "skills"
        else:
            skills_dir = project_root / DEFAULT_SKILLS_DIR

    skills_dir.mkdir(parents=True, exist_ok=True)
    return skills_dir


def _create_extension_dir(temp_dir: Path, ext_id: str = "test-ext") -> Path:
    """Create a complete extension directory with manifest and command files."""
    ext_dir = temp_dir / ext_id
    ext_dir.mkdir()

    manifest_data = {
        "schema_version": "1.0",
        "extension": {
            "id": ext_id,
            "name": "Test Extension",
            "version": "1.0.0",
            "description": "A test extension for skill registration",
        },
        "requires": {
            "speckit_version": ">=0.1.0",
        },
        "provides": {
            "commands": [
                {
                    "name": f"speckit.{ext_id}.hello",
                    "file": "commands/hello.md",
                    "description": "Test hello command",
                },
                {
                    "name": f"speckit.{ext_id}.world",
                    "file": "commands/world.md",
                    "description": "Test world command",
                },
            ]
        },
    }

    with open(ext_dir / "extension.yml", "w") as f:
        yaml.dump(manifest_data, f)

    commands_dir = ext_dir / "commands"
    commands_dir.mkdir()

    (commands_dir / "hello.md").write_text(
        "---\n"
        "description: \"Test hello command\"\n"
        "---\n"
        "\n"
        "# Hello Command\n"
        "\n"
        "Run this to say hello.\n"
        "$ARGUMENTS\n"
    )

    (commands_dir / "world.md").write_text(
        "---\n"
        "description: \"Test world command\"\n"
        "---\n"
        "\n"
        "# World Command\n"
        "\n"
        "Run this to greet the world.\n"
    )

    return ext_dir


# ===== Fixtures =====

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project directory."""
    proj_dir = temp_dir / "project"
    proj_dir.mkdir()

    # Create .specify directory
    specify_dir = proj_dir / ".specify"
    specify_dir.mkdir()

    return proj_dir


@pytest.fixture
def extension_dir(temp_dir):
    """Create a complete extension directory."""
    return _create_extension_dir(temp_dir)


@pytest.fixture
def skills_project(project_dir):
    """Create a project with --ai-skills enabled and skills directory."""
    _create_init_options(project_dir, ai="claude", ai_skills=True)
    skills_dir = _create_skills_dir(project_dir, ai="claude")
    return project_dir, skills_dir


@pytest.fixture
def no_skills_project(project_dir):
    """Create a project without --ai-skills."""
    _create_init_options(project_dir, ai="claude", ai_skills=False)
    return project_dir


# ===== ExtensionManager._get_skills_dir Tests =====

class TestExtensionManagerGetSkillsDir:
    """Test _get_skills_dir() on ExtensionManager."""

    def test_returns_skills_dir_when_active(self, skills_project):
        """Should return skills dir when ai_skills is true and dir exists."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        result = manager._get_skills_dir()
        assert result == skills_dir

    def test_returns_none_when_no_ai_skills(self, no_skills_project):
        """Should return None when ai_skills is false."""
        manager = ExtensionManager(no_skills_project)
        result = manager._get_skills_dir()
        assert result is None

    def test_returns_none_when_no_init_options(self, project_dir):
        """Should return None when init-options.json is missing."""
        manager = ExtensionManager(project_dir)
        result = manager._get_skills_dir()
        assert result is None

    def test_returns_none_when_skills_dir_missing(self, project_dir):
        """Should return None when skills dir doesn't exist on disk."""
        _create_init_options(project_dir, ai="claude", ai_skills=True)
        # Don't create the skills directory
        manager = ExtensionManager(project_dir)
        result = manager._get_skills_dir()
        assert result is None


# ===== Extension Skill Registration Tests =====

class TestExtensionSkillRegistration:
    """Test _register_extension_skills() on ExtensionManager."""

    def test_skills_created_when_ai_skills_active(self, skills_project, extension_dir):
        """Skills should be created when ai_skills is enabled."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Check that skill directories were created
        skill_dirs = sorted([d.name for d in skills_dir.iterdir() if d.is_dir()])
        assert "speckit-test-ext-hello" in skill_dirs
        assert "speckit-test-ext-world" in skill_dirs

    def test_skill_md_content_correct(self, skills_project, extension_dir):
        """SKILL.md should have correct agentskills.io structure."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()

        # Check structure
        assert content.startswith("---\n")
        assert "name: speckit-test-ext-hello" in content
        assert "description:" in content
        assert "Test hello command" in content
        assert "source: extension:test-ext" in content
        assert "author: github-spec-kit" in content
        assert "compatibility:" in content
        assert "Run this to say hello." in content

    def test_skill_md_has_parseable_yaml(self, skills_project, extension_dir):
        """Generated SKILL.md should contain valid, parseable YAML frontmatter."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        content = skill_file.read_text()

        assert content.startswith("---\n")
        parts = content.split("---", 2)
        assert len(parts) >= 3
        parsed = yaml.safe_load(parts[1])
        assert isinstance(parsed, dict)
        assert parsed["name"] == "speckit-test-ext-hello"
        assert "description" in parsed

    def test_no_skills_when_ai_skills_disabled(self, no_skills_project, extension_dir):
        """No skills should be created when ai_skills is false."""
        manager = ExtensionManager(no_skills_project)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Verify registry
        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_skills"] == []

    def test_no_skills_when_init_options_missing(self, project_dir, extension_dir):
        """No skills should be created when init-options.json is absent."""
        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_skills"] == []

    def test_existing_skill_not_overwritten(self, skills_project, extension_dir):
        """Pre-existing SKILL.md should not be overwritten."""
        project_dir, skills_dir = skills_project

        # Pre-create a custom skill
        custom_dir = skills_dir / "speckit-test-ext-hello"
        custom_dir.mkdir(parents=True)
        custom_content = "# My Custom Hello Skill\nUser-modified content\n"
        (custom_dir / "SKILL.md").write_text(custom_content)

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Custom skill should be untouched
        assert (custom_dir / "SKILL.md").read_text() == custom_content

        # But the other skill should still be created
        metadata = manager.registry.get(manifest.id)
        assert "speckit-test-ext-world" in metadata["registered_skills"]
        # The pre-existing one should NOT be in registered_skills (it was skipped)
        assert "speckit-test-ext-hello" not in metadata["registered_skills"]

    def test_registered_skills_in_registry(self, skills_project, extension_dir):
        """Registry should contain registered_skills list."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        assert "registered_skills" in metadata
        assert len(metadata["registered_skills"]) == 2
        assert "speckit-test-ext-hello" in metadata["registered_skills"]
        assert "speckit-test-ext-world" in metadata["registered_skills"]

    def test_kimi_uses_dot_notation(self, project_dir, temp_dir):
        """Kimi agent should use dot notation for skill names."""
        _create_init_options(project_dir, ai="kimi", ai_skills=True)
        _create_skills_dir(project_dir, ai="kimi")
        ext_dir = _create_extension_dir(temp_dir, ext_id="test-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        # Kimi should use dots, not hyphens
        assert "speckit.test-ext.hello" in metadata["registered_skills"]
        assert "speckit.test-ext.world" in metadata["registered_skills"]

    def test_missing_command_file_skipped(self, skills_project, temp_dir):
        """Commands with missing source files should be skipped gracefully."""
        project_dir, skills_dir = skills_project

        ext_dir = temp_dir / "missing-cmd-ext"
        ext_dir.mkdir()
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "missing-cmd-ext",
                "name": "Missing Cmd Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.missing-cmd-ext.exists",
                        "file": "commands/exists.md",
                        "description": "Exists",
                    },
                    {
                        "name": "speckit.missing-cmd-ext.ghost",
                        "file": "commands/ghost.md",
                        "description": "Does not exist",
                    },
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "exists.md").write_text(
            "---\ndescription: Exists\n---\n\n# Exists\n\nBody.\n"
        )
        # Intentionally do NOT create ghost.md

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        assert "speckit-missing-cmd-ext-exists" in metadata["registered_skills"]
        assert "speckit-missing-cmd-ext-ghost" not in metadata["registered_skills"]


# ===== Extension Skill Unregistration Tests =====

class TestExtensionSkillUnregistration:
    """Test _unregister_extension_skills() on ExtensionManager."""

    def test_skills_removed_on_extension_remove(self, skills_project, extension_dir):
        """Removing an extension should clean up its skill directories."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Verify skills exist
        assert (skills_dir / "speckit-test-ext-hello" / "SKILL.md").exists()
        assert (skills_dir / "speckit-test-ext-world" / "SKILL.md").exists()

        # Remove extension
        result = manager.remove(manifest.id, keep_config=False)
        assert result is True

        # Skills should be gone
        assert not (skills_dir / "speckit-test-ext-hello").exists()
        assert not (skills_dir / "speckit-test-ext-world").exists()

    def test_other_skills_preserved_on_remove(self, skills_project, extension_dir):
        """Non-extension skills should not be affected by extension removal."""
        project_dir, skills_dir = skills_project

        # Pre-create a custom skill
        custom_dir = skills_dir / "my-custom-skill"
        custom_dir.mkdir(parents=True)
        (custom_dir / "SKILL.md").write_text("# My Custom Skill\n")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        manager.remove(manifest.id, keep_config=False)

        # Custom skill should still exist
        assert (custom_dir / "SKILL.md").exists()
        assert (custom_dir / "SKILL.md").read_text() == "# My Custom Skill\n"

    def test_remove_handles_already_deleted_skills(self, skills_project, extension_dir):
        """Gracefully handle case where skill dirs were already deleted."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Manually delete skill dirs before calling remove
        shutil.rmtree(skills_dir / "speckit-test-ext-hello")
        shutil.rmtree(skills_dir / "speckit-test-ext-world")

        # Should not raise
        result = manager.remove(manifest.id, keep_config=False)
        assert result is True

    def test_remove_no_skills_when_not_active(self, no_skills_project, extension_dir):
        """Removal without active skills should not attempt skill cleanup."""
        manager = ExtensionManager(no_skills_project)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Should not raise even though no skills exist
        result = manager.remove(manifest.id, keep_config=False)
        assert result is True


# ===== Command File Without Frontmatter =====

class TestExtensionSkillEdgeCases:
    """Test edge cases in extension skill registration."""

    def test_command_without_frontmatter(self, skills_project, temp_dir):
        """Commands without YAML frontmatter should still produce valid skills."""
        project_dir, skills_dir = skills_project

        ext_dir = temp_dir / "nofm-ext"
        ext_dir.mkdir()
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "nofm-ext",
                "name": "No Frontmatter Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.nofm-ext.plain",
                        "file": "commands/plain.md",
                        "description": "Plain command",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "plain.md").write_text(
            "# Plain Command\n\nBody without frontmatter.\n"
        )

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        skill_file = skills_dir / "speckit-nofm-ext-plain" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "name: speckit-nofm-ext-plain" in content
        # Fallback description when no frontmatter description
        assert "Extension command: speckit.nofm-ext.plain" in content
        assert "Body without frontmatter." in content

    def test_gemini_agent_skills(self, project_dir, temp_dir):
        """Gemini agent should use .gemini/skills/ for skill directory."""
        _create_init_options(project_dir, ai="gemini", ai_skills=True)
        _create_skills_dir(project_dir, ai="gemini")
        ext_dir = _create_extension_dir(temp_dir, ext_id="test-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        skills_dir = project_dir / ".gemini" / "skills"
        assert (skills_dir / "speckit-test-ext-hello" / "SKILL.md").exists()
        assert (skills_dir / "speckit-test-ext-world" / "SKILL.md").exists()

    def test_multiple_extensions_independent_skills(self, skills_project, temp_dir):
        """Installing and removing different extensions should be independent."""
        project_dir, skills_dir = skills_project

        ext_dir_a = _create_extension_dir(temp_dir, ext_id="ext-a")
        ext_dir_b = _create_extension_dir(temp_dir, ext_id="ext-b")

        manager = ExtensionManager(project_dir)
        manifest_a = manager.install_from_directory(
            ext_dir_a, "0.1.0", register_commands=False
        )
        manifest_b = manager.install_from_directory(
            ext_dir_b, "0.1.0", register_commands=False
        )

        # Both should have skills
        assert (skills_dir / "speckit-ext-a-hello" / "SKILL.md").exists()
        assert (skills_dir / "speckit-ext-b-hello" / "SKILL.md").exists()

        # Remove ext-a
        manager.remove("ext-a", keep_config=False)

        # ext-a skills gone, ext-b skills preserved
        assert not (skills_dir / "speckit-ext-a-hello").exists()
        assert (skills_dir / "speckit-ext-b-hello" / "SKILL.md").exists()

    def test_malformed_frontmatter_handled(self, skills_project, temp_dir):
        """Commands with invalid YAML frontmatter should still produce valid skills."""
        project_dir, skills_dir = skills_project

        ext_dir = temp_dir / "badfm-ext"
        ext_dir.mkdir()
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "badfm-ext",
                "name": "Bad Frontmatter Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.badfm-ext.broken",
                        "file": "commands/broken.md",
                        "description": "Broken frontmatter",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        # Malformed YAML: invalid key-value syntax
        (ext_dir / "commands" / "broken.md").write_text(
            "---\n"
            "description: [invalid yaml\n"
            "  unclosed: bracket\n"
            "---\n"
            "\n"
            "# Broken Command\n"
            "\n"
            "This body should still be used.\n"
        )

        manager = ExtensionManager(project_dir)
        # Should not raise
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        skill_file = skills_dir / "speckit-badfm-ext-broken" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        # Fallback description since frontmatter was invalid
        assert "Extension command: speckit.badfm-ext.broken" in content
        assert "This body should still be used." in content

    def test_remove_cleans_up_when_init_options_deleted(self, skills_project, extension_dir):
        """Skills should be cleaned up even if init-options.json is deleted after install."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Verify skills exist
        assert (skills_dir / "speckit-test-ext-hello" / "SKILL.md").exists()

        # Delete init-options.json to simulate user change
        init_opts = project_dir / ".specify" / "init-options.json"
        init_opts.unlink()

        # Remove should still clean up via fallback scan
        result = manager.remove(manifest.id, keep_config=False)
        assert result is True
        assert not (skills_dir / "speckit-test-ext-hello").exists()
        assert not (skills_dir / "speckit-test-ext-world").exists()

    def test_remove_cleans_up_when_ai_skills_toggled(self, skills_project, extension_dir):
        """Skills should be cleaned up even if ai_skills is toggled to false after install."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        # Verify skills exist
        assert (skills_dir / "speckit-test-ext-hello" / "SKILL.md").exists()

        # Toggle ai_skills to false
        _create_init_options(project_dir, ai="claude", ai_skills=False)

        # Remove should still clean up via fallback scan
        result = manager.remove(manifest.id, keep_config=False)
        assert result is True
        assert not (skills_dir / "speckit-test-ext-hello").exists()
        assert not (skills_dir / "speckit-test-ext-world").exists()
