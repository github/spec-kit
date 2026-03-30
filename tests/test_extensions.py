"""
Unit tests for the extension system.

Tests cover:
- Extension manifest validation
- Extension registry operations
- Extension manager installation/removal
- Command registration
- Catalog stack (multi-catalog support)
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from tests.conftest import strip_ansi
from specify_cli.extensions import (
    CatalogEntry,
    CORE_COMMAND_NAMES,
    ExtensionManifest,
    ExtensionRegistry,
    ExtensionManager,
    CommandRegistrar,
    HookExecutor,
    ExtensionCatalog,
    ExtensionError,
    ValidationError,
    CompatibilityError,
    normalize_priority,
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
                    "name": "speckit.test-ext.hello",
                    "file": "commands/hello.md",
                    "description": "Test command",
                }
            ]
        },
        "hooks": {
            "after_tasks": {
                "command": "speckit.test-ext.hello",
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


# ===== normalize_priority Tests =====

class TestNormalizePriority:
    """Test normalize_priority helper function."""

    def test_valid_integer(self):
        """Test with valid integer priority."""
        assert normalize_priority(5) == 5
        assert normalize_priority(1) == 1
        assert normalize_priority(100) == 100

    def test_valid_string_number(self):
        """Test with string that can be converted to int."""
        assert normalize_priority("5") == 5
        assert normalize_priority("10") == 10

    def test_zero_returns_default(self):
        """Test that zero priority returns default."""
        assert normalize_priority(0) == 10
        assert normalize_priority(0, default=5) == 5

    def test_negative_returns_default(self):
        """Test that negative priority returns default."""
        assert normalize_priority(-1) == 10
        assert normalize_priority(-100, default=5) == 5

    def test_none_returns_default(self):
        """Test that None returns default."""
        assert normalize_priority(None) == 10
        assert normalize_priority(None, default=5) == 5

    def test_invalid_string_returns_default(self):
        """Test that non-numeric string returns default."""
        assert normalize_priority("invalid") == 10
        assert normalize_priority("abc", default=5) == 5

    def test_float_truncates(self):
        """Test that float is truncated to int."""
        assert normalize_priority(5.9) == 5
        assert normalize_priority(3.1) == 3

    def test_empty_string_returns_default(self):
        """Test that empty string returns default."""
        assert normalize_priority("") == 10

    def test_custom_default(self):
        """Test custom default value."""
        assert normalize_priority(None, default=20) == 20
        assert normalize_priority("invalid", default=1) == 1


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
        assert manifest.commands[0]["name"] == "speckit.test-ext.hello"

    def test_core_command_names_match_bundled_templates(self):
        """Core command reservations should stay aligned with bundled templates."""
        commands_dir = Path(__file__).resolve().parent.parent / "templates" / "commands"
        expected = {
            command_file.stem
            for command_file in commands_dir.iterdir()
            if command_file.is_file() and command_file.suffix == ".md"
        }

        assert CORE_COMMAND_NAMES == expected

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
        """Test manifest with command name that cannot be auto-corrected raises ValidationError."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["name"] = "invalid-name"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        with pytest.raises(ValidationError, match="Invalid command name"):
            ExtensionManifest(manifest_path)

    def test_command_name_autocorrect_speckit_prefix(self, temp_dir, valid_manifest_data):
        """Test that 'speckit.command' is auto-corrected to 'speckit.{ext_id}.command'."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["name"] = "speckit.hello"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.commands[0]["name"] == "speckit.test-ext.hello"
        assert len(manifest.warnings) == 1
        assert "speckit.hello" in manifest.warnings[0]
        assert "speckit.test-ext.hello" in manifest.warnings[0]

    def test_command_name_autocorrect_no_speckit_prefix(self, temp_dir, valid_manifest_data):
        """Test that 'extension.command' is auto-corrected to 'speckit.extension.command'."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["name"] = "docguard.guard"

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.commands[0]["name"] == "speckit.docguard.guard"
        assert len(manifest.warnings) == 1
        assert "docguard.guard" in manifest.warnings[0]
        assert "speckit.docguard.guard" in manifest.warnings[0]

    def test_alias_autocorrect_speckit_prefix(self, temp_dir, valid_manifest_data):
        """Test that a legacy 'speckit.command' alias is auto-corrected."""
        import yaml

        valid_manifest_data["provides"]["commands"][0]["aliases"] = ["speckit.hello"]

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.commands[0]["aliases"] == ["speckit.test-ext.hello"]
        assert len(manifest.warnings) == 1
        assert "speckit.hello" in manifest.warnings[0]
        assert "speckit.test-ext.hello" in manifest.warnings[0]

    def test_valid_command_name_has_no_warnings(self, temp_dir, valid_manifest_data):
        """Test that a correctly-named command produces no warnings."""
        import yaml

        manifest_path = temp_dir / "extension.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_manifest_data, f)

        manifest = ExtensionManifest(manifest_path)

        assert manifest.warnings == []

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

    def test_update_preserves_installed_at(self, temp_dir):
        """Test that update() preserves the original installed_at timestamp."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0", "enabled": True})

        # Get original installed_at
        original_data = registry.get("test-ext")
        original_installed_at = original_data["installed_at"]

        # Update with new metadata
        registry.update("test-ext", {"version": "2.0.0", "enabled": False})

        # Verify installed_at is preserved
        updated_data = registry.get("test-ext")
        assert updated_data["installed_at"] == original_installed_at
        assert updated_data["version"] == "2.0.0"
        assert updated_data["enabled"] is False

    def test_update_merges_with_existing(self, temp_dir):
        """Test that update() merges new metadata with existing fields."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {
            "version": "1.0.0",
            "enabled": True,
            "registered_commands": {"claude": ["cmd1", "cmd2"]},
        })

        # Update with partial metadata (only enabled field)
        registry.update("test-ext", {"enabled": False})

        # Verify existing fields are preserved
        updated_data = registry.get("test-ext")
        assert updated_data["enabled"] is False
        assert updated_data["version"] == "1.0.0"  # Preserved
        assert updated_data["registered_commands"] == {"claude": ["cmd1", "cmd2"]}  # Preserved

    def test_update_raises_for_missing_extension(self, temp_dir):
        """Test that update() raises KeyError for non-installed extension."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        with pytest.raises(KeyError, match="not installed"):
            registry.update("nonexistent-ext", {"enabled": False})

    def test_restore_overwrites_completely(self, temp_dir):
        """Test that restore() overwrites the registry entry completely."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "2.0.0", "enabled": True})

        # Restore with complete backup data
        backup_data = {
            "version": "1.0.0",
            "enabled": False,
            "installed_at": "2024-01-01T00:00:00+00:00",
            "registered_commands": {"claude": ["old-cmd"]},
        }
        registry.restore("test-ext", backup_data)

        # Verify entry is exactly as restored
        restored_data = registry.get("test-ext")
        assert restored_data == backup_data

    def test_restore_can_recreate_removed_entry(self, temp_dir):
        """Test that restore() can recreate an entry after remove()."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0"})

        # Save backup and remove
        backup = registry.get("test-ext").copy()
        registry.remove("test-ext")
        assert not registry.is_installed("test-ext")

        # Restore should recreate the entry
        registry.restore("test-ext", backup)
        assert registry.is_installed("test-ext")
        assert registry.get("test-ext")["version"] == "1.0.0"

    def test_restore_rejects_none_metadata(self, temp_dir):
        """Test restore() raises ValueError for None metadata."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-ext", None)

    def test_restore_rejects_non_dict_metadata(self, temp_dir):
        """Test restore() raises ValueError for non-dict metadata."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-ext", "not-a-dict")

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-ext", ["list", "not", "dict"])

    def test_restore_uses_deep_copy(self, temp_dir):
        """Test restore() deep copies metadata to prevent mutation."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        original_metadata = {
            "version": "1.0.0",
            "nested": {"key": "original"},
        }
        registry.restore("test-ext", original_metadata)

        # Mutate the original metadata after restore
        original_metadata["version"] = "MUTATED"
        original_metadata["nested"]["key"] = "MUTATED"

        # Registry should have the original values
        stored = registry.get("test-ext")
        assert stored["version"] == "1.0.0"
        assert stored["nested"]["key"] == "original"

    def test_get_returns_deep_copy(self, temp_dir):
        """Test that get() returns deep copies for nested structures."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        metadata = {
            "version": "1.0.0",
            "registered_commands": {"claude": ["cmd1"]},
        }
        registry.add("test-ext", metadata)

        fetched = registry.get("test-ext")
        fetched["registered_commands"]["claude"].append("cmd2")

        # Internal registry must remain unchanged.
        internal = registry.data["extensions"]["test-ext"]
        assert internal["registered_commands"] == {"claude": ["cmd1"]}

    def test_get_returns_none_for_corrupted_entry(self, temp_dir):
        """Test that get() returns None for corrupted (non-dict) entries."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        # Directly corrupt the registry with non-dict entries
        registry.data["extensions"]["corrupted-string"] = "not a dict"
        registry.data["extensions"]["corrupted-list"] = ["not", "a", "dict"]
        registry.data["extensions"]["corrupted-int"] = 42
        registry._save()

        # All corrupted entries should return None
        assert registry.get("corrupted-string") is None
        assert registry.get("corrupted-list") is None
        assert registry.get("corrupted-int") is None
        # Non-existent should also return None
        assert registry.get("nonexistent") is None

    def test_list_returns_deep_copy(self, temp_dir):
        """Test that list() returns deep copies for nested structures."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        metadata = {
            "version": "1.0.0",
            "registered_commands": {"claude": ["cmd1"]},
        }
        registry.add("test-ext", metadata)

        listed = registry.list()
        listed["test-ext"]["registered_commands"]["claude"].append("cmd2")

        # Internal registry must remain unchanged.
        internal = registry.data["extensions"]["test-ext"]
        assert internal["registered_commands"] == {"claude": ["cmd1"]}

    def test_list_returns_empty_dict_for_corrupted_registry(self, temp_dir):
        """Test that list() returns empty dict when extensions is not a dict."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()
        registry = ExtensionRegistry(extensions_dir)

        # Corrupt the registry - extensions is a list instead of dict
        registry.data["extensions"] = ["not", "a", "dict"]
        registry._save()

        # list() should return empty dict, not crash
        result = registry.list()
        assert result == {}


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

    def test_install_rejects_extension_id_in_core_namespace(self, temp_dir, project_dir):
        """Install should reject extension IDs that shadow core commands."""
        import yaml

        ext_dir = temp_dir / "analyze-ext"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "analyze",
                "name": "Analyze Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.analyze.extra",
                        "file": "commands/cmd.md",
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest_data))
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        with pytest.raises(ValidationError, match="conflicts with core command namespace"):
            manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

    def test_install_autocorrects_alias_without_extension_namespace(self, temp_dir, project_dir):
        """Legacy short aliases are auto-corrected to 'speckit.{ext_id}.{cmd}' with a warning."""
        import yaml

        ext_dir = temp_dir / "alias-shortcut"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "alias-shortcut",
                "name": "Alias Shortcut",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.alias-shortcut.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.shortcut"],
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest_data))
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        manifest = manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        assert manifest.commands[0]["aliases"] == ["speckit.alias-shortcut.shortcut"]
        assert len(manifest.warnings) == 1
        assert "speckit.shortcut" in manifest.warnings[0]
        assert "speckit.alias-shortcut.shortcut" in manifest.warnings[0]

    def test_install_rejects_namespace_squatting(self, temp_dir, project_dir):
        """Install should reject commands and aliases outside the extension namespace."""
        import yaml

        ext_dir = temp_dir / "squat-ext"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "squat-ext",
                "name": "Squat Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.other-ext.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.squat-ext.ok"],
                    }
                ]
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest_data))
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        with pytest.raises(ValidationError, match="must use extension namespace 'squat-ext'"):
            manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

    def test_install_rejects_command_collision_with_installed_extension(self, temp_dir, project_dir):
        """Install should reject names already claimed by an installed legacy extension."""
        import yaml

        first_dir = temp_dir / "ext-one"
        first_dir.mkdir()
        (first_dir / "commands").mkdir()
        first_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-one",
                "name": "Extension One",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-one.sync",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.shared.sync"],
                    }
                ]
            },
        }
        (first_dir / "extension.yml").write_text(yaml.dump(first_manifest))
        (first_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")
        installed_ext_dir = project_dir / ".specify" / "extensions" / "ext-one"
        installed_ext_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(first_dir, installed_ext_dir)

        second_dir = temp_dir / "ext-two"
        second_dir.mkdir()
        (second_dir / "commands").mkdir()
        second_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "shared",
                "name": "Shared Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.shared.sync",
                        "file": "commands/cmd.md",
                    }
                ]
            },
        }
        (second_dir / "extension.yml").write_text(yaml.dump(second_manifest))
        (second_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nBody")

        manager = ExtensionManager(project_dir)
        manager.registry.add("ext-one", {"version": "1.0.0", "source": "local"})

        with pytest.raises(ValidationError, match="already provided by extension 'ext-one'"):
            manager.install_from_directory(second_dir, "0.1.0", register_commands=False)

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

    def test_kiro_cli_agent_config_present(self):
        """Kiro CLI should be mapped to .kiro/prompts and legacy q removed."""
        assert "kiro-cli" in CommandRegistrar.AGENT_CONFIGS
        assert CommandRegistrar.AGENT_CONFIGS["kiro-cli"]["dir"] == ".kiro/prompts"
        assert "q" not in CommandRegistrar.AGENT_CONFIGS

    def test_codex_agent_config_present(self):
        """Codex should be mapped to .agents/skills."""
        assert "codex" in CommandRegistrar.AGENT_CONFIGS
        assert CommandRegistrar.AGENT_CONFIGS["codex"]["dir"] == ".agents/skills"
        assert CommandRegistrar.AGENT_CONFIGS["codex"]["extension"] == "/SKILL.md"

    def test_pi_agent_config_present(self):
        """Pi should be mapped to .pi/prompts."""
        assert "pi" in CommandRegistrar.AGENT_CONFIGS
        cfg = CommandRegistrar.AGENT_CONFIGS["pi"]
        assert cfg["dir"] == ".pi/prompts"
        assert cfg["format"] == "markdown"
        assert cfg["args"] == "$ARGUMENTS"
        assert cfg["extension"] == ".md"

    def test_qwen_agent_config_is_markdown(self):
        """Qwen should use Markdown format with $ARGUMENTS (not TOML)."""
        assert "qwen" in CommandRegistrar.AGENT_CONFIGS
        cfg = CommandRegistrar.AGENT_CONFIGS["qwen"]
        assert cfg["dir"] == ".qwen/commands"
        assert cfg["format"] == "markdown"
        assert cfg["args"] == "$ARGUMENTS"
        assert cfg["extension"] == ".md"

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

    def test_parse_frontmatter_non_mapping_returns_empty_dict(self):
        """Non-mapping YAML frontmatter should not crash downstream renderers."""
        content = """---
- item1
- item2
---

# Command body
"""
        registrar = CommandRegistrar()
        frontmatter, body = registrar.parse_frontmatter(content)

        assert frontmatter == {}
        assert "Command body" in body

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

    def test_render_frontmatter_unicode(self):
        """Test rendering frontmatter preserves non-ASCII characters."""
        frontmatter = {
            "description": "Prüfe Konformität der Implementierung"
        }

        registrar = CommandRegistrar()
        output = registrar.render_frontmatter(frontmatter)

        assert "Prüfe Konformität" in output
        assert "\\u" not in output

    def test_adjust_script_paths_does_not_mutate_input(self):
        """Path adjustments should not mutate caller-owned frontmatter dicts."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        original = {
            "scripts": {
                "sh": "../../scripts/bash/setup-plan.sh {ARGS}",
                "ps": "../../scripts/powershell/setup-plan.ps1 {ARGS}",
            }
        }
        before = json.loads(json.dumps(original))

        adjusted = registrar._adjust_script_paths(original)

        assert original == before
        assert adjusted["scripts"]["sh"] == ".specify/scripts/bash/setup-plan.sh {ARGS}"
        assert adjusted["scripts"]["ps"] == ".specify/scripts/powershell/setup-plan.ps1 {ARGS}"

    def test_adjust_script_paths_preserves_extension_local_paths(self):
        """Extension-local script paths should not be rewritten into .specify/.specify."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        original = {
            "scripts": {
                "sh": ".specify/extensions/test-ext/scripts/setup.sh {ARGS}",
                "ps": "scripts/powershell/setup-plan.ps1 {ARGS}",
            }
        }

        adjusted = registrar._adjust_script_paths(original)

        assert adjusted["scripts"]["sh"] == ".specify/extensions/test-ext/scripts/setup.sh {ARGS}"
        assert adjusted["scripts"]["ps"] == ".specify/scripts/powershell/setup-plan.ps1 {ARGS}"

    def test_rewrite_project_relative_paths_preserves_extension_local_body_paths(self):
        """Body rewrites should preserve extension-local assets while fixing top-level refs."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar

        body = (
            "Read `.specify/extensions/test-ext/templates/spec.md`\n"
            "Run scripts/bash/setup-plan.sh\n"
        )

        rewritten = AgentCommandRegistrar.rewrite_project_relative_paths(body)

        assert ".specify/extensions/test-ext/templates/spec.md" in rewritten
        assert ".specify/scripts/bash/setup-plan.sh" in rewritten

    def test_render_toml_command_handles_embedded_triple_double_quotes(self):
        """TOML renderer should stay valid when body includes triple double-quotes."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        output = registrar.render_toml_command(
            {"description": "x"},
            'line1\n"""danger"""\nline2',
            "extension:test-ext",
        )

        assert "prompt = '''" in output
        assert '"""danger"""' in output

    def test_render_toml_command_escapes_when_both_triple_quote_styles_exist(self):
        """If body has both triple quote styles, fall back to escaped basic string."""
        from specify_cli.agents import CommandRegistrar as AgentCommandRegistrar
        registrar = AgentCommandRegistrar()
        output = registrar.render_toml_command(
            {"description": "x"},
            'a """ b\nc \'\'\' d',
            "extension:test-ext",
        )

        assert 'prompt = "' in output
        assert "\\n" in output
        assert "\\\"\\\"\\\"" in output

    def test_register_commands_for_claude(self, extension_dir, project_dir):
        """Test registering commands for Claude agent."""
        # Create .claude directory
        claude_dir = project_dir / ".claude" / "skills"
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
        assert "speckit.test-ext.hello" in registered

        # Check command file was created
        cmd_file = claude_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert cmd_file.exists()

        content = cmd_file.read_text()
        assert "description: Test hello command" in content
        assert "test-ext" in content

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
                        "name": "speckit.ext-alias.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.ext-alias.shortcut"],
                    }
                ]
            },
        }

        with open(ext_dir / "extension.yml", 'w') as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Test\n---\n\nTest")

        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_claude(manifest, ext_dir, project_dir)

        assert len(registered) == 2
        assert "speckit.ext-alias.cmd" in registered
        assert "speckit.ext-alias.shortcut" in registered
        assert (claude_dir / "speckit-ext-alias-cmd" / "SKILL.md").exists()
        assert (claude_dir / "speckit-ext-alias-shortcut" / "SKILL.md").exists()

    def test_unregister_commands_for_codex_skills_uses_mapped_names(self, project_dir):
        """Codex skill cleanup should use the same mapped names as registration."""
        skills_dir = project_dir / ".agents" / "skills"
        (skills_dir / "speckit-specify").mkdir(parents=True)
        (skills_dir / "speckit-specify" / "SKILL.md").write_text("body")
        (skills_dir / "speckit-shortcut").mkdir(parents=True)
        (skills_dir / "speckit-shortcut" / "SKILL.md").write_text("body")

        registrar = CommandRegistrar()
        registrar.unregister_commands(
            {"codex": ["speckit.specify", "speckit.shortcut"]},
            project_dir,
        )

        assert not (skills_dir / "speckit-specify" / "SKILL.md").exists()
        assert not (skills_dir / "speckit-shortcut" / "SKILL.md").exists()

    def test_register_commands_for_all_agents_distinguishes_codex_from_amp(self, extension_dir, project_dir):
        """A Codex project under .agents/skills should not implicitly activate Amp."""
        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_all_agents(manifest, extension_dir, project_dir)

        assert "codex" in registered
        assert "amp" not in registered
        assert not (project_dir / ".agents" / "commands").exists()

    def test_codex_skill_registration_writes_skill_frontmatter(self, extension_dir, project_dir):
        """Codex SKILL.md output should use skills-oriented frontmatter."""
        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, extension_dir, project_dir)

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "name: speckit-test-ext-hello" in content
        assert "description: Test hello command" in content
        assert "compatibility:" in content
        assert "metadata:" in content
        assert "source: test-ext:commands/hello.md" in content
        assert "<!-- Extension:" not in content

    def test_codex_skill_registration_resolves_script_placeholders(self, project_dir, temp_dir):
        """Codex SKILL.md overrides should resolve script placeholders."""
        import yaml

        ext_dir = temp_dir / "ext-scripted"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-scripted",
                "name": "Scripted Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-scripted.plan",
                        "file": "commands/plan.md",
                        "description": "Scripted command",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "Scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
  ps: ../../scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: ../../scripts/bash/update-agent-context.sh __AGENT__
  ps: ../../scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

