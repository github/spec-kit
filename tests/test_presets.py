"""
Unit tests for the preset system.

Tests cover:
- Preset manifest validation
- Preset registry operations
- Preset manager installation/removal
- Template catalog search
- Template resolver priority stack
- Extension-provided templates
"""

import pytest
import json
import tempfile
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timezone

import yaml

from tests.conftest import strip_ansi
from specify_cli.presets import (
    PresetManifest,
    PresetRegistry,
    PresetManager,
    PresetCatalog,
    PresetCatalogEntry,
    PresetResolver,
    PresetError,
    PresetValidationError,
    PresetCompatibilityError,
    VALID_PRESET_TEMPLATE_TYPES,
)
from specify_cli.extensions import ExtensionRegistry


# ===== Fixtures =====


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def valid_pack_data():
    """Valid preset manifest data."""
    return {
        "schema_version": "1.0",
        "preset": {
            "id": "test-pack",
            "name": "Test Preset",
            "version": "1.0.0",
            "description": "A test preset",
            "author": "Test Author",
            "repository": "https://github.com/test/test-pack",
            "license": "MIT",
        },
        "requires": {
            "speckit_version": ">=0.1.0",
        },
        "provides": {
            "templates": [
                {
                    "type": "template",
                    "name": "spec-template",
                    "file": "templates/spec-template.md",
                    "description": "Custom spec template",
                    "replaces": "spec-template",
                }
            ]
        },
        "tags": ["testing", "example"],
    }


@pytest.fixture
def pack_dir(temp_dir, valid_pack_data):
    """Create a complete preset directory structure."""
    p_dir = temp_dir / "test-pack"
    p_dir.mkdir()

    # Write manifest
    manifest_path = p_dir / "preset.yml"
    with open(manifest_path, 'w') as f:
        yaml.dump(valid_pack_data, f)

    # Create templates directory
    templates_dir = p_dir / "templates"
    templates_dir.mkdir()

    # Write template file
    tmpl_file = templates_dir / "spec-template.md"
    tmpl_file.write_text("# Custom Spec Template\n\nThis is a custom template.\n")

    return p_dir


@pytest.fixture
def project_dir(temp_dir):
    """Create a mock spec-kit project directory."""
    proj_dir = temp_dir / "project"
    proj_dir.mkdir()

    # Create .specify directory
    specify_dir = proj_dir / ".specify"
    specify_dir.mkdir()

    # Create templates directory with core templates
    templates_dir = specify_dir / "templates"
    templates_dir.mkdir()

    # Create core spec-template
    core_spec = templates_dir / "spec-template.md"
    core_spec.write_text("# Core Spec Template\n")

    # Create core plan-template
    core_plan = templates_dir / "plan-template.md"
    core_plan.write_text("# Core Plan Template\n")

    # Create commands subdirectory
    commands_dir = templates_dir / "commands"
    commands_dir.mkdir()

    return proj_dir


# ===== PresetManifest Tests =====


class TestPresetManifest:
    """Test PresetManifest validation and parsing."""

    def test_valid_manifest(self, pack_dir):
        """Test loading a valid manifest."""
        manifest = PresetManifest(pack_dir / "preset.yml")
        assert manifest.id == "test-pack"
        assert manifest.name == "Test Preset"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test preset"
        assert manifest.author == "Test Author"
        assert manifest.requires_speckit_version == ">=0.1.0"
        assert len(manifest.templates) == 1
        assert manifest.tags == ["testing", "example"]

    def test_missing_manifest(self, temp_dir):
        """Test that missing manifest raises error."""
        with pytest.raises(PresetValidationError, match="Manifest not found"):
            PresetManifest(temp_dir / "nonexistent.yml")

    def test_invalid_yaml(self, temp_dir):
        """Test that invalid YAML raises error."""
        bad_file = temp_dir / "bad.yml"
        bad_file.write_text(": invalid: yaml: {{{")
        with pytest.raises(PresetValidationError, match="Invalid YAML"):
            PresetManifest(bad_file)

    def test_missing_schema_version(self, temp_dir, valid_pack_data):
        """Test missing schema_version field."""
        del valid_pack_data["schema_version"]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Missing required field: schema_version"):
            PresetManifest(manifest_path)

    def test_wrong_schema_version(self, temp_dir, valid_pack_data):
        """Test unsupported schema version."""
        valid_pack_data["schema_version"] = "2.0"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Unsupported schema version"):
            PresetManifest(manifest_path)

    def test_missing_pack_id(self, temp_dir, valid_pack_data):
        """Test missing preset.id field."""
        del valid_pack_data["preset"]["id"]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Missing preset.id"):
            PresetManifest(manifest_path)

    def test_invalid_pack_id_format(self, temp_dir, valid_pack_data):
        """Test invalid pack ID format."""
        valid_pack_data["preset"]["id"] = "Invalid_ID"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid preset ID"):
            PresetManifest(manifest_path)

    def test_invalid_version(self, temp_dir, valid_pack_data):
        """Test invalid semantic version."""
        valid_pack_data["preset"]["version"] = "not-a-version"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid version"):
            PresetManifest(manifest_path)

    def test_missing_speckit_version(self, temp_dir, valid_pack_data):
        """Test missing requires.speckit_version."""
        del valid_pack_data["requires"]["speckit_version"]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Missing requires.speckit_version"):
            PresetManifest(manifest_path)

    def test_no_templates_provided(self, temp_dir, valid_pack_data):
        """Test pack with no templates."""
        valid_pack_data["provides"]["templates"] = []
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="must provide at least one template"):
            PresetManifest(manifest_path)

    def test_invalid_template_type(self, temp_dir, valid_pack_data):
        """Test template with invalid type."""
        valid_pack_data["provides"]["templates"][0]["type"] = "invalid"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid template type"):
            PresetManifest(manifest_path)

    def test_valid_template_types(self):
        """Test that all expected template types are valid."""
        assert "template" in VALID_PRESET_TEMPLATE_TYPES
        assert "command" in VALID_PRESET_TEMPLATE_TYPES
        assert "script" in VALID_PRESET_TEMPLATE_TYPES

    def test_template_missing_required_fields(self, temp_dir, valid_pack_data):
        """Test template missing required fields."""
        valid_pack_data["provides"]["templates"] = [{"type": "template"}]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="missing 'type', 'name', or 'file'"):
            PresetManifest(manifest_path)

    def test_invalid_template_name_format(self, temp_dir, valid_pack_data):
        """Test template with invalid name format."""
        valid_pack_data["provides"]["templates"][0]["name"] = "Invalid Name"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid template name"):
            PresetManifest(manifest_path)

    def test_get_hash(self, pack_dir):
        """Test manifest hash calculation."""
        manifest = PresetManifest(pack_dir / "preset.yml")
        hash_val = manifest.get_hash()
        assert hash_val.startswith("sha256:")
        assert len(hash_val) > 10

    def test_multiple_templates(self, temp_dir, valid_pack_data):
        """Test pack with multiple templates of different types."""
        valid_pack_data["provides"]["templates"] = [
            {"type": "template", "name": "spec-template", "file": "templates/spec-template.md"},
            {"type": "template", "name": "plan-template", "file": "templates/plan-template.md"},
            {"type": "command", "name": "specify", "file": "commands/specify.md"},
            {"type": "script", "name": "create-new-feature", "file": "scripts/create-new-feature.sh"},
        ]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert len(manifest.templates) == 4


# ===== PresetRegistry Tests =====


class TestPresetRegistry:
    """Test PresetRegistry operations."""

    def test_empty_registry(self, temp_dir):
        """Test empty registry initialization."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)
        assert registry.list() == {}
        assert not registry.is_installed("test-pack")

    def test_add_and_get(self, temp_dir):
        """Test adding and retrieving a pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0", "source": "local"})
        assert registry.is_installed("test-pack")

        metadata = registry.get("test-pack")
        assert metadata is not None
        assert metadata["version"] == "1.0.0"
        assert "installed_at" in metadata

    def test_remove(self, temp_dir):
        """Test removing a pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0"})
        assert registry.is_installed("test-pack")

        registry.remove("test-pack")
        assert not registry.is_installed("test-pack")

    def test_remove_nonexistent(self, temp_dir):
        """Test removing a pack that doesn't exist."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)
        registry.remove("nonexistent")  # Should not raise

    def test_list(self, temp_dir):
        """Test listing all packs."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-a", {"version": "1.0.0"})
        registry.add("pack-b", {"version": "2.0.0"})

        all_packs = registry.list()
        assert len(all_packs) == 2
        assert "pack-a" in all_packs
        assert "pack-b" in all_packs

    def test_persistence(self, temp_dir):
        """Test that registry data persists across instances."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()

        # Add with first instance
        registry1 = PresetRegistry(packs_dir)
        registry1.add("test-pack", {"version": "1.0.0"})

        # Load with second instance
        registry2 = PresetRegistry(packs_dir)
        assert registry2.is_installed("test-pack")

    def test_corrupted_registry(self, temp_dir):
        """Test recovery from corrupted registry file."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()

        registry_file = packs_dir / ".registry"
        registry_file.write_text("not valid json{{{")

        registry = PresetRegistry(packs_dir)
        assert registry.list() == {}

    def test_get_nonexistent(self, temp_dir):
        """Test getting a nonexistent pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)
        assert registry.get("nonexistent") is None

    def test_restore(self, temp_dir):
        """Test restore() preserves timestamps exactly."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        # Create original entry with a specific timestamp
        original_metadata = {
            "version": "1.0.0",
            "source": "local",
            "installed_at": "2025-01-15T10:30:00+00:00",
            "enabled": True,
        }
        registry.restore("test-pack", original_metadata)

        # Verify exact restoration
        restored = registry.get("test-pack")
        assert restored["installed_at"] == "2025-01-15T10:30:00+00:00"
        assert restored["version"] == "1.0.0"
        assert restored["enabled"] is True

    def test_restore_rejects_none_metadata(self, temp_dir):
        """Test restore() raises ValueError for None metadata."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-pack", None)

    def test_restore_rejects_non_dict_metadata(self, temp_dir):
        """Test restore() raises ValueError for non-dict metadata."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-pack", "not-a-dict")

        with pytest.raises(ValueError, match="metadata must be a dict"):
            registry.restore("test-pack", ["list", "not", "dict"])

    def test_restore_uses_deep_copy(self, temp_dir):
        """Test restore() deep copies metadata to prevent mutation."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        original_metadata = {
            "version": "1.0.0",
            "nested": {"key": "original"},
        }
        registry.restore("test-pack", original_metadata)

        # Mutate the original metadata after restore
        original_metadata["version"] = "MUTATED"
        original_metadata["nested"]["key"] = "MUTATED"

        # Registry should have the original values
        stored = registry.get("test-pack")
        assert stored["version"] == "1.0.0"
        assert stored["nested"]["key"] == "original"

    def test_get_returns_deep_copy(self, temp_dir):
        """Test that get() returns a deep copy to prevent mutation."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0", "nested": {"key": "original"}})

        # Get and mutate the returned copy
        metadata = registry.get("test-pack")
        metadata["version"] = "MUTATED"
        metadata["nested"]["key"] = "MUTATED"

        # Original should be unchanged
        fresh = registry.get("test-pack")
        assert fresh["version"] == "1.0.0"
        assert fresh["nested"]["key"] == "original"

    def test_get_returns_none_for_corrupted_entry(self, temp_dir):
        """Test that get() returns None for corrupted (non-dict) entries."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        # Directly corrupt the registry with non-dict entries
        registry.data["presets"]["corrupted-string"] = "not a dict"
        registry.data["presets"]["corrupted-list"] = ["not", "a", "dict"]
        registry.data["presets"]["corrupted-int"] = 42
        registry._save()

        # All corrupted entries should return None
        assert registry.get("corrupted-string") is None
        assert registry.get("corrupted-list") is None
        assert registry.get("corrupted-int") is None
        # Non-existent should also return None
        assert registry.get("nonexistent") is None

    def test_list_returns_deep_copy(self, temp_dir):
        """Test that list() returns deep copies to prevent mutation."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0", "nested": {"key": "original"}})

        # Get list and mutate
        all_packs = registry.list()
        all_packs["test-pack"]["version"] = "MUTATED"
        all_packs["test-pack"]["nested"]["key"] = "MUTATED"

        # Original should be unchanged
        fresh = registry.get("test-pack")
        assert fresh["version"] == "1.0.0"
        assert fresh["nested"]["key"] == "original"

    def test_list_returns_empty_dict_for_corrupted_registry(self, temp_dir):
        """Test that list() returns empty dict when presets is not a dict."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        # Corrupt the registry - presets is a list instead of dict
        registry.data["presets"] = ["not", "a", "dict"]
        registry._save()

        # list() should return empty dict, not crash
        result = registry.list()
        assert result == {}

    def test_list_by_priority_excludes_disabled(self, temp_dir):
        """Test that list_by_priority excludes disabled presets by default."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("pack-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})
        registry.add("pack-default", {"version": "1.0.0", "priority": 10})  # no enabled field = True

        # Default: exclude disabled
        by_priority = registry.list_by_priority()
        pack_ids = [p[0] for p in by_priority]
        assert "pack-enabled" in pack_ids
        assert "pack-default" in pack_ids
        assert "pack-disabled" not in pack_ids

    def test_list_by_priority_includes_disabled_when_requested(self, temp_dir):
        """Test that list_by_priority includes disabled presets when requested."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-enabled", {"version": "1.0.0", "enabled": True, "priority": 5})
        registry.add("pack-disabled", {"version": "1.0.0", "enabled": False, "priority": 1})

        # Include disabled
        by_priority = registry.list_by_priority(include_disabled=True)
        pack_ids = [p[0] for p in by_priority]
        assert "pack-enabled" in pack_ids
        assert "pack-disabled" in pack_ids
        # Disabled pack has lower priority number, so it comes first when included
        assert pack_ids[0] == "pack-disabled"


# ===== PresetManager Tests =====


