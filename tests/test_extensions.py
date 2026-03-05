"""
Unit tests for the extension system.

Tests cover:
- Extension manifest validation
- Extension registry operations
- Extension manager installation/removal
- Command registration
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from specify_cli.extensions import (
    ExtensionManifest,
    ExtensionRegistry,
    ExtensionManager,
    CommandRegistrar,
    ExtensionCatalog,
    ExtensionError,
    ValidationError,
    CompatibilityError,
    version_satisfies,
)


# ===== Fixtures =====

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def valid_manifest_data():
    """Valid extension manifest data."""
    return {
        "schema_version": "1.0",
        "extension": {
            "id": "test-ext",
            "name": "Test Extension",
            "version": "1.0.0",
            "description": "A test extension",
            "author": "Test Author",
            "repository": "https://github.com/test/test-ext",
            "license": "MIT",
        },
        "requires": {
            "speckit_version": ">=0.1.0",
            "commands": ["speckit.tasks"],
        },
        "provides": {
            "commands": [
                {
                    "name": "speckit.test.hello",
                    "file": "commands/hello.md",
                    "description": "Test command",
                }
            ]
        },
        "hooks": {
            "after_tasks": {
                "command": "speckit.test.hello",
                "optional": True,
                "prompt": "Run test?",
            }
        },
        "tags": ["testing", "example"],
    }


@pytest.fixture
def extension_dir(temp_dir, valid_manifest_data):
    """Create a complete extension directory structure."""
    ext_dir = temp_dir / "test-ext"
    ext_dir.mkdir()

    # Write manifest
    import yaml
    manifest_path = ext_dir / "extension.yml"
    with open(manifest_path, 'w') as f:
        yaml.dump(valid_manifest_data, f)

    # Create commands directory
    commands_dir = ext_dir / "commands"
    commands_dir.mkdir()

    # Write command file
    cmd_file = commands_dir / "hello.md"
    cmd_file.write_text("""---
description: "Test hello command"
---

# Test Hello Command

$ARGUMENTS
""")

    return ext_dir


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project directory."""
    proj_dir = temp_dir / "project"
    proj_dir.mkdir()

    # Create .specify directory
    specify_dir = proj_dir / ".specify"
    specify_dir.mkdir()

    return proj_dir


# ===== ExtensionManifest Tests =====