Run {SCRIPT}
Then {AGENT_SCRIPT}
Agent __AGENT__
"""
        )

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text('{"ai":"codex","ai_skills":true,"script":"sh"}')

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        skill_file = skills_dir / "speckit-ext-scripted-plan" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "{SCRIPT}" not in content
        assert "{AGENT_SCRIPT}" not in content
        assert "__AGENT__" not in content
        assert "{ARGS}" not in content
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content
        assert ".specify/scripts/bash/update-agent-context.sh codex" in content

    def test_codex_skill_alias_frontmatter_matches_alias_name(self, project_dir, temp_dir):
        """Codex alias skills should render their own matching `name:` frontmatter."""
        import yaml

        ext_dir = temp_dir / "ext-alias-skill"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-alias-skill",
                "name": "Alias Skill Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-alias-skill.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.ext-alias-skill.shortcut"],
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "cmd.md").write_text("---\ndescription: Alias skill\n---\n\nBody\n")

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        primary = skills_dir / "speckit-ext-alias-skill-cmd" / "SKILL.md"
        alias = skills_dir / "speckit-ext-alias-skill-shortcut" / "SKILL.md"

        assert primary.exists()
        assert alias.exists()
        assert "name: speckit-ext-alias-skill-cmd" in primary.read_text()
        assert "name: speckit-ext-alias-skill-shortcut" in alias.read_text()

    def test_codex_skill_registration_uses_fallback_script_variant_without_init_options(
        self, project_dir, temp_dir
    ):
        """Codex placeholder substitution should still work without init-options.json."""
        import yaml

        ext_dir = temp_dir / "ext-script-fallback"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-script-fallback",
                "name": "Script fallback",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-script-fallback.plan",
                        "file": "commands/plan.md",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "Fallback scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
  ps: ../../scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: ../../scripts/bash/update-agent-context.sh __AGENT__
---

Run {SCRIPT}
Then {AGENT_SCRIPT}
"""
        )

        # Intentionally do NOT create .specify/init-options.json
        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        skill_file = skills_dir / "speckit-ext-script-fallback-plan" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "{SCRIPT}" not in content
        assert "{AGENT_SCRIPT}" not in content
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content
        assert ".specify/scripts/bash/update-agent-context.sh codex" in content

    def test_codex_skill_registration_handles_non_dict_init_options(
        self, project_dir, temp_dir
    ):
        """Non-dict init-options payloads should not crash skill placeholder resolution."""
        import yaml

        ext_dir = temp_dir / "ext-script-list-init"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-script-list-init",
                "name": "List init options",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-script-list-init.plan",
                        "file": "commands/plan.md",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "List init scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