class TestPresetManager:
    """Test PresetManager installation and removal."""

    def test_install_from_directory(self, project_dir, pack_dir):
        """Test installing a preset from a directory."""
        manager = PresetManager(project_dir)
        manifest = manager.install_from_directory(pack_dir, "0.1.5")

        assert manifest.id == "test-pack"
        assert manager.registry.is_installed("test-pack")

        # Verify files are copied
        installed_dir = project_dir / ".specify" / "presets" / "test-pack"
        assert installed_dir.exists()
        assert (installed_dir / "preset.yml").exists()
        assert (installed_dir / "templates" / "spec-template.md").exists()

    def test_install_already_installed(self, project_dir, pack_dir):
        """Test installing an already-installed pack raises error."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        with pytest.raises(PresetError, match="already installed"):
            manager.install_from_directory(pack_dir, "0.1.5")

    def test_install_incompatible(self, project_dir, temp_dir, valid_pack_data):
        """Test installing an incompatible pack raises error."""
        valid_pack_data["requires"]["speckit_version"] = ">=99.0.0"
        incompat_dir = temp_dir / "incompat-pack"
        incompat_dir.mkdir()
        manifest_path = incompat_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (incompat_dir / "templates").mkdir()
        (incompat_dir / "templates" / "spec-template.md").write_text("test")

        manager = PresetManager(project_dir)
        with pytest.raises(PresetCompatibilityError):
            manager.install_from_directory(incompat_dir, "0.1.5")

    def test_install_from_zip(self, project_dir, pack_dir, temp_dir):
        """Test installing from a ZIP file."""
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in pack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(pack_dir)
                    zf.write(file_path, arcname)

        manager = PresetManager(project_dir)
        manifest = manager.install_from_zip(zip_path, "0.1.5")
        assert manifest.id == "test-pack"
        assert manager.registry.is_installed("test-pack")

    def test_install_from_zip_nested(self, project_dir, pack_dir, temp_dir):
        """Test installing from ZIP with nested directory."""
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in pack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = Path("test-pack-v1.0.0") / file_path.relative_to(pack_dir)
                    zf.write(file_path, arcname)

        manager = PresetManager(project_dir)
        manifest = manager.install_from_zip(zip_path, "0.1.5")
        assert manifest.id == "test-pack"

    def test_install_from_zip_no_manifest(self, project_dir, temp_dir):
        """Test installing from ZIP without manifest raises error."""
        zip_path = temp_dir / "bad.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("readme.txt", "no manifest here")

        manager = PresetManager(project_dir)
        with pytest.raises(PresetValidationError, match="No preset.yml found"):
            manager.install_from_zip(zip_path, "0.1.5")

    def test_remove(self, project_dir, pack_dir):
        """Test removing a preset."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        assert manager.registry.is_installed("test-pack")

        result = manager.remove("test-pack")
        assert result is True
        assert not manager.registry.is_installed("test-pack")

        installed_dir = project_dir / ".specify" / "presets" / "test-pack"
        assert not installed_dir.exists()

    def test_remove_nonexistent(self, project_dir):
        """Test removing a pack that doesn't exist."""
        manager = PresetManager(project_dir)
        result = manager.remove("nonexistent")
        assert result is False

    def test_list_installed(self, project_dir, pack_dir):
        """Test listing installed packs."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-pack"
        assert installed[0]["name"] == "Test Preset"
        assert installed[0]["version"] == "1.0.0"
        assert installed[0]["template_count"] == 1

    def test_list_installed_empty(self, project_dir):
        """Test listing when no packs installed."""
        manager = PresetManager(project_dir)
        assert manager.list_installed() == []

    def test_get_pack(self, project_dir, pack_dir):
        """Test getting a specific installed pack."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        pack = manager.get_pack("test-pack")
        assert pack is not None
        assert pack.id == "test-pack"

    def test_get_pack_not_installed(self, project_dir):
        """Test getting a non-installed pack returns None."""
        manager = PresetManager(project_dir)
        assert manager.get_pack("nonexistent") is None

    def test_check_compatibility_valid(self, pack_dir, temp_dir):
        """Test compatibility check with valid version."""
        manager = PresetManager(temp_dir)
        manifest = PresetManifest(pack_dir / "preset.yml")
        assert manager.check_compatibility(manifest, "0.1.5") is True

    def test_check_compatibility_invalid(self, pack_dir, temp_dir):
        """Test compatibility check with invalid specifier."""
        manager = PresetManager(temp_dir)
        manifest = PresetManifest(pack_dir / "preset.yml")
        manifest.data["requires"]["speckit_version"] = "not-a-specifier"
        with pytest.raises(PresetCompatibilityError, match="Invalid version specifier"):
            manager.check_compatibility(manifest, "0.1.5")

    def test_install_with_priority(self, project_dir, pack_dir):
        """Test installing a pack with custom priority."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=5)

        metadata = manager.registry.get("test-pack")
        assert metadata is not None
        assert metadata["priority"] == 5

    def test_install_default_priority(self, project_dir, pack_dir):
        """Test that default priority is 10."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        metadata = manager.registry.get("test-pack")
        assert metadata is not None
        assert metadata["priority"] == 10

    def test_list_installed_includes_priority(self, project_dir, pack_dir):
        """Test that list_installed includes priority."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=3)

        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["priority"] == 3


class TestRegistryPriority:
    """Test registry priority sorting."""

    def test_list_by_priority(self, temp_dir):
        """Test that list_by_priority sorts by priority number."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-high", {"version": "1.0.0", "priority": 1})
        registry.add("pack-low", {"version": "1.0.0", "priority": 20})
        registry.add("pack-mid", {"version": "1.0.0", "priority": 10})

        sorted_packs = registry.list_by_priority()
        assert len(sorted_packs) == 3
        assert sorted_packs[0][0] == "pack-high"
        assert sorted_packs[1][0] == "pack-mid"
        assert sorted_packs[2][0] == "pack-low"

    def test_list_by_priority_default(self, temp_dir):
        """Test that packs without priority default to 10."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-a", {"version": "1.0.0"})  # no priority, defaults to 10
        registry.add("pack-b", {"version": "1.0.0", "priority": 5})

        sorted_packs = registry.list_by_priority()
        assert sorted_packs[0][0] == "pack-b"
        assert sorted_packs[1][0] == "pack-a"

    def test_list_by_priority_invalid_priority_defaults(self, temp_dir):
        """Malformed priority values fall back to the default priority."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = PresetRegistry(packs_dir)

        registry.add("pack-high", {"version": "1.0.0", "priority": 1})
        registry.data["presets"]["pack-invalid"] = {
            "version": "1.0.0",
            "priority": "high",
        }
        registry._save()

        sorted_packs = registry.list_by_priority()

        assert [item[0] for item in sorted_packs] == ["pack-high", "pack-invalid"]
        assert sorted_packs[1][1]["priority"] == 10


# ===== PresetResolver Tests =====


class TestPresetResolver:
    """Test PresetResolver priority stack."""

    def test_resolve_core_template(self, project_dir):
        """Test resolving a core template."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert result.name == "spec-template.md"
        assert "Core Spec Template" in result.read_text()

    def test_resolve_nonexistent(self, project_dir):
        """Test resolving a nonexistent template returns None."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("nonexistent-template")
        assert result is None

    def test_resolve_higher_priority_pack_wins(self, project_dir, temp_dir, valid_pack_data):
        """Test that a pack with lower priority number wins over higher number."""
        manager = PresetManager(project_dir)

        # Create pack A (priority 10 — lower precedence)
        pack_a_dir = temp_dir / "pack-a"
        pack_a_dir.mkdir()
        data_a = {**valid_pack_data}
        data_a["preset"] = {**valid_pack_data["preset"], "id": "pack-a", "name": "Pack A"}
        with open(pack_a_dir / "preset.yml", 'w') as f:
            yaml.dump(data_a, f)
        (pack_a_dir / "templates").mkdir()
        (pack_a_dir / "templates" / "spec-template.md").write_text("# From Pack A\n")

        # Create pack B (priority 1 — higher precedence)
        pack_b_dir = temp_dir / "pack-b"
        pack_b_dir.mkdir()
        data_b = {**valid_pack_data}
        data_b["preset"] = {**valid_pack_data["preset"], "id": "pack-b", "name": "Pack B"}
        with open(pack_b_dir / "preset.yml", 'w') as f:
            yaml.dump(data_b, f)
        (pack_b_dir / "templates").mkdir()
        (pack_b_dir / "templates" / "spec-template.md").write_text("# From Pack B\n")

        # Install A first (priority 10), B second (priority 1)
        manager.install_from_directory(pack_a_dir, "0.1.5", priority=10)
        manager.install_from_directory(pack_b_dir, "0.1.5", priority=1)

        # Pack B should win because lower priority number
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "From Pack B" in result.read_text()

    def test_resolve_override_takes_priority(self, project_dir):
        """Test that project overrides take priority over core."""
        # Create override
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override Spec Template\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Override Spec Template" in result.read_text()

    def test_resolve_pack_takes_priority_over_core(self, project_dir, pack_dir):
        """Test that installed packs take priority over core templates."""
        # Install the pack
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()

    def test_resolve_override_takes_priority_over_pack(self, project_dir, pack_dir):
        """Test that overrides take priority over installed packs."""
        # Install the pack
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Create override
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override Spec Template\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Override Spec Template" in result.read_text()

    def test_resolve_extension_provided_templates(self, project_dir):
        """Test resolving templates provided by extensions."""
        # Create extension with templates
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "custom-template.md"
        ext_template.write_text("# Extension Custom Template\n")

        # Register extension in registry
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("my-ext", {"version": "1.0.0", "priority": 10})

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("custom-template")
        assert result is not None
        assert "Extension Custom Template" in result.read_text()

    def test_resolve_disabled_extension_templates_skipped(self, project_dir):
        """Test that disabled extension templates are not resolved."""
        # Create extension with templates
        ext_dir = project_dir / ".specify" / "extensions" / "disabled-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "disabled-template.md"
        ext_template.write_text("# Disabled Extension Template\n")

        # Register extension as disabled
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("disabled-ext", {"version": "1.0.0", "priority": 1, "enabled": False})

        # Template should NOT be resolved because extension is disabled
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("disabled-template")
        assert result is None, "Disabled extension template should not be resolved"

    def test_resolve_disabled_extension_not_picked_up_as_unregistered(self, project_dir):
        """Test that disabled extensions are not picked up via unregistered dir scan."""
        # Create extension directory with templates
        ext_dir = project_dir / ".specify" / "extensions" / "test-disabled-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "unique-disabled-template.md"
        ext_template.write_text("# Should Not Resolve\n")

        # Register the extension but disable it
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("test-disabled-ext", {"version": "1.0.0", "enabled": False})

        # Verify the template is NOT resolved (even though the directory exists)
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("unique-disabled-template")
        assert result is None, "Disabled extension should not be picked up as unregistered"

    def test_resolve_pack_over_extension(self, project_dir, pack_dir, temp_dir, valid_pack_data):
        """Test that pack templates take priority over extension templates."""
        # Create extension with templates
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "spec-template.md"
        ext_template.write_text("# Extension Spec Template\n")

        # Install a pack with the same template
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        # Pack should win over extension
        assert "Custom Spec Template" in result.read_text()

    def test_resolve_with_source_core(self, project_dir):
        """Test resolve_with_source for core template."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("spec-template")
        assert result is not None
        assert result["source"] == "core"
        assert "spec-template.md" in result["path"]

    def test_resolve_with_source_override(self, project_dir):
        """Test resolve_with_source for override template."""
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("spec-template")
        assert result is not None
        assert result["source"] == "project override"

    def test_resolve_with_source_pack(self, project_dir, pack_dir):
        """Test resolve_with_source for pack template."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("spec-template")
        assert result is not None
        assert "test-pack" in result["source"]
        assert "v1.0.0" in result["source"]

    def test_resolve_with_source_extension(self, project_dir):
        """Test resolve_with_source for extension-provided template."""
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "unique-template.md"
        ext_template.write_text("# Unique\n")

        # Register extension in registry
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("my-ext", {"version": "1.0.0", "priority": 10})

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("unique-template")
        assert result is not None
        assert result["source"] == "extension:my-ext v1.0.0"

    def test_resolve_with_source_not_found(self, project_dir):
        """Test resolve_with_source for nonexistent template."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("nonexistent")
        assert result is None

    def test_resolve_skips_hidden_extension_dirs(self, project_dir):
        """Test that hidden directories in extensions are skipped."""
        ext_dir = project_dir / ".specify" / "extensions" / ".backup"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "hidden-template.md"
        ext_template.write_text("# Hidden\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("hidden-template")
        assert result is None


class TestResolveCore:
    """Test PresetResolver.resolve_core() skips the installed-presets tier."""

    def test_resolve_core_does_not_return_preset_files(self, project_dir):
        """resolve_core must not return files from .specify/presets/."""
        preset_cmd_dir = project_dir / ".specify" / "presets" / "my-preset" / "commands"
        preset_cmd_dir.mkdir(parents=True)
        (preset_cmd_dir / "specify.md").write_text("---\ndescription: preset wrap\n---\n\nwrap body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("specify", "command")
        # The preset file must never be returned — but the bundled core may be.
        if result is not None:
            assert "presets" not in result.parts

    def test_resolve_core_returns_core_template(self, project_dir):
        """resolve_core falls through to core templates (tier 4)."""
        core_cmd_dir = project_dir / ".specify" / "templates" / "commands"
        core_cmd_dir.mkdir(parents=True, exist_ok=True)
        (core_cmd_dir / "specify.md").write_text("---\ndescription: core\n---\n\ncore body\n")

        # Also place a preset file — resolve_core must still return the core
        preset_cmd_dir = project_dir / ".specify" / "presets" / "my-preset" / "commands"
        preset_cmd_dir.mkdir(parents=True)
        (preset_cmd_dir / "specify.md").write_text("---\ndescription: preset wrap\n---\n\nwrap body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("specify", "command")
        assert result is not None
        assert "presets" not in result.parts
        assert result.parts[-3:] == ("templates", "commands", "specify.md")

    def test_resolve_core_returns_override(self, project_dir):
        """resolve_core returns tier-1 override if present."""
        override_dir = project_dir / ".specify" / "templates" / "overrides"
        override_dir.mkdir(parents=True)
        (override_dir / "specify.md").write_text("---\ndescription: override\n---\n\noverride body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("specify", "command")
        assert result is not None
        assert result.parts[-2:] == ("overrides", "specify.md")

    def test_resolve_core_returns_extension_template(self, project_dir):
        """resolve_core returns extension templates (tier 3)."""
        ext_cmd_dir = project_dir / ".specify" / "extensions" / "myext" / "commands"
        ext_cmd_dir.mkdir(parents=True)
        (ext_cmd_dir / "myext-cmd.md").write_text("---\ndescription: ext\n---\n\next body\n")

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("myext-cmd", "command")
        assert result is not None
        assert result.parts[-4:-1] == ("extensions", "myext", "commands")

    def test_resolve_core_returns_none_when_nothing_found(self, project_dir):
        """resolve_core returns None when no file found in tiers 1/3/4."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_core("nonexistent", "command")
        assert result is None

    def test_resolve_extension_command_via_manifest_skips_oserror_manifests(self, project_dir):
        """resolve_extension_command_via_manifest skips extensions whose manifest raises OSError."""
        import unittest.mock as mock

        ext_dir = project_dir / ".specify" / "extensions" / "bad-ext"
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "mycmd.md").write_text("---\ndescription: d\n---\n\nbody\n")
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: bad-ext\n  name: Bad\n  version: 1.0.0\n"
            "  description: d\n  author: a\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n  commands:\n"
            "    - name: speckit.bad-ext.mycmd\n"
            "      file: commands/mycmd.md\n"
            "      description: My command\n"
        )

        resolver = PresetResolver(project_dir)
        # Simulate a permission error when opening the manifest file.
        with mock.patch("builtins.open", side_effect=PermissionError("denied")):
            result = resolver.resolve_extension_command_via_manifest("speckit.bad-ext.mycmd")

        assert result is None, "OSError during manifest load must be silently skipped"