class TestExtensionManifest:
    """Test ExtensionManifest validation and parsing."""

    def test_valid_manifest(self, extension_dir):
        """Test loading a valid manifest."""
        manifest_path = extension_dir / "extension.yml"
        manifest = ExtensionManifest(manifest_path)

        assert manifest.id == "test-ext"
        assert manifest.name == "Test Extension"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test extension"
        assert len(manifest.commands) == 1
        assert manifest.commands[0]["name"] == "speckit.test.hello"

    def test_missing_required_field(self, temp_dir):
        """Test manifest missing required field."""
        import yaml

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump({"schema_version": "1.0"}, f)  # Missing 'extension'

        with pytest.raises(ValidationError, match="Missing required field"):
            ExtensionManifest(manifest_path)

    def test_invalid_extension_id(self, temp_dir, valid_manifest_data):
        """Test manifest with invalid extension ID format."""
        import yaml

        valid_manifest_data["extension"]["id"] = "Invalid_ID"  # Uppercase not allowed

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid extension ID"):
            ExtensionManifest(manifest_path)

    def test_invalid_version(self, temp_dir, valid_manifest_data):
        """Test manifest with invalid semantic version."""
        import yaml

        valid_manifest_data["extension"]["version"] = "invalid"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid version"):
            ExtensionManifest(manifest_path)

    def test_invalid_command_name(self, temp_dir, valid_manifest_data):
        """Test manifest with invalid command name format."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["name"] = "invalid-name"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid command name"):
            ExtensionManifest(manifest_path)

    def test_no_commands(self, temp_dir, valid_manifest_data):
        """Test manifest with no commands provided."""
        import yaml

        valid_manifest_data["provides"]["commands"] = []

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="must provide at least one command"):
            ExtensionManifest(manifest_path)

    def test_manifest_hash(self, extension_dir):
        """Test manifest hash calculation."""
        manifest_path = extension_dir / "extension.yml"
        manifest = ExtensionManifest(manifest_path)

        hash_value = manifest.get_hash()
        assert hash_value.startswith("sha256:")
        assert len(hash_value) > 10


# ===== ExtensionRegistry Tests =====

class TestExtensionRegistry:
    """Test ExtensionRegistry operations."""

    def test_empty_registry(self, temp_dir):
        """Test creating a new empty registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        assert registry.data["schema_version"] == "1.0"
        assert registry.data["extensions"] == {}
        assert len(registry.list()) == 0

    def test_add_extension(self, temp_dir):
        """Test adding an extension to registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        metadata = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
        }
        registry.add("test-ext", metadata)

        assert registry.is_installed("test-ext")
        ext_data = registry.get("test-ext")
        assert ext_data["version"] == "1.0.0"
        assert "installed_at" in ext_data

    def test_remove_extension(self, temp_dir):
        """Test removing an extension from registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0"})

        assert registry.is_installed("test-ext")

        registry.remove("test-ext")

        assert not registry.is_installed("test-ext")
        assert registry.get("test-ext") is None

    def test_registry_persistence(self, temp_dir):
        """Test that registry persists to disk."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        # Create registry and add extension
        registry1 = ExtensionRegistry(extensions_dir)
        registry1.add("test-ext", {"version": "1.0.0"})

        # Load new registry instance
        registry2 = ExtensionRegistry(extensions_dir)

        # Should still have the extension
        assert registry2.is_installed("test-ext")
        assert registry2.get("test-ext")["version"] == "1.0.0"


# ===== ExtensionManager Tests =====

class TestExtensionManager:
    """Test ExtensionManager installation and removal."""

    def test_check_compatibility_valid(self, extension_dir, project_dir):
        """Test compatibility check with valid version."""
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        # Should not raise
        result = manager.check_compatibility(manifest, "0.1.0")
        assert result is True

    def test_check_compatibility_invalid(self, extension_dir, project_dir):
        """Test compatibility check with invalid version."""
        manager = ExtensionManager(project_dir)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        # Requires >=0.1.0, but we have 0.0.1
        with pytest.raises(CompatibilityError, match="Extension requires spec-kit"):
            manager.check_compatibility(manifest, "0.0.1")

    def test_install_from_directory(self, extension_dir, project_dir):
        """Test installing extension from directory."""
        manager = ExtensionManager(project_dir)

        manifest = manager.install_from_directory(
            extension_dir,
            "0.1.0",
            register_commands=False  # Skip command registration for now
        )

        assert manifest.id == "test-ext"
        assert manager.registry.is_installed("test-ext")

        # Check extension directory was copied
        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        assert ext_dir.exists()
        assert (ext_dir / "extension.yml").exists()
        assert (ext_dir / "commands" / "hello.md").exists()

    def test_install_duplicate(self, extension_dir, project_dir):
        """Test installing already installed extension."""
        manager = ExtensionManager(project_dir)

        # Install once
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Try to install again
        with pytest.raises(ExtensionError, match="already installed"):
            manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

    def test_remove_extension(self, extension_dir, project_dir):
        """Test removing an installed extension."""
        manager = ExtensionManager(project_dir)

        # Install extension
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        assert ext_dir.exists()

        # Remove extension
        result = manager.remove("test-ext", keep_config=False)

        assert result is True
        assert not manager.registry.is_installed("test-ext")
        assert not ext_dir.exists()

    def test_remove_nonexistent(self, project_dir):
        """Test removing non-existent extension."""
        manager = ExtensionManager(project_dir)

        result = manager.remove("nonexistent")
        assert result is False

    def test_list_installed(self, extension_dir, project_dir):
        """Test listing installed extensions."""
        manager = ExtensionManager(project_dir)

        # Initially empty
        assert len(manager.list_installed()) == 0

        # Install extension
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Should have one extension
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-ext"
        assert installed[0]["name"] == "Test Extension"
        assert installed[0]["version"] == "1.0.0"
        assert installed[0]["command_count"] == 1
        assert installed[0]["hook_count"] == 1

    def test_config_backup_on_remove(self, extension_dir, project_dir):
        """Test that config files are backed up on removal."""
        manager = ExtensionManager(project_dir)

        # Install extension
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Create a config file
        ext_dir = project_dir / ".specify" / "extensions" / "test-ext"
        config_file = ext_dir / "test-ext-config.yml"
        config_file.write_text("test: config")

        # Remove extension (without keep_config)
        manager.remove("test-ext", keep_config=False)

        # Check backup was created (now in subdirectory per extension)
        backup_dir = project_dir / ".specify" / "extensions" / ".backup" / "test-ext"
        backup_file = backup_dir / "test-ext-config.yml"
        assert backup_file.exists()
        assert backup_file.read_text() == "test: config"


# ===== CommandRegistrar Tests =====

class TestCommandRegistrar:
    """Test CommandRegistrar command registration."""

    def test_parse_frontmatter_valid(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
description: "Test command"
tools:
  - tool1
  - tool2
---

# Command body
$ARGUMENTS
"""
        registrar = CommandRegistrar()
        frontmatter, body = registrar.parse_frontmatter(content)

        assert frontmatter["description"] == "Test command"
        assert frontmatter["tools"] == ["tool1", "tool2"]
        assert "Command body" in body
        assert "$ARGUMENTS" in body

    def test_parse_frontmatter_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "# Just a command\n$ARGUMENTS"

        registrar = CommandRegistrar()
        frontmatter, body = registrar.parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_render_frontmatter(self):
        """Test rendering frontmatter to YAML."""
        frontmatter = {
            "description": "Test command",
            "tools": ["tool1", "tool2"]
        }

        registrar = CommandRegistrar()
        output = registrar.render_frontmatter(frontmatter)

        assert output.startswith("---\n")
        assert output.endswith("---\n")
        assert "description: Test command" in output

    def test_register_commands_for_claude(self, extension_dir, project_dir):
        """Test registering commands for Claude agent."""
        # Create .claude directory
        claude_dir = project_dir / ".claude" / "commands"
        claude_dir.mkdir(parents=True)

        ExtensionManager(project_dir)  # Initialize manager (side effects only)
        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_claude(
            manifest,
            extension_dir,
            project_dir
        )

        assert len(registered) == 1
        assert "speckit.test.hello" in registered

        # Check command file was created
        cmd_file = claude_dir / "speckit.test.hello.md"
        assert cmd_file.exists()

        content = cmd_file.read_text()
        assert "description: Test hello command" in content
        assert "<!-- Extension: test-ext -->" in content
        assert "<!-- Config: .specify/extensions/test-ext/ -->" in content

    def test_command_with_aliases(self, project_dir, temp_dir):
        """Test registering a command with aliases."""
        import yaml

        # Create extension with command alias
        ext_dir = temp_dir / "ext-alias"
        ext_dir.mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-alias",
                "name": "Extension with Alias",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {
                "speckit_version": ">=0.1.0",
            },
            "provides": {
                "commands": [
                    {
                        "name": "speckit.alias.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.shortcut"],
                    }
                ]
            },
        }

        with open(ext_dir / "extension.yml", 'w') as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nTest")

        claude_dir = project_dir / ".claude" / "commands"
        claude_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_claude(manifest, ext_dir, project_dir)

        assert len(registered) == 2
        assert "speckit.alias.cmd" in registered
        assert "speckit.shortcut" in registered
        assert (claude_dir / "speckit.alias.cmd.md").exists()
        assert (claude_dir / "speckit.shortcut.md").exists()