---

Run {SCRIPT}
"""
        )

        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text("[]")

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        content = (skills_dir / "speckit-ext-script-list-init-plan" / "SKILL.md").read_text()
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content

    def test_codex_skill_registration_fallback_prefers_powershell_on_windows(
        self, project_dir, temp_dir, monkeypatch
    ):
        """Without init metadata, Windows fallback should prefer ps scripts over sh."""
        import yaml

        monkeypatch.setattr("specify_cli.agents.platform.system", lambda: "Windows")

        ext_dir = temp_dir / "ext-script-windows-fallback"
        ext_dir.mkdir()
        (ext_dir / "commands").mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-script-windows-fallback",
                "name": "Script fallback windows",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-script-windows-fallback.plan",
                        "file": "commands/plan.md",
                    }
                ]
            },
        }
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands" / "plan.md").write_text(
            """---
description: "Windows fallback scripted command"
scripts:
  sh: ../../scripts/bash/setup-plan.sh --json "{ARGS}"
  ps: ../../scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: ../../scripts/bash/update-agent-context.sh __AGENT__
  ps: ../../scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

Run {SCRIPT}
Then {AGENT_SCRIPT}
"""
        )

        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, ext_dir, project_dir)

        skill_file = skills_dir / "speckit-ext-script-windows-fallback-plan" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert ".specify/scripts/powershell/setup-plan.ps1 -Json" in content
        assert ".specify/scripts/powershell/update-agent-context.ps1 -AgentType codex" in content
        assert ".specify/scripts/bash/setup-plan.sh" not in content

    def test_register_commands_for_copilot(self, extension_dir, project_dir):
        """Test registering commands for Copilot agent with .agent.md extension."""
        # Create .github/agents directory (Copilot project)
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_agent(
            "copilot", manifest, extension_dir, project_dir
        )

        assert len(registered) == 1
        assert "speckit.test-ext.hello" in registered

        # Verify command file uses .agent.md extension
        cmd_file = agents_dir / "speckit.test-ext.hello.agent.md"
        assert cmd_file.exists()

        # Verify NO plain .md file was created
        plain_md_file = agents_dir / "speckit.test-ext.hello.md"
        assert not plain_md_file.exists()

        content = cmd_file.read_text()
        assert "description: Test hello command" in content
        assert "test-ext" in content

    def test_copilot_companion_prompt_created(self, extension_dir, project_dir):
        """Test that companion .prompt.md files are created in .github/prompts/."""
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "copilot", manifest, extension_dir, project_dir
        )

        # Verify companion .prompt.md file exists
        prompt_file = project_dir / ".github" / "prompts" / "speckit.test-ext.hello.prompt.md"
        assert prompt_file.exists()

        # Verify content has correct agent frontmatter
        content = prompt_file.read_text()
        assert content == "---\nagent: speckit.test-ext.hello\n---\n"

    def test_copilot_aliases_get_companion_prompts(self, project_dir, temp_dir):
        """Test that aliases also get companion .prompt.md files for Copilot."""
        import yaml

        ext_dir = temp_dir / "ext-alias-copilot"
        ext_dir.mkdir()

        manifest_data = {
            "schema_version": "1.0",
            "extension": {
                "id": "ext-alias-copilot",
                "name": "Extension with Alias",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.ext-alias-copilot.cmd",
                        "file": "commands/cmd.md",
                        "aliases": ["speckit.ext-alias-copilot.shortcut"],
                    }
                ]
            },
        }

        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(manifest_data, f)

        (ext_dir / "commands").mkdir()
        (ext_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Test\n---\n\nTest"
        )

        # Set up Copilot project
        (project_dir / ".github" / "agents").mkdir(parents=True)

        manifest = ExtensionManifest(ext_dir / "extension.yml")
        registrar = CommandRegistrar()
        registered = registrar.register_commands_for_agent(
            "copilot", manifest, ext_dir, project_dir
        )

        assert len(registered) == 2

        # Both primary and alias get companion .prompt.md
        prompts_dir = project_dir / ".github" / "prompts"
        assert (prompts_dir / "speckit.ext-alias-copilot.cmd.prompt.md").exists()
        assert (prompts_dir / "speckit.ext-alias-copilot.shortcut.prompt.md").exists()

    def test_non_copilot_agent_no_companion_file(self, extension_dir, project_dir):
        """Test that non-copilot agents do NOT create .prompt.md files."""
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")

        registrar = CommandRegistrar()
        registrar.register_commands_for_agent(
            "claude", manifest, extension_dir, project_dir
        )

        # No .github/prompts directory should exist
        prompts_dir = project_dir / ".github" / "prompts"
        assert not prompts_dir.exists()


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
        (project_dir / ".claude" / "skills").mkdir(parents=True)

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
        cmd_file = project_dir / ".claude" / "skills" / "speckit-test-ext-hello" / "SKILL.md"
        assert cmd_file.exists()

        # Verify registry has registered commands (now a dict keyed by agent)
        metadata = manager.registry.get("test-ext")
        registered_commands = metadata["registered_commands"]
        # Check that the command is registered for at least one agent
        assert any(
            "speckit.test-ext.hello" in cmds
            for cmds in registered_commands.values()
        )

        # Remove
        result = manager.remove("test-ext")
        assert result is True

        # Verify removal
        assert not manager.registry.is_installed("test-ext")
        assert not cmd_file.exists()
        assert len(manager.list_installed()) == 0

    def test_copilot_cleanup_removes_prompt_files(self, extension_dir, project_dir):
        """Test that removing a Copilot extension also removes .prompt.md files."""
        agents_dir = project_dir / ".github" / "agents"
        agents_dir.mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=True)

        # Verify copilot was detected and registered
        metadata = manager.registry.get("test-ext")
        assert "copilot" in metadata["registered_commands"]

        # Verify files exist before cleanup
        agent_file = agents_dir / "speckit.test-ext.hello.agent.md"
        prompt_file = project_dir / ".github" / "prompts" / "speckit.test-ext.hello.prompt.md"
        assert agent_file.exists()
        assert prompt_file.exists()

        # Use the extension manager to remove — exercises the copilot prompt cleanup code
        result = manager.remove("test-ext")
        assert result is True

        assert not agent_file.exists()
        assert not prompt_file.exists()

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
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

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
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

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
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

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
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

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
        import yaml as yaml_module

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()

        # Use a single-catalog config so community extensions don't interfere
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump(
                {
                    "catalogs": [
                        {
                            "name": "test-catalog",
                            "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                            "priority": 1,
                            "install_allowed": True,
                        }
                    ]
                },
                f,
            )

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


# ===== CatalogEntry Tests =====

class TestCatalogEntry:
    """Test CatalogEntry dataclass."""

    def test_catalog_entry_creation(self):
        """Test creating a CatalogEntry."""
        entry = CatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
        )
        assert entry.url == "https://example.com/catalog.json"
        assert entry.name == "test"
        assert entry.priority == 1
        assert entry.install_allowed is True


# ===== Catalog Stack Tests =====

class TestCatalogStack:
    """Test multi-catalog stack support."""

    def _make_project(self, temp_dir: Path) -> Path:
        """Create a minimal spec-kit project directory."""
        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        return project_dir

    def _write_catalog_config(self, project_dir: Path, catalogs: list) -> None:
        """Write extension-catalogs.yml to project .specify dir."""
        import yaml as yaml_module

        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump({"catalogs": catalogs}, f)

    def _write_valid_cache(
        self, catalog: ExtensionCatalog, extensions: dict, url: str = "http://test.com"
    ) -> None:
        """Populate the primary cache file with mock extension data."""
        catalog_data = {"schema_version": "1.0", "extensions": extensions}
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": url,
                }
            )
        )

    # --- get_active_catalogs ---

    def test_default_stack(self, temp_dir):
        """Default stack includes default and community catalogs."""
        project_dir = self._make_project(temp_dir)
        catalog = ExtensionCatalog(project_dir)

        entries = catalog.get_active_catalogs()

        assert len(entries) == 2
        assert entries[0].url == ExtensionCatalog.DEFAULT_CATALOG_URL
        assert entries[0].name == "default"
        assert entries[0].priority == 1
        assert entries[0].install_allowed is True
        assert entries[1].url == ExtensionCatalog.COMMUNITY_CATALOG_URL
        assert entries[1].name == "community"
        assert entries[1].priority == 2
        assert entries[1].install_allowed is False

    def test_env_var_overrides_default_stack(self, temp_dir, monkeypatch):
        """SPECKIT_CATALOG_URL replaces the entire default stack."""
        project_dir = self._make_project(temp_dir)
        custom_url = "https://example.com/catalog.json"
        monkeypatch.setenv("SPECKIT_CATALOG_URL", custom_url)

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 1
        assert entries[0].url == custom_url
        assert entries[0].install_allowed is True

    def test_env_var_invalid_url_raises(self, temp_dir, monkeypatch):
        """SPECKIT_CATALOG_URL with http:// (non-localhost) raises ValidationError."""
        project_dir = self._make_project(temp_dir)
        monkeypatch.setenv("SPECKIT_CATALOG_URL", "http://example.com/catalog.json")

        catalog = ExtensionCatalog(project_dir)
        with pytest.raises(ValidationError, match="HTTPS"):
            catalog.get_active_catalogs()

    def test_project_config_overrides_defaults(self, temp_dir):
        """Project-level extension-catalogs.yml overrides default stack."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "custom",
                    "url": "https://example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 1
        assert entries[0].url == "https://example.com/catalog.json"
        assert entries[0].name == "custom"

    def test_project_config_sorted_by_priority(self, temp_dir):
        """Catalog entries are sorted by priority (ascending)."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "secondary",
                    "url": "https://example.com/secondary.json",
                    "priority": 5,
                    "install_allowed": False,
                },
                {
                    "name": "primary",
                    "url": "https://example.com/primary.json",
                    "priority": 1,
                    "install_allowed": True,
                },
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 2
        assert entries[0].name == "primary"
        assert entries[1].name == "secondary"

    def test_project_config_invalid_url_raises(self, temp_dir):
        """Project config with HTTP (non-localhost) URL raises ValidationError."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "bad",
                    "url": "http://example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        with pytest.raises(ValidationError, match="HTTPS"):
            catalog.get_active_catalogs()

    def test_empty_project_config_raises_error(self, temp_dir):
        """Empty catalogs list in config raises ValidationError (fail-closed for security)."""
        import yaml as yaml_module

        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump({"catalogs": []}, f)

        catalog = ExtensionCatalog(project_dir)

        # Fail-closed: empty config should raise, not fall back to defaults
        with pytest.raises(ValidationError) as exc_info:
            catalog.get_active_catalogs()
        assert "contains no 'catalogs' entries" in str(exc_info.value)

    def test_catalog_entries_without_urls_raises_error(self, temp_dir):
        """Catalog entries without URLs raise ValidationError (fail-closed for security)."""
        import yaml as yaml_module

        project_dir = self._make_project(temp_dir)
        config_path = project_dir / ".specify" / "extension-catalogs.yml"
        with open(config_path, "w") as f:
            yaml_module.dump({
                "catalogs": [
                    {"name": "no-url-catalog", "priority": 1},
                    {"name": "another-no-url", "description": "Also missing URL"},
                ]
            }, f)

        catalog = ExtensionCatalog(project_dir)

        # Fail-closed: entries without URLs should raise, not fall back to defaults
        with pytest.raises(ValidationError) as exc_info:
            catalog.get_active_catalogs()
        assert "none have valid URLs" in str(exc_info.value)

    # --- _load_catalog_config ---

    def test_load_catalog_config_missing_file(self, temp_dir):
        """Returns None when config file doesn't exist."""
        project_dir = self._make_project(temp_dir)
        catalog = ExtensionCatalog(project_dir)

        result = catalog._load_catalog_config(project_dir / ".specify" / "nonexistent.yml")
        assert result is None

    def test_load_catalog_config_localhost_allowed(self, temp_dir):
        """Localhost HTTP URLs are allowed in config."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "local",
                    "url": "http://localhost:8000/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        entries = catalog.get_active_catalogs()

        assert len(entries) == 1
        assert entries[0].url == "http://localhost:8000/catalog.json"

    # --- Merge conflict resolution ---

    def test_merge_conflict_higher_priority_wins(self, temp_dir):
        """When same extension id is in two catalogs, higher priority wins."""
        project_dir = self._make_project(temp_dir)

        # Write project config with two catalogs
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "primary",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1,
                    "install_allowed": True,
                },
                {
                    "name": "secondary",
                    "url": ExtensionCatalog.COMMUNITY_CATALOG_URL,
                    "priority": 2,
                    "install_allowed": False,
                },
            ],
        )

        catalog = ExtensionCatalog(project_dir)

        # Write primary cache with jira v2.0.0
        primary_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "2.0.0",
                    "description": "Primary Jira",
                }
            },
        }
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text(json.dumps(primary_data))
        catalog.cache_metadata_file.write_text(
            json.dumps({"cached_at": datetime.now(timezone.utc).isoformat(), "catalog_url": "http://test.com"})
        )

        # Write secondary cache (URL-hash-based) with jira v1.0.0 (should lose)
        import hashlib

        url_hash = hashlib.sha256(ExtensionCatalog.COMMUNITY_CATALOG_URL.encode()).hexdigest()[:16]
        secondary_cache = catalog.cache_dir / f"catalog-{url_hash}.json"
        secondary_meta = catalog.cache_dir / f"catalog-{url_hash}-metadata.json"
        secondary_data = {
            "schema_version": "1.0",
            "extensions": {
                "jira": {
                    "name": "Jira Integration Community",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Community Jira",
                },
                "linear": {
                    "name": "Linear",
                    "id": "linear",
                    "version": "0.9.0",
                    "description": "Linear from secondary",
                },
            },
        }
        secondary_cache.write_text(json.dumps(secondary_data))
        secondary_meta.write_text(
            json.dumps({"cached_at": datetime.now(timezone.utc).isoformat(), "catalog_url": ExtensionCatalog.COMMUNITY_CATALOG_URL})
        )

        results = catalog.search()
        jira_results = [r for r in results if r["id"] == "jira"]
        assert len(jira_results) == 1
        # Primary catalog wins
        assert jira_results[0]["version"] == "2.0.0"
        assert jira_results[0]["_catalog_name"] == "primary"
        assert jira_results[0]["_install_allowed"] is True

        # linear comes from secondary
        linear_results = [r for r in results if r["id"] == "linear"]
        assert len(linear_results) == 1
        assert linear_results[0]["_catalog_name"] == "secondary"
        assert linear_results[0]["_install_allowed"] is False

    def test_install_allowed_false_from_get_extension_info(self, temp_dir):
        """get_extension_info includes _install_allowed from source catalog."""
        project_dir = self._make_project(temp_dir)

        # Single catalog that is install_allowed=False
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "discovery",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1,
                    "install_allowed": False,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        self._write_valid_cache(
            catalog,
            {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                }
            },
        )

        info = catalog.get_extension_info("jira")
        assert info is not None
        assert info["_install_allowed"] is False
        assert info["_catalog_name"] == "discovery"

    def test_search_results_include_catalog_metadata(self, temp_dir):
        """Search results include _catalog_name and _install_allowed."""
        project_dir = self._make_project(temp_dir)
        self._write_catalog_config(
            project_dir,
            [
                {
                    "name": "org",
                    "url": ExtensionCatalog.DEFAULT_CATALOG_URL,
                    "priority": 1,
                    "install_allowed": True,
                }
            ],
        )

        catalog = ExtensionCatalog(project_dir)
        self._write_valid_cache(
            catalog,
            {
                "jira": {
                    "name": "Jira Integration",
                    "id": "jira",
                    "version": "1.0.0",
                    "description": "Jira integration",
                }
            },
        )

        results = catalog.search()
        assert len(results) == 1
        assert results[0]["_catalog_name"] == "org"
        assert results[0]["_install_allowed"] is True


class TestExtensionIgnore:
    """Test .extensionignore support during extension installation."""

    def _make_extension(self, temp_dir, valid_manifest_data, extra_files=None, ignore_content=None):
        """Helper to create an extension directory with optional extra files and .extensionignore."""
        import yaml

        ext_dir = temp_dir / "ignored-ext"
        ext_dir.mkdir()

        # Write manifest
        with open(ext_dir / "extension.yml", "w") as f:
            yaml.dump(valid_manifest_data, f)

        # Create commands directory with a command file
        commands_dir = ext_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "hello.md").write_text(
            "---\ndescription: \"Test hello command\"\n---\n\n# Hello\n\n$ARGUMENTS\n"
        )

        # Create any extra files/dirs
        if extra_files:
            for rel_path, content in extra_files.items():
                p = ext_dir / rel_path
                p.parent.mkdir(parents=True, exist_ok=True)
                if content is None:
                    # Create directory
                    p.mkdir(parents=True, exist_ok=True)
                else:
                    p.write_text(content)

        # Write .extensionignore
        if ignore_content is not None:
            (ext_dir / ".extensionignore").write_text(ignore_content)

        return ext_dir

    def test_no_extensionignore(self, temp_dir, valid_manifest_data):
        """Without .extensionignore, all files are copied."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "tests/test_foo.py": "pass"},
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert (dest / "tests" / "test_foo.py").exists()

    def test_extensionignore_excludes_files(self, temp_dir, valid_manifest_data):
        """Files matching .extensionignore patterns are excluded."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "README.md": "# Hello",
                "tests/test_foo.py": "pass",
                "tests/test_bar.py": "pass",
                ".github/workflows/ci.yml": "on: push",
            },
            ignore_content="tests/\n.github/\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # Included
        assert (dest / "README.md").exists()
        assert (dest / "extension.yml").exists()
        assert (dest / "commands" / "hello.md").exists()
        # Excluded
        assert not (dest / "tests").exists()
        assert not (dest / ".github").exists()

    def test_extensionignore_glob_patterns(self, temp_dir, valid_manifest_data):
        """Glob patterns like *.pyc are respected."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "README.md": "# Hello",
                "helpers.pyc": b"\x00".decode("latin-1"),
                "commands/cache.pyc": b"\x00".decode("latin-1"),
            },
            ignore_content="*.pyc\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert not (dest / "helpers.pyc").exists()
        assert not (dest / "commands" / "cache.pyc").exists()

    def test_extensionignore_comments_and_blanks(self, temp_dir, valid_manifest_data):
        """Comments and blank lines in .extensionignore are ignored."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "notes.txt": "some notes"},
            ignore_content="# This is a comment\n\nnotes.txt\n\n# Another comment\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert not (dest / "notes.txt").exists()

    def test_extensionignore_itself_excluded(self, temp_dir, valid_manifest_data):
        """.extensionignore is never copied to the destination."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            ignore_content="# nothing special here\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "extension.yml").exists()
        assert not (dest / ".extensionignore").exists()

    def test_extensionignore_relative_path_match(self, temp_dir, valid_manifest_data):
        """Patterns matching relative paths work correctly."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/guide.md": "# Guide",
                "docs/internal/draft.md": "draft",
                "README.md": "# Hello",
            },
            ignore_content="docs/internal/draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "docs" / "guide.md").exists()
        assert not (dest / "docs" / "internal" / "draft.md").exists()

    def test_extensionignore_dotdot_pattern_is_noop(self, temp_dir, valid_manifest_data):
        """Patterns with '..' should not escape the extension root."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello"},
            ignore_content="../sibling/\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # Everything should still be copied — the '..' pattern matches nothing inside
        assert (dest / "README.md").exists()
        assert (dest / "extension.yml").exists()
        assert (dest / "commands" / "hello.md").exists()

    def test_extensionignore_absolute_path_pattern_is_noop(self, temp_dir, valid_manifest_data):
        """Absolute path patterns should not match anything."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "passwd": "sensitive"},
            ignore_content="/etc/passwd\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # Nothing matches — /etc/passwd is anchored to root and there's no 'etc' dir
        assert (dest / "README.md").exists()
        assert (dest / "passwd").exists()

    def test_extensionignore_empty_file(self, temp_dir, valid_manifest_data):
        """An empty .extensionignore should exclude only itself."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={"README.md": "# Hello", "notes.txt": "notes"},
            ignore_content="",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "README.md").exists()
        assert (dest / "notes.txt").exists()
        assert (dest / "extension.yml").exists()
        # .extensionignore itself is still excluded
        assert not (dest / ".extensionignore").exists()

    def test_extensionignore_windows_backslash_patterns(self, temp_dir, valid_manifest_data):
        """Backslash patterns (Windows-style) are normalised to forward slashes."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/internal/draft.md": "draft",
                "docs/guide.md": "# Guide",
            },
            ignore_content="docs\\internal\\draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert (dest / "docs" / "guide.md").exists()
        assert not (dest / "docs" / "internal" / "draft.md").exists()

    def test_extensionignore_star_does_not_cross_directories(self, temp_dir, valid_manifest_data):
        """'*' should NOT match across directory boundaries (gitignore semantics)."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/api.draft.md": "draft",
                "docs/sub/api.draft.md": "nested draft",
            },
            ignore_content="docs/*.draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # docs/*.draft.md should only match directly inside docs/, NOT subdirs
        assert not (dest / "docs" / "api.draft.md").exists()
        assert (dest / "docs" / "sub" / "api.draft.md").exists()

    def test_extensionignore_doublestar_crosses_directories(self, temp_dir, valid_manifest_data):
        """'**' should match across directory boundaries."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/api.draft.md": "draft",
                "docs/sub/api.draft.md": "nested draft",
                "docs/guide.md": "guide",
            },
            ignore_content="docs/**/*.draft.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        assert not (dest / "docs" / "api.draft.md").exists()
        assert not (dest / "docs" / "sub" / "api.draft.md").exists()
        assert (dest / "docs" / "guide.md").exists()

    def test_extensionignore_negation_pattern(self, temp_dir, valid_manifest_data):
        """'!' negation re-includes a previously excluded file."""
        ext_dir = self._make_extension(
            temp_dir,
            valid_manifest_data,
            extra_files={
                "docs/guide.md": "# Guide",
                "docs/internal.md": "internal",
                "docs/api.md": "api",
            },
            ignore_content="docs/*.md\n!docs/api.md\n",
        )

        proj_dir = temp_dir / "project"
        proj_dir.mkdir()
        (proj_dir / ".specify").mkdir()

        manager = ExtensionManager(proj_dir)
        manager.install_from_directory(ext_dir, "0.1.0", register_commands=False)

        dest = proj_dir / ".specify" / "extensions" / "test-ext"
        # docs/*.md excludes all .md in docs, but !docs/api.md re-includes it
        assert not (dest / "docs" / "guide.md").exists()
        assert not (dest / "docs" / "internal.md").exists()
        assert (dest / "docs" / "api.md").exists()


class TestExtensionAddCLI:
    """CLI integration tests for extension add command."""

    def test_add_by_display_name_uses_resolved_id_for_download(self, tmp_path):
        """extension add by display name should use resolved ID for download_extension()."""
        from typer.testing import CliRunner
        from unittest.mock import patch, MagicMock
        from specify_cli import app

        runner = CliRunner()

        # Create project structure
        project_dir = tmp_path / "test-project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".specify" / "extensions").mkdir(parents=True)

        # Mock catalog that returns extension by display name
        mock_catalog = MagicMock()
        mock_catalog.get_extension_info.return_value = None  # ID lookup fails
        mock_catalog.search.return_value = [
            {
                "id": "acme-jira-integration",
                "name": "Jira Integration",
                "version": "1.0.0",
                "description": "Jira integration extension",
                "_install_allowed": True,
            }
        ]

        # Track what ID was passed to download_extension
        download_called_with = []
        def mock_download(extension_id):
            download_called_with.append(extension_id)
            # Return a path that will fail install (we just want to verify the ID)
            raise ExtensionError("Mock download - checking ID was resolved")

        mock_catalog.download_extension.side_effect = mock_download

        with patch("specify_cli.extensions.ExtensionCatalog", return_value=mock_catalog), \
             patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(
                app,
                ["extension", "add", "Jira Integration"],
                catch_exceptions=True,
            )

        assert result.exit_code != 0, (
            f"Expected non-zero exit code since mock download raises, got {result.exit_code}"
        )

        # Verify download_extension was called with the resolved ID, not the display name
        assert len(download_called_with) == 1
        assert download_called_with[0] == "acme-jira-integration", (
            f"Expected download_extension to be called with resolved ID 'acme-jira-integration', "
            f"but was called with '{download_called_with[0]}'"
        )


class TestExtensionUpdateCLI:
    """CLI integration tests for extension update command."""

    @staticmethod
    def _create_extension_source(base_dir: Path, version: str, include_config: bool = False) -> Path:
        """Create a minimal extension source directory for install tests."""
        import yaml

        ext_dir = base_dir / f"test-ext-{version}"
        ext_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": version,
                "description": "A test extension",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.test-ext.hello",
                        "file": "commands/hello.md",
                        "description": "Test command",
                    }
                ]
            },
            "hooks": {
                "after_tasks": {
                    "command": "speckit.test-ext.hello",
                    "optional": True,
                }
            },
        }

        (ext_dir / "extension.yml").write_text(yaml.dump(manifest, sort_keys=False))
        commands_dir = ext_dir / "commands"
        commands_dir.mkdir(exist_ok=True)
        (commands_dir / "hello.md").write_text("---\ndescription: Test\n---\n\n$ARGUMENTS\n")
        if include_config:
            (ext_dir / "linear-config.yml").write_text("custom: true\nvalue: original\n")
        return ext_dir

    @staticmethod
    def _create_catalog_zip(zip_path: Path, version: str):
        """Create a minimal ZIP that passes extension_update ID validation."""
        import zipfile
        import yaml

        manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "test-ext",
                "name": "Test Extension",
                "version": version,
                "description": "A test extension",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"commands": [{"name": "speckit.test-ext.hello", "file": "commands/hello.md"}]},
        }

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("extension.yml", yaml.dump(manifest, sort_keys=False))

    def test_update_success_preserves_installed_at(self, tmp_path):
        """Successful update should keep original installed_at and apply new version."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0", include_config=True)
        manager.install_from_directory(v1_dir, "0.1.0")
        original_installed_at = manager.registry.get("test-ext")["installed_at"]
        original_config_content = (
            project_dir / ".specify" / "extensions" / "test-ext" / "linear-config.yml"
        ).read_text()

        zip_path = tmp_path / "test-ext-update.zip"
        self._create_catalog_zip(zip_path, "2.0.0")
        v2_dir = self._create_extension_source(tmp_path, "2.0.0")

        def fake_install_from_zip(self_obj, _zip_path, speckit_version):
            return self_obj.install_from_directory(v2_dir, speckit_version)

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path), \
             patch.object(ExtensionManager, "install_from_zip", fake_install_from_zip):
            result = runner.invoke(app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True)

        assert result.exit_code == 0, result.output

        updated = ExtensionManager(project_dir).registry.get("test-ext")
        assert updated["version"] == "2.0.0"
        assert updated["installed_at"] == original_installed_at
        restored_config_content = (
            project_dir / ".specify" / "extensions" / "test-ext" / "linear-config.yml"
        ).read_text()
        assert restored_config_content == original_config_content

    def test_update_failure_rolls_back_registry_hooks_and_commands(self, tmp_path):
        """Failed update should restore original registry, hooks, and command files."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        import yaml

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")

        backup_registry_entry = manager.registry.get("test-ext")
        hooks_before = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())

        registered_commands = backup_registry_entry.get("registered_commands", {})
        command_files = []
        from specify_cli.agents import CommandRegistrar as AgentRegistrar
        agent_registrar = AgentRegistrar()
        for agent_name, cmd_names in registered_commands.items():
            if agent_name not in agent_registrar.AGENT_CONFIGS:
                continue
            agent_cfg = agent_registrar.AGENT_CONFIGS[agent_name]
            commands_dir = project_dir / agent_cfg["dir"]
            for cmd_name in cmd_names:
                output_name = AgentRegistrar._compute_output_name(agent_name, cmd_name, agent_cfg)
                cmd_path = commands_dir / f"{output_name}{agent_cfg['extension']}"
                command_files.append(cmd_path)

        assert command_files, "Expected at least one registered command file"
        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to exist before update: {cmd_file}"

        zip_path = tmp_path / "test-ext-update.zip"
        self._create_catalog_zip(zip_path, "2.0.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path), \
             patch.object(ExtensionManager, "install_from_zip", side_effect=RuntimeError("install failed")):
            result = runner.invoke(app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True)

        assert result.exit_code == 1, result.output

        restored_entry = ExtensionManager(project_dir).registry.get("test-ext")
        assert restored_entry == backup_registry_entry

        hooks_after = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())
        assert hooks_after == hooks_before

        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to be restored after rollback: {cmd_file}"


class TestExtensionListCLI:
    """Test extension list CLI output format."""

    def test_list_shows_extension_id(self, extension_dir, project_dir):
        """extension list should display the extension ID."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install the extension using the manager
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "list"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        # Verify the extension ID is shown in the output
        assert "test-ext" in plain
        # Verify name and version are also shown
        assert "Test Extension" in plain
        assert "1.0.0" in plain