class TestExtensionPriorityResolution:
    """Test extension priority resolution with registered and unregistered extensions."""

    def test_unregistered_beats_registered_with_lower_precedence(self, project_dir):
        """Unregistered extension (implicit priority 10) beats registered with priority 20."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create registered extension with priority 20 (lower precedence than 10)
        registered_dir = extensions_dir / "registered-ext"
        (registered_dir / "templates").mkdir(parents=True)
        (registered_dir / "templates" / "test-template.md").write_text("# From Registered\n")

        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("registered-ext", {"version": "1.0.0", "priority": 20})

        # Create unregistered extension directory (implicit priority 10)
        unregistered_dir = extensions_dir / "unregistered-ext"
        (unregistered_dir / "templates").mkdir(parents=True)
        (unregistered_dir / "templates" / "test-template.md").write_text("# From Unregistered\n")

        # Unregistered (priority 10) should beat registered (priority 20)
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("test-template")
        assert result is not None
        assert "From Unregistered" in result.read_text()

    def test_registered_with_higher_precedence_beats_unregistered(self, project_dir):
        """Registered extension with priority 5 beats unregistered (implicit priority 10)."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create registered extension with priority 5 (higher precedence than 10)
        registered_dir = extensions_dir / "registered-ext"
        (registered_dir / "templates").mkdir(parents=True)
        (registered_dir / "templates" / "test-template.md").write_text("# From Registered\n")

        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("registered-ext", {"version": "1.0.0", "priority": 5})

        # Create unregistered extension directory (implicit priority 10)
        unregistered_dir = extensions_dir / "unregistered-ext"
        (unregistered_dir / "templates").mkdir(parents=True)
        (unregistered_dir / "templates" / "test-template.md").write_text("# From Unregistered\n")

        # Registered (priority 5) should beat unregistered (priority 10)
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("test-template")
        assert result is not None
        assert "From Registered" in result.read_text()

    def test_unregistered_attribution_with_priority_ordering(self, project_dir):
        """Test resolve_with_source correctly attributes unregistered extension."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create registered extension with priority 20
        registered_dir = extensions_dir / "registered-ext"
        (registered_dir / "templates").mkdir(parents=True)
        (registered_dir / "templates" / "test-template.md").write_text("# From Registered\n")

        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("registered-ext", {"version": "1.0.0", "priority": 20})

        # Create unregistered extension (implicit priority 10)
        unregistered_dir = extensions_dir / "unregistered-ext"
        (unregistered_dir / "templates").mkdir(parents=True)
        (unregistered_dir / "templates" / "test-template.md").write_text("# From Unregistered\n")

        # Attribution should show unregistered extension
        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("test-template")
        assert result is not None
        assert "unregistered-ext" in result["source"]
        assert "(unregistered)" in result["source"]

    def test_same_priority_sorted_alphabetically(self, project_dir):
        """Extensions with same priority are sorted alphabetically by ID."""
        extensions_dir = project_dir / ".specify" / "extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)

        # Create two unregistered extensions (both implicit priority 10)
        # "aaa-ext" should come before "zzz-ext" alphabetically
        zzz_dir = extensions_dir / "zzz-ext"
        (zzz_dir / "templates").mkdir(parents=True)
        (zzz_dir / "templates" / "test-template.md").write_text("# From ZZZ\n")

        aaa_dir = extensions_dir / "aaa-ext"
        (aaa_dir / "templates").mkdir(parents=True)
        (aaa_dir / "templates" / "test-template.md").write_text("# From AAA\n")

        # AAA should win due to alphabetical ordering at same priority
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("test-template")
        assert result is not None
        assert "From AAA" in result.read_text()


# ===== PresetCatalog Tests =====


class TestPresetCatalog:
    """Test template catalog functionality."""

    def test_default_catalog_url(self, project_dir):
        """Test default catalog URL."""
        catalog = PresetCatalog(project_dir)
        assert catalog.DEFAULT_CATALOG_URL.startswith("https://")
        assert catalog.DEFAULT_CATALOG_URL.endswith("/presets/catalog.json")

    def test_community_catalog_url(self, project_dir):
        """Test community catalog URL."""
        catalog = PresetCatalog(project_dir)
        assert "presets/catalog.community.json" in catalog.COMMUNITY_CATALOG_URL

    def test_cache_validation_no_cache(self, project_dir):
        """Test cache validation when no cache exists."""
        catalog = PresetCatalog(project_dir)
        assert catalog.is_cache_valid() is False

    def test_cache_validation_valid(self, project_dir):
        """Test cache validation with valid cache."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text(json.dumps({
            "schema_version": "1.0",
            "presets": {},
        }))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        assert catalog.is_cache_valid() is True

    def test_cache_validation_expired(self, project_dir):
        """Test cache validation with expired cache."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text(json.dumps({
            "schema_version": "1.0",
            "presets": {},
        }))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": "2020-01-01T00:00:00+00:00",
        }))

        assert catalog.is_cache_valid() is False

    def test_cache_validation_corrupted(self, project_dir):
        """Test cache validation with corrupted metadata."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text("not json")
        catalog.cache_metadata_file.write_text("not json")

        assert catalog.is_cache_valid() is False

    def test_clear_cache(self, project_dir):
        """Test clearing the cache."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}")
        catalog.cache_metadata_file.write_text("{}")

        catalog.clear_cache()

        assert not catalog.cache_file.exists()
        assert not catalog.cache_metadata_file.exists()

    def test_search_with_cached_data(self, project_dir, monkeypatch):
        """Test search with cached catalog data."""
        from unittest.mock import patch

        monkeypatch.delenv("SPECKIT_PRESET_CATALOG_URL", raising=False)
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog_data = {
            "schema_version": "1.0",
            "presets": {
                "safe-agile": {
                    "name": "SAFe Agile Templates",
                    "description": "SAFe-aligned templates",
                    "author": "agile-community",
                    "version": "1.0.0",
                    "tags": ["safe", "agile"],
                },
                "healthcare": {
                    "name": "Healthcare Compliance",
                    "description": "HIPAA-compliant templates",
                    "author": "healthcare-org",
                    "version": "1.0.0",
                    "tags": ["healthcare", "hipaa"],
                },
            }
        }

        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        # Isolate from community catalog so results are deterministic
        default_only = [PresetCatalogEntry(url=catalog.DEFAULT_CATALOG_URL, name="default", priority=1, install_allowed=True)]
        with patch.object(catalog, "get_active_catalogs", return_value=default_only):
            # Search by query
            results = catalog.search(query="agile")
            assert len(results) == 1
            assert results[0]["id"] == "safe-agile"

            # Search by tag
            results = catalog.search(tag="hipaa")
            assert len(results) == 1
            assert results[0]["id"] == "healthcare"

            # Search by author
            results = catalog.search(author="agile-community")
            assert len(results) == 1

            # Search all
            results = catalog.search()
            assert len(results) == 2

    def test_get_pack_info(self, project_dir):
        """Test getting info for a specific pack."""
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog_data = {
            "schema_version": "1.0",
            "presets": {
                "test-pack": {
                    "name": "Test Pack",
                    "version": "1.0.0",
                },
            }
        }

        catalog.cache_file.write_text(json.dumps(catalog_data))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        info = catalog.get_pack_info("test-pack")
        assert info is not None
        assert info["name"] == "Test Pack"
        assert info["id"] == "test-pack"

        assert catalog.get_pack_info("nonexistent") is None

    def test_validate_catalog_url_https(self, project_dir):
        """Test that HTTPS URLs are accepted."""
        catalog = PresetCatalog(project_dir)
        catalog._validate_catalog_url("https://example.com/catalog.json")

    def test_validate_catalog_url_http_rejected(self, project_dir):
        """Test that HTTP URLs are rejected."""
        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="must use HTTPS"):
            catalog._validate_catalog_url("http://example.com/catalog.json")

    def test_validate_catalog_url_localhost_http_allowed(self, project_dir):
        """Test that HTTP is allowed for localhost."""
        catalog = PresetCatalog(project_dir)
        catalog._validate_catalog_url("http://localhost:8080/catalog.json")
        catalog._validate_catalog_url("http://127.0.0.1:8080/catalog.json")

    def test_env_var_catalog_url(self, project_dir, monkeypatch):
        """Test catalog URL from environment variable."""
        monkeypatch.setenv("SPECKIT_PRESET_CATALOG_URL", "https://custom.example.com/catalog.json")
        catalog = PresetCatalog(project_dir)
        assert catalog.get_catalog_url() == "https://custom.example.com/catalog.json"

    # --- _make_request / GitHub auth ---

    def test_make_request_no_token_no_auth_header(self, project_dir, monkeypatch):
        """Without a token, requests carry no Authorization header."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_whitespace_only_github_token_ignored(self, project_dir, monkeypatch):
        """A whitespace-only GITHUB_TOKEN is treated as unset."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_whitespace_github_token_falls_back_to_gh_token(self, project_dir, monkeypatch):
        """When GITHUB_TOKEN is whitespace-only, GH_TOKEN is used as fallback."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.setenv("GH_TOKEN", "ghp_fallback")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_fallback"

    def test_make_request_github_token_added_for_github_url(self, project_dir, monkeypatch):
        """GITHUB_TOKEN is attached for raw.githubusercontent.com URLs."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_gh_token_fallback(self, project_dir, monkeypatch):
        """GH_TOKEN is used when GITHUB_TOKEN is absent."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GH_TOKEN", "ghp_ghtoken")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://github.com/org/repo/releases/download/v1/pack.zip")
        assert req.get_header("Authorization") == "Bearer ghp_ghtoken"

    def test_make_request_github_token_takes_precedence(self, project_dir, monkeypatch):
        """GITHUB_TOKEN takes precedence over GH_TOKEN when both are set."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_primary")
        monkeypatch.setenv("GH_TOKEN", "ghp_secondary")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://api.github.com/repos/org/repo")
        assert req.get_header("Authorization") == "Bearer ghp_primary"

    def test_make_request_token_added_for_codeload_github_com(self, project_dir, monkeypatch):
        """GITHUB_TOKEN is attached for codeload.github.com URLs (GitHub archive redirects)."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://codeload.github.com/org/repo/zip/refs/tags/v1.0.0")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_token_not_added_for_non_github_url(self, project_dir, monkeypatch):
        """Auth header is never attached to non-GitHub URLs to prevent credential leakage."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://internal.example.com/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_token_not_added_for_github_lookalike_host(self, project_dir, monkeypatch):
        """Auth header is not attached to hosts that include github.com as a suffix."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://github.com.evil.com/org/repo/releases/download/v1/pack.zip")
        assert "Authorization" not in req.headers

    def test_make_request_token_not_added_for_github_in_path(self, project_dir, monkeypatch):
        """Auth header is not attached when github.com appears only in the URL path."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://evil.example.com/github.com/org/repo/releases/download/v1/pack.zip")
        assert "Authorization" not in req.headers

    def test_make_request_token_not_added_for_github_in_query(self, project_dir, monkeypatch):
        """Auth header is not attached when github.com appears only in the query string."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://evil.example.com/download?source=https://github.com/org/repo/v1/pack.zip")
        assert "Authorization" not in req.headers

    def test_fetch_single_catalog_sends_auth_header(self, project_dir, monkeypatch):
        """_fetch_single_catalog passes Authorization header via opener for GitHub URLs."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        catalog = PresetCatalog(project_dir)

        catalog_data = {"schema_version": "1.0", "presets": {}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(catalog_data).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        captured = {}
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured["req"] = req
            return mock_response

        mock_opener.open.side_effect = fake_open

        entry = PresetCatalogEntry(
            url="https://raw.githubusercontent.com/org/repo/main/presets/catalog.json",
            name="private",
            priority=1,
            install_allowed=True,
        )

        with patch("urllib.request.build_opener", return_value=mock_opener):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert captured["req"].get_header("Authorization") == "Bearer ghp_testtoken"

    def test_download_pack_sends_auth_header(self, project_dir, monkeypatch):
        """download_pack passes Authorization header via opener for GitHub URLs."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        catalog = PresetCatalog(project_dir)

        import io
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", "id: test-pack\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        mock_response = MagicMock()
        mock_response.read.return_value = zip_bytes
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        captured = {}
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured["req"] = req
            return mock_response

        mock_opener.open.side_effect = fake_open

        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://github.com/org/repo/releases/download/v1/test-pack.zip",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch("urllib.request.build_opener", return_value=mock_opener):
            catalog.download_pack("test-pack", target_dir=project_dir)

        assert captured["req"].get_header("Authorization") == "Bearer ghp_testtoken"


# ===== Integration Tests =====


