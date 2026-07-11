"""
Unit tests for extension skill auto-registration.

Tests cover:
- SKILL.md generation when skills mode was used during init
- No skills created when ai_skills not active
- SKILL.md content correctness
- Existing user-modified skills not overwritten
- Skill cleanup on extension removal
- Registry metadata includes registered_skills
"""

import json
import os
import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from typing import Any

from specify_cli.extensions import (
    ExtensionManifest,
    ExtensionManager,
)


# ===== Helpers =====

def _create_init_options(
    project_root: Path, ai: str = "claude", ai_skills: Any = True
):
    """Write a .specify/init-options.json file."""
    opts_dir = project_root / ".specify"
    opts_dir.mkdir(parents=True, exist_ok=True)
    opts_file = opts_dir / "init-options.json"
    opts_file.write_text(json.dumps({
        "ai": ai,
        "ai_skills": ai_skills,
        "script": "sh",
    }), encoding="utf-8")


def _create_skills_dir(project_root: Path, ai: str = "claude") -> Path:
    """Create and return the expected skills directory for the given agent."""
    # Match the logic in _get_skills_dir() from specify_cli
    from specify_cli import AGENT_CONFIG

    agent_config = AGENT_CONFIG.get(ai, {})
    agent_folder = agent_config.get("folder", "")
    if agent_folder:
        skills_dir = project_root / agent_folder.rstrip("/") / "skills"
    else:
        skills_dir = project_root / ".agents" / "skills"

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
        yaml.safe_dump(manifest_data, f)

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


def _create_unicode_extension_dir(temp_dir: Path, ext_id: str = "uni-ext") -> Path:
    """Create an extension whose command description contains non-ASCII characters."""
    ext_dir = temp_dir / ext_id
    ext_dir.mkdir()
    description = "Prüfe Konformität der Implementierung"

    manifest_data = {
        "schema_version": "1.0",
        "extension": {
            "id": ext_id,
            "name": "Unicode Extension",
            "version": "1.0.0",
            "description": description,
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "commands": [
                {
                    "name": f"speckit.{ext_id}.hello",
                    "file": "commands/hello.md",
                    "description": description,
                },
            ]
        },
    }

    with open(ext_dir / "extension.yml", "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest_data, f, allow_unicode=True)

    commands_dir = ext_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "hello.md").write_text(
        "---\n"
        f'description: "{description}"\n'
        "---\n"
        "\n"
        "# Hello\n"
        "\n"
        "Body.\n",
        encoding="utf-8",
    )
    return ext_dir


def _can_create_symlink(temp_dir: Path) -> bool:
    """Return True when the current platform/user can create file symlinks."""
    target = temp_dir / "symlink-target.txt"
    link = temp_dir / "symlink-link.txt"
    target.write_text("ok", encoding="utf-8")
    try:
        os.symlink(target, link)
    except OSError:
        return False
    return link.is_symlink()


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
    """Create a project with skills mode enabled and skills directory."""
    _create_init_options(project_dir, ai="claude", ai_skills=True)
    skills_dir = _create_skills_dir(project_dir, ai="claude")
    return project_dir, skills_dir