class TestExtensionPriority:
    """Test extension priority-based resolution."""

    def test_list_by_priority_empty(self, temp_dir):
        """Test list_by_priority on empty registry."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        result = registry.list_by_priority()

        assert result == []

    def test_list_by_priority_single(self, temp_dir):
        """Test list_by_priority with single extension."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0", "priority": 5})

        result = registry.list_by_priority()

        assert len(result) == 1
        assert result[0][0] == "test-ext"
        assert result[0][1]["priority"] == 5

    def test_list_by_priority_ordering(self, temp_dir):
        """Test list_by_priority returns extensions sorted by priority."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        # Add in non-priority order
        registry.add("ext-low", {"version": "1.0.0", "priority": 20})
        registry.add("ext-high", {"version": "1.0.0", "priority": 1})
        registry.add("ext-mid", {"version": "1.0.0", "priority": 10})

        result = registry.list_by_priority()

        assert len(result) == 3
        # Lower priority number = higher precedence (first)
        assert result[0][0] == "ext-high"
        assert result[1][0] == "ext-mid"
        assert result[2][0] == "ext-low"

    def test_list_by_priority_default(self, temp_dir):
        """Test list_by_priority uses default priority of 10."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        # Add without explicit priority
        registry.add("ext-default", {"version": "1.0.0"})
        registry.add("ext-high", {"version": "1.0.0", "priority": 1})
        registry.add("ext-low", {"version": "1.0.0", "priority": 20})

        result = registry.list_by_priority()

        assert len(result) == 3
        # ext-high (1), ext-default (10), ext-low (20)
        assert result[0][0] == "ext-high"
        assert result[1][0] == "ext-default"
        assert result[2][0] == "ext-low"

    def test_list_by_priority_invalid_priority_defaults(self, temp_dir):
        """Malformed priority values fall back to the default priority."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("ext-high", {"version": "1.0.0", "priority": 1})
        registry.data["extensions"]["ext-invalid"] = {
            "version": "1.0.0",
            "priority": "high",
        }
        registry._save()

        result = registry.list_by_priority()

        assert [item[0] for item in result] == ["ext-high", "ext-invalid"]
        assert result[1][1]["priority"] == 10

    def test_list_by_priority_excludes_disabled(self, temp_dir):
        """Test that list_by_priority excludes disabled extensions by default."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("ext-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("ext-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})
        registry.add("ext-default", {"version": "1.0.0", "priority": 10})  # no enabled field = True

        # Default: exclude disabled
        by_priority = registry.list_by_priority()
        ext_ids = [p[0] for p in by_priority]
        assert "ext-enabled" in ext_ids
        assert "ext-default" in ext_ids
        assert "ext-disabled" not in ext_ids

    def test_list_by_priority_includes_disabled_when_requested(self, temp_dir):
        """Test that list_by_priority includes disabled extensions when requested."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("ext-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("ext-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})

        # Include disabled
        by_priority = registry.list_by_priority(include_disabled=True)
        ext_ids = [p[0] for p in by_priority]
        assert "ext-enabled" in ext_ids
        assert "ext-disabled" in ext_ids
        # Disabled ext has lower priority number, so it comes first when included
        assert ext_ids[0] == "ext-disabled"

    def test_install_with_priority(self, extension_dir, project_dir):
        """Test that install_from_directory stores priority."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=5)

        metadata = manager.registry.get("test-ext")
        assert metadata["priority"] == 5

    def test_install_default_priority(self, extension_dir, project_dir):
        """Test that install_from_directory uses default priority of 10."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        metadata = manager.registry.get("test-ext")
        assert metadata["priority"] == 10

    def test_list_installed_includes_priority(self, extension_dir, project_dir):
        """Test that list_installed includes priority in returned data."""
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=3)

        installed = manager.list_installed()

        assert len(installed) == 1
        assert installed[0]["priority"] == 3

    def test_priority_preserved_on_update(self, temp_dir):
        """Test that registry update preserves priority."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)
        registry.add("test-ext", {"version": "1.0.0", "priority": 5, "enabled": True})

        # Update with new metadata (no priority specified)
        registry.update("test-ext", {"enabled": False})

        updated = registry.get("test-ext")
        assert updated["priority"] == 5  # Preserved
        assert updated["enabled"] is False  # Updated

    def test_corrupted_extension_entry_not_picked_up_as_unregistered(self, project_dir):
        """Corrupted registry entries are still tracked and NOT picked up as unregistered."""
        extensions_dir = project_dir / ".specify" / "extensions"

        valid_dir = extensions_dir / "valid-ext" / "templates"
        valid_dir.mkdir(parents=True)
        (valid_dir / "other-template.md").write_text("# Valid\n")

        broken_dir = extensions_dir / "broken-ext" / "templates"
        broken_dir.mkdir(parents=True)
        (broken_dir / "target-template.md").write_text("# Broken Target\n")

        registry = ExtensionRegistry(extensions_dir)
        registry.add("valid-ext", {"version": "1.0.0", "priority": 10})
        # Corrupt the entry - should still be tracked, not picked up as unregistered
        registry.data["extensions"]["broken-ext"] = "corrupted"
        registry._save()

        from specify_cli.presets import PresetResolver

        resolver = PresetResolver(project_dir)
        # Corrupted extension templates should NOT be resolved
        resolved = resolver.resolve("target-template")
        assert resolved is None

        # Valid extension template should still resolve
        valid_resolved = resolver.resolve("other-template")
        assert valid_resolved is not None
        assert "Valid" in valid_resolved.read_text()


class TestExtensionPriorityCLI:
    """Test extension priority CLI integration."""

    def test_add_with_priority_option(self, extension_dir, project_dir):
        """Test extension add command with --priority option."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, [
                "extension", "add", str(extension_dir), "--dev", "--priority", "3"
            ])

        assert result.exit_code == 0, result.output

        manager = ExtensionManager(project_dir)
        metadata = manager.registry.get("test-ext")
        assert metadata["priority"] == 3

    def test_list_shows_priority(self, extension_dir, project_dir):
        """Test extension list shows priority."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension with priority
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=7)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "list"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "Priority: 7" in plain

    def test_set_priority_changes_priority(self, extension_dir, project_dir):
        """Test set-priority command changes extension priority."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension with default priority
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Verify default priority
        assert manager.registry.get("test-ext")["priority"] == 10

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "priority changed: 10 → 5" in plain

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 5

    def test_set_priority_same_value_no_change(self, extension_dir, project_dir):
        """Test set-priority with same value shows already set message."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension with priority 5
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False, priority=5)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "already has priority 5" in plain

    def test_set_priority_invalid_value(self, extension_dir, project_dir):
        """Test set-priority rejects invalid priority values."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "test-ext", "0"])

        assert result.exit_code == 1, result.output
        assert "Priority must be a positive integer" in result.output

    def test_set_priority_not_installed(self, project_dir):
        """Test set-priority fails for non-installed extension."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Ensure .specify exists
        (project_dir / ".specify").mkdir(parents=True, exist_ok=True)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "nonexistent", "5"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower() or "no extensions installed" in result.output.lower()

    def test_set_priority_by_display_name(self, extension_dir, project_dir):
        """Test set-priority works with extension display name."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install extension
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Use display name "Test Extension" instead of ID "test-ext"
        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["extension", "set-priority", "Test Extension", "3"])

        assert result.exit_code == 0, result.output
        assert "priority changed" in result.output

        # Reload registry to see updated value
        manager2 = ExtensionManager(project_dir)
        assert manager2.registry.get("test-ext")["priority"] == 3


class TestExtensionPriorityBackwardsCompatibility:
    """Test backwards compatibility for extensions installed before priority feature."""

    def test_legacy_extension_without_priority_field(self, temp_dir):
        """Extensions installed before priority feature should default to 10."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        # Simulate legacy registry entry without priority field
        registry = ExtensionRegistry(extensions_dir)
        registry.data["extensions"]["legacy-ext"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            "installed_at": "2025-01-01T00:00:00Z",
            # No "priority" field - simulates pre-feature extension
        }
        registry._save()

        # Reload registry
        registry2 = ExtensionRegistry(extensions_dir)

        # list_by_priority should use default of 10
        result = registry2.list_by_priority()
        assert len(result) == 1
        assert result[0][0] == "legacy-ext"
        # Priority defaults to 10 and is normalized in returned metadata
        assert result[0][1]["priority"] == 10

    def test_legacy_extension_in_list_installed(self, extension_dir, project_dir):
        """list_installed returns priority=10 for legacy extensions without priority field."""
        manager = ExtensionManager(project_dir)

        # Install extension normally
        manager.install_from_directory(extension_dir, "0.1.0", register_commands=False)

        # Manually remove priority to simulate legacy extension
        ext_data = manager.registry.data["extensions"]["test-ext"]
        del ext_data["priority"]
        manager.registry._save()

        # list_installed should still return priority=10
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["priority"] == 10

    def test_mixed_legacy_and_new_extensions_ordering(self, temp_dir):
        """Legacy extensions (no priority) sort with default=10 among prioritized extensions."""
        extensions_dir = temp_dir / "extensions"
        extensions_dir.mkdir()

        registry = ExtensionRegistry(extensions_dir)

        # Add extension with explicit priority=5
        registry.add("ext-with-priority", {"version": "1.0.0", "priority": 5})

        # Add legacy extension without priority (manually)
        registry.data["extensions"]["legacy-ext"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            # No priority field
        }
        registry._save()

        # Add extension with priority=15
        registry.add("ext-low-priority", {"version": "1.0.0", "priority": 15})

        # Reload and check ordering
        registry2 = ExtensionRegistry(extensions_dir)
        result = registry2.list_by_priority()

        assert len(result) == 3
        # Order: ext-with-priority (5), legacy-ext (defaults to 10), ext-low-priority (15)
        assert result[0][0] == "ext-with-priority"
        assert result[1][0] == "legacy-ext"
        assert result[2][0] == "ext-low-priority"