class TestIntegration:
    """Integration tests for complete preset workflows."""

    def test_full_install_resolve_remove_cycle(self, project_dir, pack_dir):
        """Test complete lifecycle: install → resolve → remove."""
        # Install
        manager = PresetManager(project_dir)
        manifest = manager.install_from_directory(pack_dir, "0.1.5")
        assert manifest.id == "test-pack"

        # Resolve — pack template should win over core
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()

        # Remove
        manager.remove("test-pack")

        # Resolve — should fall back to core
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Core Spec Template" in result.read_text()

    def test_override_beats_pack_beats_extension_beats_core(self, project_dir, pack_dir):
        """Test the full priority stack: override > pack > extension > core."""
        resolver = PresetResolver(project_dir)

        # Core should resolve
        result = resolver.resolve_with_source("spec-template")
        assert result["source"] == "core"

        # Add extension template
        ext_dir = project_dir / ".specify" / "extensions" / "my-ext"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        (ext_templates_dir / "spec-template.md").write_text("# Extension\n")

        # Register extension in registry
        extensions_dir = project_dir / ".specify" / "extensions"
        ext_registry = ExtensionRegistry(extensions_dir)
        ext_registry.add("my-ext", {"version": "1.0.0", "priority": 10})

        result = resolver.resolve_with_source("spec-template")
        assert result["source"] == "extension:my-ext v1.0.0"

        # Install pack — should win over extension
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        result = resolver.resolve_with_source("spec-template")
        assert "test-pack" in result["source"]

        # Add override — should win over pack
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "spec-template.md").write_text("# Override\n")

        result = resolver.resolve_with_source("spec-template")
        assert result["source"] == "project override"

    def test_install_from_zip_then_resolve(self, project_dir, pack_dir, temp_dir):
        """Test installing from ZIP and then resolving."""
        # Create ZIP
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in pack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(pack_dir)
                    zf.write(file_path, arcname)

        # Install
        manager = PresetManager(project_dir)
        manager.install_from_zip(zip_path, "0.1.5")

        # Resolve
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()


# ===== PresetCatalogEntry Tests =====


class TestPresetCatalogEntry:
    """Test PresetCatalogEntry dataclass."""

    def test_create_entry(self):
        """Test creating a catalog entry."""
        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=True,
            description="Test catalog",
        )
        assert entry.url == "https://example.com/catalog.json"
        assert entry.name == "test"
        assert entry.priority == 1
        assert entry.install_allowed is True
        assert entry.description == "Test catalog"

    def test_default_description(self):
        """Test default empty description."""
        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="test",
            priority=1,
            install_allowed=False,
        )
        assert entry.description == ""


# ===== Multi-Catalog Tests =====


class TestPresetCatalogMultiCatalog:
    """Test multi-catalog support in PresetCatalog."""

    def test_default_active_catalogs(self, project_dir):
        """Test that default catalogs are returned when no config exists."""
        catalog = PresetCatalog(project_dir)
        active = catalog.get_active_catalogs()
        assert len(active) == 2
        assert active[0].name == "default"
        assert active[0].priority == 1
        assert active[0].install_allowed is True
        assert active[1].name == "community"
        assert active[1].priority == 2
        assert active[1].install_allowed is False

    def test_env_var_overrides_catalogs(self, project_dir, monkeypatch):
        """Test that SPECKIT_PRESET_CATALOG_URL env var overrides defaults."""
        monkeypatch.setenv(
            "SPECKIT_PRESET_CATALOG_URL",
            "https://custom.example.com/catalog.json",
        )
        catalog = PresetCatalog(project_dir)
        active = catalog.get_active_catalogs()
        assert len(active) == 1
        assert active[0].name == "custom"
        assert active[0].url == "https://custom.example.com/catalog.json"
        assert active[0].install_allowed is True

    def test_project_config_overrides_defaults(self, project_dir):
        """Test that project-level config overrides built-in defaults."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "my-catalog",
                    "url": "https://my.example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        active = catalog.get_active_catalogs()
        assert len(active) == 1
        assert active[0].name == "my-catalog"
        assert active[0].url == "https://my.example.com/catalog.json"

    def test_load_catalog_config_nonexistent(self, project_dir):
        """Test loading config from nonexistent file returns None."""
        catalog = PresetCatalog(project_dir)
        result = catalog._load_catalog_config(
            project_dir / ".specify" / "nonexistent.yml"
        )
        assert result is None

    def test_load_catalog_config_empty(self, project_dir):
        """Test loading empty config returns None."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text("")

        catalog = PresetCatalog(project_dir)
        result = catalog._load_catalog_config(config_path)
        assert result is None

    def test_load_catalog_config_invalid_yaml(self, project_dir):
        """Test loading invalid YAML raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(": invalid: {{{")

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Failed to read"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_not_a_list(self, project_dir):
        """Test that non-list catalogs key raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({"catalogs": "not-a-list"}))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="must be a list"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_invalid_entry(self, project_dir):
        """Test that non-dict entry raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({"catalogs": ["not-a-dict"]}))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="expected a mapping"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_http_url_rejected(self, project_dir):
        """Test that HTTP URLs are rejected."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "bad",
                    "url": "http://insecure.example.com/catalog.json",
                    "priority": 1,
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="must use HTTPS"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_priority_sorting(self, project_dir):
        """Test that catalogs are sorted by priority."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "low-priority",
                    "url": "https://low.example.com/catalog.json",
                    "priority": 10,
                    "install_allowed": False,
                },
                {
                    "name": "high-priority",
                    "url": "https://high.example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": True,
                },
            ]
        }))

        catalog = PresetCatalog(project_dir)
        entries = catalog._load_catalog_config(config_path)
        assert entries is not None
        assert len(entries) == 2
        assert entries[0].name == "high-priority"
        assert entries[1].name == "low-priority"

    def test_load_catalog_config_invalid_priority(self, project_dir):
        """Test that invalid priority raises error."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "bad",
                    "url": "https://example.com/catalog.json",
                    "priority": "not-a-number",
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid priority"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_install_allowed_string(self, project_dir):
        """Test that install_allowed accepts string values."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "test",
                    "url": "https://example.com/catalog.json",
                    "priority": 1,
                    "install_allowed": "true",
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        entries = catalog._load_catalog_config(config_path)
        assert entries is not None
        assert entries[0].install_allowed is True

    def test_get_catalog_url_uses_highest_priority(self, project_dir):
        """Test that get_catalog_url returns URL of highest priority catalog."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "secondary",
                    "url": "https://secondary.example.com/catalog.json",
                    "priority": 5,
                },
                {
                    "name": "primary",
                    "url": "https://primary.example.com/catalog.json",
                    "priority": 1,
                },
            ]
        }))

        catalog = PresetCatalog(project_dir)
        assert catalog.get_catalog_url() == "https://primary.example.com/catalog.json"

    def test_cache_paths_default_url(self, project_dir):
        """Test cache paths for default catalog URL use legacy locations."""
        catalog = PresetCatalog(project_dir)
        cache_file, metadata_file = catalog._get_cache_paths(
            PresetCatalog.DEFAULT_CATALOG_URL
        )
        assert cache_file == catalog.cache_file
        assert metadata_file == catalog.cache_metadata_file

    def test_cache_paths_custom_url(self, project_dir):
        """Test cache paths for custom URLs use hash-based files."""
        catalog = PresetCatalog(project_dir)
        cache_file, metadata_file = catalog._get_cache_paths(
            "https://custom.example.com/catalog.json"
        )
        assert cache_file != catalog.cache_file
        assert "catalog-" in cache_file.name
        assert cache_file.name.endswith(".json")

    def test_url_cache_valid(self, project_dir):
        """Test URL-specific cache validation."""
        catalog = PresetCatalog(project_dir)
        url = "https://custom.example.com/catalog.json"
        cache_file, metadata_file = catalog._get_cache_paths(url)

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"schema_version": "1.0", "presets": {}}))
        metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        assert catalog._is_url_cache_valid(url) is True

    def test_url_cache_expired(self, project_dir):
        """Test URL-specific cache expiration."""
        catalog = PresetCatalog(project_dir)
        url = "https://custom.example.com/catalog.json"
        cache_file, metadata_file = catalog._get_cache_paths(url)

        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"schema_version": "1.0", "presets": {}}))
        metadata_file.write_text(json.dumps({
            "cached_at": "2020-01-01T00:00:00+00:00",
        }))

        assert catalog._is_url_cache_valid(url) is False


# ===== Self-Test Preset Tests =====


SELF_TEST_PRESET_DIR = Path(__file__).parent.parent / "presets" / "self-test"

CORE_TEMPLATE_NAMES = [
    "spec-template",
    "plan-template",
    "tasks-template",
    "checklist-template",
    "constitution-template",
]


class TestSelfTestPreset:
    """Tests using the self-test preset that ships with the repo."""

    def test_self_test_preset_exists(self):
        """Verify the self-test preset directory and manifest exist."""
        assert SELF_TEST_PRESET_DIR.exists()
        assert (SELF_TEST_PRESET_DIR / "preset.yml").exists()

    def test_self_test_manifest_valid(self):
        """Verify the self-test preset manifest is valid."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        assert manifest.id == "self-test"
        assert manifest.name == "Self-Test Preset"
        assert manifest.version == "1.0.0"
        assert len(manifest.templates) == 8  # 6 templates + 2 commands

    def test_self_test_provides_all_core_templates(self):
        """Verify the self-test preset provides an override for every core template."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        provided_names = {t["name"] for t in manifest.templates}
        for name in CORE_TEMPLATE_NAMES:
            assert name in provided_names, f"Self-test preset missing template: {name}"

    def test_self_test_template_files_exist(self):
        """Verify that all declared template files actually exist on disk."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        for tmpl in manifest.templates:
            tmpl_path = SELF_TEST_PRESET_DIR / tmpl["file"]
            assert tmpl_path.exists(), f"Missing template file: {tmpl['file']}"

    def test_self_test_templates_have_marker(self):
        """Verify each template contains the preset:self-test marker."""
        for name in CORE_TEMPLATE_NAMES:
            tmpl_path = SELF_TEST_PRESET_DIR / "templates" / f"{name}.md"
            content = tmpl_path.read_text()
            assert "preset:self-test" in content, f"{name}.md missing preset:self-test marker"

    def test_install_self_test_preset(self, project_dir):
        """Test installing the self-test preset from its directory."""
        manager = PresetManager(project_dir)
        manifest = manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")
        assert manifest.id == "self-test"
        assert manager.registry.is_installed("self-test")

    def test_self_test_overrides_all_core_templates(self, project_dir):
        """Test that installing self-test overrides every core template."""
        # Set up core templates in the project
        templates_dir = project_dir / ".specify" / "templates"
        for name in CORE_TEMPLATE_NAMES:
            (templates_dir / f"{name}.md").write_text(f"# Core {name}\n")

        # Install self-test preset
        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        # Every core template should now resolve from the preset
        resolver = PresetResolver(project_dir)
        for name in CORE_TEMPLATE_NAMES:
            result = resolver.resolve(name)
            assert result is not None, f"{name} did not resolve"
            content = result.read_text()
            assert "preset:self-test" in content, (
                f"{name} resolved but not from self-test preset"
            )

    def test_self_test_resolve_with_source(self, project_dir):
        """Test that resolve_with_source attributes templates to self-test."""
        templates_dir = project_dir / ".specify" / "templates"
        for name in CORE_TEMPLATE_NAMES:
            (templates_dir / f"{name}.md").write_text(f"# Core {name}\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        resolver = PresetResolver(project_dir)
        for name in CORE_TEMPLATE_NAMES:
            result = resolver.resolve_with_source(name)
            assert result is not None, f"{name} did not resolve"
            assert "self-test" in result["source"], (
                f"{name} source is '{result['source']}', expected self-test"
            )

    def test_self_test_removal_restores_core(self, project_dir):
        """Test that removing self-test falls back to core templates."""
        templates_dir = project_dir / ".specify" / "templates"
        for name in CORE_TEMPLATE_NAMES:
            (templates_dir / f"{name}.md").write_text(f"# Core {name}\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")
        manager.remove("self-test")

        resolver = PresetResolver(project_dir)
        for name in CORE_TEMPLATE_NAMES:
            result = resolver.resolve_with_source(name)
            assert result is not None
            assert result["source"] == "core"

    def test_self_test_not_in_catalog(self):
        """Verify the self-test preset is NOT in the catalog (it's local-only)."""
        catalog_path = Path(__file__).parent.parent / "presets" / "catalog.json"
        catalog_data = json.loads(catalog_path.read_text())
        assert "self-test" not in catalog_data["presets"]

    def test_self_test_has_command(self):
        """Verify the self-test preset includes a command override."""
        manifest = PresetManifest(SELF_TEST_PRESET_DIR / "preset.yml")
        commands = [t for t in manifest.templates if t["type"] == "command"]
        assert len(commands) >= 1
        assert commands[0]["name"] == "speckit.specify"

    def test_self_test_command_file_exists(self):
        """Verify the self-test command file exists on disk."""
        cmd_path = SELF_TEST_PRESET_DIR / "commands" / "speckit.specify.md"
        assert cmd_path.exists()
        content = cmd_path.read_text()
        assert "preset:self-test" in content

    def test_self_test_registers_commands_for_claude(self, project_dir):
        """Test that installing self-test registers skills in .claude/skills/."""
        # Create Claude skills directory to simulate Claude being set up
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        # Check the skill was registered
        cmd_file = claude_dir / "speckit-specify" / "SKILL.md"
        assert cmd_file.exists(), "Skill not registered in .claude/skills/"
        content = cmd_file.read_text()
        assert "self-test" in content
        assert "source:" in content  # skill frontmatter includes metadata.source

    def test_self_test_registers_commands_for_gemini(self, project_dir):
        """Test that installing self-test registers commands in .gemini/commands/ as TOML."""
        # Create Gemini agent directory
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        # Check the command was registered in TOML format
        cmd_file = gemini_dir / "speckit.specify.toml"
        assert cmd_file.exists(), "Command not registered in .gemini/commands/"
        content = cmd_file.read_text()
        assert "prompt" in content  # TOML format has a prompt field
        assert "{{args}}" in content  # Gemini uses {{args}} placeholder

    def test_self_test_unregisters_commands_on_remove(self, project_dir):
        """Test that removing self-test cleans up registered commands."""
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        cmd_file = claude_dir / "speckit-specify" / "SKILL.md"
        assert cmd_file.exists()

        manager.remove("self-test")
        assert not cmd_file.exists(), "Command not cleaned up after preset removal"

    def test_self_test_no_commands_without_agent_dirs(self, project_dir):
        """Test that no commands are registered when no agent dirs exist."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        metadata = manager.registry.get("self-test")
        assert metadata["registered_commands"] == {}

    def test_extension_command_skipped_when_extension_missing(self, project_dir, temp_dir):
        """Test that extension command overrides are skipped if the extension isn't installed."""
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        preset_dir = temp_dir / "ext-override-preset"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\nOverridden content"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-override",
                "name": "Ext Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                        "description": "Override fakeext cmd",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        # Extension not installed — command should NOT be registered
        cmd_file = claude_dir / "speckit.fakeext.cmd.md"
        assert not cmd_file.exists(), "Command registered for missing extension"
        metadata = manager.registry.get("ext-override")
        assert metadata["registered_commands"] == {}

    def test_extension_command_registered_when_extension_present(self, project_dir, temp_dir):
        """Test that extension command overrides ARE registered when the extension is installed."""
        claude_dir = project_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)
        (project_dir / ".specify" / "extensions" / "fakeext").mkdir(parents=True)

        preset_dir = temp_dir / "ext-override-preset2"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\nOverridden content"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-override2",
                "name": "Ext Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                        "description": "Override fakeext cmd",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_file = claude_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert cmd_file.exists(), "Skill not registered despite extension being present"