@pytest.fixture
def no_skills_project(project_dir):
    """Create a project without skills mode."""
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
        """Should return None when ai_skills is false and not create the dir."""
        manager = ExtensionManager(no_skills_project)
        result = manager._get_skills_dir()
        assert result is None
        # Ensure the directory was NOT created on disk
        from specify_cli import _get_skills_dir as resolve_skills_dir
        skills_path = resolve_skills_dir(no_skills_project, "claude")
        assert not skills_path.exists()

    def test_returns_none_when_no_init_options(self, project_dir):
        """Should return None when init-options.json is missing and not create any dir."""
        manager = ExtensionManager(project_dir)
        result = manager._get_skills_dir()
        assert result is None
        # No agent skills directory should have been created
        assert not (project_dir / ".claude" / "skills").exists()
        assert not (project_dir / ".agents" / "skills").exists()

    def test_creates_skills_dir_on_demand(self, project_dir):
        """Should create skills dir when ai_skills is enabled but dir is missing."""
        _create_init_options(project_dir, ai="claude", ai_skills=True)
        # Don't create the skills directory — _get_skills_dir should do it
        manager = ExtensionManager(project_dir)
        result = manager._get_skills_dir()
        assert result is not None
        assert result.is_dir()

    def test_returns_kimi_skills_dir_when_ai_skills_disabled(self, project_dir):
        """Kimi should still use its native skills dir when ai_skills is false."""
        _create_init_options(project_dir, ai="kimi", ai_skills=False)
        skills_dir = _create_skills_dir(project_dir, ai="kimi")
        manager = ExtensionManager(project_dir)
        result = manager._get_skills_dir()
        assert result == skills_dir

    def test_returns_none_when_ai_skills_is_non_boolean_truthy(self, project_dir):
        """Corrupted truthy ai_skills values should not enable skills mode."""
        _create_init_options(project_dir, ai="claude", ai_skills="false")

        manager = ExtensionManager(project_dir)
        result = manager._get_skills_dir()
        assert result is None
        assert not (project_dir / ".claude" / "skills").exists()

    def test_returns_none_for_non_dict_init_options(self, project_dir):
        """Corrupted-but-parseable init-options should not crash skill-dir lookup."""
        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text("[]", encoding="utf-8")
        _create_skills_dir(project_dir, ai="claude")
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
        manager.install_from_directory(
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
        assert parsed["disable-model-invocation"] is False

    def test_argument_hint_preserved_for_extension_command(
        self, skills_project, temp_dir
    ):
        """argument-hint from an extension command must survive into SKILL.md.

        Regression for #2903: the field was dropped for extension-provided
        commands while being kept for core template commands. The source
        description is intentionally long so it folds across multiple lines
        when serialized, guarding against an in-place string injection that
        would split the folded scalar and produce invalid YAML.
        """
        project_dir, skills_dir = skills_project

        long_description = (
            "Build and maintain a lean, static context/ knowledge folder so "
            "coding agents load only what is relevant and save tokens"
        )
        arg_hint = "<init | update | list | check> [area] [slug] [-- notes]"

        ext_dir = temp_dir / "hint-ext"
        ext_dir.mkdir()
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "hint-ext",
                "name": "Hint Extension",
                "version": "1.0.0",
                "description": "Extension exercising argument-hint preservation",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.hint-ext.build-context",
                        "file": "commands/build-context.md",
                        "description": long_description,
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)
        commands_dir = ext_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "build-context.md").write_text(
            "---\n"
            f'description: "{long_description}"\n'
            f'argument-hint: "{arg_hint}"\n'
            "---\n"
            "\n"
            "# Build Context\n"
            "\n"
            "Do the thing.\n"
            "$ARGUMENTS\n",
            encoding="utf-8",
        )

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        skill_file = skills_dir / "speckit-hint-ext-build-context" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")

        # Frontmatter must parse cleanly even though the description folds.
        parts = content.split("---", 2)
        assert len(parts) >= 3
        parsed = yaml.safe_load(parts[1])
        assert parsed["argument-hint"] == arg_hint
        assert parsed["description"] == long_description

    def test_argument_hint_not_added_for_non_claude_agent(self, project_dir, temp_dir):
        """argument-hint must stay Claude-only — other skills agents are untouched.

        The hint is carried only for integrations that support it (currently
        Claude, the sole integration defining inject_argument_hint). A non-Claude
        skills agent such as kimi must keep the shared build_skill_frontmatter
        shape (name/description/compatibility/metadata) with no argument-hint.
        """
        _create_init_options(project_dir, ai="kimi", ai_skills=True)
        skills_dir = _create_skills_dir(project_dir, ai="kimi")

        arg_hint = "<init | update | list | check> [area]"
        ext_dir = temp_dir / "hint-ext-kimi"
        ext_dir.mkdir()
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "hint-ext-kimi",
                "name": "Hint Extension Kimi",
                "version": "1.0.0",
                "description": "Extension exercising argument-hint gating",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.hint-ext-kimi.build-context",
                        "file": "commands/build-context.md",
                        "description": "Build context",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)
        commands_dir = ext_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "build-context.md").write_text(
            "---\n"
            'description: "Build context"\n'
            f'argument-hint: "{arg_hint}"\n'
            "---\n"
            "\n"
            "# Build Context\n"
            "\n"
            "Do the thing.\n"
            "$ARGUMENTS\n",
            encoding="utf-8",
        )

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        skill_file = skills_dir / "speckit-hint-ext-kimi-build-context" / "SKILL.md"
        assert skill_file.exists()
        parsed = yaml.safe_load(skill_file.read_text(encoding="utf-8").split("---", 2)[1])
        assert "argument-hint" not in parsed

    def test_skill_md_unicode(self, skills_project, temp_dir):
        """SKILL.md generation should preserve non-ASCII characters."""
        project_dir, skills_dir = skills_project
        ext_dir = _create_unicode_extension_dir(temp_dir)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        skill_file = skills_dir / "speckit-uni-ext-hello" / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        assert "Prüfe Konformität" in content

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

    def test_dev_skill_symlink_refreshes_existing_cache(
        self, skills_project, extension_dir, temp_dir
    ):
        """Dev-mode skill symlinks should refresh rendered cache content."""
        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        manager._register_extension_skills(
            manifest,
            extension_dir,
            link_outputs=True,
        )

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert skill_file.is_symlink()
        assert "Run this to say hello." in skill_file.read_text(encoding="utf-8")

        (extension_dir / "commands" / "hello.md").write_text(
            "---\n"
            "description: \"Updated test hello command\"\n"
            "---\n"
            "\n"
            "# Hello Command\n"
            "\n"
            "Run this updated hello.\n"
        )

        written = manager._register_extension_skills(
            manifest,
            extension_dir,
            link_outputs=True,
        )

        assert "speckit-test-ext-hello" in written
        assert "Run this updated hello." in skill_file.read_text(encoding="utf-8")

    def test_codex_dev_skill_registration_replaces_existing_dev_symlink(
        self, project_dir, extension_dir, temp_dir
    ):
        """Codex dev skill registration should migrate prior dev symlinks to files."""
        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        _create_init_options(project_dir, ai="codex", ai_skills=True)
        skills_dir = _create_skills_dir(project_dir, ai="codex")
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file = (
            extension_dir
            / ".specify-dev"
            / "extension-skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        cache_file.parent.mkdir(parents=True)
        cache_file.write_text("old linked content", encoding="utf-8")
        os.symlink(os.path.relpath(cache_file, skill_file.parent), skill_file)

        written = manager._register_extension_skills(
            manifest,
            extension_dir,
            link_outputs=True,
        )

        assert "speckit-test-ext-hello" in written
        assert skill_file.exists()
        assert not skill_file.is_symlink()
        assert "Run this to say hello." in skill_file.read_text(encoding="utf-8")
        assert cache_file.read_text(encoding="utf-8") == "old linked content"

    def test_codex_dev_skill_registration_preserves_unrelated_symlink(
        self, project_dir, extension_dir, temp_dir
    ):
        """Codex dev registration should not overwrite user-owned symlinks."""
        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        _create_init_options(project_dir, ai="codex", ai_skills=True)
        skills_dir = _create_skills_dir(project_dir, ai="codex")
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        unrelated_cache_file = (
            temp_dir
            / "other-extension"
            / ".specify-dev"
            / "extension-skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        )
        unrelated_cache_file.parent.mkdir(parents=True)
        unrelated_cache_file.write_text("user-owned linked content", encoding="utf-8")
        os.symlink(
            os.path.relpath(unrelated_cache_file, skill_file.parent), skill_file
        )

        written = manager._register_extension_skills(
            manifest,
            extension_dir,
            link_outputs=True,
        )

        assert "speckit-test-ext-hello" not in written
        assert skill_file.is_symlink()
        assert skill_file.resolve(strict=True) == unrelated_cache_file.resolve()
        assert unrelated_cache_file.read_text(encoding="utf-8") == (
            "user-owned linked content"
        )

    def test_dev_skill_registration_falls_back_to_copy_when_symlink_fails(
        self, skills_project, extension_dir, monkeypatch
    ):
        """Dev-mode skill registration works when Windows cannot create symlinks."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        def raise_windows_symlink_error(target, link):
            raise OSError("A required privilege is not held by the client")

        monkeypatch.setattr(
            "specify_cli.extensions.os.symlink", raise_windows_symlink_error
        )

        written = manager._register_extension_skills(
            manifest,
            extension_dir,
            link_outputs=True,
        )

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert "speckit-test-ext-hello" in written
        assert skill_file.exists()
        assert not skill_file.is_symlink()
        assert "Run this to say hello." in skill_file.read_text(encoding="utf-8")
        assert (
            extension_dir
            / ".specify-dev"
            / "extension-skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        ).exists()

    def test_dev_skill_registration_falls_back_to_copy_when_relpath_fails(
        self, skills_project, extension_dir, monkeypatch
    ):
        """Dev-mode skill registration stays functional across Windows drive roots."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        def raise_relpath_error(path, start=None):
            raise ValueError("path is on mount 'D:', start on mount 'C:'")

        monkeypatch.setattr(
            "specify_cli.extensions.os.path.relpath", raise_relpath_error
        )

        written = manager._register_extension_skills(
            manifest,
            extension_dir,
            link_outputs=True,
        )

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert "speckit-test-ext-hello" in written
        assert skill_file.exists()
        assert not skill_file.is_symlink()
        assert "Run this to say hello." in skill_file.read_text(encoding="utf-8")
        assert (
            extension_dir
            / ".specify-dev"
            / "extension-skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        ).exists()

    def test_dev_skill_registration_falls_back_to_copy_when_cache_write_fails(
        self, skills_project, extension_dir, monkeypatch
    ):
        """Dev-mode skill registration stays functional when the dev cache is unwritable."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")
        original_write_text = Path.write_text

        def raise_cache_write_error(path, *args, **kwargs):
            if ".specify-dev" in path.parts:
                raise OSError("cache is not writable")
            return original_write_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", raise_cache_write_error)

        written = manager._register_extension_skills(
            manifest,
            extension_dir,
            link_outputs=True,
        )

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert "speckit-test-ext-hello" in written
        assert skill_file.exists()
        assert not skill_file.is_symlink()
        assert "Run this to say hello." in skill_file.read_text(encoding="utf-8")
        assert not (
            extension_dir
            / ".specify-dev"
            / "extension-skills"
            / "speckit-test-ext-hello"
            / "SKILL.md"
        ).exists()

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

    def test_kimi_uses_hyphenated_skill_names(self, project_dir, temp_dir):
        """Kimi agent should use the same hyphenated skill names as hooks."""
        _create_init_options(project_dir, ai="kimi", ai_skills=True)
        _create_skills_dir(project_dir, ai="kimi")
        ext_dir = _create_extension_dir(temp_dir, ext_id="test-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        assert "speckit-test-ext-hello" in metadata["registered_skills"]
        assert "speckit-test-ext-world" in metadata["registered_skills"]

    def test_kimi_creates_skills_when_ai_skills_disabled(self, project_dir, temp_dir):
        """Kimi should still auto-register extension skills in native-skills mode."""
        _create_init_options(project_dir, ai="kimi", ai_skills=False)
        skills_dir = _create_skills_dir(project_dir, ai="kimi")
        ext_dir = _create_extension_dir(temp_dir, ext_id="test-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        assert "speckit-test-ext-hello" in metadata["registered_skills"]
        assert "speckit-test-ext-world" in metadata["registered_skills"]
        assert (skills_dir / "speckit-test-ext-hello" / "SKILL.md").exists()

    def test_skill_registration_resolves_script_placeholders(self, project_dir, temp_dir):
        """Auto-registered extension skills should resolve script placeholders."""
        _create_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = _create_skills_dir(project_dir, ai="claude")

        ext_dir = temp_dir / "scripted-ext"
        ext_dir.mkdir()
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "scripted-ext",
                "name": "Scripted Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.scripted-ext.plan",
                        "file": "commands/plan.md",
                        "description": "Scripted plan command",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.safe_dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "plan.md").write_text(
            "---\n"
            "description: Scripted plan command\n"
            "scripts:\n"
            "  sh: ../../scripts/bash/setup-plan.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "Run {SCRIPT}\n"
            "Review templates/checklist.md and memory/constitution.md for __AGENT__.\n"
        )

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        content = (skills_dir / "speckit-scripted-ext-plan" / "SKILL.md").read_text()
        assert "{SCRIPT}" not in content
        assert "{ARGS}" not in content
        assert "__AGENT__" not in content
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content
        assert ".specify/templates/checklist.md" in content
        assert ".specify/memory/constitution.md" in content

    def test_skill_registration_uses_extension_local_script_paths(self, project_dir, temp_dir):
        """Auto-registered skills should not rewrite extension scripts into core scripts."""
        _create_init_options(project_dir, ai="claude", ai_skills=True)
        skills_dir = _create_skills_dir(project_dir, ai="claude")

        ext_dir = temp_dir / "scripted-ext"
        ext_dir.mkdir()
        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "scripted-ext",
                "name": "Scripted Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.scripted-ext.check",
                        "file": "commands/check.md",
                        "description": "Scripted check command",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.safe_dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "scripts" / "bash").mkdir(parents=True)
        (ext_dir / "scripts" / "bash" / "resolve-skill.sh").write_text(
            "#!/usr/bin/env bash\n"
        )
        (ext_dir / "scripts" / "bash" / "ensure-skills.sh").write_text(
            "#!/usr/bin/env bash\n"
        )
        (ext_dir / "commands" / "check.md").write_text(
            "---\n"
            "description: Scripted check command\n"
            "scripts:\n"
            '  sh: scripts/bash/resolve-skill.sh "{ARGS}"\n'
            "---\n\n"
            "Run {SCRIPT}\n"
            "Then run scripts/bash/ensure-skills.sh.\n"
        )

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        content = (skills_dir / "speckit-scripted-ext-check" / "SKILL.md").read_text()
        assert "{SCRIPT}" not in content
        assert "{ARGS}" not in content
        assert (
            '.specify/extensions/scripted-ext/scripts/bash/resolve-skill.sh "$ARGUMENTS"'
            in content
        )
        assert ".specify/extensions/scripted-ext/scripts/bash/ensure-skills.sh" in content
        assert ".specify/scripts/bash/resolve-skill.sh" not in content
        assert ".specify/scripts/bash/ensure-skills.sh" not in content

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
            yaml.safe_dump(manifest_data, f)

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

    @pytest.mark.parametrize("ai", ["claude", "codex"])
    def test_skills_registered_when_dir_missing(self, project_dir, temp_dir, ai):
        """Extension add should create skills dir on demand and register skills.

        Regression test for https://github.com/github/spec-kit/issues/2682:
        when an extension is installed before the agent skills directory exists,
        skills must still be materialized (the directory is created on demand).
        """
        _create_init_options(project_dir, ai=ai, ai_skills=True)
        # Deliberately do NOT create the skills directory
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        # Skills dir should have been created automatically
        from specify_cli import _get_skills_dir as resolve_skills_dir
        skills_dir = resolve_skills_dir(project_dir, ai)
        assert skills_dir.is_dir()

        # SKILL.md files should exist
        assert (skills_dir / "speckit-early-ext-hello" / "SKILL.md").exists()
        assert (skills_dir / "speckit-early-ext-world" / "SKILL.md").exists()

        # Registry should record them
        metadata = manager.registry.get(manifest.id)
        assert len(metadata["registered_skills"]) == 2
        assert "speckit-early-ext-hello" in metadata["registered_skills"]
        assert "speckit-early-ext-world" in metadata["registered_skills"]

    def test_commands_registered_when_claude_skills_dir_missing(self, project_dir, temp_dir):
        """Extension install should not silently skip Claude when skills dir is missing."""
        _create_init_options(project_dir, ai="claude", ai_skills=True)
        (project_dir / ".claude").mkdir()
        # Deliberately do NOT create .claude/skills
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        skills_dir = project_dir / ".claude" / "skills"
        assert skills_dir.is_dir()

        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_commands"] == {
            "claude": [
                "speckit.early-ext.hello",
                "speckit.early-ext.world",
            ]
        }
        assert metadata["registered_skills"] == []

        skill_file = skills_dir / "speckit-early-ext-hello" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text(encoding="utf-8")
        assert "source: early-ext:commands/hello.md" in content

    def test_hermes_global_skills_dir_used_when_marker_is_recovered(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Hermes recovery must not use the project marker as the output dir."""
        home = temp_dir / "home"
        home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: home)
        _create_init_options(project_dir, ai="hermes", ai_skills=True)
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_commands"] == {
            "hermes": [
                "speckit.early-ext.hello",
                "speckit.early-ext.world",
            ]
        }
        assert metadata["registered_skills"] == []

        global_skills_dir = home / ".hermes" / "skills"
        assert (
            global_skills_dir / "speckit-early-ext-hello" / "SKILL.md"
        ).exists()
        assert (
            global_skills_dir / "speckit-early-ext-world" / "SKILL.md"
        ).exists()

        marker = project_dir / ".hermes" / "skills"
        assert marker.is_dir()
        assert list(marker.glob("speckit-*/SKILL.md")) == []

    def test_hermes_get_skills_dir_creates_global_output_dir(
        self, project_dir, temp_dir, monkeypatch
    ):
        """ExtensionManager should create the agent-specific output dir it returns."""
        home = temp_dir / "home"
        home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: home)
        _create_init_options(project_dir, ai="hermes", ai_skills=True)

        manager = ExtensionManager(project_dir)
        skills_dir = manager._get_skills_dir()

        assert skills_dir == home / ".hermes" / "skills"
        assert skills_dir.is_dir()
        assert (project_dir / ".hermes" / "skills").is_dir()

    def test_unusable_hermes_global_skills_dir_skips_skill_registration(
        self, project_dir, temp_dir, monkeypatch, capsys
    ):
        """An unusable agent-specific output dir should warn and skip skills."""
        home = temp_dir / "home"
        hermes_dir = home / ".hermes"
        hermes_dir.mkdir(parents=True)
        (hermes_dir / "skills").write_text("not a directory", encoding="utf-8")
        monkeypatch.setattr(Path, "home", lambda: home)
        _create_init_options(project_dir, ai="hermes", ai_skills=True)
        ext_dir = _create_extension_dir(temp_dir, ext_id="blocked-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_skills"] == []
        captured = capsys.readouterr()
        assert "Warning:" in captured.out
        assert "Continuing without skill registration." in captured.out

    def test_detect_dir_marker_file_does_not_register_hermes_commands(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Regular files at detect_dir marker paths should not detect agents."""
        home = temp_dir / "home"
        global_skills_dir = home / ".hermes" / "skills"
        global_skills_dir.mkdir(parents=True)
        monkeypatch.setattr(Path, "home", lambda: home)
        _create_init_options(project_dir, ai="hermes", ai_skills=True)
        marker_parent = project_dir / ".hermes"
        marker_parent.mkdir()
        marker_file = marker_parent / "skills"
        marker_file.write_text("not a directory", encoding="utf-8")
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        assert marker_file.is_file()
        assert marker_file.read_text(encoding="utf-8") == "not a directory"
        assert not (
            global_skills_dir / "speckit-early-ext-hello" / "SKILL.md"
        ).exists()
        assert not (
            global_skills_dir / "speckit-early-ext-world" / "SKILL.md"
        ).exists()

        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_commands"] == {}
        assert metadata["registered_skills"] == []

    def test_non_boolean_ai_skills_does_not_recover_missing_skills_dir(
        self, project_dir, temp_dir
    ):
        """Corrupted truthy ai_skills values should not recover skills dirs."""
        _create_init_options(project_dir, ai="claude", ai_skills="false")
        (project_dir / ".claude").mkdir()
        # Deliberately do NOT create .claude/skills.
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_commands"] == {}
        assert metadata["registered_skills"] == []
        assert not (project_dir / ".claude" / "skills").exists()

    def test_non_boolean_ai_skills_does_not_skip_default_agent_reregistration(
        self, project_dir, temp_dir
    ):
        """Corrupted ai_skills values should not trigger skills-mode skips."""
        _create_init_options(project_dir, ai="copilot", ai_skills="false")
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=False
        )
        manager.register_enabled_extensions_for_agent("copilot")

        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_commands"] == {
            "copilot": [
                "speckit.early-ext.hello",
                "speckit.early-ext.world",
            ]
        }
        assert metadata["registered_skills"] == []
        assert (project_dir / ".github" / "agents").is_dir()

    def test_one_failing_extension_does_not_abort_the_rest(
        self, project_dir, temp_dir, monkeypatch
    ):
        """A single failing extension must not block registration of the others.

        Regression for #2950: ``register_enabled_extensions_for_agent`` iterates
        enabled extensions; before the per-extension isolation, the first one
        that raised (e.g. an OSError writing a command file) aborted the loop and
        the exception propagated, so every later extension was silently skipped.
        """
        from specify_cli.extensions import CommandRegistrar

        _create_init_options(project_dir, ai="claude", ai_skills=False)
        manager = ExtensionManager(project_dir)
        # Two enabled extensions; the first one iterated ("aaa-fail") will raise.
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="aaa-fail"), "0.1.0",
            register_commands=False,
        )
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="bbb-ok"), "0.1.0",
            register_commands=False,
        )

        original = CommandRegistrar.register_commands_for_agent

        def flaky(self, agent_name, manifest, ext_dir, project_root, link_outputs=False):
            if manifest.id == "aaa-fail":
                raise OSError("simulated command-file write failure")
            return original(
                self, agent_name, manifest, ext_dir, project_root,
                link_outputs=link_outputs,
            )

        monkeypatch.setattr(CommandRegistrar, "register_commands_for_agent", flaky)

        # Must not propagate, despite the first extension failing.
        manager.register_enabled_extensions_for_agent("claude")

        # The healthy extension was still registered for the agent...
        ok_meta = manager.registry.get("bbb-ok")
        assert "claude" in ok_meta["registered_commands"], (
            "a later extension must still register after an earlier one fails (#2950)"
        )
        # ...and the failing one was not.
        fail_meta = manager.registry.get("aaa-fail")
        assert "claude" not in fail_meta.get("registered_commands", {})

    def test_skill_registration_failure_preserves_registered_commands(
        self, project_dir, temp_dir, monkeypatch, capsys
    ):
        """Persist successful command registration even if skills fail.

        If command files are written but skill generation raises, the command
        registry must still be updated so later unregister/cleanup can find the
        command files.
        """
        _create_init_options(project_dir, ai="claude", ai_skills=False)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="skill-fail"), "0.1.0",
            register_commands=False,
        )

        def fail_skills(self, manifest, ext_dir, link_outputs=False):
            raise OSError("simulated skill directory failure")

        monkeypatch.setattr(
            ExtensionManager, "_register_extension_skills", fail_skills
        )

        manager.register_enabled_extensions_for_agent("claude")

        metadata = manager.registry.get("skill-fail")
        assert metadata is not None
        assert metadata["registered_commands"] == {
            "claude": [
                "speckit.skill-fail.hello",
                "speckit.skill-fail.world",
            ]
        }
        assert metadata["registered_skills"] == []

        captured = capsys.readouterr()
        assert "register extension skills for extension 'skill-fail'" in captured.out
        assert "Continuing with available registration results" in captured.out

    def test_rescaffold_toggle_command_to_skills_removes_stale_extension_command_file(
        self, project_dir, temp_dir
    ):
        """Toggling the *same* active agent from command mode to skills mode
        must remove the stale extension command-mode artifact, not just add
        the skills-mode one.

        Copilot stays the active agent throughout (mirroring ``integration
        upgrade copilot --skills``, not a switch to a different agent).
        ``register_enabled_extensions_for_agent`` skips the commands phase
        once ``skills_mode_active`` is true, but before this fix it never
        removed the ``.agent.md`` file (and ``registered_commands["copilot"]``
        entry) the commands phase previously wrote while command mode was
        active — leaving both artifacts on disk at once and violating the
        command/skill mutual-exclusion the PR description claims (#2948).
        """
        _create_init_options(project_dir, ai="copilot", ai_skills=False)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="toggle-ext"), "0.1.0",
            register_commands=False,
        )
        manager.register_enabled_extensions_for_agent("copilot")

        agents_dir = project_dir / ".github" / "agents"
        cmd_file = agents_dir / "speckit.toggle-ext.hello.agent.md"
        assert cmd_file.exists(), "sanity: command mode should write .agent.md"

        # Toggle ai_skills on for the same active agent (copilot) and
        # rescaffold, mirroring `integration upgrade copilot --skills`.
        _create_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_extensions_for_agent("copilot")

        assert not cmd_file.exists(), (
            "the stale command-mode .agent.md file must be removed once "
            "this agent toggles to skills mode, not left alongside the "
            "new SKILL.md (#2948)"
        )
        metadata = manager.registry.get("toggle-ext")
        registered_commands = metadata.get("registered_commands", {})
        assert not registered_commands.get("copilot"), (
            "registered_commands tracking for copilot must be cleared "
            "once its command file is removed on toggle (#2948)"
        )
        skills_dir = project_dir / ".github" / "skills"
        skill_file = skills_dir / "speckit-toggle-ext-hello" / "SKILL.md"
        assert skill_file.exists(), "sanity: skills mode should write SKILL.md"

    def test_toggle_command_to_skills_preserves_old_extension_command_on_skills_failure(
        self, project_dir, temp_dir, monkeypatch
    ):
        """An extension command->skills toggle must not destroy the old
        command artifact before the new skill registration has actually
        succeeded.

        Mirrors the analogous preset-side fix
        (``test_toggle_command_to_skills_preserves_old_command_on_skills_failure``
        in ``tests/test_presets.py``): before the fix, the stale
        command-mode file/tracking was unregistered unconditionally as soon
        as the commands phase was skipped for ``skills_mode_active``,
        regardless of whether the subsequent, independently-fallible
        ``_register_extension_skills()`` call actually succeeded. If skills
        raises, the exception handler just warns and continues, leaving
        neither the old command file nor a new skill file (#2948).
        """
        _create_init_options(project_dir, ai="copilot", ai_skills=False)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="toggle-fail-ext"), "0.1.0",
            register_commands=False,
        )
        manager.register_enabled_extensions_for_agent("copilot")

        agents_dir = project_dir / ".github" / "agents"
        cmd_file = agents_dir / "speckit.toggle-fail-ext.hello.agent.md"
        assert cmd_file.exists(), "sanity: command mode should write .agent.md"
        metadata = manager.registry.get("toggle-fail-ext")
        assert metadata.get("registered_commands", {}).get("copilot"), (
            "sanity: the command-mode write should be tracked for copilot"
        )

        # Toggle ai_skills on for the same active agent (copilot), but with
        # skills registration injected to fail.
        _create_init_options(project_dir, ai="copilot", ai_skills=True)

        def _raise_register_extension_skills(*args, **kwargs):
            raise OSError("simulated extension skills-phase failure")

        monkeypatch.setattr(
            manager, "_register_extension_skills", _raise_register_extension_skills
        )
        manager.register_enabled_extensions_for_agent("copilot")

        assert cmd_file.exists(), (
            "the old command-mode artifact must survive when the "
            "replacement skills registration fails — deleting it before "
            "the new artifact is confirmed leaves neither in place (#2948)"
        )
        metadata = manager.registry.get("toggle-fail-ext")
        assert metadata.get("registered_commands", {}).get("copilot"), (
            "registered_commands must keep tracking copilot's still-live "
            "command file when the skills replacement failed (#2948)"
        )

    def test_rescaffold_toggle_skills_to_command_removes_stale_extension_skill_file(
        self, project_dir, temp_dir
    ):
        """Toggling the *same* active agent from skills mode to command mode
        must remove the stale extension skills-mode artifact, not just add
        the command-mode one.

        Mirror image of the command->skills toggle: ``_register_extension_skills``
        returns an empty list once skills mode is off for this agent (its
        skills directory no longer resolves), but before this fix an empty
        result was silently treated as "nothing to register" rather than
        "this agent's skill was rendered here previously and is now stale",
        so the ``SKILL.md`` this extension wrote while skills mode was
        active stayed on disk even though a fresh ``.agent.md`` was written
        right alongside it (#2948).
        """
        _create_init_options(project_dir, ai="copilot", ai_skills=True)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="toggle-ext2"), "0.1.0",
            register_commands=False,
        )
        manager.register_enabled_extensions_for_agent("copilot")

        skills_dir = project_dir / ".github" / "skills"
        skill_file = skills_dir / "speckit-toggle-ext2-hello" / "SKILL.md"
        assert skill_file.exists(), "sanity: skills mode should write SKILL.md"

        # Toggle ai_skills off for the same active agent (copilot) and
        # rescaffold, mirroring `integration upgrade copilot` (no --skills).
        _create_init_options(project_dir, ai="copilot", ai_skills=False)
        manager.register_enabled_extensions_for_agent("copilot")

        agents_dir = project_dir / ".github" / "agents"
        cmd_file = agents_dir / "speckit.toggle-ext2.hello.agent.md"
        assert cmd_file.exists(), "sanity: command mode should write .agent.md"

        assert not skill_file.exists(), (
            "the stale skills-mode SKILL.md file must be removed once this "
            "agent toggles to command mode, not left alongside the new "
            ".agent.md (#2948)"
        )
        metadata = manager.registry.get("toggle-ext2")
        registered_skills = metadata.get("registered_skills", [])
        assert "speckit-toggle-ext2-hello" not in registered_skills, (
            "registered_skills tracking must be cleared for the removed "
            "skill file, not left dangling once it's orphaned (#2948)"
        )

    def test_toggle_to_command_preserves_tracking_for_mirror_in_other_agent_dir(
        self, project_dir, temp_dir
    ):
        """Skills->command toggle cleanup must not drop global tracking for a
        skill name that still has a mirror under a *different* agent's
        skills directory from an earlier activation.

        ``registered_skills`` is a flat, agent-agnostic list for extensions
        (skills are only ever rendered for the currently active agent, by
        design). Auggie is activated first (skills mode), writing a mirror
        under ``.augment/skills``. Copilot is then activated (also skills
        mode), writing its own mirror under ``.github/skills`` for the same
        skill names — the flat list already contains those names, so
        nothing new is added. Copilot is then toggled to command mode: its
        own ``.github/skills`` mirror becomes stale and must be removed,
        but the still-existing Auggie mirror means the extension still
        globally owns these skill names. Before this fix, the recompute
        after toggle-cleanup only checked *copilot's* directory, so it
        dropped the names from ``registered_skills`` entirely — losing
        track of Auggie's still-existing mirror, which a later `remove()`
        would then never find and clean up (or restore during override
        reconciliation), permanently orphaning it (#2948).
        """
        _create_init_options(project_dir, ai="auggie", ai_skills=True)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="multi-agent-ext"), "0.1.0",
            register_commands=False,
        )
        manager.register_enabled_extensions_for_agent("auggie")

        auggie_skills_dir = project_dir / ".augment" / "skills"
        auggie_hello = auggie_skills_dir / "speckit-multi-agent-ext-hello" / "SKILL.md"
        auggie_world = auggie_skills_dir / "speckit-multi-agent-ext-world" / "SKILL.md"
        assert auggie_hello.exists() and auggie_world.exists(), (
            "sanity: auggie's skills-mode activation should mirror both "
            "extension commands as SKILL.md files"
        )

        # Activate copilot in skills mode too (no intervening removal of
        # auggie's mirrors) — the same extension's skills get mirrored a
        # second time, under a different agent's directory.
        _create_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_extensions_for_agent("copilot")

        copilot_skills_dir = project_dir / ".github" / "skills"
        copilot_hello = copilot_skills_dir / "speckit-multi-agent-ext-hello" / "SKILL.md"
        copilot_world = copilot_skills_dir / "speckit-multi-agent-ext-world" / "SKILL.md"
        assert copilot_hello.exists() and copilot_world.exists(), (
            "sanity: copilot's skills-mode activation should also mirror "
            "both extension commands"
        )

        # Toggle copilot to command mode (mirroring `integration upgrade
        # copilot` with no --skills) — copilot's mirror is now stale.
        _create_init_options(project_dir, ai="copilot", ai_skills=False)
        manager.register_enabled_extensions_for_agent("copilot")

        assert not copilot_hello.exists() and not copilot_world.exists(), (
            "copilot's own stale skills-mode mirrors must be removed once "
            "it toggles to command mode"
        )
        assert auggie_hello.exists() and auggie_world.exists(), (
            "auggie's mirrors from an earlier activation must be left "
            "untouched by copilot's own toggle cleanup"
        )

        metadata = manager.registry.get("multi-agent-ext")
        registered_skills = metadata.get("registered_skills", [])
        assert set(registered_skills) == {
            "speckit-multi-agent-ext-hello",
            "speckit-multi-agent-ext-world",
        }, (
            "registered_skills must retain both names: auggie's mirrors "
            "still exist on disk, so the extension still globally owns "
            "these skill names even though copilot's own copy is now gone "
            "(#2948)"
        )

        # Full removal must still find and clean up Auggie's remaining
        # mirrors via the preserved tracking.
        assert manager.remove("multi-agent-ext") is True
        assert not auggie_hello.exists() and not auggie_world.exists(), (
            "removal must clean up every remaining extension-owned mirror, "
            "not just the ones under the last-active agent's directory — "
            "this only works if registered_skills tracking wasn't "
            "prematurely dropped during the earlier toggle (#2948)"
        )

    def test_remove_while_second_agent_still_in_skills_mode_cleans_up_first_agent_mirror(
        self, project_dir, temp_dir
    ):
        """Full extension removal must clean up every previously-active
        agent's mirror, not just the currently active one, even with no
        intervening toggle.

        Auggie is activated first (skills mode), writing a mirror.
        Copilot is then activated (also skills mode, still active at
        removal time) and writes its own mirror for the same names.
        ``remove()`` calls ``_unregister_extension_skills(registered_skills,
        extension_id)`` with no explicit ``skills_dir`` — genuinely
        unscoped, "clean up everywhere this extension owns something".
        Before this fix, omitting ``skills_dir`` caused the method to
        resolve the *currently active* agent's directory via
        ``_get_skills_dir()`` and take the scoped fast path instead of the
        all-directory fallback scan, so only Copilot's mirror was removed
        and Auggie's was silently left orphaned (#2948).
        """
        _create_init_options(project_dir, ai="auggie", ai_skills=True)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="remove-multi-agent-ext"), "0.1.0",
            register_commands=False,
        )
        manager.register_enabled_extensions_for_agent("auggie")

        auggie_skills_dir = project_dir / ".augment" / "skills"
        auggie_hello = auggie_skills_dir / "speckit-remove-multi-agent-ext-hello" / "SKILL.md"
        auggie_world = auggie_skills_dir / "speckit-remove-multi-agent-ext-world" / "SKILL.md"
        assert auggie_hello.exists() and auggie_world.exists(), (
            "sanity: auggie's skills-mode activation should mirror both "
            "extension commands as SKILL.md files"
        )

        _create_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_extensions_for_agent("copilot")

        copilot_skills_dir = project_dir / ".github" / "skills"
        copilot_hello = copilot_skills_dir / "speckit-remove-multi-agent-ext-hello" / "SKILL.md"
        copilot_world = copilot_skills_dir / "speckit-remove-multi-agent-ext-world" / "SKILL.md"
        assert copilot_hello.exists() and copilot_world.exists(), (
            "sanity: copilot's skills-mode activation should also mirror "
            "both extension commands"
        )

        # Remove the extension while copilot (the second agent) is still
        # the active, skills-mode agent — no toggle, no intervening
        # rescaffold for auggie.
        assert manager.remove("remove-multi-agent-ext") is True

        assert not copilot_hello.exists() and not copilot_world.exists(), (
            "sanity: the currently active agent's mirrors must be removed"
        )
        assert not auggie_hello.exists() and not auggie_world.exists(), (
            "removal must also clean up the first agent's (auggie) "
            "mirrors even though it is no longer the active agent — "
            "omitting skills_dir must trigger the all-directory fallback "
            "scan, not silently narrow to the currently active agent's "
            "directory (#2948)"
        )

    def test_unregister_agent_artifacts_stays_scoped_when_agent_dir_absent(
        self, project_dir, temp_dir
    ):
        """``unregister_agent_artifacts`` must remain scoped to the given
        agent even when that agent's own skills directory does not exist —
        it must never fall through to the genuinely-unscoped, all-directory
        removal semantics reserved for ``remove()``.

        Auggie and Copilot are both activated in skills mode, each writing
        its own mirror. ``unregister_agent_artifacts("cursor-agent")`` is
        then called for a supported agent that was *never* activated, so
        its skills directory does not exist on disk. Before this fix, the
        caller converted the resolved-but-absent directory to ``None``
        before calling ``_unregister_extension_skills`` — and after the
        prior fix (1d8f9e3), omitting ``skills_dir`` means "scan and clean
        up every configured agent's directory", not "this specific agent
        has nothing to clean up". That silently deleted Auggie's and
        Copilot's still-live mirrors while "cleaning up" an agent that was
        never even active.
        """
        _create_init_options(project_dir, ai="auggie", ai_skills=True)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="scoped-unregister-ext"), "0.1.0",
            register_commands=False,
        )
        manager.register_enabled_extensions_for_agent("auggie")

        auggie_skills_dir = project_dir / ".augment" / "skills"
        auggie_hello = auggie_skills_dir / "speckit-scoped-unregister-ext-hello" / "SKILL.md"
        auggie_world = auggie_skills_dir / "speckit-scoped-unregister-ext-world" / "SKILL.md"
        assert auggie_hello.exists() and auggie_world.exists(), (
            "sanity: auggie's skills-mode activation should mirror both "
            "extension commands as SKILL.md files"
        )

        _create_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_extensions_for_agent("copilot")

        copilot_skills_dir = project_dir / ".github" / "skills"
        copilot_hello = copilot_skills_dir / "speckit-scoped-unregister-ext-hello" / "SKILL.md"
        copilot_world = copilot_skills_dir / "speckit-scoped-unregister-ext-world" / "SKILL.md"
        assert copilot_hello.exists() and copilot_world.exists(), (
            "sanity: copilot's skills-mode activation should also mirror "
            "both extension commands"
        )

        cursor_skills_dir = project_dir / ".cursor" / "skills"
        assert not cursor_skills_dir.exists(), (
            "sanity: cursor-agent was never activated so it has no "
            "skills directory on disk"
        )

        # Unregister artifacts for an agent that was never activated (its
        # skills directory is absent). This must be a no-op with respect
        # to other agents' live mirrors.
        manager.unregister_agent_artifacts("cursor-agent")

        assert auggie_hello.exists() and auggie_world.exists(), (
            "unregistering a never-activated agent's artifacts must not "
            "delete auggie's live mirror — an absent target directory "
            "must not widen cleanup to every configured agent directory"
        )
        assert copilot_hello.exists() and copilot_world.exists(), (
            "unregistering a never-activated agent's artifacts must not "
            "delete copilot's live mirror — an absent target directory "
            "must not widen cleanup to every configured agent directory"
        )

    def test_unregister_agent_artifacts_preserves_tracking_for_other_agent_mirror(
        self, project_dir, temp_dir
    ):
        """Present-directory reconciliation in ``unregister_agent_artifacts``
        must not drop global ``registered_skills`` tracking for a name that
        still has a marker-verified mirror under a *different* agent's
        directory.

        Auggie and Copilot are both activated in skills mode, each writing
        its own mirror for the same extension skill names into the single,
        agent-agnostic flat ``registered_skills`` list.
        ``unregister_agent_artifacts("auggie")`` removes auggie's own
        mirror (its directory exists, so the fast path finds and deletes
        it) — but before this fix, the registry reconciliation afterward
        only checked whether each name still existed under *auggie's* own
        (now-empty) directory, concluding every name was gone and wiping
        ``registered_skills`` to ``[]`` even though Copilot's mirror was
        still live and now untracked. A later full ``remove()`` would then
        read an empty registry and leave Copilot's mirror permanently
        orphaned (#2948).
        """
        _create_init_options(project_dir, ai="auggie", ai_skills=True)
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            _create_extension_dir(temp_dir, ext_id="dual-agent-unregister-ext"), "0.1.0",
            register_commands=False,
        )
        manager.register_enabled_extensions_for_agent("auggie")

        auggie_skills_dir = project_dir / ".augment" / "skills"
        auggie_hello = auggie_skills_dir / "speckit-dual-agent-unregister-ext-hello" / "SKILL.md"
        auggie_world = auggie_skills_dir / "speckit-dual-agent-unregister-ext-world" / "SKILL.md"
        assert auggie_hello.exists() and auggie_world.exists(), (
            "sanity: auggie's skills-mode activation should mirror both "
            "extension commands as SKILL.md files"
        )

        _create_init_options(project_dir, ai="copilot", ai_skills=True)
        manager.register_enabled_extensions_for_agent("copilot")

        copilot_skills_dir = project_dir / ".github" / "skills"
        copilot_hello = copilot_skills_dir / "speckit-dual-agent-unregister-ext-hello" / "SKILL.md"
        copilot_world = copilot_skills_dir / "speckit-dual-agent-unregister-ext-world" / "SKILL.md"
        assert copilot_hello.exists() and copilot_world.exists(), (
            "sanity: copilot's skills-mode activation should also mirror "
            "both extension commands"
        )

        # Unregister artifacts for auggie only (its directory exists and
        # is cleaned up), while copilot's mirror is untouched and remains
        # live on disk.
        manager.unregister_agent_artifacts("auggie")

        assert not auggie_hello.exists() and not auggie_world.exists(), (
            "sanity: auggie's own mirror must be removed"
        )
        assert copilot_hello.exists() and copilot_world.exists(), (
            "sanity: copilot's mirror must be untouched by an auggie-scoped "
            "unregister call"
        )

        registry_metadata = manager.registry.get("dual-agent-unregister-ext")
        tracked = registry_metadata.get("registered_skills", [])
        assert "speckit-dual-agent-unregister-ext-hello" in tracked, (
            "registered_skills tracking must be preserved for names still "
            "owned by copilot's live mirror, even though they were removed "
            "from auggie's own (now nonexistent) directory — reconciling "
            "against only the just-cleaned agent's directory incorrectly "
            "concludes the name is gone everywhere (#2948)"
        )
        assert "speckit-dual-agent-unregister-ext-world" in tracked, (
            "registered_skills tracking must be preserved for names still "
            "owned by copilot's live mirror, even though they were removed "
            "from auggie's own (now nonexistent) directory — reconciling "
            "against only the just-cleaned agent's directory incorrectly "
            "concludes the name is gone everywhere (#2948)"
        )

        # A subsequent full extension removal must still find and clean up
        # copilot's remaining mirror via the preserved tracking.
        assert manager.remove("dual-agent-unregister-ext") is True
        assert not copilot_hello.exists() and not copilot_world.exists(), (
            "full removal must clean up copilot's remaining mirror — this "
            "only works if registered_skills tracking wasn't prematurely "
            "dropped by the earlier auggie-scoped unregister call (#2948)"
        )

    def test_extension_owned_skill_names_rejects_symlinked_candidate_directory(
        self, project_dir, temp_dir
    ):
        """Provenance probing must not follow a symlinked candidate skills
        directory that escapes the project root, even when a marker-
        matching SKILL.md exists at the symlink target.

        Both ``_extension_owned_skill_names`` and its sibling
        ``_unregister_extension_skills`` previously called
        ``skills_candidate.resolve()`` and then checked children relative
        to that *already-resolved* candidate — so if the candidate
        directory itself (e.g. ``.gemini/skills``) was a symlink pointing
        outside the project root, both the resolve and the subsequent
        containment check silently passed *through* the symlink instead
        of rejecting it. A marker-matching ``SKILL.md`` at the symlink
        target would therefore be falsely attributed to the extension.
        """
        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        external_dir = temp_dir / "external-skills-root"
        external_dir.mkdir()
        (external_dir / "precious_file.txt").write_text(
            "do not touch", encoding="utf-8"
        )
        external_skill_subdir = external_dir / "speckit-sym-escape-ext-hello"
        external_skill_subdir.mkdir()
        (external_skill_subdir / "SKILL.md").write_text(
            "---\n"
            "name: speckit-sym-escape-ext-hello\n"
            "description: external marker-matching skill\n"
            "metadata:\n"
            "  source: extension:sym-escape-ext\n"
            "---\n\n"
            "external body\n",
            encoding="utf-8",
        )

        gemini_dir = project_dir / ".gemini"
        gemini_dir.mkdir()
        os.symlink(str(external_dir), str(gemini_dir / "skills"))

        manager = ExtensionManager(project_dir)
        owned = manager._extension_owned_skill_names(
            ["speckit-sym-escape-ext-hello"], "sym-escape-ext"
        )

        assert owned == [], (
            "a symlinked candidate skills directory escaping the project "
            "root must never be followed for provenance attribution, "
            "even when a marker-matching SKILL.md exists at its target"
        )

    def test_unregister_extension_skills_fallback_does_not_follow_symlinked_dir(
        self, project_dir, temp_dir
    ):
        """Fallback removal scanning must not delete through a symlinked
        candidate skills directory escaping the project root.

        Mirrors the previous test but exercises the actual deletion path:
        before the fix, a symlinked ``.gemini/skills`` pointing outside
        the project root would be resolved and scanned, and the
        marker-matching external ``SKILL.md`` directory would be deleted
        via ``shutil.rmtree`` — collateral damage to unrelated external
        content (here, ``precious_file.txt`` sitting alongside it).
        """
        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        external_dir = temp_dir / "external-skills-root2"
        external_dir.mkdir()
        precious_file = external_dir / "precious_file.txt"
        precious_file.write_text("do not touch", encoding="utf-8")
        external_skill_subdir = external_dir / "speckit-sym-escape-ext2-hello"
        external_skill_subdir.mkdir()
        external_skill_md = external_skill_subdir / "SKILL.md"
        external_skill_md.write_text(
            "---\n"
            "name: speckit-sym-escape-ext2-hello\n"
            "description: external marker-matching skill\n"
            "metadata:\n"
            "  source: extension:sym-escape-ext2\n"
            "---\n\n"
            "external body\n",
            encoding="utf-8",
        )

        gemini_dir = project_dir / ".gemini"
        gemini_dir.mkdir()
        os.symlink(str(external_dir), str(gemini_dir / "skills"))

        manager = ExtensionManager(project_dir)
        # Exercise the fallback scan (skills_dir=None) exactly as a full
        # `remove()` would invoke it.
        manager._unregister_extension_skills(
            ["speckit-sym-escape-ext2-hello"], "sym-escape-ext2"
        )

        assert precious_file.exists(), (
            "unrelated external content must survive: the fallback scan "
            "must never delete through a symlinked candidate directory "
            "escaping the project root"
        )
        assert external_skill_md.exists(), (
            "the external marker-matching skill directory itself must "
            "not be removed via a symlinked candidate path"
        )

    def test_unregister_extension_skills_fast_path_rejects_symlinked_explicit_dir(
        self, project_dir, temp_dir
    ):
        """Explicit-skills_dir fast path must reject a symlinked directory
        escaping the project root, mirroring the register-time call site
        where a caller resolves a specific agent's directory without
        side effects and passes it straight through.
        """
        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        external_dir = temp_dir / "external-skills-root3"
        external_dir.mkdir()
        precious_file = external_dir / "precious_file.txt"
        precious_file.write_text("do not touch", encoding="utf-8")
        external_skill_subdir = external_dir / "speckit-sym-escape-ext3-hello"
        external_skill_subdir.mkdir()
        (external_skill_subdir / "SKILL.md").write_text(
            "---\n"
            "name: speckit-sym-escape-ext3-hello\n"
            "description: external marker-matching skill\n"
            "metadata:\n"
            "  source: extension:sym-escape-ext3\n"
            "---\n\n"
            "external body\n",
            encoding="utf-8",
        )

        gemini_dir = project_dir / ".gemini"
        gemini_dir.mkdir()
        symlinked_skills_dir = gemini_dir / "skills"
        os.symlink(str(external_dir), str(symlinked_skills_dir))

        manager = ExtensionManager(project_dir)
        manager._unregister_extension_skills(
            ["speckit-sym-escape-ext3-hello"],
            "sym-escape-ext3",
            skills_dir=symlinked_skills_dir,
        )

        assert precious_file.exists(), (
            "unrelated external content must survive: the fast path must "
            "refuse to delete through an explicit but symlinked skills_dir "
            "escaping the project root"
        )
        assert external_skill_subdir.exists(), (
            "the external marker-matching skill directory must not be "
            "removed via an explicit symlinked directory argument"
        )

    def test_extension_owned_skill_names_rejects_symlinked_child_skill_dir(
        self, project_dir, temp_dir
    ):
        """Provenance probing must reject a per-skill child directory that
        is itself a symlink, even when its resolved target stays inside
        the (real, non-symlinked) skills root.

        Both ``_extension_owned_skill_names`` and
        ``_unregister_extension_skills`` previously only validated the
        *parent* ``skills_dir`` for symlink escape, then resolved
        ``skills_dir / skill_name`` and checked containment relative to
        the already-resolved parent. A child symlink whose target
        resolves inside that same root passes that containment check, so
        a corrupted or attacker-controlled registry entry naming a
        symlink alias could cause a legitimate, unrelated skill directory
        to be falsely attributed as extension-owned via the alias.
        """
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        # A real, legitimately marker-matching skill directory under its
        # own name — this represents genuine extension-owned content.
        real_skill_dir = skills_dir / "speckit-child-sym-real"
        real_skill_dir.mkdir()
        (real_skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: speckit-child-sym-real\n"
            "description: real skill\n"
            "metadata:\n"
            "  source: extension:child-sym-ext\n"
            "---\n\n"
            "real body\n",
            encoding="utf-8",
        )

        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        # A *different* registered name that is merely a symlink alias
        # pointing at the real skill directory above — both still live
        # inside the same, non-symlinked skills root.
        alias_name = "speckit-child-sym-alias"
        os.symlink(str(real_skill_dir), str(skills_dir / alias_name))

        manager = ExtensionManager(project_dir)
        owned = manager._extension_owned_skill_names(
            [alias_name], "child-sym-ext"
        )

        assert owned == [], (
            "a per-skill child directory that is itself a symlink must "
            "never be followed for provenance attribution, even when its "
            "resolved target remains inside the skills root"
        )

    def test_unregister_extension_skills_explicit_dir_rejects_symlinked_child(
        self, project_dir, temp_dir
    ):
        """Fast (explicit ``skills_dir``) removal path must refuse to
        delete through a per-skill child directory that is itself a
        symlink, even when the resolved target stays inside the skills
        root — deleting the resolved target would destroy a legitimate,
        differently-named skill directory via the alias.
        """
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        precious_skill_dir = skills_dir / "speckit-child-sym-precious"
        precious_skill_dir.mkdir()
        precious_skill_md = precious_skill_dir / "SKILL.md"
        precious_skill_md.write_text(
            "---\n"
            "name: speckit-child-sym-precious\n"
            "description: precious skill\n"
            "metadata:\n"
            "  source: extension:child-sym-ext2\n"
            "---\n\n"
            "precious body\n",
            encoding="utf-8",
        )

        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        alias_name = "speckit-child-sym-alias2"
        os.symlink(str(precious_skill_dir), str(skills_dir / alias_name))

        manager = ExtensionManager(project_dir)
        manager._unregister_extension_skills(
            [alias_name], "child-sym-ext2", skills_dir=skills_dir,
        )

        assert precious_skill_dir.exists(), (
            "the real skill directory reached only through a symlink "
            "alias must survive removal of the alias name (#2948)"
        )
        assert precious_skill_md.exists(), (
            "the real skill directory's SKILL.md must not be deleted via "
            "a differently-named symlink alias"
        )

    def test_unregister_extension_skills_fallback_rejects_symlinked_child(
        self, project_dir, temp_dir
    ):
        """Fallback (unscoped, ``skills_dir=None``) removal scan must also
        refuse to delete through a per-skill child symlink, mirroring the
        explicit-dir fast path.
        """
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        precious_skill_dir = skills_dir / "speckit-child-sym-precious3"
        precious_skill_dir.mkdir()
        precious_skill_md = precious_skill_dir / "SKILL.md"
        precious_skill_md.write_text(
            "---\n"
            "name: speckit-child-sym-precious3\n"
            "description: precious skill\n"
            "metadata:\n"
            "  source: extension:child-sym-ext3\n"
            "---\n\n"
            "precious body\n",
            encoding="utf-8",
        )

        if not _can_create_symlink(temp_dir):
            pytest.skip("Current platform/user cannot create symlinks")

        alias_name = "speckit-child-sym-alias3"
        os.symlink(str(precious_skill_dir), str(skills_dir / alias_name))

        manager = ExtensionManager(project_dir)
        manager._unregister_extension_skills([alias_name], "child-sym-ext3")

        assert precious_skill_dir.exists(), (
            "the real skill directory reached only through a symlink "
            "alias must survive the unscoped fallback removal scan (#2948)"
        )
        assert precious_skill_md.exists(), (
            "the real skill directory's SKILL.md must not be deleted via "
            "a differently-named symlink alias during fallback removal"
        )

    def test_existing_agent_command_path_file_is_not_detected(
        self, project_dir, temp_dir
    ):
        """Existing files at command-dir paths should not count as detected agents."""
        _create_init_options(project_dir, ai="claude", ai_skills=False)
        claude_dir = project_dir / ".claude"
        claude_dir.mkdir()
        skills_file = claude_dir / "skills"
        skills_file.write_text("not a directory", encoding="utf-8")
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        assert skills_file.read_text(encoding="utf-8") == "not a directory"
        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_commands"] == {}
        assert metadata["registered_skills"] == []

    def test_missing_shared_skills_dir_registers_only_active_agent(self, project_dir, temp_dir):
        """Recreating shared skills dirs should not activate unrelated agents."""
        _create_init_options(project_dir, ai="agy", ai_skills=True)
        (project_dir / ".agents").mkdir()
        # Deliberately do NOT create .agents/skills, shared by agy and codex.
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        skills_dir = project_dir / ".agents" / "skills"
        assert skills_dir.is_dir()

        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_commands"] == {
            "agy": [
                "speckit.early-ext.hello",
                "speckit.early-ext.world",
            ]
        }
        assert metadata["registered_skills"] == []

    def test_missing_shared_skills_dir_uses_normalized_guard_for_later_agents(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Shared-dir suppression should tolerate lexical path differences."""
        _create_init_options(project_dir, ai="agy", ai_skills=True)
        (project_dir / ".agents").mkdir()
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        from specify_cli.agents import CommandRegistrar as AgentRegistrar

        original_resolve_agent_dir = AgentRegistrar._resolve_agent_dir
        original_register_commands = AgentRegistrar.register_commands
        attempted_agents = []

        def resolve_codex_with_parent_segment(self, agent_name, agent_config, root):
            if agent_name == "codex":
                return root / ".agents" / ".." / ".agents" / "skills"
            return original_resolve_agent_dir(agent_name, agent_config, root)

        def record_registration(self, agent_name, *args, **kwargs):
            attempted_agents.append(agent_name)
            return original_register_commands(self, agent_name, *args, **kwargs)

        monkeypatch.setattr(
            AgentRegistrar, "_resolve_agent_dir", resolve_codex_with_parent_segment
        )
        monkeypatch.setattr(AgentRegistrar, "register_commands", record_registration)

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        assert attempted_agents == ["agy"]
        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_commands"] == {
            "agy": [
                "speckit.early-ext.hello",
                "speckit.early-ext.world",
            ]
        }
        assert metadata["registered_skills"] == []

    def test_missing_shared_skills_dir_write_oserror_does_not_register_other_agents(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Failed active registration must not make shared skills dirs detected."""
        _create_init_options(project_dir, ai="agy", ai_skills=True)
        (project_dir / ".agents").mkdir()
        # Deliberately do NOT create .agents/skills, shared by agy and codex.
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        from specify_cli.agents import CommandRegistrar as AgentRegistrar

        original_register_commands = AgentRegistrar.register_commands
        attempted_agents = []

        def fail_recovered_agy_registration(self, agent_name, *args, **kwargs):
            attempted_agents.append(agent_name)
            if agent_name == "agy":
                raise PermissionError("denied")
            return original_register_commands(self, agent_name, *args, **kwargs)

        monkeypatch.setattr(
            AgentRegistrar, "register_commands", fail_recovered_agy_registration
        )

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        skills_dir = project_dir / ".agents" / "skills"
        assert skills_dir.is_dir()
        assert attempted_agents == ["agy"]

        metadata = manager.registry.get(manifest.id)
        assert metadata is not None
        assert metadata["registered_commands"] == {}
        assert "speckit-early-ext-hello" in metadata["registered_skills"]
        assert "speckit-early-ext-world" in metadata["registered_skills"]

    def test_missing_active_skills_dir_does_not_follow_symlinked_parent(
        self, project_dir, temp_dir
    ):
        """Recovered command registration must reuse active skills-dir safety checks."""
        if not hasattr(os, "symlink"):
            pytest.skip("symlinks are unavailable")

        _create_init_options(project_dir, ai="claude", ai_skills=True)
        outside = temp_dir / "outside-claude"
        outside.mkdir()
        try:
            os.symlink(outside, project_dir / ".claude", target_is_directory=True)
        except OSError:
            pytest.skip("Current platform/user cannot create directory symlinks")
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_commands"] == {}
        assert metadata["registered_skills"] == []
        assert not (outside / "skills").exists()

    def test_missing_active_skills_dir_invalid_parent_skips_without_aborting(
        self, project_dir, temp_dir
    ):
        """Invalid active skill parents should not abort extension installation."""
        _create_init_options(project_dir, ai="claude", ai_skills=True)
        (project_dir / ".claude").write_text("not a directory", encoding="utf-8")
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_commands"] == {}
        assert metadata["registered_skills"] == []

    def test_missing_active_skills_dir_write_oserror_skips_without_aborting(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Filesystem failures in recovered command registration should skip safely."""
        _create_init_options(project_dir, ai="claude", ai_skills=True)
        (project_dir / ".claude").mkdir()
        ext_dir = _create_extension_dir(temp_dir, ext_id="early-ext")

        from specify_cli.agents import CommandRegistrar as AgentRegistrar

        original_register_commands = AgentRegistrar.register_commands

        def fail_recovered_claude_registration(self, agent_name, *args, **kwargs):
            if agent_name == "claude":
                raise PermissionError("denied")
            return original_register_commands(self, agent_name, *args, **kwargs)

        monkeypatch.setattr(
            AgentRegistrar, "register_commands", fail_recovered_claude_registration
        )

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            ext_dir, "0.1.0", register_commands=True
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_commands"] == {}
        assert "speckit-early-ext-hello" in metadata["registered_skills"]
        assert "speckit-early-ext-world" in metadata["registered_skills"]


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

    def test_install_with_non_dict_init_options_does_not_crash(self, project_dir, extension_dir):
        """Corrupted init-options payloads should disable skill registration, not crash install."""
        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text("[]", encoding="utf-8")
        _create_skills_dir(project_dir, ai="claude")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        metadata = manager.registry.get(manifest.id)
        assert metadata["registered_skills"] == []

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
            yaml.safe_dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "plain.md").write_text(
            "# Plain Command\n\nBody without frontmatter.\n"
        )

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
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
        manager.install_from_directory(
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
        manager.install_from_directory(
            ext_dir_a, "0.1.0", register_commands=False
        )
        manager.install_from_directory(
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
            yaml.safe_dump(manifest_data, f)

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
        manager.install_from_directory(
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