class TestHookInvocationRendering:
    """Test hook invocation formatting for different agent modes."""

    def test_kimi_hooks_render_skill_invocation(self, project_dir):
        """Kimi projects should render /skill:speckit-* invocations."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "before_plan",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.plan",
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/skill:speckit-plan`" in message
        assert "EXECUTE_COMMAND: speckit.plan" in message
        assert "EXECUTE_COMMAND_INVOCATION: /skill:speckit-plan" in message

    def test_codex_hooks_render_dollar_skill_invocation(self, project_dir):
        """Codex projects with --ai-skills should render $speckit-* invocations."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "codex", "ai_skills": True}))

        hook_executor = HookExecutor(project_dir)
        execution = hook_executor.execute_hook(
            {
                "extension": "test-ext",
                "command": "speckit.tasks",
                "optional": False,
            }
        )

        assert execution["command"] == "speckit.tasks"
        assert execution["invocation"] == "$speckit-tasks"

    def test_non_skill_command_keeps_slash_invocation(self, project_dir):
        """Custom hook commands should keep slash invocation style."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "before_tasks",
            [
                {
                    "extension": "test-ext",
                    "command": "pre_tasks_test",
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/pre_tasks_test`" in message
        assert "EXECUTE_COMMAND: pre_tasks_test" in message
        assert "EXECUTE_COMMAND_INVOCATION: /pre_tasks_test" in message

    def test_extension_command_uses_hyphenated_skill_invocation(self, project_dir):
        """Multi-segment extension command ids should map to hyphenated skills."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "after_tasks",
            [
                {
                    "extension": "test-ext",
                    "command": "speckit.test-ext.hello",
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/skill:speckit-test-ext-hello`" in message
        assert "EXECUTE_COMMAND: speckit.test-ext.hello" in message
        assert "EXECUTE_COMMAND_INVOCATION: /skill:speckit-test-ext-hello" in message

    def test_hook_executor_caches_init_options_lookup(self, project_dir, monkeypatch):
        """Init options should be loaded once per executor instance."""
        calls = {"count": 0}

        def fake_load_init_options(_project_root):
            calls["count"] += 1
            return {"ai": "kimi", "ai_skills": False}

        monkeypatch.setattr("specify_cli.load_init_options", fake_load_init_options)

        hook_executor = HookExecutor(project_dir)
        assert hook_executor._render_hook_invocation("speckit.plan") == "/skill:speckit-plan"
        assert hook_executor._render_hook_invocation("speckit.tasks") == "/skill:speckit-tasks"
        assert calls["count"] == 1

    def test_hook_message_falls_back_when_invocation_is_empty(self, project_dir):
        """Hook messages should still render actionable command placeholders."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text(json.dumps({"ai": "kimi", "ai_skills": False}))

        hook_executor = HookExecutor(project_dir)
        message = hook_executor.format_hook_message(
            "after_tasks",
            [
                {
                    "extension": "test-ext",
                    "command": None,
                    "optional": False,
                }
            ],
        )

        assert "Executing: `/<missing command>`" in message
        assert "EXECUTE_COMMAND: <missing command>" in message
        assert "EXECUTE_COMMAND_INVOCATION: /<missing command>" in message