# ===== Init Options and Skills Tests =====


class TestInitOptions:
    """Tests for save_init_options / load_init_options helpers."""

    def test_save_and_load_round_trip(self, project_dir):
        from specify_cli import save_init_options, load_init_options

        opts = {"ai": "claude", "ai_skills": True, "here": False}
        save_init_options(project_dir, opts)

        loaded = load_init_options(project_dir)
        assert loaded["ai"] == "claude"
        assert loaded["ai_skills"] is True

    def test_load_returns_empty_when_missing(self, project_dir):
        from specify_cli import load_init_options

        assert load_init_options(project_dir) == {}

    def test_load_returns_empty_on_invalid_json(self, project_dir):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text("{bad json")

        assert load_init_options(project_dir) == {}


class TestPresetSkills:
    """Tests for preset skill registration and unregistration."""

    def _write_init_options(self, project_dir, ai="claude", ai_skills=True, script="sh"):
        from specify_cli import save_init_options

        save_init_options(project_dir, {"ai": ai, "ai_skills": ai_skills, "script": script})

    def _create_skill(self, skills_dir, skill_name, body="original body"):
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_name}\n---\n\n{body}\n"
        )
        return skill_dir

    def test_skill_overridden_on_preset_install(self, project_dir, temp_dir):
        """When --ai-skills was used, a preset command override should update the skill."""
        # Simulate --ai-skills having been used: write init-options + create skill
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # Also create the claude commands dir so commands get registered
        (project_dir / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

        # Install self-test preset (has a command override for speckit.specify)
        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content, "Skill should reference preset source"
        assert "disable-model-invocation: false" in content

        # Verify it was recorded in registry
        metadata = manager.registry.get("self-test")
        assert "speckit-specify" in metadata.get("registered_skills", [])

    def test_skill_not_updated_when_ai_skills_disabled(self, project_dir, temp_dir):
        """When --ai-skills was NOT used, preset install should not touch skills."""
        self._write_init_options(project_dir, ai="qwen", ai_skills=False)
        skills_dir = project_dir / ".qwen" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()
        assert "untouched" in content, "Skill should not be modified when ai_skills=False"

    def test_get_skills_dir_returns_none_for_non_string_ai(self, project_dir):
        """Corrupted init-options ai values should not crash preset skill resolution."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text('{"ai":["codex"],"ai_skills":true,"script":"sh"}')

        manager = PresetManager(project_dir)

        assert manager._get_skills_dir() is None

    def test_get_skills_dir_returns_none_for_non_dict_init_options(self, project_dir):
        """Corrupted non-dict init-options payloads should fail closed."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text("[]")

        manager = PresetManager(project_dir)

        assert manager._get_skills_dir() is None

    def test_skill_not_updated_without_init_options(self, project_dir, temp_dir):
        """When no init-options.json exists, preset install should not touch skills."""
        skills_dir = project_dir / ".qwen" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        file_content = skill_file.read_text()
        assert "untouched" in file_content

    def test_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """When a preset is removed, skills should be restored from core templates."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        (project_dir / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

        # Set up core command template in the project so restoration works
        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text("---\ndescription: Core specify command\n---\n\nCore specify body\n")

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        # Verify preset content is in the skill
        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset:self-test" in skill_file.read_text()

        # Remove the preset
        manager.remove("self-test")

        # Skill should be restored (core specify.md template exists)
        assert skill_file.exists(), "Skill should still exist after preset removal"
        content = skill_file.read_text()
        assert "preset:self-test" not in content, "Preset content should be gone"
        assert "templates/commands/specify.md" in content, "Should reference core template"
        assert "disable-model-invocation: false" in content

    def test_skill_restored_on_remove_resolves_script_placeholders(self, project_dir):
        """Core restore should resolve {SCRIPT}/{ARGS} placeholders like other skill paths."""
        self._write_init_options(project_dir, ai="claude", ai_skills=True, script="sh")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="old")
        (project_dir / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\n"
            "description: Core specify command\n"
            "scripts:\n"
            "  sh: .specify/scripts/bash/create-new-feature.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "Run:\n"
            "{SCRIPT}\n"
        )

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")
        manager.remove("self-test")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "{SCRIPT}" not in content
        assert "{ARGS}" not in content
        assert ".specify/scripts/bash/create-new-feature.sh --json \"$ARGUMENTS\"" in content

    def test_skill_not_overridden_when_skill_path_is_file(self, project_dir):
        """Preset install should skip non-directory skill targets."""
        self._write_init_options(project_dir, ai="qwen")
        skills_dir = project_dir / ".qwen" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "speckit-specify").write_text("not-a-directory")

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        assert (skills_dir / "speckit-specify").is_file()
        metadata = manager.registry.get("self-test")
        assert "speckit-specify" not in metadata.get("registered_skills", [])

    def test_no_skills_registered_when_no_skill_dir_exists(self, project_dir, temp_dir):
        """Skills should not be created when no existing skill dir is found."""
        self._write_init_options(project_dir, ai="claude")
        # Don't create skills dir — simulate --ai-skills never created them

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        metadata = manager.registry.get("self-test")
        assert metadata.get("registered_skills", []) == []

    def test_extension_skill_override_matches_hyphenated_multisegment_name(self, project_dir, temp_dir):
        """Preset overrides for speckit.<ext>.<cmd> should target speckit-<ext>-<cmd> skills."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="untouched")
        (project_dir / ".specify" / "extensions" / "fakeext").mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / "ext-skill-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset:ext-skill-override\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-skill-override",
                "name": "Ext Skill Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:ext-skill-override" in content
        assert "name: speckit-fakeext-cmd" in content
        assert "# Speckit Fakeext Cmd Skill" in content

        metadata = manager.registry.get("ext-skill-override")
        assert "speckit-fakeext-cmd" in metadata.get("registered_skills", [])

    def test_extension_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """Preset removal should restore an extension-backed skill instead of deleting it."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="original extension skill")

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\n"
            "description: Extension fakeext cmd\n"
            "scripts:\n"
            "  sh: ../../scripts/bash/setup-plan.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "extension:fakeext\n"
            "Run {SCRIPT}\n"
        )
        extension_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "fakeext",
                "name": "Fake Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/cmd.md",
                        "description": "Fake extension command",
                    }
                ]
            },
        }
        with open(extension_dir / "extension.yml", "w") as f:
            yaml.dump(extension_manifest, f)

        preset_dir = temp_dir / "ext-skill-restore"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset:ext-skill-restore\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-skill-restore",
                "name": "Ext Skill Restore",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert "preset:ext-skill-restore" in skill_file.read_text()

        manager.remove("ext-skill-restore")

        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:ext-skill-restore" not in content
        assert "source: extension:fakeext" in content
        assert "extension:fakeext" in content
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content
        assert "# Fakeext Cmd Skill" in content

    def test_preset_remove_skips_skill_dir_without_skill_file(self, project_dir, temp_dir):
        """Preset removal should not delete arbitrary directories missing SKILL.md."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        stray_skill_dir = skills_dir / "speckit-fakeext-cmd"
        stray_skill_dir.mkdir(parents=True, exist_ok=True)
        note_file = stray_skill_dir / "notes.txt"
        note_file.write_text("user content", encoding="utf-8")

        preset_dir = temp_dir / "ext-skill-missing-file"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset:ext-skill-missing-file\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-skill-missing-file",
                "name": "Ext Skill Missing File",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        installed_preset_dir = manager.presets_dir / "ext-skill-missing-file"
        shutil.copytree(preset_dir, installed_preset_dir)
        manager.registry.add(
            "ext-skill-missing-file",
            {
                "version": "1.0.0",
                "source": str(preset_dir),
                "provides_templates": ["speckit.fakeext.cmd"],
                "registered_skills": ["speckit-fakeext-cmd"],
                "priority": 10,
            },
        )

        manager.remove("ext-skill-missing-file")

        assert stray_skill_dir.is_dir()
        assert note_file.read_text(encoding="utf-8") == "user content"

    def test_kimi_legacy_dotted_skill_override_still_applies(self, project_dir, temp_dir):
        """Preset overrides should still target legacy dotted Kimi skill directories."""
        self._write_init_options(project_dir, ai="kimi")
        skills_dir = project_dir / ".kimi" / "skills"
        self._create_skill(skills_dir, "speckit.specify", body="untouched")

        (project_dir / ".kimi" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        self_test_dir = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(self_test_dir, "0.1.5")

        skill_file = skills_dir / "speckit.specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content
        assert "name: speckit.specify" in content

        metadata = manager.registry.get("self-test")
        assert "speckit.specify" in metadata.get("registered_skills", [])

    def test_kimi_skill_updated_even_when_ai_skills_disabled(self, project_dir, temp_dir):
        """Kimi presets should still propagate command overrides to existing skills."""
        self._write_init_options(project_dir, ai="kimi", ai_skills=False)
        skills_dir = project_dir / ".kimi" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        (project_dir / ".kimi" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        self_test_dir = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(self_test_dir, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content
        assert "name: speckit-specify" in content

        metadata = manager.registry.get("self-test")
        assert "speckit-specify" in metadata.get("registered_skills", [])

    def test_kimi_new_skill_created_even_when_ai_skills_disabled(self, project_dir, temp_dir):
        """Kimi native skills should still receive brand-new preset commands."""
        self._write_init_options(project_dir, ai="kimi", ai_skills=False)
        skills_dir = project_dir / ".kimi" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / "kimi-new-skill"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.research.md").write_text(
            "---\n"
            "description: Kimi research workflow\n"
            "---\n\n"
            "preset:kimi-new-skill\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "kimi-new-skill",
                "name": "Kimi New Skill",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.research",
                        "file": "commands/speckit.research.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-research" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:kimi-new-skill" in content
        assert "name: speckit-research" in content

        metadata = manager.registry.get("kimi-new-skill")
        assert "speckit-research" in metadata.get("registered_skills", [])

    def test_kimi_preset_skill_override_resolves_script_placeholders(self, project_dir, temp_dir):
        """Kimi preset skill overrides should resolve placeholders and rewrite project paths."""
        self._write_init_options(project_dir, ai="kimi", ai_skills=False, script="sh")
        skills_dir = project_dir / ".kimi" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")
        (project_dir / ".kimi" / "commands").mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / "kimi-placeholder-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.specify.md").write_text(
            "---\n"
            "description: Kimi placeholder override\n"
            "scripts:\n"
            "  sh: scripts/bash/create-new-feature.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "Execute `{SCRIPT}` for __AGENT__\n"
            "Review templates/checklist.md and memory/constitution.md\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "kimi-placeholder-override",
                "name": "Kimi Placeholder Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.specify",
                        "file": "commands/speckit.specify.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "{SCRIPT}" not in content
        assert "__AGENT__" not in content
        assert ".specify/scripts/bash/create-new-feature.sh --json \"$ARGUMENTS\"" in content
        assert ".specify/templates/checklist.md" in content
        assert ".specify/memory/constitution.md" in content
        assert "for kimi" in content

    def test_agy_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """Agy preset removal should restore native skills instead of deleting them."""
        self._write_init_options(project_dir, ai="agy", ai_skills=True)
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="before override")

        core_command = project_dir / ".specify" / "templates" / "commands" / "specify.md"
        core_command.write_text(
            "---\n"
            "description: Restored core specify workflow\n"
            "---\n\n"
            "restored core body\n"
        )

        preset_dir = temp_dir / "agy-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.specify.md").write_text(
            "---\n"
            "description: Agy override\n"
            "---\n\n"
            "preset agy body\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "agy-override",
                "name": "Agy Override",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.specify",
                        "file": "commands/speckit.specify.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert "preset agy body" in skill_file.read_text()

        assert manager.remove("agy-override") is True
        assert skill_file.exists()
        restored = skill_file.read_text()
        assert "restored core body" in restored
        assert "name: speckit-specify" in restored

    def test_preset_skill_registration_handles_non_dict_init_options(self, project_dir, temp_dir):
        """Non-dict init-options payloads should not crash preset install/remove flows."""
        init_options = project_dir / ".specify" / "init-options.json"
        init_options.parent.mkdir(parents=True, exist_ok=True)
        init_options.write_text("[]")

        skills_dir = project_dir / ".qwen" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        manager = PresetManager(project_dir)
        self_test_dir = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(self_test_dir, "0.1.5")

        skill_content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "untouched" in skill_content


class TestPresetSetPriority:
    """Test preset set-priority CLI command."""

    def test_set_priority_changes_priority(self, project_dir, pack_dir):
        """Test set-priority command changes preset priority."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset with default priority
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Verify default priority
        assert manager.registry.get("test-pack")["priority"] == 10

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "priority changed: 10 → 5" in plain

        # Reload registry to see updated value
        manager2 = PresetManager(project_dir)
        assert manager2.registry.get("test-pack")["priority"] == 5

    def test_set_priority_same_value_no_change(self, project_dir, pack_dir):
        """Test set-priority with same value shows already set message."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset with priority 5
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=5)

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "5"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        assert "already has priority 5" in plain

    def test_set_priority_invalid_value(self, project_dir, pack_dir):
        """Test set-priority rejects invalid priority values."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "0"])

        assert result.exit_code == 1, result.output
        assert "Priority must be a positive integer" in result.output

    def test_set_priority_not_installed(self, project_dir):
        """Test set-priority fails for non-installed preset."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "nonexistent", "5"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower()


class TestPresetPriorityBackwardsCompatibility:
    """Test backwards compatibility for presets installed before priority feature."""

    def test_legacy_preset_without_priority_field(self, temp_dir):
        """Presets installed before priority feature should default to 10."""
        presets_dir = temp_dir / ".specify" / "presets"
        presets_dir.mkdir(parents=True)

        # Simulate legacy registry entry without priority field
        registry = PresetRegistry(presets_dir)
        registry.data["presets"]["legacy-pack"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            "installed_at": "2025-01-01T00:00:00Z",
            # No "priority" field - simulates pre-feature preset
        }
        registry._save()

        # Reload registry
        registry2 = PresetRegistry(presets_dir)

        # list_by_priority should use default of 10
        result = registry2.list_by_priority()
        assert len(result) == 1
        assert result[0][0] == "legacy-pack"
        # Priority defaults to 10 and is normalized in returned metadata
        assert result[0][1]["priority"] == 10

    def test_legacy_preset_in_list_installed(self, project_dir, pack_dir):
        """list_installed returns priority=10 for legacy presets without priority field."""
        manager = PresetManager(project_dir)

        # Install preset normally
        manager.install_from_directory(pack_dir, "0.1.5")

        # Manually remove priority to simulate legacy preset
        pack_data = manager.registry.data["presets"]["test-pack"]
        del pack_data["priority"]
        manager.registry._save()

        # list_installed should still return priority=10
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["priority"] == 10

    def test_mixed_legacy_and_new_presets_ordering(self, temp_dir):
        """Legacy presets (no priority) sort with default=10 among prioritized presets."""
        presets_dir = temp_dir / ".specify" / "presets"
        presets_dir.mkdir(parents=True)

        registry = PresetRegistry(presets_dir)

        # Add preset with explicit priority=5
        registry.add("pack-with-priority", {"version": "1.0.0", "priority": 5})

        # Add legacy preset without priority (manually)
        registry.data["presets"]["legacy-pack"] = {
            "version": "1.0.0",
            "source": "local",
            "enabled": True,
            # No priority field
        }

        # Add another preset with priority=15
        registry.add("low-priority-pack", {"version": "1.0.0", "priority": 15})
        registry._save()

        # Reload and check ordering
        registry2 = PresetRegistry(presets_dir)
        sorted_presets = registry2.list_by_priority()

        # Should be: pack-with-priority (5), legacy-pack (default 10), low-priority-pack (15)
        assert [p[0] for p in sorted_presets] == [
            "pack-with-priority",
            "legacy-pack",
            "low-priority-pack",
        ]


class TestPresetEnableDisable:
    """Test preset enable/disable CLI commands."""

    def test_disable_preset(self, project_dir, pack_dir):
        """Test disable command sets enabled=False."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Verify initially enabled
        assert manager.registry.get("test-pack").get("enabled", True) is True

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "disabled" in result.output.lower()

        # Reload registry to see updated value
        manager2 = PresetManager(project_dir)
        assert manager2.registry.get("test-pack")["enabled"] is False

    def test_enable_preset(self, project_dir, pack_dir):
        """Test enable command sets enabled=True."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset and disable it
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manager.registry.update("test-pack", {"enabled": False})

        # Verify disabled
        assert manager.registry.get("test-pack")["enabled"] is False

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "enable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "enabled" in result.output.lower()

        # Reload registry to see updated value
        manager2 = PresetManager(project_dir)
        assert manager2.registry.get("test-pack")["enabled"] is True

    def test_disable_already_disabled(self, project_dir, pack_dir):
        """Test disable on already disabled preset shows warning."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset and disable it
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manager.registry.update("test-pack", {"enabled": False})

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "already disabled" in result.output.lower()

    def test_enable_already_enabled(self, project_dir, pack_dir):
        """Test enable on already enabled preset shows warning."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset (enabled by default)
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "enable", "test-pack"])

        assert result.exit_code == 0, result.output
        assert "already enabled" in result.output.lower()

    def test_disable_not_installed(self, project_dir):
        """Test disable fails for non-installed preset."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "nonexistent"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower()

    def test_enable_not_installed(self, project_dir):
        """Test enable fails for non-installed preset."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "enable", "nonexistent"])

        assert result.exit_code == 1, result.output
        assert "not installed" in result.output.lower()

    def test_disabled_preset_excluded_from_resolution(self, project_dir, pack_dir):
        """Test that disabled presets are excluded from template resolution."""
        # Install preset with a template
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Create a template in the preset directory
        preset_template = project_dir / ".specify" / "presets" / "test-pack" / "templates" / "test-template.md"
        preset_template.parent.mkdir(parents=True, exist_ok=True)
        preset_template.write_text("# Template from test-pack")

        resolver = PresetResolver(project_dir)

        # Template should be found when enabled
        result = resolver.resolve("test-template", "template")
        assert result is not None
        assert "test-pack" in str(result)

        # Disable the preset
        manager.registry.update("test-pack", {"enabled": False})

        # Template should NOT be found when disabled
        resolver2 = PresetResolver(project_dir)
        result2 = resolver2.resolve("test-template", "template")
        assert result2 is None

    def test_enable_corrupted_registry_entry(self, project_dir, pack_dir):
        """Test enable fails gracefully for corrupted registry entry."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset then corrupt the registry entry
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manager.registry.data["presets"]["test-pack"] = "corrupted-string"
        manager.registry._save()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "enable", "test-pack"])

        assert result.exit_code == 1
        assert "corrupted state" in result.output.lower()

    def test_disable_corrupted_registry_entry(self, project_dir, pack_dir):
        """Test disable fails gracefully for corrupted registry entry."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        # Install preset then corrupt the registry entry
        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        manager.registry.data["presets"]["test-pack"] = "corrupted-string"
        manager.registry._save()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "disable", "test-pack"])

        assert result.exit_code == 1
        assert "corrupted state" in result.output.lower()