# ===== Utility Function Tests =====

class TestVersionSatisfies:
    """Test version_satisfies utility function."""

    def test_version_satisfies_simple(self):
        """Test simple version comparison."""
        assert version_satisfies("1.0.0", ">=1.0.0")
        assert version_satisfies("1.0.1", ">=1.0.0")
        assert not version_satisfies("0.9.9", ">=1.0.0")

    def test_version_satisfies_range(self):
        """Test version range."""
        assert version_satisfies("1.5.0", ">=1.0.0,<2.0.0")
        assert not version_satisfies("2.0.0", ">=1.0.0,<2.0.0")
        assert not version_satisfies("0.9.0", ">=1.0.0,<2.0.0")

    def test_version_satisfies_complex(self):
        """Test complex version specifier."""
        assert version_satisfies("1.0.5", ">=1.0.0,!=1.0.3")
        assert not version_satisfies("1.0.3", ">=1.0.0,!=1.0.3")

    def test_version_satisfies_invalid(self):
        """Test invalid version strings."""
        assert not version_satisfies("invalid", ">=1.0.0")
        assert not version_satisfies("1.0.0", "invalid specifier")


# ===== Integration Tests =====

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_install_and_remove_workflow(self, extension_dir, project_dir):
        """Test complete installation and removal workflow."""
        # Create Claude directory
        (project_dir / ".claude" / "commands").mkdir(parents=True)

        manager = ExtensionManager(project_dir)

        # Install
        manager.install_from_directory(
            extension_dir,
            "0.1.0",
            register_commands=True
        )

        # Verify installation
        assert manager.registry.is_installed("test-ext")
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-ext"

        # Verify command registered
        cmd_file = project_dir / ".claude" / "commands" / "speckit.test.hello.md"
        assert cmd_file.exists()

        # Verify registry has registered commands (now a dict keyed by agent)
        metadata = manager.registry.get("test-ext")
        registered_commands = metadata["registered_commands"]
        # Check that the command is registered for at least one agent
        assert any(
            "speckit.test.hello" in cmds
            for cmds in registered_commands.values()
        )

        # Remove
        result = manager.remove("test-ext")
        assert result is True

        # Verify removal
        assert not manager.registry.is_installed("test-ext")
        assert not cmd_file.exists()
        assert len(manager.list_installed()) == 0

    def test_multiple_extensions(self, temp_dir, project_dir):
        """Test installing multiple extensions."""
        import yaml

        # Create two extensions
        for i in range(1, 3):
            ext_dir = temp_dir / f"ext{i}"
            ext_dir.mkdir()

            manifest_data = {
                "schema_version": "1.0",
                "extension": {
                    "id": f"ext{i}",
                    "name": f"Extension {i}",
                    "version": "1.0.0",
                    "description": f"Extension {i}",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "commands": [
                        {
                            "name": f"speckit.ext{i}.cmd",
                            "file": "commands/cmd.md",
                        }
                    ]
                },
            }

            with open(ext_dir / "extension.yml", 'w') as f:
                yaml.dump(manifest_data, f)

            (ext_dir / "commands").mkdir()
            (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\nTest")

        manager = ExtensionManager(project_dir)

        # Install both
        manager.install_from_directory(temp_dir / "ext1", "0.1.0", register_commands=False)
        manager.install_from_directory(temp_dir / "ext2", "0.1.0", register_commands=False)

        # Verify both installed
        installed = manager.list_installed()
        assert len(installed) == 2
        assert {ext["id"] for ext in installed} == {"ext1", "ext2"}

        # Remove first
        manager.remove("ext1")

        # Verify only second remains
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "ext2"


# ===== Extension Catalog Tests =====


class TestExtensionCatalog:
    """Test extension catalog functionality."""

    def test_catalog_initialization(self, temp_dir):
        """Test catalog initialization."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        assert catalog.project_root == project_dir
        assert catalog.cache_dir == project_dir / ".specify" / "extensions" / ".cache"

    def test_cache_directory_creation(self, temp_dir):
        """Test catalog cache directory is created when fetching."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog data
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "test-ext": {
                    "name": "Test Extension",
                    "id": "test-ext",
                    "version": "1.0.0",
                    "description": "Test",
                }
            },
        }

        # Manually save to cache to test cache reading
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com/catalog.json",
                }
            )
        )

        # Should use cache
        result = catalog.fetch_catalog()
        assert result == catalog_data

    def test_cache_expiration(self, temp_dir):
        """Test that expired cache is not used."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create expired cache
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog_data = {"schema_version": "1.0", "extensions": {}}
        catalog.cache_file.write_text(json.dumps(catalog_data))

        # Set cache time to 2 hours ago (expired)
        expired_time = datetime.now(timezone.utc).timestamp() - 7200
        expired_datetime = datetime.fromtimestamp(expired_time, tz=timezone.utc)
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": expired_datetime.isoformat(),
                    "catalog_url": "http://test.com/catalog.json",
                }
            )
        )

        # Cache should be invalid
        assert not catalog.is_cache_valid()

    def test_search_all_extensions(self, temp_dir):
        """Test searching all extensions without filters."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                    "author": "Stats Perform",
                    "tags": ["issue-tracking", "jira"],
                    "verified": True,
                },
                "linear": {
                    "name": "Linear Integration",
                    "id": "linear",
                    "version": "0.9.0",
                    "description": "Linear integration",
                    "author": "Community",
                    "tags": ["issue-tracking"],
                    "verified": False,
                },
            },
        }

        # Save to cache
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search without filters
        results = catalog.search()
        assert len(results) == 2

    def test_search_by_query(self, temp_dir):
        """Test searching by query text."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira issue tracking",
                    "tags": ["jira"],
                },
                "linear": {
                    "name": "Linear Integration",
                    "id": "linear",
                    "version": "1.0.0",
                    "description": "Linear project management",
                    "tags": ["linear"],
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search for "jira"
        results = catalog.search(query="jira")
        assert len(results) == 1
        assert results[0]["id"] == "jira"

    def test_search_by_tag(self, temp_dir):
        """Test searching by tag."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira",
                    "tags": ["issue-tracking", "jira"],
                },
                "linear": {
                    "name": "Linear",
                    "id": "linear",
                    "version": "1.0.0",
                    "description": "Linear",
                    "tags": ["issue-tracking", "linear"],
                },
                "github": {
                    "name": "GitHub",
                    "id": "github",
                    "version": "1.0.0",
                    "description": "GitHub",
                    "tags": ["vcs", "github"],
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search by tag "issue-tracking"
        results = catalog.search(tag="issue-tracking")
        assert len(results) == 2
        assert {r["id"] for r in results} == {"jira", "linear"}

    def test_search_verified_only(self, temp_dir):
        """Test searching verified extensions only."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira",
                    "verified": True,
                },
                "linear": {
                    "name": "Linear",
                    "id": "linear",
                    "version": "1.0.0",
                    "description": "Linear",
                    "verified": False,
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Search verified only
        results = catalog.search(verified_only=True)
        assert len(results) == 1
        assert results[0]["id"] == "jira"

    def test_get_extension_info(self, temp_dir):
        """Test getting specific extension info."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create mock catalog
        catalog_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                    "author": "Stats Perform",
                },
            },
        }

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": "http://test.com",
                }
            )
        )

        # Get extension info
        info = catalog.get_extension_info("jira")
        assert info is not None
        assert info["id"] == "jira"
        assert info["name"] == "Jira Integration"

        # Non-existent extension
        info = catalog.get_extension_info("nonexistent")
        assert info is None

    def test_clear_cache(self, temp_dir):
        """Test clearing catalog cache."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        catalog = ExtensionCatalog(project_dir)

        # Create cache
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}")
        catalog.cache_metadata_file.write_text("{}")

        assert catalog.cache_file.exists()
        assert catalog.cache_metadata_file.exists()

        # Clear cache
        catalog.clear_cache()

        assert not catalog.cache_file.exists()
        assert not catalog.cache_metadata_file.exists()