# ===== Lean Preset Tests =====


LEAN_PRESET_DIR = Path(__file__).parent.parent / "presets" / "lean"

LEAN_COMMAND_NAMES = [
    "speckit.specify",
    "speckit.plan",
    "speckit.tasks",
    "speckit.implement",
    "speckit.constitution",
]


class TestLeanPreset:
    """Tests for the lean preset that ships with the repo."""

    def test_lean_preset_exists(self):
        """Verify the lean preset directory and manifest exist."""
        assert LEAN_PRESET_DIR.exists()
        assert (LEAN_PRESET_DIR / "preset.yml").exists()

    def test_lean_manifest_valid(self):
        """Verify the lean preset manifest is valid."""
        manifest = PresetManifest(LEAN_PRESET_DIR / "preset.yml")
        assert manifest.id == "lean"
        assert manifest.name == "Lean Workflow"
        assert manifest.version == "1.0.0"
        assert len(manifest.templates) == 5  # 5 commands

    def test_lean_provides_core_workflow_commands(self):
        """Verify the lean preset provides overrides for core workflow commands."""
        manifest = PresetManifest(LEAN_PRESET_DIR / "preset.yml")
        provided_names = {t["name"] for t in manifest.templates}
        for name in LEAN_COMMAND_NAMES:
            assert name in provided_names, f"Lean preset missing command: {name}"

    def test_lean_command_files_exist(self):
        """Verify that all declared command files actually exist on disk."""
        manifest = PresetManifest(LEAN_PRESET_DIR / "preset.yml")
        for tmpl in manifest.templates:
            tmpl_path = LEAN_PRESET_DIR / tmpl["file"]
            assert tmpl_path.exists(), f"Missing command file: {tmpl['file']}"

    def test_lean_commands_have_no_scripts(self):
        """Verify lean commands have no scripts in frontmatter."""
        from specify_cli.agents import CommandRegistrar

        for name in LEAN_COMMAND_NAMES:
            cmd_path = LEAN_PRESET_DIR / "commands" / f"speckit.{name.split('.')[-1]}.md"
            content = cmd_path.read_text()
            frontmatter, _ = CommandRegistrar.parse_frontmatter(content)
            assert "scripts" not in frontmatter, f"{name} should not have scripts in frontmatter"

    def test_lean_commands_have_no_hooks(self):
        """Verify lean commands do not contain extension hook boilerplate."""
        for name in LEAN_COMMAND_NAMES:
            cmd_path = LEAN_PRESET_DIR / "commands" / f"speckit.{name.split('.')[-1]}.md"
            content = cmd_path.read_text()
            assert "hooks." not in content, f"{name} should not reference extension hooks"
            assert "extensions.yml" not in content, f"{name} should not reference extensions.yml"

    def test_install_lean_preset(self, project_dir):
        """Test installing the lean preset from its directory."""
        manager = PresetManager(project_dir)
        manifest = manager.install_from_directory(LEAN_PRESET_DIR, "0.6.0")
        assert manifest.id == "lean"
        assert manager.registry.is_installed("lean")

    def test_lean_overrides_commands(self, project_dir):
        """Test that lean preset overrides are resolved correctly."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(LEAN_PRESET_DIR, "0.6.0")

        resolver = PresetResolver(project_dir)
        for name in LEAN_COMMAND_NAMES:
            result = resolver.resolve(name, template_type="command")
            assert result is not None, f"Lean override for {name} not resolved"


# ===== Bundled Preset Locator Tests =====


class TestBundledPresetLocator:
    """Tests for _locate_bundled_preset discovery function."""

    def test_locate_bundled_lean_preset(self):
        """_locate_bundled_preset finds the lean preset."""
        from specify_cli import _locate_bundled_preset

        path = _locate_bundled_preset("lean")
        assert path is not None
        assert (path / "preset.yml").is_file()

    def test_locate_bundled_preset_not_found(self):
        """_locate_bundled_preset returns None for nonexistent preset."""
        from specify_cli import _locate_bundled_preset

        path = _locate_bundled_preset("nonexistent-preset")
        assert path is None

    def test_locate_bundled_preset_rejects_invalid_id(self):
        """_locate_bundled_preset rejects IDs with invalid characters."""
        from specify_cli import _locate_bundled_preset

        assert _locate_bundled_preset("../escape") is None
        assert _locate_bundled_preset("UPPERCASE") is None
        assert _locate_bundled_preset("has spaces") is None

    def test_bundled_preset_add_via_cli(self, project_dir):
        """Test that 'specify preset add lean' installs the bundled preset."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.get_speckit_version", return_value="0.6.0"):
            result = runner.invoke(app, ["preset", "add", "lean"])

        assert result.exit_code == 0, result.output
        assert "Lean Workflow" in result.output
        assert "installed" in result.output.lower()

    def test_bundled_preset_in_catalog(self):
        """Verify the lean preset is listed in catalog.json with bundled marker."""
        catalog_path = Path(__file__).parent.parent / "presets" / "catalog.json"
        catalog = json.loads(catalog_path.read_text())
        assert "lean" in catalog["presets"]
        assert catalog["presets"]["lean"]["bundled"] is True
        assert "download_url" not in catalog["presets"]["lean"]

    def test_bundled_preset_download_raises_error(self, project_dir):
        """download_pack raises PresetError for bundled presets without download_url."""
        catalog = PresetCatalog(project_dir)

        catalog_data = {
            "test-bundled": {
                "name": "Test Bundled",
                "version": "1.0.0",
                "bundled": True,
            }
        }
        from unittest.mock import patch
        with patch.object(catalog, "_get_merged_packs", return_value=catalog_data):
            with pytest.raises(PresetError, match="bundled with spec-kit"):
                catalog.download_pack("test-bundled")

    def test_bundled_preset_missing_locally_cli_error(self, project_dir):
        """CLI shows clear error when bundled preset cannot be found locally."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()
        # Patch _locate_bundled_preset to return None (simulating missing files)
        # and mock the catalog to return a bundled entry for "lean"
        fake_pack_info = {
            "id": "lean",
            "name": "Lean Workflow",
            "version": "1.0.0",
            "bundled": True,
            "_install_allowed": True,
        }
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli._locate_bundled_preset", return_value=None), \
             patch("specify_cli.presets.PresetCatalog") as MockCatalog:
            MockCatalog.return_value.get_pack_info.return_value = fake_pack_info
            result = runner.invoke(app, ["preset", "add", "lean"])

        # Should fail with a helpful error explaining this is a bundled preset
        # and suggesting how to recover.
        assert result.exit_code == 1
        output = strip_ansi(result.output).lower()
        assert "bundled" in output, result.output
        assert "reinstall" in output, result.output


class TestWrapStrategy:
    """Tests for strategy: wrap preset command substitution."""

    def test_substitute_core_template_replaces_placeholder(self, project_dir):
        """Core template body replaces {CORE_TEMPLATE} in preset command body."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        # Set up a core command template
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\n---\n\n# Core Specify\n\nDo the thing.\n"
        )

        registrar = CommandRegistrar()
        body = "## Pre-Logic\n\nBefore stuff.\n\n{CORE_TEMPLATE}\n\n## Post-Logic\n\nAfter stuff.\n"
        result, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)

        assert "{CORE_TEMPLATE}" not in result
        assert "# Core Specify" in result
        assert "## Pre-Logic" in result
        assert "## Post-Logic" in result
        assert core_fm.get("description") == "core"

    def test_substitute_core_template_no_op_when_placeholder_absent(self, project_dir):
        """Returns body unchanged when {CORE_TEMPLATE} is not present."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCore body.\n")

        registrar = CommandRegistrar()
        body = "## No placeholder here.\n"
        result, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)
        assert result == body
        assert core_fm == {}

    def test_substitute_core_template_no_op_when_core_missing(self, project_dir):
        """Returns body unchanged when core template file does not exist."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        registrar = CommandRegistrar()
        body = "Pre.\n\n{CORE_TEMPLATE}\n\nPost.\n"
        result, core_fm = _substitute_core_template(body, "nonexistent", project_dir, registrar)
        assert result == body
        assert "{CORE_TEMPLATE}" in result
        assert core_fm == {}

    def test_register_commands_substitutes_core_template_for_wrap_strategy(self, project_dir):
        """register_commands substitutes {CORE_TEMPLATE} when strategy: wrap."""
        from specify_cli.agents import CommandRegistrar

        # Set up core command template
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\n---\n\n# Core Specify\n\nCore body here.\n"
        )

        # Create a preset command dir with a wrap-strategy command
        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: wrap test\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        commands = [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}]
        registrar = CommandRegistrar()

        # Use a generic agent that writes markdown to commands/
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Patch AGENT_CONFIGS to use a simple markdown agent pointing at our dir
        import copy
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-agent", commands, "test-preset",
                project_dir / "preset", project_dir
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "# Core Specify" in written
        assert "## Pre" in written
        assert "## Post" in written

    def test_end_to_end_wrap_via_self_test_preset(self, project_dir):
        """Installing self-test preset with a wrap command substitutes {CORE_TEMPLATE}."""
        from specify_cli.presets import PresetManager

        # Install a core template that wrap-test will wrap around
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "wrap-test.md").write_text(
            "---\ndescription: core wrap-test\n---\n\n# Core Wrap-Test Body\n"
        )

        # Set up skills dir (simulating --ai claude)
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        skill_subdir = skills_dir / "speckit-wrap-test"
        skill_subdir.mkdir()
        (skill_subdir / "SKILL.md").write_text("---\nname: speckit-wrap-test\n---\n\nold content\n")

        # Write init-options so _register_skills finds the claude skills dir
        import json
        (project_dir / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "claude", "ai_skills": True})
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        written = (skill_subdir / "SKILL.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "# Core Wrap-Test Body" in written
        assert "preset:self-test wrap-pre" in written
        assert "preset:self-test wrap-post" in written

    def test_substitute_core_template_returns_core_scripts(self, project_dir):
        """core_frontmatter in the returned tuple includes scripts/agent_scripts."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: run.sh\nagent_scripts:\n  sh: agent-run.sh\n---\n\n# Body\n"
        )

        registrar = CommandRegistrar()
        body = "## Wrapper\n\n{CORE_TEMPLATE}\n"
        result, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)

        assert "# Body" in result
        assert core_fm.get("scripts") == {"sh": "run.sh"}
        assert core_fm.get("agent_scripts") == {"sh": "agent-run.sh"}

    def test_register_skills_inherits_scripts_from_core_when_preset_omits_them(self, project_dir):
        """_register_skills merges scripts/agent_scripts from core when preset lacks them."""
        from specify_cli.presets import PresetManager
        import json

        # Core template with scripts
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "wrap-test.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        # Skills dir for claude
        skills_dir = project_dir / ".claude" / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        skill_subdir = skills_dir / "speckit-wrap-test"
        skill_subdir.mkdir()
        (skill_subdir / "SKILL.md").write_text("---\nname: speckit-wrap-test\n---\n\nold\n")

        (project_dir / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "claude", "ai_skills": True})
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        written = (skill_subdir / "SKILL.md").read_text()
        # {SCRIPT} should have been resolved (not left as a literal placeholder)
        assert "{SCRIPT}" not in written

    def test_register_skills_preset_scripts_take_precedence_over_core(self, project_dir):
        """preset-defined scripts/agent_scripts are not overwritten by core frontmatter."""
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: core-run.sh\n---\n\nCore body.\n"
        )

        registrar = CommandRegistrar()
        body = "{CORE_TEMPLATE}"
        _, core_fm = _substitute_core_template(body, "specify", project_dir, registrar)

        # Simulate preset frontmatter that already defines scripts
        preset_fm = {"description": "preset", "strategy": "wrap", "scripts": {"sh": "preset-run.sh"}}
        for key in ("scripts", "agent_scripts"):
            if key not in preset_fm and key in core_fm:
                preset_fm[key] = core_fm[key]

        # Preset's scripts must not be overwritten by core
        assert preset_fm["scripts"] == {"sh": "preset-run.sh"}

    def test_register_commands_inherits_scripts_from_core(self, project_dir):
        """register_commands merges scripts/agent_scripts from core and normalizes paths."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        # Preset has strategy: wrap but no scripts of its own
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: wrap no scripts\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "Run:" in written
        assert "scripts:" in written
        assert "run.sh" in written

    def test_register_commands_toml_resolves_inherited_scripts(self, project_dir):
        """TOML agents resolve {SCRIPT} from inherited core scripts when preset omits them."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: toml wrap\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        toml_dir = project_dir / ".gemini" / "commands"
        toml_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-toml-agent"] = {
            "dir": str(toml_dir.relative_to(project_dir)),
            "format": "toml",
            "args": "{{args}}",
            "extension": ".toml",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-toml-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (toml_dir / "speckit.specify.toml").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "{SCRIPT}" not in written
        assert "run.sh" in written
        # args token must use TOML format, not the intermediate $ARGUMENTS
        assert "$ARGUMENTS" not in written
        assert "{{args}}" in written

    def test_register_commands_markdown_resolves_inherited_scripts(self, project_dir):
        """Markdown agents resolve {SCRIPT} from inherited core scripts when preset omits them."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: markdown wrap\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-md-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "$ARGUMENTS",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-md-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{CORE_TEMPLATE}" not in written
        assert "{SCRIPT}" not in written
        assert "run.sh" in written
        assert "strategy" not in written

    def test_register_commands_markdown_converts_args_after_script_resolution(self, project_dir):
        """Markdown agents re-run arg placeholder conversion after resolve_skill_placeholders.

        resolve_skill_placeholders injects $ARGUMENTS (via {ARGS} expansion). A second
        _convert_argument_placeholder call must convert those to the agent's native format.
        """
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text(
            "---\ndescription: core\nscripts:\n  sh: .specify/scripts/run.sh {ARGS}\n---\n\n"
            "Run: {SCRIPT}\n"
        )

        cmd_dir = project_dir / "preset" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: forge wrap\nstrategy: wrap\n---\n\n"
            "## Pre\n\n{CORE_TEMPLATE}\n\n## Post\n"
        )

        agent_dir = project_dir / ".forge" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-forge-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown",
            "args": "{{parameters}}",
            "extension": ".md",
            "strip_frontmatter_keys": [],
        }
        try:
            registrar.register_commands(
                "test-forge-agent",
                [{"name": "speckit.specify", "file": "commands/speckit.specify.md"}],
                "test-preset",
                project_dir / "preset",
                project_dir,
            )
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "{SCRIPT}" not in written
        assert "run.sh" in written
        # $ARGUMENTS injected by resolve_skill_placeholders must be re-converted
        assert "$ARGUMENTS" not in written
        assert "{{parameters}}" in written

    def test_extension_command_resolves_via_extension_directory(self, project_dir):
        """Extension commands (e.g. speckit.git.feature) resolve from the extension directory.

        Both _register_skills and register_commands pass the full cmd_name to
        _substitute_core_template, which tries the full name first via PresetResolver
        and finds speckit.git.feature.md in the extension commands directory.
        """
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        # Place the template where a real extension would install it
        ext_cmd_dir = project_dir / ".specify" / "extensions" / "git" / "commands"
        ext_cmd_dir.mkdir(parents=True, exist_ok=True)
        (ext_cmd_dir / "speckit.git.feature.md").write_text(
            "---\ndescription: git feature core\n---\n\n# Git Feature Core\n"
        )
        # Ensure a hyphenated or dot-separated fallback does NOT exist
        assert not (project_dir / ".specify" / "templates" / "commands" / "git.feature.md").exists()
        assert not (project_dir / ".specify" / "templates" / "commands" / "git-feature.md").exists()

        registrar = CommandRegistrar()
        body = "## Wrapper\n\n{CORE_TEMPLATE}\n"

        # Both call sites now pass the full cmd_name
        result, _ = _substitute_core_template(body, "speckit.git.feature", project_dir, registrar)

        assert "# Git Feature Core" in result
        assert "{CORE_TEMPLATE}" not in result

    def test_extension_command_resolves_via_manifest_when_filename_differs(self, project_dir):
        """Extension commands whose filename differs from the command name resolve via extension.yml.

        The selftest extension maps speckit.selftest.extension → commands/selftest.md.
        Name-based lookup would look for commands/speckit.selftest.extension.md and fail;
        manifest-based lookup must find the actual file declared in the manifest.
        """
        from specify_cli.presets import _substitute_core_template
        from specify_cli.agents import CommandRegistrar

        ext_dir = project_dir / ".specify" / "extensions" / "selftest"
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)

        # File is named selftest.md, NOT speckit.selftest.extension.md
        (cmd_dir / "selftest.md").write_text(
            "---\ndescription: selftest core\n---\n\n# Selftest Core\n"
        )
        # Manifest maps the command name to the actual file
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: selftest\n  name: Self-Test\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  commands:\n"
            "    - name: speckit.selftest.extension\n"
            "      file: commands/selftest.md\n"
            "      description: Selftest command\n"
        )

        registrar = CommandRegistrar()
        body = "## Wrapper\n\n{CORE_TEMPLATE}\n"
        result, _ = _substitute_core_template(body, "speckit.selftest.extension", project_dir, registrar)

        assert "# Selftest Core" in result
        assert "{CORE_TEMPLATE}" not in result


# ===== _replay_wraps_for_command Tests =====

def _make_wrap_preset_dir(
    base: Path,
    preset_id: str,
    cmd_name: str,
    pre: str,
    post: str,
    aliases: list[str] | None = None,
    file_rel: str | None = None,
) -> Path:
    """Create a minimal wrap-strategy preset directory for testing."""
    preset_dir = base / preset_id
    cmd_dir = preset_dir / "commands"
    cmd_dir.mkdir(parents=True)
    file_rel = file_rel or f"commands/{cmd_name}.md"
    template = {
        "type": "command",
        "name": cmd_name,
        "file": file_rel,
        "description": f"{preset_id} wrap",
    }
    if aliases is not None:
        template["aliases"] = aliases
    manifest = {
        "schema_version": "1.0",
        "preset": {
            "id": preset_id,
            "name": preset_id,
            "version": "1.0.0",
            "description": f"Preset {preset_id}",
            "author": "test",
            "repository": "https://example.com",
            "license": "MIT",
        },
        "requires": {"speckit_version": ">=0.1.0"},
        "provides": {
            "templates": [template]
        },
        "tags": [],
    }
    import yaml as _yaml
    (preset_dir / "preset.yml").write_text(_yaml.dump(manifest))
    command_path = preset_dir / file_rel
    command_path.parent.mkdir(parents=True, exist_ok=True)
    command_path.write_text(
        f"---\ndescription: {preset_id} wrap\nstrategy: wrap\n---\n\n"
        f"[{pre}]\n\n{{CORE_TEMPLATE}}\n\n[{post}]\n"
    )
    return preset_dir


class TestReplayWrapsForCommand:
    """Tests for PresetManager._replay_wraps_for_command()."""

    def test_replay_no_op_when_no_wrap_presets(self, project_dir):
        """replay does nothing when no presets declare wrap_commands for the command."""
        manager = PresetManager(project_dir)
        # Should not raise
        manager._replay_wraps_for_command("speckit.specify")

    def test_replay_no_op_when_core_missing(self, project_dir, temp_dir):
        """replay exits gracefully when resolve_core returns None."""
        from specify_cli.agents import CommandRegistrar
        import copy

        preset_dir = _make_wrap_preset_dir(temp_dir, "preset-a", "speckit.nonexistent-cmd", "pre-a", "post-a")
        installed = project_dir / ".specify" / "presets" / "preset-a"
        import shutil as _shutil
        _shutil.copytree(preset_dir, installed)

        manager = PresetManager(project_dir)
        manager.registry.add("preset-a", {
            "version": "1.0.0", "source": "local", "enabled": True,
            "priority": 10, "manifest_hash": "x",
            "registered_commands": {}, "registered_skills": [],
            "wrap_commands": ["speckit.nonexistent-cmd"],
        })

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True)

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            # No core file exists for this command — replay should return without writing
            manager._replay_wraps_for_command("speckit.nonexistent-cmd")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        assert not (agent_dir / "speckit.nonexistent-cmd.md").exists()

    def test_replay_single_preset_writes_composed_output(self, project_dir, temp_dir):
        """Single wrap preset: replay writes pre + core + post to agent dirs."""
        from specify_cli.agents import CommandRegistrar
        import copy, shutil as _shutil

        # Core template
        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\ncore body\n")

        # Install preset-a
        preset_dir = _make_wrap_preset_dir(temp_dir, "preset-a", "speckit.specify", "pre-a", "post-a")
        installed = project_dir / ".specify" / "presets" / "preset-a"
        _shutil.copytree(preset_dir, installed)

        manager = PresetManager(project_dir)
        manager.registry.add("preset-a", {
            "version": "1.0.0", "source": "local", "enabled": True,
            "priority": 10, "manifest_hash": "x",
            "registered_commands": {}, "registered_skills": [],
            "wrap_commands": ["speckit.specify"],
        })

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True)
        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager._replay_wraps_for_command("speckit.specify")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "[pre-a]" in written
        assert "core body" in written
        assert "[post-a]" in written
        assert "{CORE_TEMPLATE}" not in written
        assert "strategy" not in written

    def test_replay_uses_manifest_command_file_mapping(self, project_dir, temp_dir):
        """Replay reads wrapper files from preset.yml instead of assuming command-name paths."""
        from specify_cli.agents import CommandRegistrar
        import copy, shutil as _shutil

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        preset_dir = _make_wrap_preset_dir(
            temp_dir,
            "preset-a",
            "speckit.specify",
            "pre-a",
            "post-a",
            file_rel="commands/custom-wrapper.md",
        )
        installed = project_dir / ".specify" / "presets" / "preset-a"
        _shutil.copytree(preset_dir, installed)

        manager = PresetManager(project_dir)
        manager.registry.add("preset-a", {
            "version": "1.0.0", "source": "local", "enabled": True,
            "priority": 10, "manifest_hash": "x",
            "registered_commands": {}, "registered_skills": [],
            "wrap_commands": ["speckit.specify"],
        })

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True)
        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager._replay_wraps_for_command("speckit.specify")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        assert "[pre-a]" in written
        assert "CORE" in written
        assert "[post-a]" in written

    def test_replay_resolves_extension_core_via_manifest_mapping(self, project_dir, temp_dir):
        """Replay finds extension core commands whose manifest file differs from command name."""
        from specify_cli.agents import CommandRegistrar
        import copy, shutil as _shutil

        ext_dir = project_dir / ".specify" / "extensions" / "selftest"
        cmd_dir = ext_dir / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        (cmd_dir / "selftest.md").write_text(
            "---\ndescription: selftest core\n---\n\nEXTENSION-CORE\n"
        )
        (ext_dir / "extension.yml").write_text(
            "schema_version: '1.0'\n"
            "extension:\n  id: selftest\n  name: Self-Test\n  version: 1.0.0\n"
            "  description: test\n  author: test\n  repository: https://example.com\n"
            "  license: MIT\n"
            "requires:\n  speckit_version: '>=0.2.0'\n"
            "provides:\n"
            "  commands:\n"
            "    - name: speckit.selftest.extension\n"
            "      file: commands/selftest.md\n"
            "      description: Selftest command\n"
        )

        preset_dir = _make_wrap_preset_dir(
            temp_dir, "preset-a", "speckit.selftest.extension", "pre-a", "post-a"
        )
        installed = project_dir / ".specify" / "presets" / "preset-a"
        _shutil.copytree(preset_dir, installed)

        manager = PresetManager(project_dir)
        manager.registry.add("preset-a", {
            "version": "1.0.0", "source": "local", "enabled": True,
            "priority": 10, "manifest_hash": "x",
            "registered_commands": {}, "registered_skills": [],
            "wrap_commands": ["speckit.selftest.extension"],
        })

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True)
        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager._replay_wraps_for_command("speckit.selftest.extension")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.selftest.extension.md").read_text()
        assert "[pre-a]" in written
        assert "EXTENSION-CORE" in written
        assert "[post-a]" in written

    def test_replay_priority_order_lower_number_outermost(self, project_dir, temp_dir):
        """Two wrap presets: lower priority number = outermost wrapper."""
        from specify_cli.agents import CommandRegistrar
        import copy, shutil as _shutil

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        for pid in ("preset-outer", "preset-inner"):
            src = _make_wrap_preset_dir(temp_dir, pid, "speckit.specify", f"pre-{pid}", f"post-{pid}")
            _shutil.copytree(src, project_dir / ".specify" / "presets" / pid)

        manager = PresetManager(project_dir)
        # preset-outer has priority 1 (highest precedence = outermost)
        # preset-inner has priority 10 (lowest precedence = innermost)
        for pid, pri in (("preset-outer", 1), ("preset-inner", 10)):
            manager.registry.add(pid, {
                "version": "1.0.0", "source": "local", "enabled": True,
                "priority": pri, "manifest_hash": "x",
                "registered_commands": {}, "registered_skills": [],
                "wrap_commands": ["speckit.specify"],
            })

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True)
        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager._replay_wraps_for_command("speckit.specify")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        # Outermost (preset-outer, p=1) wraps everything; innermost (preset-inner, p=10) is next
        outer_pre = written.index("[pre-preset-outer]")
        inner_pre = written.index("[pre-preset-inner]")
        core_pos = written.index("CORE")
        inner_post = written.index("[post-preset-inner]")
        outer_post = written.index("[post-preset-outer]")
        assert outer_pre < inner_pre < core_pos < inner_post < outer_post

    def test_replay_install_order_independent(self, project_dir, temp_dir):
        """Nesting order is determined by priority, not install order."""
        from specify_cli.agents import CommandRegistrar
        import copy, shutil as _shutil

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        for pid in ("preset-a", "preset-b"):
            src = _make_wrap_preset_dir(temp_dir, pid, "speckit.specify", f"pre-{pid}", f"post-{pid}")
            _shutil.copytree(src, project_dir / ".specify" / "presets" / pid)

        manager = PresetManager(project_dir)
        # preset-a priority=5 (outermost), preset-b priority=10 (innermost)
        # Install in reverse order to verify install order doesn't affect nesting
        for pid, pri in (("preset-b", 10), ("preset-a", 5)):
            manager.registry.add(pid, {
                "version": "1.0.0", "source": "local", "enabled": True,
                "priority": pri, "manifest_hash": "x",
                "registered_commands": {}, "registered_skills": [],
                "wrap_commands": ["speckit.specify"],
            })

        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True)
        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager._replay_wraps_for_command("speckit.specify")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        a_pre = written.index("[pre-preset-a]")
        b_pre = written.index("[pre-preset-b]")
        core_pos = written.index("CORE")
        b_post = written.index("[post-preset-b]")
        a_post = written.index("[post-preset-a]")
        # preset-a (p=5) is outermost regardless of install order
        assert a_pre < b_pre < core_pos < b_post < a_post

    def test_replay_updates_skill_outputs(self, project_dir, temp_dir):
        """Replay also rewrites SKILL.md-backed agent outputs."""
        import json
        import shutil as _shutil

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        preset_dir = _make_wrap_preset_dir(temp_dir, "preset-a", "speckit.specify", "pre-a", "post-a")
        _shutil.copytree(preset_dir, project_dir / ".specify" / "presets" / "preset-a")

        manager = PresetManager(project_dir)
        manager.registry.add("preset-a", {
            "version": "1.0.0", "source": "local", "enabled": True,
            "priority": 10, "manifest_hash": "x",
            "registered_commands": {}, "registered_skills": [],
            "wrap_commands": ["speckit.specify"],
        })

        skills_dir = project_dir / ".claude" / "skills"
        skill_subdir = skills_dir / "speckit-specify"
        skill_subdir.mkdir(parents=True)
        (skill_subdir / "SKILL.md").write_text("---\nname: speckit-specify\n---\n\nold\n")
        (project_dir / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "claude", "ai_skills": True})
        )

        manager._replay_wraps_for_command("speckit.specify")

        written = (skill_subdir / "SKILL.md").read_text()
        assert "[pre-a]" in written
        assert "CORE" in written
        assert "[post-a]" in written

    def test_replay_applies_integration_post_processing_to_skill(self, project_dir, temp_dir):
        """_replay_skill_override must call post_process_skill_content, matching _register_skills."""
        import json
        import shutil as _shutil

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        preset_dir = _make_wrap_preset_dir(temp_dir, "preset-a", "speckit.specify", "pre-a", "post-a")
        _shutil.copytree(preset_dir, project_dir / ".specify" / "presets" / "preset-a")

        manager = PresetManager(project_dir)
        manager.registry.add("preset-a", {
            "version": "1.0.0", "source": "local", "enabled": True,
            "priority": 10, "manifest_hash": "x",
            "registered_commands": {}, "registered_skills": [],
            "wrap_commands": ["speckit.specify"],
        })

        skills_dir = project_dir / ".claude" / "skills"
        skill_subdir = skills_dir / "speckit-specify"
        skill_subdir.mkdir(parents=True)
        (skill_subdir / "SKILL.md").write_text("---\nname: speckit-specify\n---\n\nold\n")
        (project_dir / ".specify" / "init-options.json").write_text(
            json.dumps({"ai": "claude", "ai_skills": True})
        )

        manager._replay_wraps_for_command("speckit.specify")

        # ClaudeIntegration.post_process_skill_content injects these flags.
        # Their presence proves the integration hook ran during replay.
        written = (skill_subdir / "SKILL.md").read_text()
        assert "disable-model-invocation: false" in written, (
            "_replay_skill_override must call post_process_skill_content "
            "(same as _register_skills)"
        )


class TestInstallRemoveWrapLifecycle:
    """Tests for wrap_commands stored on install and replayed on remove."""

    def _setup_agent(self, project_dir, registrar, agent_configs_dict):
        """Register a test markdown agent and return its commands dir."""
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        agent_configs_dict["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        return agent_dir

    def test_install_stores_wrap_commands_in_registry(self, project_dir, temp_dir):
        """install_from_directory stores wrap_commands in the registry entry."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\ncore\n")

        preset_src = _make_wrap_preset_dir(temp_dir, "preset-a", "speckit.specify", "pre", "post")

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager = PresetManager(project_dir)
            manager.install_from_directory(preset_src, "0.1.0", priority=10)
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        meta = manager.registry.get("preset-a")
        assert "wrap_commands" in meta
        assert "speckit.specify" in meta["wrap_commands"]

    def test_install_replay_produces_correct_nested_output(self, project_dir, temp_dir):
        """After installing two wrap presets, agent file contains correctly nested output."""
        from specify_cli.agents import CommandRegistrar
        import copy, shutil as _shutil

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager = PresetManager(project_dir)
            # Install outermost first (priority=5), then innermost (priority=10)
            outer_src = _make_wrap_preset_dir(temp_dir, "preset-outer", "speckit.specify", "OUTER-PRE", "OUTER-POST")
            # Rename to avoid id conflict with fixture
            inner_src = _make_wrap_preset_dir(temp_dir, "preset-inner", "speckit.specify", "INNER-PRE", "INNER-POST")
            manager.install_from_directory(outer_src, "0.1.0", priority=5)
            manager.install_from_directory(inner_src, "0.1.0", priority=10)
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        outer_pre = written.index("OUTER-PRE")
        inner_pre = written.index("INNER-PRE")
        core_pos = written.index("CORE")
        inner_post = written.index("INNER-POST")
        outer_post = written.index("OUTER-POST")
        assert outer_pre < inner_pre < core_pos < inner_post < outer_post

    def test_remove_replays_remaining_wraps(self, project_dir, temp_dir):
        """Removing one wrap preset re-composes the remaining wraps correctly."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager = PresetManager(project_dir)
            outer_src = _make_wrap_preset_dir(temp_dir, "preset-outer", "speckit.specify", "OUTER-PRE", "OUTER-POST")
            inner_src = _make_wrap_preset_dir(temp_dir, "preset-inner", "speckit.specify", "INNER-PRE", "INNER-POST")
            manager.install_from_directory(outer_src, "0.1.0", priority=5)
            manager.install_from_directory(inner_src, "0.1.0", priority=10)
            manager.remove("preset-outer")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        written = (agent_dir / "speckit.specify.md").read_text()
        # Only inner wrap remains — should be: INNER-PRE + CORE + INNER-POST, no OUTER
        assert "INNER-PRE" in written
        assert "CORE" in written
        assert "INNER-POST" in written
        assert "OUTER-PRE" not in written
        assert "OUTER-POST" not in written

    def test_wrap_aliases_are_replayed_and_removed(self, project_dir, temp_dir):
        """Replay preserves wrap aliases across install/remove lifecycle changes."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager = PresetManager(project_dir)
            outer_src = _make_wrap_preset_dir(
                temp_dir,
                "preset-outer",
                "speckit.specify",
                "OUTER-PRE",
                "OUTER-POST",
                aliases=["speckit.alias"],
            )
            inner_src = _make_wrap_preset_dir(
                temp_dir, "preset-inner", "speckit.specify", "INNER-PRE", "INNER-POST"
            )
            manager.install_from_directory(outer_src, "0.1.0", priority=5)
            manager.install_from_directory(inner_src, "0.1.0", priority=10)

            alias_file = agent_dir / "speckit.alias.md"
            written = alias_file.read_text()
            assert "OUTER-PRE" in written
            assert "INNER-PRE" in written
            assert "INNER-POST" in written
            assert "OUTER-POST" in written

            manager.remove("preset-inner")
            written = alias_file.read_text()
            assert "OUTER-PRE" in written
            assert "OUTER-POST" in written
            assert "INNER-PRE" not in written
            assert "INNER-POST" not in written

            manager.remove("preset-outer")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        assert not (agent_dir / "speckit.alias.md").exists()

    def test_remove_last_wrap_preset_deletes_agent_file(self, project_dir, temp_dir):
        """Removing the only wrap preset deletes the agent command file."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager = PresetManager(project_dir)
            src = _make_wrap_preset_dir(temp_dir, "preset-only", "speckit.specify", "PRE", "POST")
            manager.install_from_directory(src, "0.1.0", priority=10)
            assert (agent_dir / "speckit.specify.md").exists()
            manager.remove("preset-only")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        assert not (agent_dir / "speckit.specify.md").exists()

    def test_remove_keeps_registry_entry_when_directory_delete_fails(self, project_dir, monkeypatch):
        """A failed preset directory delete must not leave files untracked by the registry."""
        manager = PresetManager(project_dir)
        pack_dir = manager.presets_dir / "preset-a"
        pack_dir.mkdir(parents=True)
        manager.registry.add("preset-a", {
            "version": "1.0.0", "source": "local", "enabled": True,
            "priority": 10, "manifest_hash": "x",
            "registered_commands": {}, "registered_skills": [],
            "wrap_commands": [],
        })

        def fail_rmtree(_path):
            raise OSError("locked")

        monkeypatch.setattr(shutil, "rmtree", fail_rmtree)

        with pytest.raises(OSError, match="locked"):
            manager.remove("preset-a")

        assert manager.registry.is_installed("preset-a")
        assert pack_dir.exists()

    def test_non_wrap_commands_unaffected_by_wrap_lifecycle(self, project_dir, temp_dir):
        """wrap_commands is empty for a preset with no strategy:wrap commands."""
        from specify_cli.agents import CommandRegistrar
        import copy
        import yaml as _yaml

        # Create a preset with a non-wrap command
        preset_dir = temp_dir / "non-wrap-preset"
        cmd_dir = preset_dir / "commands"
        cmd_dir.mkdir(parents=True)
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "non-wrap-preset", "name": "Non-wrap", "version": "1.0.0",
                "description": "no wrap", "author": "test",
                "repository": "https://example.com", "license": "MIT",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"templates": [
                {"type": "command", "name": "speckit.specify",
                 "file": "commands/speckit.specify.md", "description": "override"},
            ]},
            "tags": [],
        }
        (preset_dir / "preset.yml").write_text(_yaml.dump(manifest))
        (cmd_dir / "speckit.specify.md").write_text(
            "---\ndescription: plain override\n---\n\nplain body\n"
        )

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager = PresetManager(project_dir)
            manager.install_from_directory(preset_dir, "0.1.0", priority=10)
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        meta = manager.registry.get("non-wrap-preset")
        assert meta.get("wrap_commands", []) == []
        written = (agent_dir / "speckit.specify.md").read_text()
        assert "plain body" in written
