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
import io
import json
import tempfile
import shutil
import warnings
import zipfile
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

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

    def test_utf8_non_ascii_description_loads(self, temp_dir, valid_pack_data):
        """Regression for #2325: non-ASCII (UTF-8) description loads on any platform.

        On Windows, Python's default text-mode encoding is the locale codepage
        (e.g. cp1252/GBK), which raises UnicodeDecodeError on UTF-8 bytes
        outside the ASCII range. The loader must open with encoding='utf-8'.
        """
        valid_pack_data["preset"]["description"] = "中文测试 — émojis 🚀"
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_bytes(
            yaml.safe_dump(valid_pack_data, allow_unicode=True).encode("utf-8")
        )

        manifest = PresetManifest(manifest_path)
        assert manifest.description == "中文测试 — émojis 🚀"

    def test_invalid_utf8_bytes_raises_validation_error(self, temp_dir):
        """Negative case: file containing invalid UTF-8 bytes raises PresetValidationError, not raw UnicodeDecodeError."""
        manifest_path = temp_dir / "preset.yml"
        manifest_path.write_bytes(b"\xff\xfe not valid utf-8 \xff\n")

        with pytest.raises(PresetValidationError, match="not valid UTF-8"):
            PresetManifest(manifest_path)

    def test_non_mapping_yaml_raises_validation_error(self, temp_dir):
        """Manifest whose YAML root is a scalar or list raises PresetValidationError, not TypeError."""
        manifest_path = temp_dir / "preset.yml"
        for bad_content in ("42\n", "[1, 2]\n"):
            manifest_path.write_text(bad_content, encoding="utf-8")
            with pytest.raises(PresetValidationError, match="YAML mapping"):
                PresetManifest(manifest_path)

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

    def test_check_compatibility_prerelease(self, pack_dir, temp_dir):
        """Test compatibility check allows prereleases and fails on boundary."""
        manager = PresetManager(temp_dir)
        manifest = PresetManifest(pack_dir / "preset.yml")
        # manifest requires >=0.1.0
        assert manager.check_compatibility(manifest, "0.8.8.dev0") is True
        with pytest.raises(PresetCompatibilityError, match="Preset requires spec-kit"):
            manager.check_compatibility(manifest, "0.1.0.dev0")

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

    def _install_pack_with_manifest_file(self, project_dir, *, extra_file=False):
        """Create a pack whose manifest declares a NON-convention file: path.

        Returns the pack dir under the project. The declared file lives at
        custom/spec.md (not the convention templates/spec-template.md).
        """
        presets_dir = project_dir / ".specify" / "presets"
        pack_dir = presets_dir / "mypack"
        (pack_dir / "custom").mkdir(parents=True)
        (pack_dir / "custom" / "spec.md").write_text(
            "# Manifest-declared Spec\n", encoding="utf-8"
        )
        if extra_file:
            # An undeclared convention-path file the manifest points away from.
            (pack_dir / "templates").mkdir()
            (pack_dir / "templates" / "spec-template.md").write_text(
                "# Stray Convention Spec\n", encoding="utf-8"
            )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "mypack",
                "name": "My Pack",
                "version": "1.0.0",
                "description": "declares a non-convention file path",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "template",
                        "name": "spec-template",
                        "file": "custom/spec.md",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(pack_dir / "preset.yml", "w") as f:
            yaml.dump(manifest, f)
        PresetRegistry(presets_dir).add(
            "mypack", {"version": "1.0.0", "priority": 10}
        )
        return pack_dir

    def test_resolve_uses_manifest_declared_file_path(self, project_dir):
        """resolve() must honor a manifest-declared non-convention file: path.

        Previously the tier-2 loop was convention-only, so it returned the
        core template and resolve_with_source() misattributed source='core',
        diverging from collect_all_layers()/resolve_content().
        """
        pack_dir = self._install_pack_with_manifest_file(project_dir)
        resolver = PresetResolver(project_dir)

        result = resolver.resolve("spec-template")
        assert result == pack_dir / "custom" / "spec.md"
        assert "Manifest-declared Spec" in result.read_text()

        sourced = resolver.resolve_with_source("spec-template")
        assert sourced is not None
        assert "mypack" in sourced["source"]
        # resolve() must agree with collect_all_layers()'s top layer.
        layers = resolver.collect_all_layers("spec-template")
        assert Path(layers[0]["path"]) == pack_dir / "custom" / "spec.md"

    def test_resolve_manifest_file_wins_over_undeclared_convention_file(
        self, project_dir
    ):
        """A stray convention-path file must not shadow the manifest's file:."""
        pack_dir = self._install_pack_with_manifest_file(
            project_dir, extra_file=True
        )
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result == pack_dir / "custom" / "spec.md"
        assert "Manifest-declared Spec" in result.read_text()

    def test_resolve_skips_convention_when_manifest_file_missing(self, project_dir):
        """When the manifest declares a file: that does not exist, resolve()
        must NOT fall back to a convention file in the same pack (that would
        mask a typo) — it skips the pack and resolves core instead."""
        presets_dir = project_dir / ".specify" / "presets"
        pack_dir = presets_dir / "mypack"
        # Manifest declares custom/spec.md (MISSING); a convention file exists
        # in the pack and must NOT be used.
        (pack_dir / "templates").mkdir(parents=True)
        (pack_dir / "templates" / "spec-template.md").write_text(
            "# Stray Convention Spec\n", encoding="utf-8"
        )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "mypack",
                "name": "My Pack",
                "version": "1.0.0",
                "description": "declares a missing file path",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "template",
                        "name": "spec-template",
                        "file": "custom/spec.md",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(pack_dir / "preset.yml", "w") as f:
            yaml.dump(manifest, f)
        PresetRegistry(presets_dir).add(
            "mypack", {"version": "1.0.0", "priority": 10}
        )

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        content = result.read_text()
        assert "Stray Convention Spec" not in content  # pack convention skipped
        assert "Core Spec Template" in content  # fell through to core

    def test_resolve_skips_convention_when_manifest_file_is_directory(
        self, project_dir
    ):
        """When the manifest's file: path resolves to a DIRECTORY (not a regular
        file), resolve()/collect_all_layers() must treat it as missing — exists()
        would accept it and downstream read_text() on a directory would crash.
        The pack is skipped (no convention fallback), so core wins."""
        presets_dir = project_dir / ".specify" / "presets"
        pack_dir = presets_dir / "mypack"
        # Declared file: custom/spec.md is created as a DIRECTORY.
        (pack_dir / "custom" / "spec.md").mkdir(parents=True)
        # A convention file also exists and must NOT be used.
        (pack_dir / "templates").mkdir(parents=True)
        (pack_dir / "templates" / "spec-template.md").write_text(
            "# Stray Convention Spec\n", encoding="utf-8"
        )
        manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "mypack",
                "name": "My Pack",
                "version": "1.0.0",
                "description": "declares a file: that is actually a directory",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "template",
                        "name": "spec-template",
                        "file": "custom/spec.md",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(pack_dir / "preset.yml", "w") as f:
            yaml.dump(manifest, f)
        PresetRegistry(presets_dir).add(
            "mypack", {"version": "1.0.0", "priority": 10}
        )

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert result.is_file()  # never a directory
        content = result.read_text()
        assert "Stray Convention Spec" not in content  # pack convention skipped
        assert "Core Spec Template" in content  # fell through to core
        # collect_all_layers() must agree: the directory is not a layer.
        layers = resolver.collect_all_layers("spec-template")
        assert all(Path(layer["path"]).is_file() for layer in layers)
        assert all(
            Path(layer["path"]) != pack_dir / "custom" / "spec.md"
            for layer in layers
        )

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

    def test_collect_all_layers_finds_bundled_core_without_specify_commands(
        self, project_dir
    ):
        """Tier-5 fallback locates the bundled core command when
        .specify/templates/commands/ has no matching file.

        Regression test for #3086: a stale ``.parent`` chain made the
        source-checkout fallback resolve to ``src/templates/...`` (which does
        not exist), so ``wrap`` presets found no base layer. The fallback must
        resolve against the real repo-root ``templates/commands`` tree.
        """
        # project_dir's commands dir is empty, so tier-4 cannot satisfy this.
        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("speckit.implement", "command")
        assert layers, "expected a bundled core base layer to be found"
        assert layers[-1]["source"] == "core (bundled)"
        assert layers[-1]["path"].parts[-2:] == ("commands", "implement.md")

    def test_resolve_command_falls_back_to_bundled_core(self, project_dir):
        """resolve() tier-5 returns the bundled core command when
        .specify/templates/commands/ lacks it (regression for #3086)."""
        resolver = PresetResolver(project_dir)
        result = resolver.resolve("speckit.implement", "command")
        assert result is not None
        assert result.parts[-2:] == ("commands", "implement.md")


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

    def _inject_github_config(self, monkeypatch, token_env="GH_TOKEN"):
        from tests.auth_helpers import inject_github_config
        inject_github_config(monkeypatch, token_env)

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

    @pytest.mark.parametrize(
        "url",
        [
            "https://:8080",                # port only, no host
            "https://:8080/catalog.json",   # port only, with path
            "https://:0",                   # port only, no host
            "https://user@",                # userinfo only, no host
            "https://user:pass@",           # userinfo only, no host
        ],
    )
    def test_validate_catalog_url_hostless_rejected(self, project_dir, url):
        """Reject host-less URLs whose netloc is truthy but hostname is None (#3209).

        ``urlparse('https://:8080').netloc`` is ``':8080'`` (truthy) but its
        ``hostname`` is ``None``, so a netloc-based check would accept a URL
        with no actual host, contradicting the "valid URL with a host" error.
        """
        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="valid URL with a host"):
            catalog._validate_catalog_url(url)

    def test_validate_catalog_url_malformed_rejected(self, project_dir):
        """A malformed URL raises PresetValidationError, not a raw ValueError.

        ``urlparse('https://[::1').hostname`` raises ``ValueError: Invalid IPv6
        URL`` (unterminated bracket). Without wrapping, that leaks past callers'
        ``except PresetValidationError`` guards and crashes the CLI. Mirrors the
        shared ``CatalogStackBase`` (#3435) and ``IntegrationCatalog`` behaviour.
        """
        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="malformed"):
            catalog._validate_catalog_url("https://[::1")

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
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_fallback"

    def test_make_request_github_token_added_for_github_url(self, project_dir, monkeypatch):
        """GITHUB_TOKEN is attached for raw.githubusercontent.com URLs."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://raw.githubusercontent.com/org/repo/main/catalog.json")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_gh_token_fallback(self, project_dir, monkeypatch):
        """GH_TOKEN is used when GITHUB_TOKEN is absent."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GH_TOKEN", "ghp_ghtoken")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://github.com/org/repo/releases/download/v1/pack.zip")
        assert req.get_header("Authorization") == "Bearer ghp_ghtoken"

    def test_make_request_gh_token_takes_precedence(self, project_dir, monkeypatch):
        """When auth.json uses GH_TOKEN, that token is used regardless of GITHUB_TOKEN."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_secondary")
        monkeypatch.setenv("GH_TOKEN", "ghp_primary")
        self._inject_github_config(monkeypatch, token_env="GH_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://api.github.com/repos/org/repo")
        assert req.get_header("Authorization") == "Bearer ghp_primary"

    def test_make_request_token_added_for_codeload_github_com(self, project_dir, monkeypatch):
        """GITHUB_TOKEN is attached for codeload.github.com URLs."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://codeload.github.com/org/repo/zip/refs/tags/v1.0.0")
        assert req.get_header("Authorization") == "Bearer ghp_testtoken"

    def test_make_request_no_auth_for_non_matching_host(self, project_dir, monkeypatch):
        """Auth is NOT attached to hosts not listed in auth.json."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://internal.example.com/catalog.json")
        assert "Authorization" not in req.headers

    def test_make_request_no_auth_when_no_config(self, project_dir, monkeypatch):
        """No auth header when no auth.json config exists."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        catalog = PresetCatalog(project_dir)
        req = catalog._make_request("https://github.com/org/repo/releases/download/v1/pack.zip")
        assert "Authorization" not in req.headers

    def test_fetch_single_catalog_sends_auth_header(self, project_dir, monkeypatch):
        """_fetch_single_catalog passes Authorization header when configured."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)

        catalog_data = {"schema_version": "1.0", "presets": {}}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(catalog_data).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.geturl.return_value = "https://raw.githubusercontent.com/org/repo/main/presets/catalog.json"

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

        with patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog._fetch_single_catalog(entry, force_refresh=True)

        assert captured["req"].get_header("Authorization") == "Bearer ghp_testtoken"

    @pytest.mark.parametrize(
        "payload",
        [
            # Root is not a JSON object.
            [],
            "oops",
            42,
            None,
            # Root is fine but ``presets`` is the wrong type.
            {"schema_version": "1.0", "presets": []},
            {"schema_version": "1.0", "presets": "oops"},
            {"schema_version": "1.0", "presets": None},
            {"schema_version": "1.0", "presets": 42},
        ],
    )
    def test_fetch_single_catalog_rejects_malformed_payload(self, project_dir, payload):
        """Malformed catalog payloads raise PresetError, not AttributeError.

        Without this guard, a payload like ``{"presets": []}`` would pass the
        key-presence check and then crash with ``AttributeError: 'list' object
        has no attribute 'items'`` deep inside ``_get_merged_packs``. The
        sibling integration catalog reader already validates both the root
        object and the nested mapping (see ``integrations/catalog.py``); the
        preset catalog must stay consistent.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response):
            with pytest.raises(PresetError, match="Invalid preset catalog format"):
                catalog._fetch_single_catalog(entry, force_refresh=True)

    @pytest.mark.parametrize(
        "cached_payload",
        [
            [],
            "oops",
            42,
            None,
            {"schema_version": "1.0", "presets": []},
            {"schema_version": "1.0", "presets": "oops"},
            {"schema_version": "1.0", "presets": None},
        ],
    )
    def test_fetch_single_catalog_rejects_malformed_cached_payload(
        self, project_dir, cached_payload
    ):
        """A poisoned cache silently falls back to the network instead of
        crashing — cached payloads pass through the same shape validation
        as freshly-fetched ones.

        Without this, a cache poisoned by an older spec-kit version (or a
        manual edit, or an upstream that briefly served a bad payload
        before the network guards landed) would re-crash every invocation
        of ``_get_merged_packs`` despite the cache being "valid" by age.
        The recovery contract is: if the cached payload fails validation,
        drop it and refetch — never propagate ``AttributeError`` to the
        caller.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)

        # Poison the default-URL cache. ``DEFAULT_CATALOG_URL`` and
        # non-default URLs both flow through the same cache-load branch.
        cache_file, metadata_file = catalog._get_cache_paths(
            catalog.DEFAULT_CATALOG_URL
        )
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cached_payload))
        metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": catalog.DEFAULT_CATALOG_URL,
                }
            )
        )

        # Network refetch returns a valid payload so the recovery path
        # can complete.
        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        entry = PresetCatalogEntry(
            url=catalog.DEFAULT_CATALOG_URL,
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog._fetch_single_catalog(entry, force_refresh=False)

        # The poisoned cache was discarded and the network payload returned.
        assert result == valid

    @pytest.mark.parametrize(
        "payload",
        [
            # Root is not a JSON object.
            [],
            "oops",
            42,
            None,
            # Root is fine but ``presets`` is the wrong type.
            {"schema_version": "1.0", "presets": []},
            {"schema_version": "1.0", "presets": "oops"},
            {"schema_version": "1.0", "presets": None},
        ],
    )
    def test_fetch_catalog_rejects_malformed_payload(self, project_dir, payload):
        """Legacy ``fetch_catalog`` reuses the same shape-validation helper.

        Before this change ``fetch_catalog`` only checked key presence —
        so a payload like ``42`` would crash with
        ``TypeError: argument of type 'int' is not iterable`` during the
        ``"schema_version" in catalog_data`` check, and an entry mapping
        of the wrong type would crash downstream. Reusing
        ``_validate_catalog_payload`` keeps the network-side behaviour of
        the legacy single-catalog method consistent with the multi-catalog
        ``_fetch_single_catalog`` path.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            with pytest.raises(PresetError, match="Invalid preset catalog format"):
                catalog.fetch_catalog(force_refresh=True)

    def test_fetch_catalog_recovers_from_unreadable_cache(self, project_dir):
        """An unreadable / wrong-encoded cache file silently refetches.

        The cache contract is best-effort: a JSON-decode failure, an OS
        read failure (permissions / disk / handle limit), or an invalid
        text encoding on a cache file written by an older client must
        all fall through to the network fetch rather than crash the
        caller. Covers Copilot's review point that the previous
        ``except (json.JSONDecodeError, OSError)`` was missing
        ``UnicodeError``.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        # Invalid UTF-8 bytes so ``read_text`` raises ``UnicodeDecodeError``
        # (a subclass of ``UnicodeError``).
        catalog.cache_file.write_bytes(b"\xff\xfe\x00not-utf-8")
        catalog.cache_metadata_file.write_text(
            json.dumps(
                {
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                    "catalog_url": catalog.get_catalog_url(),
                }
            ),
            encoding="utf-8",
        )

        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog.fetch_catalog(force_refresh=False)

        # Recovered via network rather than crashing on the unreadable cache.
        assert result == valid

    def test_fetch_catalog_recovers_from_unreadable_metadata(self, project_dir):
        """A wrongly-encoded metadata file degrades to a cache miss.

        ``is_cache_valid`` is consulted *before* the cache payload is
        read; if the metadata file itself can't be decoded (e.g. it was
        written on a host whose default codec isn't UTF-8) the validity
        check must return ``False`` rather than propagate
        ``UnicodeDecodeError``. Without that guard, a corrupted metadata
        file would crash every invocation instead of falling through to
        a network refetch.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}", encoding="utf-8")
        # Bytes that are not valid UTF-8 — ``read_text(encoding="utf-8")``
        # will raise ``UnicodeDecodeError`` (subclass of ``UnicodeError``).
        catalog.cache_metadata_file.write_bytes(b"\xff\xfe\x00bad")

        # is_cache_valid must absorb the decode failure, not crash.
        assert catalog.is_cache_valid() is False

        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            result = catalog.fetch_catalog(force_refresh=False)

        assert result == valid

    @pytest.mark.parametrize(
        "non_mapping_metadata",
        [
            "[]",       # JSON array
            '"oops"',   # JSON string
            "42",       # JSON number
            "true",     # JSON bool
            "null",     # JSON null
        ],
    )
    def test_is_cache_valid_handles_non_mapping_metadata(
        self, project_dir, non_mapping_metadata
    ):
        """Metadata that parses to a non-mapping degrades to cache-invalid.

        The cache-validity check calls ``metadata.get("cached_at", "")``
        immediately after ``json.loads``. If the metadata file is valid
        JSON but parses to a non-mapping (``[]``, ``"oops"``, ``42``,
        ``true``, ``null``), ``.get`` raises ``AttributeError`` — which
        previously slipped past the except tuple and crashed the
        caller. The contract documented on ``is_cache_valid`` says any
        decode/shape failure should return ``False`` so ``fetch_catalog``
        falls through to a network refetch. This test pins that
        contract across every JSON non-mapping root type.
        """
        catalog = PresetCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}", encoding="utf-8")
        catalog.cache_metadata_file.write_text(
            non_mapping_metadata, encoding="utf-8"
        )

        # Must not raise — the contract is "any decode/shape failure → False".
        assert catalog.is_cache_valid() is False

    def test_fetch_catalog_writes_cache_as_utf8(self, project_dir, monkeypatch):
        """Cache + metadata writes pass ``encoding="utf-8"``, observably.

        The earlier version of this test claimed to assert UTF-8 at the
        byte level but actually only round-tripped a non-ASCII string
        through ``json.dumps`` and ``read_text(encoding="utf-8")``.
        Because ``json.dumps`` defaults to ``ensure_ascii=True``, "café"
        was serialized as the all-ASCII escape ``caf\\u00e9`` before it
        ever reached ``write_text`` — the bytes on disk were identical
        regardless of the encoding kwarg. The drift Copilot's review
        flagged wasn't actually being caught.

        Fix: directly observe the ``encoding`` argument passed to every
        ``write_text`` call made against the cache directory. This is
        the production code's encoding choice, which is exactly what
        the regression guard cares about.
        """
        from unittest.mock import patch, MagicMock
        from pathlib import Path as _PathCls

        catalog = PresetCatalog(project_dir)
        payload = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        # Record every ``write_text`` call's encoding kwarg so the
        # assertion observes the production writer's argument directly.
        recorded: list[dict] = []
        real_write_text = _PathCls.write_text

        def recording_write_text(self, data, *args, **kwargs):
            recorded.append(
                {"path": str(self), "encoding": kwargs.get("encoding")}
            )
            return real_write_text(self, data, *args, **kwargs)

        monkeypatch.setattr(_PathCls, "write_text", recording_write_text)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            catalog.fetch_catalog(force_refresh=True)

        cache_writes = [
            r for r in recorded if str(catalog.cache_dir) in r["path"]
        ]
        assert cache_writes, "fetch_catalog made no writes to the cache dir"
        for record in cache_writes:
            assert record["encoding"] == "utf-8", (
                f"write_text on {record['path']} used encoding "
                f"{record['encoding']!r}; expected 'utf-8'"
            )

    def test_fetch_catalog_survives_unwritable_cache(self, project_dir, monkeypatch):
        """An unwritable cache dir doesn't fail a successful fetch.

        Cache writes are best-effort, mirroring the read side and the
        ``integrations/catalog.py`` precedent: if ``mkdir``/``write_text``
        raises ``OSError`` (read-only checkout, permissions), the
        already-fetched-and-validated payload must still be returned —
        not swallowed into the broad except and re-raised as a
        ``PresetError``.
        """
        from unittest.mock import patch, MagicMock
        from pathlib import Path as _PathCls

        catalog = PresetCatalog(project_dir)
        valid = {
            "schema_version": "1.0",
            "presets": {"foo": {"name": "Foo", "version": "1.0.0"}},
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(valid).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        # Simulate an unwritable cache dir: every write_text under the
        # cache directory raises PermissionError (an OSError subclass).
        real_write_text = _PathCls.write_text

        def failing_write_text(self, data, *args, **kwargs):
            if str(catalog.cache_dir) in str(self):
                raise PermissionError("cache dir is read-only")
            return real_write_text(self, data, *args, **kwargs)

        monkeypatch.setattr(_PathCls, "write_text", failing_write_text)

        with patch.object(catalog, "_open_url", return_value=mock_response):
            # Legacy single-catalog path.
            assert catalog.fetch_catalog(force_refresh=True) == valid

            # Multi-catalog path.
            entry = PresetCatalogEntry(
                url=catalog.DEFAULT_CATALOG_URL,
                name="default",
                priority=1,
                install_allowed=True,
            )
            assert (
                catalog._fetch_single_catalog(entry, force_refresh=True) == valid
            )

    def test_get_merged_packs_skips_non_mapping_entries(self, project_dir):
        """Per-entry guard: one malformed entry shouldn't poison the merge.

        ``_fetch_single_catalog`` validates that ``presets`` is a mapping,
        but it doesn't (and shouldn't) validate every entry inside it — a
        single bad entry in an otherwise-valid catalog should be skipped,
        not crash the whole resolve path. Mirrors the per-entry skip in
        ``integrations/catalog.py``: a malformed entry returns no error,
        valid entries continue to merge normally.
        """
        from unittest.mock import patch, MagicMock

        catalog = PresetCatalog(project_dir)
        payload = {
            "schema_version": "1.0",
            "presets": {
                "good": {"name": "Good", "version": "1.0.0"},
                "bad-list": [],
                "bad-str": "oops",
            },
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        entry = PresetCatalogEntry(
            url="https://example.com/catalog.json",
            name="default",
            priority=1,
            install_allowed=True,
        )

        with patch.object(catalog, "_open_url", return_value=mock_response), \
             patch.object(catalog, "get_active_catalogs", return_value=[entry]):
            merged = catalog._get_merged_packs(force_refresh=True)

        # Only the well-formed entry survives; the two malformed entries are
        # silently dropped rather than raising or crashing.
        assert list(merged.keys()) == ["good"]

    def test_download_pack_sends_auth_header(self, project_dir, monkeypatch):
        """download_pack passes Authorization header when configured."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)

        import io
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", "id: test-pack\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        release_response = MagicMock()
        release_response.read.return_value = json.dumps(
            {
                "assets": [
                    {
                        "name": "test-pack.zip",
                        "url": "https://api.github.com/repos/org/repo/releases/assets/1",
                    }
                ]
            }
        ).encode()
        release_response.__enter__ = lambda s: s
        release_response.__exit__ = MagicMock(return_value=False)

        asset_response = MagicMock()
        asset_response.read.return_value = zip_bytes
        asset_response.__enter__ = lambda s: s
        asset_response.__exit__ = MagicMock(return_value=False)

        captured = []
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured.append(req)
            if req.full_url.endswith("/releases/tags/v1"):
                return release_response
            return asset_response

        mock_opener.open.side_effect = fake_open

        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://github.com/org/repo/releases/download/v1/test-pack.zip",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog.download_pack("test-pack", target_dir=project_dir)

        assert captured[0].full_url == "https://api.github.com/repos/org/repo/releases/tags/v1"
        assert captured[0].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[1].full_url == "https://api.github.com/repos/org/repo/releases/assets/1"
        assert captured[1].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[1].get_header("Accept") == "application/octet-stream"

    def _pack_zip_and_response(self):
        """Build a minimal preset ZIP and a context-manager mock response."""
        from unittest.mock import MagicMock
        import io

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", "id: test-pack\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        resp = MagicMock()
        resp.read.return_value = zip_bytes
        # Configure the context-manager protocol explicitly so `with resp`
        # yields `resp` itself, independent of how the protocol is invoked.
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return zip_bytes, resp

    def test_download_pack_accepts_matching_sha256(self, project_dir):
        """A catalog ``sha256`` that matches the preset archive is accepted."""
        import hashlib
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        zip_bytes, resp = self._pack_zip_and_response()
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "sha256": hashlib.sha256(zip_bytes).hexdigest(),
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=resp):
            zip_path = catalog.download_pack("test-pack", target_dir=project_dir)

        assert zip_path.read_bytes() == zip_bytes

    def test_download_pack_rejects_sha256_mismatch(self, project_dir):
        """A catalog ``sha256`` that does not match the archive aborts install."""
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        _zip_bytes, resp = self._pack_zip_and_response()
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "sha256": "0" * 64,  # deliberately wrong
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=resp):
            with pytest.raises(PresetError, match="[Ii]ntegrity"):
                catalog.download_pack("test-pack", target_dir=project_dir)

    def test_download_pack_without_sha256_skips_verification(self, project_dir):
        """A catalog entry with no ``sha256`` keeps working: verification is
        opt-in, so the backwards-compatible path (``pack_info.get("sha256")``
        is ``None``) must download without aborting — mirrors the extensions
        coverage so the helper never silently becomes mandatory for presets.
        """
        from unittest.mock import patch

        catalog = PresetCatalog(project_dir)
        zip_bytes, resp = self._pack_zip_and_response()
        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://example.com/test-pack.zip",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch.object(catalog, "_open_url", return_value=resp):
            zip_path = catalog.download_pack("test-pack", target_dir=project_dir)

        assert zip_path.read_bytes() == zip_bytes

    def test_download_pack_accepts_direct_github_rest_asset_url(self, project_dir, monkeypatch):
        """download_pack can use a GitHub REST release asset URL directly."""
        from unittest.mock import patch, MagicMock

        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        self._inject_github_config(monkeypatch, token_env="GITHUB_TOKEN")
        catalog = PresetCatalog(project_dir)

        import io
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", "id: test-pack\nname: Test\nversion: 1.0.0\n")
        zip_bytes = zip_buf.getvalue()

        asset_response = MagicMock()
        asset_response.read.return_value = zip_bytes
        asset_response.__enter__ = lambda s: s
        asset_response.__exit__ = MagicMock(return_value=False)

        captured = []
        mock_opener = MagicMock()

        def fake_open(req, timeout=None):
            captured.append(req)
            return asset_response

        mock_opener.open.side_effect = fake_open

        pack_info = {
            "id": "test-pack",
            "name": "Test Pack",
            "version": "1.0.0",
            "download_url": "https://api.github.com/repos/org/repo/releases/assets/1",
            "_install_allowed": True,
        }

        with patch.object(catalog, "get_pack_info", return_value=pack_info), \
             patch("specify_cli.authentication.http.urllib.request.build_opener", return_value=mock_opener):
            catalog.download_pack("test-pack", target_dir=project_dir)

        assert len(captured) == 1
        assert captured[0].full_url == "https://api.github.com/repos/org/repo/releases/assets/1"
        assert captured[0].get_header("Authorization") == "Bearer ghp_testtoken"
        assert captured[0].get_header("Accept") == "application/octet-stream"


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

    def test_load_catalog_config_rejects_boolean_priority(self, project_dir):
        """A YAML ``priority: true`` is a typo, not a request for priority 1.

        ``bool`` is a subclass of ``int`` in Python, so ``int(True)`` silently
        returns ``1``. Without an explicit guard a malformed config like
        ``priority: yes`` would be accepted as a valid priority of 1 and
        silently change catalog ordering. The sibling integration-catalog
        reader rejects this case (see ``catalogs.py``); the preset catalog
        reader must stay consistent.
        """
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "bool-priority",
                    "url": "https://example.com/catalog.json",
                    "priority": True,
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid priority|expected integer"):
            catalog._load_catalog_config(config_path)

    def test_load_catalog_config_rejects_infinite_priority(self, project_dir):
        """A ``priority: .inf`` yields a clean validation error, not an uncaught
        OverflowError from int(float('inf'))."""
        config_path = project_dir / ".specify" / "preset-catalogs.yml"
        config_path.write_text(yaml.dump({
            "catalogs": [
                {
                    "name": "inf-priority",
                    "url": "https://example.com/catalog.json",
                    "priority": float("inf"),
                }
            ]
        }))

        catalog = PresetCatalog(project_dir)
        with pytest.raises(PresetValidationError, match="Invalid priority|expected integer"):
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
SELF_TEST_WRAP_WARNING = (
    r"Cannot compose command 'speckit\.wrap-test': no base layer\. "
    r"Stale command files may remain\."
)

CORE_TEMPLATE_NAMES = [
    "spec-template",
    "plan-template",
    "tasks-template",
    "checklist-template",
    "constitution-template",
]


def install_self_test_preset(manager: PresetManager, speckit_version: str = "0.1.5") -> PresetManifest:
    """Install self-test while filtering its intentionally missing wrap base."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=SELF_TEST_WRAP_WARNING,
            category=UserWarning,
            module=r"specify_cli\.presets",
        )
        return manager.install_from_directory(SELF_TEST_PRESET_DIR, speckit_version)


def _make_convention_constitution_preset(temp_dir: Path) -> Path:
    """Create a preset whose constitution is found by convention, not its manifest."""
    preset_dir = temp_dir / "convention-constitution"
    (preset_dir / "templates").mkdir(parents=True)
    (preset_dir / "templates" / "constitution-template.md").write_text(
        "# Convention Constitution\n"
    )
    (preset_dir / "templates" / "spec-template.md").write_text("# Spec\n")
    (preset_dir / "preset.yml").write_text(
        yaml.dump(
            {
                "schema_version": "1.0",
                "preset": {
                    "id": "convention-constitution",
                    "name": "Convention Constitution",
                    "version": "1.0.0",
                    "description": "Convention-based constitution for testing",
                },
                "requires": {"speckit_version": ">=0.1.0"},
                "provides": {
                    "templates": [
                        {
                            "type": "template",
                            "name": "spec-template",
                            "file": "templates/spec-template.md",
                        }
                    ]
                },
            }
        )
    )
    return preset_dir


class TestSelfTestPreset:
    """Tests using the self-test preset that ships with the repo.

    The self-test preset ships a wrap-strategy command (``speckit.wrap-test``)
    without a corresponding core base layer; reconciliation deliberately
    surfaces a UserWarning in that case. Tests install via
    ``install_self_test_preset`` (defined above), which scopes a narrow
    ``warnings.filterwarnings`` block to that specific message and
    ``UserWarning`` category — so the expected warning stays quiet without
    masking unrelated warnings or real reconciliation failures.
    """

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
        assert len(manifest.templates) == 7  # 5 templates + 2 commands

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
        manifest = install_self_test_preset(manager)
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
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)
        manager.remove("self-test")

        resolver = PresetResolver(project_dir)
        for name in CORE_TEMPLATE_NAMES:
            result = resolver.resolve_with_source(name)
            assert result is not None
            assert result["source"] == "core"

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Core constitution-template\n"

    def test_self_test_removal_preserves_edited_constitution(self, project_dir):
        """Removing a preset does not overwrite an edited generated constitution."""
        templates_dir = project_dir / ".specify" / "templates"
        (templates_dir / "constitution-template.md").write_text("# Core Constitution\n")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        edited = memory.read_text() + "\n## Authored amendment\n"
        memory.write_text(edited)

        manager.remove("self-test")

        assert memory.read_text() == edited

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
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)

        cmd_file = claude_dir / "speckit-specify" / "SKILL.md"
        assert cmd_file.exists()

        manager.remove("self-test")
        assert not cmd_file.exists(), "Command not cleaned up after preset removal"

    def test_self_test_no_commands_without_agent_dirs(self, project_dir):
        """Test that no commands are registered when no agent dirs exist."""
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        metadata = manager.registry.get("self-test")
        assert metadata["registered_commands"] == {}

    def test_self_test_seeds_constitution_when_memory_absent(self, project_dir):
        """Installing a preset seeds memory/constitution.md from its template."""
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.exists(), "constitution.md was not seeded from the preset"
        assert "preset:self-test" in memory.read_text(), (
            "constitution.md was not seeded from the self-test preset template"
        )

    def test_self_test_reseeds_exact_core_constitution(self, project_dir):
        """An unchanged core constitution is re-seeded from the preset template."""
        resolver = PresetResolver(project_dir)
        bundled_core = resolver._find_bundled_core(
            "constitution-template", "template", ".md"
        )
        assert bundled_core is not None
        core = bundled_core.read_bytes()
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_bytes(core)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        content = memory.read_text()
        assert "preset:self-test" in content, "placeholder constitution was not re-seeded"
        assert "[PROJECT_NAME]" not in content

    @pytest.mark.parametrize(
        "provenance_content",
        [
            '{"sha256": "does-not-match", "source": "old-preset"}\n',
            "{not valid json",
        ],
        ids=["hash-mismatch", "malformed"],
    )
    def test_self_test_preserves_core_content_with_existing_invalid_provenance(
        self, project_dir, provenance_content
    ):
        """A present invalid sidecar disables legacy core-template migration."""
        resolver = PresetResolver(project_dir)
        bundled_core = resolver._find_bundled_core(
            "constitution-template", "template", ".md"
        )
        assert bundled_core is not None
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_bytes(bundled_core.read_bytes())
        (memory.parent / ".constitution-template.json").write_text(
            provenance_content
        )
        original = memory.read_bytes()

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        assert memory.read_bytes() == original

    def test_self_test_preserves_mutable_project_core_copy(self, project_dir):
        """A project template copy does not establish generated provenance."""
        authored = "# Acme Organization Constitution\n\nOrganization policy.\n"
        project_template = (
            project_dir / ".specify" / "templates" / "constitution-template.md"
        )
        project_template.write_text(authored)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        assert memory.read_text() == authored
        assert not (memory.parent / ".constitution-template.json").exists()

    def test_core_prefixed_preset_does_not_establish_generated_provenance(
        self, project_dir, temp_dir
    ):
        """A preset ID beginning with core is not an immutable core source."""
        authored = "# Acme Organization Constitution\n\nOrganization policy.\n"
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        memory.write_text(authored)

        preset_dir = temp_dir / "core-company"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(authored)
        (preset_dir / "preset.yml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "core-company",
                        "name": "Core Company",
                        "version": "1.0.0",
                        "description": "Company constitution preset",
                        "author": "Test Author",
                        "repository": "https://github.com/test/core-company",
                        "license": "MIT",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "description": "Company constitution",
                                "replaces": "constitution-template",
                            }
                        ]
                    },
                }
            )
        )

        PresetManager(project_dir).install_from_directory(preset_dir, "0.1.5")

        assert memory.read_text() == authored
        assert not (memory.parent / ".constitution-template.json").exists()

    def test_self_test_preserves_authored_constitution_with_placeholder(
        self, project_dir
    ):
        """A placeholder mention does not establish generated provenance."""
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        authored = "# Acme Constitution\n\nGuidance for [PROJECT_NAME].\n"
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        assert memory.read_text() == authored

    def test_self_test_preserves_authored_constitution(self, project_dir):
        """An authored (placeholder-free) constitution is never overwritten."""
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        authored = "# Acme Constitution\n\n### I. Ship It\nAuthored by a human.\n"
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        assert memory.read_text() == authored, "authored constitution was overwritten"

    def test_self_test_override_resolves_constitution_template(self, project_dir):
        """The preset override of constitution-template resolves to the preset file."""
        templates_dir = project_dir / ".specify" / "templates"
        (templates_dir / "constitution-template.md").write_text("# Core constitution\n")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("constitution-template", "template")
        assert result is not None
        assert "preset:self-test" in result.read_text()

    def test_constitution_seed_composes_wrap_strategy(self, project_dir, temp_dir):
        """Seeding memory composes wrap constitution-template layers."""
        templates_dir = project_dir / ".specify" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        (templates_dir / "constitution-template.md").write_text(
            "# Core Constitution\n\n## Core Principle\n"
        )

        preset_dir = temp_dir / "constitution-wrap"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Wrapper Constitution\n\n{CORE_TEMPLATE}\n\n## Wrapper Footer\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "constitution-wrap",
                        "name": "Constitution Wrap",
                        "version": "1.0.0",
                        "description": "Wrap constitution template for testing",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "wrap",
                                "description": "Wrapped constitution template",
                            }
                        ]
                    },
                }
            )
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        content = memory.read_text()
        assert "{CORE_TEMPLATE}" not in content
        assert "# Wrapper Constitution" in content
        assert "## Core Principle" in content

    def test_constitution_follows_priority_when_winning_preset_removed(
        self, project_dir, temp_dir
    ):
        """An unchanged generated constitution follows priority and fallback layers."""
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        preset_dir = temp_dir / "higher-priority"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Higher Priority Constitution\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "higher-priority",
                        "name": "Higher Priority",
                        "version": "1.0.0",
                        "description": "Higher-priority constitution",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "replace",
                                "description": "Higher-priority constitution",
                            }
                        ]
                    },
                }
            )
        )

        manager.install_from_directory(preset_dir, "0.1.5", priority=1)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Higher Priority Constitution\n"

        manager.remove("higher-priority")

        assert "preset:self-test" in memory.read_text()

    def test_convention_constitution_removal_restores_remaining_layer(
        self, project_dir, temp_dir
    ):
        """Removing a convention layer rematerializes the remaining resolver layer."""
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5", priority=1
        )

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Convention Constitution\n"

        manager.remove("convention-constitution")

        assert "preset:self-test" in memory.read_text()

    def test_convention_constitution_removal_preserves_edited_content(
        self, project_dir, temp_dir
    ):
        """Removing a convention layer does not overwrite edited generated content."""
        from specify_cli.commands.init import ensure_constitution_from_template

        templates_dir = project_dir / ".specify" / "templates"
        (templates_dir / "constitution-template.md").write_text("# Core Constitution\n")
        manager = PresetManager(project_dir)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5"
        )
        ensure_constitution_from_template(project_dir)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        edited = memory.read_text() + "\n## Authored amendment\n"
        memory.write_text(edited)

        manager.remove("convention-constitution")

        assert memory.read_text() == edited

    def test_custom_constitution_removal_recovers_with_invalid_manifest(
        self, project_dir, temp_dir
    ):
        """Provenance triggers fallback when a custom-path manifest is invalid."""
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        preset_dir = temp_dir / "custom-constitution"
        (preset_dir / "policy").mkdir(parents=True)
        (preset_dir / "policy" / "charter.md").write_text("# Custom Constitution\n")
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "custom-constitution",
                        "name": "Custom Constitution",
                        "version": "1.0.0",
                        "description": "Custom-path constitution for testing",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "policy/charter.md",
                            }
                        ]
                    },
                }
            )
        )
        manager.install_from_directory(preset_dir, "0.1.5", priority=1)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Custom Constitution\n"

        installed_manifest = (
            project_dir
            / ".specify"
            / "presets"
            / "custom-constitution"
            / "preset.yml"
        )
        installed_manifest.write_text("invalid: [")

        manager.remove("custom-constitution")

        assert "preset:self-test" in memory.read_text()

    def test_constitution_seed_rejects_symlinked_memory_directory(
        self, project_dir, temp_dir
    ):
        """Preset installation cannot seed through a symlinked memory directory."""
        outside = temp_dir / "outside"
        outside.mkdir()
        try:
            (project_dir / ".specify" / "memory").symlink_to(
                outside, target_is_directory=True
            )
        except OSError:
            pytest.skip("symlinks are unavailable")

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="symlinked"):
            install_self_test_preset(manager)

        assert manager.registry.is_installed("self-test")
        assert not (outside / "constitution.md").exists()

    def test_constitution_seed_rejects_dangling_destination_symlink(
        self, project_dir, temp_dir
    ):
        """Preset installation cannot seed through a dangling destination symlink."""
        memory = project_dir / ".specify" / "memory"
        memory.mkdir(parents=True)
        outside = temp_dir / "outside-constitution.md"
        try:
            (memory / "constitution.md").symlink_to(outside)
        except OSError:
            pytest.skip("symlinks are unavailable")

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="symlinked"):
            install_self_test_preset(manager)

        assert manager.registry.is_installed("self-test")
        assert not outside.exists()

    def test_constitution_materialization_error_is_nonfatal(
        self, project_dir, temp_dir
    ):
        """An invalid wrap warns without reporting an uninstalled preset."""
        preset_dir = temp_dir / "invalid-wrap"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Missing core placeholder\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "invalid-wrap",
                        "name": "Invalid Wrap",
                        "version": "1.0.0",
                        "description": "Invalid wrapping constitution",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "wrap",
                                "description": "Invalid wrap",
                            }
                        ]
                    },
                }
            )
        )

        manager = PresetManager(project_dir)
        with pytest.warns(UserWarning, match="Failed to seed constitution"):
            manifest = manager.install_from_directory(preset_dir, "0.1.5")

        assert manifest.id == "invalid-wrap"
        assert manager.registry.is_installed("invalid-wrap")

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

    def test_save_and_load_available_from_init_options_module(self, project_dir):
        from specify_cli._init_options import load_init_options, save_init_options

        opts = {"ai": "codex", "ai_skills": True, "script": "sh"}
        save_init_options(project_dir, opts)

        assert load_init_options(project_dir) == opts

    def test_save_uses_utf8_encoding(self, project_dir, monkeypatch):
        from specify_cli import save_init_options

        original_write_text = Path.write_text
        seen: dict[str, str | None] = {}

        def spy_write_text(path, data, *args, **kwargs):
            if path == project_dir / ".specify" / "init-options.json":
                seen["encoding"] = kwargs.get("encoding")
            return original_write_text(path, data, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", spy_write_text)

        save_init_options(project_dir, {"label": "中文测试"})

        assert seen["encoding"] == "utf-8"

    def test_load_uses_utf8_encoding(self, project_dir, monkeypatch):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text('{"ai": "codex"}', encoding="utf-8")

        original_read_text = Path.read_text
        seen: dict[str, str | None] = {}

        def spy_read_text(path, *args, **kwargs):
            if path == opts_file:
                seen["encoding"] = kwargs.get("encoding")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", spy_read_text)

        assert load_init_options(project_dir) == {"ai": "codex"}
        assert seen["encoding"] == "utf-8"

    def test_load_returns_empty_when_missing(self, project_dir):
        from specify_cli import load_init_options

        assert load_init_options(project_dir) == {}

    def test_load_returns_empty_on_invalid_json(self, project_dir):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text("{bad json")

        assert load_init_options(project_dir) == {}

    @pytest.mark.parametrize(
        "value",
        ["名前-プロジェクト", "café-résumé", "Ωmega-Δelta", "🚀-launch"],
    )
    def test_save_load_round_trip_preserves_non_ascii(self, project_dir, value):
        """Non-ASCII values round-trip via explicit UTF-8 encoding.

        ``Path.write_text`` / ``Path.read_text`` default to the system
        locale codec on Windows (cp1252 / gb2312 / cp932). Without
        ``encoding="utf-8"`` pinned on both ends, a project name like
        ``café`` written on a UTF-8 host becomes garbled or unreadable on
        a cp1252 host (and vice versa). Pin UTF-8 explicitly so init
        options round-trip across machines and CI.

        Note: this test only meaningfully exercises the encoding pin
        because ``save_init_options`` now writes JSON with
        ``ensure_ascii=False`` — otherwise ``json.dumps`` would output
        ASCII-only ``\\uXXXX`` escapes and the encoding pin would be a
        no-op for any value here. ``test_save_writes_real_utf8_bytes``
        below asserts that contract directly.
        """
        from specify_cli import save_init_options, load_init_options

        save_init_options(project_dir, {"ai": "claude", "project_name": value})

        loaded = load_init_options(project_dir)
        assert loaded["project_name"] == value

    def test_save_writes_real_utf8_bytes(self, project_dir):
        """The on-disk file contains real UTF-8 bytes, not ``\\uXXXX`` escapes.

        Pinning ``encoding="utf-8"`` on ``write_text`` only makes a
        difference when the serialiser actually emits non-ASCII
        characters. With ``ensure_ascii=False`` on ``json.dumps`` the
        non-ASCII bytes hit the file, so the encoding pin is the thing
        that decides between cp1252 garbage and clean UTF-8 on Windows.

        This test pins that behaviour: the on-disk bytes are valid UTF-8
        and contain the multi-byte encoding of ``café``, not its
        ``\\u00e9`` escape form. Reviewers can verify that removing
        ``ensure_ascii=False`` or ``encoding="utf-8"`` from the writer
        breaks this test, which is what Copilot's review pointed out the
        original round-trip test failed to do.
        """
        from specify_cli import save_init_options

        save_init_options(project_dir, {"project_name": "café"})

        opts_file = project_dir / ".specify" / "init-options.json"
        raw = opts_file.read_bytes()
        # 'café' in UTF-8 ends with bytes 0xC3 0xA9 ('é'). The cp1252
        # encoding of 'é' is the single byte 0xE9. The JSON-escape form
        # would be the 6-byte literal '\\u00e9'. We assert the UTF-8 form
        # is present so the test pins the actual contract.
        assert b"caf\xc3\xa9" in raw, (
            "Expected UTF-8 bytes for 'café' in the on-disk file, "
            f"got: {raw!r}"
        )
        # And the whole file decodes cleanly as UTF-8.
        raw.decode("utf-8")

    def test_load_returns_empty_on_locale_corrupted_file(self, project_dir):
        """A file written in a non-UTF-8 codec falls back to {}, not crash.

        Simulates a file produced by an old client (or by a peer machine
        with a different default locale) that contains bytes invalid as
        UTF-8. ``load_init_options`` should fall back to ``{}`` per the
        existing contract — never propagate a raw ``UnicodeDecodeError``
        to the CLI surface.
        """
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        # 0xE9 is 'é' in cp1252 but an invalid lead byte in UTF-8.
        opts_file.write_bytes(b'{"project_name": "caf\xe9"}')

        assert load_init_options(project_dir) == {}

    @pytest.mark.parametrize("payload", ["[]", '"value"', "42", "true", "null"])
    def test_load_returns_empty_on_non_object_json(self, project_dir, payload):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_text(payload, encoding="utf-8")

        assert load_init_options(project_dir) == {}

    def test_load_returns_empty_on_unicode_decode_error(self, project_dir, monkeypatch):
        from specify_cli import load_init_options

        opts_file = project_dir / ".specify" / "init-options.json"
        opts_file.parent.mkdir(parents=True, exist_ok=True)
        opts_file.write_bytes(b"{}")

        original_read_text = Path.read_text

        def raise_decode_error(path, *args, **kwargs):
            if path == opts_file:
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", raise_decode_error)

        assert load_init_options(project_dir) == {}

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, True),
            (False, False),
            ("true", False),
            ("false", False),
            (1, False),
            (0, False),
            (None, False),
        ],
    )
    def test_is_ai_skills_enabled_requires_boolean_true(self, value, expected):
        from specify_cli._init_options import is_ai_skills_enabled

        assert is_ai_skills_enabled({"ai_skills": value}) is expected


class TestPresetSkills:
    """Tests for preset skill registration and unregistration.

    Tests that install the self-test preset use ``install_self_test_preset``
    which scopes a narrow filter to the expected wrap-strategy warning.
    Reconciliation failures remain audible so real regressions surface.
    """

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

    def _create_command_preset(self, temp_dir, preset_id, command_name, description, body):
        preset_dir = temp_dir / preset_id
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        command_file = f"{command_name}.md"
        (preset_dir / "commands" / command_file).write_text(
            f"---\ndescription: {description}\n---\n\n{body}\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": preset_id,
                "name": preset_id,
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": command_name,
                        "file": f"commands/{command_file}",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)
        return preset_dir

    def test_skill_overridden_on_preset_install(self, project_dir, temp_dir):
        """When skills mode was used, a preset command override should update the skill."""
        # Simulate skills mode having been used: write init-options + create skill
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # Also create the claude commands dir so commands get registered
        (project_dir / ".claude" / "skills").mkdir(parents=True, exist_ok=True)

        # Install self-test preset (has a command override for speckit.specify)
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content, "Skill should reference preset source"
        assert "disable-model-invocation: false" in content

        # Verify it was recorded in registry
        metadata = manager.registry.get("self-test")
        assert "speckit-specify" in metadata.get("registered_skills", [])

    def _install_arg_hint_preset(self, project_dir, temp_dir, ai, skills_dir, description, arg_hint):
        """Install a preset whose command declares argument-hint; return the SKILL.md path."""
        self._write_init_options(project_dir, ai=ai)
        self._create_skill(skills_dir, "speckit-hinttest-cmd")
        (project_dir / ".specify" / "extensions" / "hinttest").mkdir(parents=True, exist_ok=True)

        preset_dir = temp_dir / f"hint-preset-{ai}"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.hinttest.cmd.md").write_text(
            "---\n"
            f'description: "{description}"\n'
            f'argument-hint: "{arg_hint}"\n'
            "---\n\n"
            "Preset command body.\n",
            encoding="utf-8",
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": f"hint-preset-{ai}",
                "name": "Hint Preset",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.hinttest.cmd",
                        "file": "commands/speckit.hinttest.cmd.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        return skills_dir / "speckit-hinttest-cmd" / "SKILL.md"

    def test_argument_hint_preserved_for_preset_command(self, project_dir, temp_dir):
        """argument-hint from a preset command must survive into the SKILL.md.

        Follow-up to #2903/#2916 for the preset skill generator. The
        description is long enough to fold across lines when serialized,
        guarding against an in-place string injection that would split the
        folded scalar into invalid YAML.
        """
        long_description = (
            "Build and maintain a lean, static context/ knowledge folder so "
            "coding agents load only what is relevant and save tokens"
        )
        arg_hint = "<init | update | list | check> [area] [slug] [-- notes]"
        skills_dir = project_dir / ".claude" / "skills"

        skill_file = self._install_arg_hint_preset(
            project_dir, temp_dir, "claude", skills_dir, long_description, arg_hint
        )
        assert skill_file.exists()
        parsed = yaml.safe_load(skill_file.read_text(encoding="utf-8").split("---", 2)[1])
        assert parsed["argument-hint"] == arg_hint
        assert parsed["description"] == long_description

    def test_argument_hint_not_added_for_non_claude_preset_command(self, project_dir, temp_dir):
        """Non-Claude skills agents must not receive argument-hint in preset skills."""
        arg_hint = "<init | update | list | check> [area]"
        skills_dir = project_dir / ".agents" / "skills"

        skill_file = self._install_arg_hint_preset(
            project_dir, temp_dir, "codex", skills_dir, "Build context", arg_hint
        )
        assert skill_file.exists()
        parsed = yaml.safe_load(skill_file.read_text(encoding="utf-8").split("---", 2)[1])
        assert "argument-hint" not in parsed

    def test_register_skills_resolves_command_refs(self, project_dir, temp_dir):
        """Preset skill overrides must resolve __SPECKIT_COMMAND_*__ tokens (issue #2717).

        ``_register_skills()`` previously ran only ``resolve_skill_placeholders()``,
        so command cross-references leaked into SKILL.md as raw placeholders
        instead of rendering as ``/speckit-<cmd>`` like the command layer.
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-install",
            "speckit.specify",
            "Override specify",
            "Run `__SPECKIT_COMMAND_SPECIFY__` then `__SPECKIT_COMMAND_PLAN__`.\n",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked into SKILL.md"
        # Claude's invoke_separator is "-", so tokens render as /speckit-<cmd>.
        assert "/speckit-specify" in content
        assert "/speckit-plan" in content

    def test_restore_skill_resolves_command_refs(self, project_dir, temp_dir):
        """Skill restore on preset removal must also resolve command tokens (issue #2717)."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "specify.md").write_text(
            "---\ndescription: Core specify\n---\n\n"
            "Then run `__SPECKIT_COMMAND_PLAN__`.\n"
        )

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-restore",
            "speckit.specify",
            "Override specify",
            "Override body\n",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("cmdref-restore")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked on restore"
        assert "/speckit-plan" in content

    def test_reconcile_override_skill_resolves_command_refs(self, project_dir, temp_dir):
        """Reconcile's project-override restore must resolve command tokens (issue #2717).

        When a preset that overrode a command is removed and a project override
        becomes the winning layer, ``_reconcile_skills`` rewrites the skill from
        the override body — which must also render ``__SPECKIT_COMMAND_*__`` tokens.
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        # Project override wins once the preset is removed; its body carries a
        # command cross-reference token. No core template exists for "specify",
        # so the skill is restored exclusively via the reconcile override branch.
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True, exist_ok=True)
        (overrides_dir / "speckit.specify.md").write_text(
            "---\ndescription: Override specify\n---\n\n"
            "Then run `__SPECKIT_COMMAND_PLAN__`.\n"
        )

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-reconcile",
            "speckit.specify",
            "Preset specify",
            "Preset body\n",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("cmdref-reconcile")

        content = (skills_dir / "speckit-specify" / "SKILL.md").read_text()
        assert "override:speckit.specify" in content, "skill should be restored from the project override"
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked on reconcile"
        assert "/speckit-plan" in content

    def test_extension_restore_resolves_command_refs(self, project_dir, temp_dir):
        """Extension-backed skill restore must resolve command tokens (issue #2717).

        When a preset override is removed and the skill is restored from an
        extension command body, ``__SPECKIT_COMMAND_*__`` tokens in that body
        must render as slash-command invocations like the core-template path.
        """
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="original extension skill")

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Then run `__SPECKIT_COMMAND_PLAN__`.\n"
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

        preset_dir = self._create_command_preset(
            temp_dir,
            "cmdref-ext-restore",
            "speckit.fakeext.cmd",
            "Override fakeext cmd",
            "Override body\n",
        )
        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("cmdref-ext-restore")

        content = (skills_dir / "speckit-fakeext-cmd" / "SKILL.md").read_text()
        assert "source: extension:fakeext" in content, "skill should be restored from the extension"
        assert "__SPECKIT_COMMAND_" not in content, "raw command token leaked on extension restore"
        assert "/speckit-plan" in content

    def test_core_command_override_skill_uses_preset_command_description(self, project_dir, temp_dir):
        """Preset skill overrides for core commands should keep preset frontmatter descriptions."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-taskstoissues")

        preset_dir = temp_dir / "taskstoissues-description"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.repro.taskstoissues.md").write_text(
            "---\n"
            "description: COMMAND-FRONTMATTER-DESCRIPTION\n"
            "---\n\n"
            "# Repro command body\n"
        )
        manifest_data = {
            "schema_version": "1.0",
            "preset": {
                "id": "taskstoissues-description",
                "name": "Taskstoissues Description",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.taskstoissues",
                        "file": "commands/speckit.repro.taskstoissues.md",
                        "description": "MANIFEST-DESCRIPTION",
                        "replaces": "speckit.taskstoissues",
                        "strategy": "replace",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-taskstoissues" / "SKILL.md"
        content = skill_file.read_text()
        assert "description: COMMAND-FRONTMATTER-DESCRIPTION" in content
        assert "Convert tasks from tasks.md into GitHub issues." not in content
        assert "source: preset:taskstoissues-description" in content

    def test_core_skill_restore_uses_core_command_description(self, project_dir, temp_dir):
        """Core skill restore should keep core command frontmatter descriptions."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-taskstoissues")

        core_cmds = project_dir / ".specify" / "templates" / "commands"
        core_cmds.mkdir(parents=True, exist_ok=True)
        (core_cmds / "taskstoissues.md").write_text(
            "---\n"
            "description: CORE-FRONTMATTER-DESCRIPTION\n"
            "---\n\n"
            "core taskstoissues body\n"
        )
        preset_dir = self._create_command_preset(
            temp_dir,
            "taskstoissues-restore",
            "speckit.taskstoissues",
            "PRESET-FRONTMATTER-DESCRIPTION",
            "preset taskstoissues body\n",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")
        manager.remove("taskstoissues-restore")

        skill_file = skills_dir / "speckit-taskstoissues" / "SKILL.md"
        content = skill_file.read_text()
        assert "description: CORE-FRONTMATTER-DESCRIPTION" in content
        assert "Convert tasks from tasks.md into GitHub issues." not in content
        assert "source: templates/commands/taskstoissues.md" in content
        assert "core taskstoissues body" in content

    def test_override_skill_reconcile_uses_override_command_description(self, project_dir, temp_dir):
        """Override skill reconciliation should keep override frontmatter descriptions."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-taskstoissues")

        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "speckit.taskstoissues.md").write_text(
            "---\n"
            "description: OVERRIDE-FRONTMATTER-DESCRIPTION\n"
            "---\n\n"
            "override taskstoissues body\n"
        )
        preset_dir = self._create_command_preset(
            temp_dir,
            "taskstoissues-reconcile",
            "speckit.taskstoissues",
            "PRESET-FRONTMATTER-DESCRIPTION",
            "preset taskstoissues body\n",
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-taskstoissues" / "SKILL.md"
        content = skill_file.read_text()
        assert "description: OVERRIDE-FRONTMATTER-DESCRIPTION" in content
        assert "Convert tasks from tasks.md into GitHub issues." not in content
        assert "source: override:speckit.taskstoissues" in content
        assert "override taskstoissues body" in content

    def test_skill_not_updated_when_ai_skills_disabled(self, project_dir, temp_dir):
        """When skills mode was NOT used, preset install should not touch skills."""
        self._write_init_options(project_dir, ai="qwen", ai_skills=False)
        skills_dir = project_dir / ".qwen" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)
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
        install_self_test_preset(manager)

        assert (skills_dir / "speckit-specify").is_file()
        metadata = manager.registry.get("self-test")
        assert "speckit-specify" not in metadata.get("registered_skills", [])

    def test_no_skills_registered_when_no_skill_dir_exists(self, project_dir, temp_dir):
        """Skills should not be created when no existing skill dir is found."""
        self._write_init_options(project_dir, ai="claude")
        # Don't create skills dir — simulate skills mode never created them

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

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
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\n"
            "description: Extension fakeext cmd\n"
            "scripts:\n"
            "  sh: ../../scripts/bash/setup-plan.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "extension:fakeext\n"
            "Run {SCRIPT}\n"
            "Read agents/control/commander.md for context.\n"
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
        # Extension-relative subdir references must resolve to their
        # installed location on restore too (#2101), not just on first
        # registration.
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "# Fakeext Cmd Skill" in content

    def test_skill_composed_over_extension_base_rewrites_subdir_paths(
        self, project_dir, temp_dir
    ):
        """When a preset composes (append) over an extension-provided base
        command, the resulting skill (read from the .composed output) must
        still resolve the extension's own subdir references (#2101), not
        just when the extension wins outright (replace)."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="original extension skill")

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Read agents/control/commander.md for context.\n"
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

        preset_dir = temp_dir / "ext-base-append-skill"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Preset overlay\n---\n\n## Extra\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-base-append-skill",
                "name": "Ext Base Append Skill",
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
                        "strategy": "append",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-fakeext-cmd" / "SKILL.md"
        content = skill_file.read_text()
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "## Extra" in content

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
        """Preset overrides should still target legacy dotted-named skill dirs.

        This exercises legacy *naming* (``speckit.specify``) under the current
        ``.kimi-code/`` base — distinct from the legacy ``.kimi/`` *location*.
        """
        self._write_init_options(project_dir, ai="kimi")
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit.specify", body="untouched")

        (project_dir / ".kimi-code" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

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
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        (project_dir / ".kimi-code" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

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
        skills_dir = project_dir / ".kimi-code" / "skills"
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
        skills_dir = project_dir / ".kimi-code" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")
        (project_dir / ".kimi-code" / "commands").mkdir(parents=True, exist_ok=True)

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
        install_self_test_preset(manager)

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

    def test_set_priority_reconciles_generated_constitution(
        self, project_dir, temp_dir
    ):
        """Changing priority rematerializes an unchanged generated constitution."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5", priority=20
        )
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert "preset:self-test" in memory.read_text()

        with patch.object(Path, "cwd", return_value=project_dir):
            result = CliRunner().invoke(
                app,
                ["preset", "set-priority", "convention-constitution", "1"],
            )

        assert result.exit_code == 0, result.output
        assert memory.read_text() == "# Convention Constitution\n"

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

    def test_set_priority_repairs_corrupted_bool(self, project_dir, pack_dir):
        """A corrupted boolean priority must be repaired, not skipped.

        ``isinstance(True, int)`` is True and ``True == 1`` in Python, so a
        stored ``True`` priority would short-circuit the ``already has
        priority 1`` skip path and never get rewritten to a real int —
        contradicting the comment that promises corrupted values are
        repaired. The guard must exclude bools (like normalize_priority).
        """
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5", priority=5)
        # Inject a corrupted boolean priority (True == 1).
        manager.registry.update("test-pack", {"priority": True})

        with patch.object(Path, "cwd", return_value=project_dir):
            result = runner.invoke(app, ["preset", "set-priority", "test-pack", "1"])

        assert result.exit_code == 0, result.output
        plain = strip_ansi(result.output)
        # The corrupted bool must be repaired, not reported as already-set.
        assert "already has priority" not in plain
        assert "priority changed" in plain

        # The stored value is now a real int, not a bool.
        reloaded = PresetManager(project_dir).registry.get("test-pack")
        assert reloaded["priority"] == 1
        assert not isinstance(reloaded["priority"], bool)

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

    def test_enable_disable_reconciles_generated_constitution(
        self, project_dir, temp_dir
    ):
        """Enable and disable rematerialize the winning constitution layer."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)
        manager.install_from_directory(
            _make_convention_constitution_preset(temp_dir), "0.1.5", priority=1
        )
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.read_text() == "# Convention Constitution\n"
        runner = CliRunner()

        with patch.object(Path, "cwd", return_value=project_dir):
            disabled = runner.invoke(
                app, ["preset", "disable", "convention-constitution"]
            )

        assert disabled.exit_code == 0, disabled.output
        assert "preset:self-test" in memory.read_text()

        with patch.object(Path, "cwd", return_value=project_dir):
            enabled = runner.invoke(
                app, ["preset", "enable", "convention-constitution"]
            )

        assert enabled.exit_code == 0, enabled.output
        assert memory.read_text() == "# Convention Constitution\n"

    def test_stack_changes_do_not_create_missing_constitution(
        self, project_dir, pack_dir
    ):
        """Stack changes for non-providers do not seed a missing constitution."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        PresetManager(project_dir).install_from_directory(pack_dir, "0.1.5")
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        runner = CliRunner()

        for args in (
            ["preset", "set-priority", "test-pack", "5"],
            ["preset", "disable", "test-pack"],
            ["preset", "enable", "test-pack"],
        ):
            with patch.object(Path, "cwd", return_value=project_dir):
                result = runner.invoke(app, args)
            assert result.exit_code == 0, result.output
            assert not memory.exists()

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

    def test_preset_add_from_url_rejects_insecure_redirect(self, project_dir, monkeypatch):
        """URL installs reject redirects from HTTPS to non-loopback HTTP."""
        import typer
        from specify_cli.presets._commands import preset_add

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "http://example.com/preset.zip"

        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")
        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            assert redirect_validator is not None
            redirect_validator(url, "http://example.com/preset.zip")
            return FakeResponse(b"zip")

        monkeypatch.setattr("specify_cli.authentication.http.open_url", fake_open_url)

        installed = False

        def fake_install_from_zip(self, zip_path, speckit_version, priority=10):
            nonlocal installed
            installed = True

        monkeypatch.setattr(PresetManager, "install_from_zip", fake_install_from_zip)

        with pytest.raises(typer.Exit) as exc_info:
            preset_add(preset_id=None, from_url="https://example.com/preset.zip", dev=None, priority=10)

        assert exc_info.value.exit_code == 1
        assert installed is False

    def test_preset_add_from_url_rejects_hostless_https_url(self, project_dir):
        """URL installs reject HTTPS URLs without a hostname before downloading."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url") as open_url:
            result = runner.invoke(app, ["preset", "add", "--from", "https:///preset.zip"])

        assert result.exit_code == 1
        output = strip_ansi(result.output)
        assert "URL must use HTTPS with a hostname" in output
        assert "got https://" not in output
        open_url.assert_not_called()

    def test_preset_add_from_malformed_ipv6_url_exits_cleanly(self, project_dir):
        """A malformed IPv6 URL must produce a clean error, not a ValueError traceback."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.authentication.http.open_url") as open_url:
            result = runner.invoke(
                app,
                ["preset", "add", "--from", "https://[::1/preset.zip"],
                catch_exceptions=True,
            )

        assert result.exit_code == 1
        assert result.exception is None or isinstance(result.exception, SystemExit)
        output = strip_ansi(result.output)
        assert "Invalid URL" in output
        open_url.assert_not_called()

    def test_preset_add_from_url_redirect_error_describes_disallowed_url(self, project_dir, monkeypatch, capsys):
        """Redirect rejection message covers hostless HTTPS, not only non-HTTPS URLs."""
        import typer
        from specify_cli.presets._commands import preset_add

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https:///preset.zip"

        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda url, timeout=None, extra_headers=None, redirect_validator=None: FakeResponse(b"zip"),
        )
        monkeypatch.setattr(PresetManager, "install_from_zip", lambda *args, **kwargs: None)

        with pytest.raises(typer.Exit) as exc_info:
            preset_add(preset_id=None, from_url="https://example.com/preset.zip", dev=None, priority=10)

        assert exc_info.value.exit_code == 1
        output = strip_ansi(capsys.readouterr().out)
        assert "redirected to a disallowed URL" in output
        assert "must use HTTPS with a hostname" in output

    def test_preset_add_from_url_streams_download_to_zip(self, project_dir, monkeypatch):
        """URL installs stream response bytes to disk before installing the ZIP."""
        from specify_cli.presets._commands import preset_add

        class FakeResponse(io.BytesIO):
            def __init__(self, data):
                super().__init__(data)
                self.read_sizes = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def geturl(self):
                return "https://example.com/preset.zip"

            def read(self, size=-1):
                assert size not in (-1, None)
                self.read_sizes.append(size)
                return super().read(size)

        response = FakeResponse(b"zip-bytes")
        installed = {}

        def fake_install_from_zip(self, zip_path, speckit_version, priority=10):
            installed["zip_bytes"] = Path(zip_path).read_bytes()
            installed["speckit_version"] = speckit_version
            installed["priority"] = priority
            return SimpleNamespace(name="Test Preset", version="1.0.0")

        monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
        monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")
        monkeypatch.setattr(
            "specify_cli.authentication.http.open_url",
            lambda url, timeout=None, extra_headers=None, redirect_validator=None: response,
        )
        monkeypatch.setattr(PresetManager, "install_from_zip", fake_install_from_zip)

        preset_add(preset_id=None, from_url="https://example.com/preset.zip", dev=None, priority=7)

        assert response.read_sizes
        assert installed == {
            "zip_bytes": b"zip-bytes",
            "speckit_version": "0.6.0",
            "priority": 7,
        }

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


class TestPresetAddFromUrlResolution:
    """CLI-level tests for preset add --from <url> GitHub release resolution."""

    def test_preset_add_from_github_release_url_resolves_and_downloads(self, project_dir):
        """'preset add --from <github-release-url>' resolves to API asset URL."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        manifest_content = yaml.dump({
            "schema_version": "1.0",
            "preset": {"id": "my-preset", "name": "My Preset", "version": "1.0.0", "description": "Test preset", "author": "Test", "license": "MIT"},
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"templates": [{"type": "template", "name": "t", "file": "templates/t.md", "description": "t"}]},
        })
        zip_buf = __import__("io").BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", manifest_content)
        zip_bytes = zip_buf.getvalue()

        captured_urls = []

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return io.BytesIO(json.dumps({
                    "assets": [{"name": "preset.zip", "url": "https://api.github.com/repos/org/repo/releases/assets/42"}]
                }).encode())
            return io.BytesIO(zip_bytes)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.get_speckit_version", return_value="1.0.0"), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "preset", "add",
                "--from", "https://github.com/org/repo/releases/download/v1.0/preset.zip",
            ])

        assert result.exit_code == 0, result.output
        assert "My Preset" in result.output
        # First call should resolve the release tag
        assert any("releases/tags/v1.0" in url for url, _ in captured_urls)
        # Second call should download from the resolved asset URL with octet-stream
        asset_calls = [(url, h) for url, h in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}

    def test_preset_add_from_direct_api_asset_url_passes_through(self, project_dir):
        """'preset add --from <api-asset-url>' uses URL directly with octet-stream."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app

        manifest_content = yaml.dump({
            "schema_version": "1.0",
            "preset": {"id": "my-preset", "name": "My Preset", "version": "1.0.0", "description": "Test preset", "author": "Test", "license": "MIT"},
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"templates": [{"type": "template", "name": "t", "file": "templates/t.md", "description": "t"}]},
        })
        zip_buf = __import__("io").BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", manifest_content)
        zip_bytes = zip_buf.getvalue()

        captured_urls = []

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append((url, extra_headers))
            return io.BytesIO(zip_bytes)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.get_speckit_version", return_value="1.0.0"), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "preset", "add",
                "--from", "https://api.github.com/repos/org/repo/releases/assets/42",
            ])

        assert result.exit_code == 0, result.output
        # Should go directly to the asset URL with Accept header
        assert len(captured_urls) == 1
        assert captured_urls[0][0] == "https://api.github.com/repos/org/repo/releases/assets/42"
        assert captured_urls[0][1] == {"Accept": "application/octet-stream"}

    def test_preset_add_from_ghes_release_url_resolves_via_api_v3(self, project_dir, monkeypatch):
        """'preset add --from <ghes-release-url>' resolves via GHES /api/v3 endpoint."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        from specify_cli.authentication import http as _auth_http
        from specify_cli.authentication.config import AuthConfigEntry

        monkeypatch.setattr(_auth_http, "_config_override", [
            AuthConfigEntry(hosts=("ghes.example",), provider="github", auth="bearer", token="t"),
        ])

        manifest_content = yaml.dump({
            "schema_version": "1.0",
            "preset": {"id": "my-preset", "name": "My Preset", "version": "1.0.0", "description": "Test preset", "author": "Test", "license": "MIT"},
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {"templates": [{"type": "template", "name": "t", "file": "templates/t.md", "description": "t"}]},
        })
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("preset.yml", manifest_content)
        zip_bytes = zip_buf.getvalue()

        captured_urls = []

        def fake_open_url(url, timeout=None, extra_headers=None, redirect_validator=None):
            captured_urls.append((url, extra_headers))
            if "releases/tags/" in url:
                return io.BytesIO(json.dumps({
                    "assets": [{"name": "preset.zip", "url": "https://ghes.example/api/v3/repos/org/repo/releases/assets/42"}]
                }).encode())
            return io.BytesIO(zip_bytes)

        runner = CliRunner()
        with patch.object(Path, "cwd", return_value=project_dir), \
             patch("specify_cli.get_speckit_version", return_value="1.0.0"), \
             patch("specify_cli.authentication.http.open_url", side_effect=fake_open_url):
            result = runner.invoke(app, [
                "preset", "add",
                "--from", "https://ghes.example/org/repo/releases/download/v1.0/preset.zip",
            ])

        assert result.exit_code == 0, result.output
        # The tag-lookup call must use the GHES /api/v3 endpoint
        assert any("ghes.example/api/v3/repos/org/repo/releases/tags/v1.0" in url for url, _ in captured_urls)
        # The asset download call must carry Accept: application/octet-stream
        asset_calls = [(url, h) for url, h in captured_urls if "releases/assets/" in url]
        assert len(asset_calls) >= 1
        assert asset_calls[0][1] == {"Accept": "application/octet-stream"}


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

        # Set up skills dir (simulating --integration claude)
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
        install_self_test_preset(manager)

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
        install_self_test_preset(manager)

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



class TestCompositionStrategyValidation:
    """Test strategy field validation in PresetManifest."""

    def test_valid_replace_strategy(self, temp_dir, valid_pack_data):
        """Test that replace strategy is accepted."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "replace"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "replace"

    def test_valid_prepend_strategy(self, temp_dir, valid_pack_data):
        """Test that prepend strategy is accepted for templates."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "prepend"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "prepend"

    def test_valid_append_strategy(self, temp_dir, valid_pack_data):
        """Test that append strategy is accepted for templates."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "append"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "append"

    def test_valid_wrap_strategy(self, temp_dir, valid_pack_data):
        """Test that wrap strategy is accepted for templates."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "wrap"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (temp_dir / "templates").mkdir(exist_ok=True)
        (temp_dir / "templates" / "spec-template.md").write_text("test")
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "wrap"

    def test_default_strategy_is_replace(self, pack_dir):
        """Test that omitting strategy defaults to replace (key is absent)."""
        manifest = PresetManifest(pack_dir / "preset.yml")
        # Strategy key should not be present in the manifest data
        assert "strategy" not in manifest.templates[0]
        # But consumers should treat missing strategy as "replace"
        assert manifest.templates[0].get("strategy", "replace") == "replace"

    def test_invalid_strategy_rejected(self, temp_dir, valid_pack_data):
        """Test that invalid strategy values are rejected."""
        valid_pack_data["provides"]["templates"][0]["strategy"] = "merge"
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid strategy"):
            PresetManifest(manifest_path)

    def test_prepend_rejected_for_scripts(self, temp_dir, valid_pack_data):
        """Test that prepend strategy is rejected for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "prepend",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid strategy.*for script"):
            PresetManifest(manifest_path)

    def test_append_rejected_for_scripts(self, temp_dir, valid_pack_data):
        """Test that append strategy is rejected for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "append",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(PresetValidationError, match="Invalid strategy.*for script"):
            PresetManifest(manifest_path)

    def test_wrap_accepted_for_scripts(self, temp_dir, valid_pack_data):
        """Test that wrap strategy is accepted for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "wrap",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "wrap"

    def test_replace_accepted_for_scripts(self, temp_dir, valid_pack_data):
        """Test that replace strategy is accepted for scripts."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "script",
            "name": "create-new-feature",
            "file": "scripts/create-new-feature.sh",
            "strategy": "replace",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "replace"

    def test_prepend_accepted_for_commands(self, temp_dir, valid_pack_data):
        """Test that prepend strategy is accepted for commands."""
        valid_pack_data["provides"]["templates"] = [{
            "type": "command",
            "name": "speckit.specify",
            "file": "commands/speckit.specify.md",
            "strategy": "prepend",
        }]
        manifest_path = temp_dir / "preset.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = PresetManifest(manifest_path)
        assert manifest.templates[0]["strategy"] == "prepend"


class TestResolveContent:
    """Test PresetResolver.resolve_content() composition."""

    def test_resolve_content_core_template(self, project_dir):
        """Test resolve_content returns core template when no composition."""
        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Core Spec Template" in content

    def test_resolve_content_nonexistent(self, project_dir):
        """Test resolve_content returns None for nonexistent template."""
        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("nonexistent")
        assert content is None

    def test_resolve_content_replace_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with default replace strategy."""
        manager = PresetManager(project_dir)
        manager.install_from_directory(
            _create_pack(temp_dir, valid_pack_data, "replace-pack",
                         "# Replaced Content\n"),
            "0.1.5"
        )

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Replaced Content" in content
        assert "Core Spec Template" not in content

    def test_resolve_content_append_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with append strategy."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "append-pack", "name": "Append"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "append-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Appended Section\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Core Spec Template" in content
        assert "Appended Section" in content
        # Core should come first, appended after
        assert content.index("Core Spec Template") < content.index("Appended Section")

    def test_resolve_content_prepend_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with prepend strategy."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "prepend-pack", "name": "Prepend"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "prepend",
            }]
        }
        pack_dir = temp_dir / "prepend-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Security Header\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Security Header" in content
        assert "Core Spec Template" in content
        # Prepended content should come first
        assert content.index("Security Header") < content.index("Core Spec Template")

    def test_resolve_content_wrap_strategy(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with wrap strategy for templates."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "wrap-pack", "name": "Wrap"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "wrap",
            }]
        }
        pack_dir = temp_dir / "wrap-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text(
            "# Wrapper Start\n\n{CORE_TEMPLATE}\n\n# Wrapper End\n"
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Wrapper Start" in content
        assert "Core Spec Template" in content
        assert "Wrapper End" in content
        # Wrapper should surround core
        assert content.index("Wrapper Start") < content.index("Core Spec Template")
        assert content.index("Core Spec Template") < content.index("Wrapper End")

    def test_resolve_content_wrap_strategy_script(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with wrap strategy for scripts uses $CORE_SCRIPT."""
        # Create core script
        scripts_dir = project_dir / ".specify" / "templates" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (scripts_dir / "test-script.sh").write_text("echo 'core script'\n")

        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "script-wrap", "name": "Script Wrap"}
        pack_data["provides"] = {
            "templates": [{
                "type": "script",
                "name": "test-script",
                "file": "scripts/test-script.sh",
                "strategy": "wrap",
            }]
        }
        pack_dir = temp_dir / "script-wrap"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "scripts").mkdir()
        (pack_dir / "scripts" / "test-script.sh").write_text(
            "#!/bin/bash\necho 'before'\n$CORE_SCRIPT\necho 'after'\n"
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("test-script", "script")
        assert content is not None
        assert "echo 'before'" in content
        assert "echo 'core script'" in content
        assert "echo 'after'" in content

    def test_resolve_content_multi_preset_chain(self, project_dir, temp_dir, valid_pack_data):
        """Test multi-preset composition chain: prepend + append stacking."""
        # Create preset A (priority 1): prepend security header
        pack_a_data = {**valid_pack_data}
        pack_a_data["preset"] = {**valid_pack_data["preset"], "id": "preset-a", "name": "A"}
        pack_a_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "prepend",
            }]
        }
        pack_a_dir = temp_dir / "preset-a"
        pack_a_dir.mkdir()
        with open(pack_a_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_a_data, f)
        (pack_a_dir / "templates").mkdir()
        (pack_a_dir / "templates" / "spec-template.md").write_text("## Security Header\n")

        # Create preset B (priority 2): append compliance footer
        pack_b_data = {**valid_pack_data}
        pack_b_data["preset"] = {**valid_pack_data["preset"], "id": "preset-b", "name": "B"}
        pack_b_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_b_dir = temp_dir / "preset-b"
        pack_b_dir.mkdir()
        with open(pack_b_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_b_data, f)
        (pack_b_dir / "templates").mkdir()
        (pack_b_dir / "templates" / "spec-template.md").write_text("## Compliance Footer\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_a_dir, "0.1.5", priority=1)
        manager.install_from_directory(pack_b_dir, "0.1.5", priority=2)

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        # Result: <security header> + <core> + <compliance footer>
        assert "Security Header" in content
        assert "Core Spec Template" in content
        assert "Compliance Footer" in content
        assert content.index("Security Header") < content.index("Core Spec Template")
        assert content.index("Core Spec Template") < content.index("Compliance Footer")

    def test_resolve_content_override_trumps_composition(self, project_dir, temp_dir, valid_pack_data):
        """Test that project overrides trump composition (replace at top priority)."""
        # Install a composing preset
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "append-pack", "name": "Append"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "append-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Appended\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Create project override (replaces everything)
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        (overrides_dir / "spec-template.md").write_text("# Override Only\n")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content is not None
        assert "Override Only" in content
        # Override replaces, so appended content should not be visible
        assert "Core Spec Template" not in content

    def test_resolve_content_command_type(self, project_dir, temp_dir, valid_pack_data):
        """Test resolve_content with command template type."""
        # Create core command using stem naming (matches real layout: plan.md, not speckit.plan.md)
        commands_dir = project_dir / ".specify" / "templates" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "plan.md").write_text("# Core Plan Command\n")

        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "cmd-append", "name": "CmdAppend"}
        pack_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.plan",
                "file": "commands/speckit.plan.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "cmd-append"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "commands").mkdir()
        (pack_dir / "commands" / "speckit.plan.md").write_text("## Additional Instructions\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.plan", "command")
        assert content is not None
        assert "Core Plan Command" in content
        assert "Additional Instructions" in content

    def test_resolve_content_command_frontmatter_stripping(self, project_dir, temp_dir, valid_pack_data):
        """Test that command composition strips frontmatter from lower layers
        and reattaches only the highest-priority frontmatter."""
        # Create core command with frontmatter
        commands_dir = project_dir / ".specify" / "templates" / "commands"
        commands_dir.mkdir(parents=True, exist_ok=True)
        (commands_dir / "check.md").write_text(
            "---\ndescription: Core check command\n---\nCore body content\n"
        )

        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "fm-test", "name": "FmTest"}
        pack_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.check",
                "file": "commands/speckit.check.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "fm-test"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "commands").mkdir()
        (pack_dir / "commands" / "speckit.check.md").write_text(
            "---\ndescription: Preset check override\n---\nPreset body content\n"
        )

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.check", "command")
        assert content is not None
        # Should have the preset (highest-priority) frontmatter
        assert "Preset check override" in content
        # Should have both bodies
        assert "Core body content" in content
        assert "Preset body content" in content
        # Core frontmatter should NOT appear in the body
        assert content.count("---") == 2  # only one frontmatter block (opening + closing)

    def test_resolve_content_blank_line_separator(self, project_dir, temp_dir, valid_pack_data):
        """Test that prepend/append use blank line separator."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "sep-test", "name": "SepTest"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "sep-test"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("appended")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        # Should have blank line separator
        assert "\n\n" in content

    def test_resolve_content_replace_over_wrap(self, project_dir, temp_dir, valid_pack_data):
        """Top-priority replace layer should win even if a lower layer uses wrap."""
        # Install a low-priority wrap preset (with no placeholder — would fail if evaluated)
        wrap_data = {**valid_pack_data}
        wrap_data["preset"] = {**valid_pack_data["preset"], "id": "wrap-lo", "name": "WrapLo"}
        wrap_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "wrap",
            }]
        }
        wrap_dir = temp_dir / "wrap-lo"
        wrap_dir.mkdir()
        with open(wrap_dir / "preset.yml", "w") as f:
            yaml.dump(wrap_data, f)
        (wrap_dir / "templates").mkdir()
        # Intentionally missing {CORE_TEMPLATE} — would error if composition ran
        (wrap_dir / "templates" / "spec-template.md").write_text("wrapper without placeholder")

        manager = PresetManager(project_dir)
        manager.install_from_directory(wrap_dir, "0.1.5", priority=10)

        # Install a high-priority replace preset
        rep_data = {**valid_pack_data}
        rep_data["preset"] = {**valid_pack_data["preset"], "id": "rep-hi", "name": "RepHi"}
        rep_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
            }]
        }
        rep_dir = temp_dir / "rep-hi"
        rep_dir.mkdir()
        with open(rep_dir / "preset.yml", "w") as f:
            yaml.dump(rep_data, f)
        (rep_dir / "templates").mkdir()
        (rep_dir / "templates" / "spec-template.md").write_text("# Replaced content\n")

        manager.install_from_directory(rep_dir, "0.1.5", priority=1)

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("spec-template")
        assert content == "# Replaced content\n"

    @pytest.mark.parametrize("strategy", ["append", "prepend", "wrap"])
    def test_resolve_content_rewrites_extension_base_subdir_paths(
        self, project_dir, temp_dir, strategy
    ):
        """Composing over an extension-provided base command must resolve the
        extension's own subdir references (agents/, knowledge-base/) to their
        installed location (#2101), not just when the extension wins outright.
        """
        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Read agents/control/commander.md for context.\n"
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

        preset_dir = temp_dir / f"ext-base-{strategy}"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        overlay_body = (
            "{CORE_TEMPLATE}\n## Extra\n" if strategy == "wrap" else "## Extra\n"
        )
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            f"---\ndescription: Preset overlay\n---\n\n{overlay_body}"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": f"ext-base-{strategy}",
                "name": "Ext Base",
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
                        "strategy": strategy,
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        content = resolver.resolve_content("speckit.fakeext.cmd", "command")
        assert content is not None
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "## Extra" in content


class TestCollectAllLayers:
    """Test PresetResolver.collect_all_layers() method."""

    def test_single_core_layer(self, project_dir):
        """Test collecting layers with only core template."""
        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        assert len(layers) == 1
        assert layers[0]["source"] == "core"
        assert layers[0]["strategy"] == "replace"

    def test_layers_include_presets(self, project_dir, temp_dir, valid_pack_data):
        """Test that layers include installed preset."""
        manager = PresetManager(project_dir)
        pack_dir = _create_pack(temp_dir, valid_pack_data, "test-pack",
                                "# From Pack\n")
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        assert len(layers) == 2
        # Highest priority first
        assert "test-pack" in layers[0]["source"]
        assert layers[1]["source"] == "core"

    def test_layers_order_matches_priority(self, project_dir, temp_dir, valid_pack_data):
        """Test that layers are ordered by priority (highest first)."""
        manager = PresetManager(project_dir)
        for pid, prio in [("pack-lo", 10), ("pack-hi", 1)]:
            d = {**valid_pack_data}
            d["preset"] = {**valid_pack_data["preset"], "id": pid, "name": pid}
            p = temp_dir / pid
            p.mkdir()
            with open(p / "preset.yml", 'w') as f:
                yaml.dump(d, f)
            (p / "templates").mkdir()
            (p / "templates" / "spec-template.md").write_text(f"# {pid}\n")
            manager.install_from_directory(p, "0.1.5", priority=prio)

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        assert len(layers) == 3  # pack-hi, pack-lo, core
        assert "pack-hi" in layers[0]["source"]
        assert "pack-lo" in layers[1]["source"]
        assert layers[2]["source"] == "core"

    def test_layers_read_strategy_from_manifest(self, project_dir, temp_dir, valid_pack_data):
        """Test that layers read strategy from preset manifest."""
        pack_data = {**valid_pack_data}
        pack_data["preset"] = {**valid_pack_data["preset"], "id": "strat-pack", "name": "Strat"}
        pack_data["provides"] = {
            "templates": [{
                "type": "template",
                "name": "spec-template",
                "file": "templates/spec-template.md",
                "strategy": "append",
            }]
        }
        pack_dir = temp_dir / "strat-pack"
        pack_dir.mkdir()
        with open(pack_dir / "preset.yml", 'w') as f:
            yaml.dump(pack_data, f)
        (pack_dir / "templates").mkdir()
        (pack_dir / "templates" / "spec-template.md").write_text("## Footer\n")

        manager = PresetManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("spec-template")
        # Preset layer should have strategy=append
        assert layers[0]["strategy"] == "append"
        # Core layer should be replace
        assert layers[1]["strategy"] == "replace"


class TestRemoveReconciliation:
    """Test that removing a preset re-registers the next layer's command."""

    def test_remove_restores_extension_command_subdir_paths_for_non_skill_agent(
        self, project_dir, temp_dir
    ):
        """When a preset override of an extension command is removed, the
        reconciled non-skill-agent command file should have the extension's
        own subdir references rewritten to their installed location (#2101),
        not left as bare, unresolvable paths."""
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Read agents/control/commander.md for context.\n"
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

        manager = PresetManager(project_dir)

        preset_dir = temp_dir / "ext-cmd-override"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset override content\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-cmd-override",
                "name": "Ext Cmd Override",
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

        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_files = list(gemini_dir.glob("*fakeext*"))
        assert cmd_files, "Command file should exist in gemini dir"
        assert "preset override content" in cmd_files[0].read_text()

        manager.remove("ext-cmd-override")

        cmd_files = list(gemini_dir.glob("*fakeext*"))
        assert cmd_files, "Command file should still exist after removal"
        content = cmd_files[0].read_text()
        assert "preset override content" not in content
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content

    def test_install_composes_extension_command_and_rewrites_subdir_paths_for_non_skill_agent(
        self, project_dir, temp_dir
    ):
        """When a preset overlays (append) an extension-provided base command,
        the initial composed non-skill-agent command file must have the
        extension's own subdir references rewritten to their installed
        location (#2101), matching the live repro: extension body
        'Read agents/control/commander.md', preset appends to
        speckit.fakeext.cmd, generated Gemini content retains the bare path."""
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control").mkdir(parents=True, exist_ok=True)
        (extension_dir / "agents" / "control" / "commander.md").write_text("# Commander\n")
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\ndescription: Extension fakeext cmd\n---\n\n"
            "Read agents/control/commander.md for context.\n"
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

        preset_dir = temp_dir / "ext-cmd-append"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Append fakeext cmd\n---\n\n## Extra\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-cmd-append",
                "name": "Ext Cmd Append",
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
                        "strategy": "append",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        cmd_files = list(gemini_dir.glob("*fakeext*"))
        assert cmd_files, "Command file should exist in gemini dir"
        content = cmd_files[0].read_text()
        assert ".specify/extensions/fakeext/agents/control/commander.md" in content
        assert "Read agents/control" not in content
        assert "## Extra" in content

    def test_remove_restores_lower_priority_command(
        self, project_dir, temp_dir, valid_pack_data
    ):
        """After removing the top-priority preset, the next preset's command
        should be re-registered in agent directories."""
        manager = PresetManager(project_dir)

        # Create a gemini commands dir so reconciliation writes there
        gemini_dir = project_dir / ".gemini" / "commands"
        gemini_dir.mkdir(parents=True)

        # Install a low-priority preset with a command
        lo_data = {**valid_pack_data}
        lo_data["preset"] = {
            **valid_pack_data["preset"],
            "id": "lo-preset",
            "name": "Lo",
        }
        lo_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.specify",
                "file": "commands/speckit.specify.md",
            }]
        }
        lo_dir = temp_dir / "lo-preset"
        lo_dir.mkdir()
        with open(lo_dir / "preset.yml", "w") as f:
            yaml.dump(lo_data, f)
        (lo_dir / "commands").mkdir()
        (lo_dir / "commands" / "speckit.specify.md").write_text(
            "---\ndescription: lo\n---\nLo content\n"
        )
        manager.install_from_directory(lo_dir, "0.1.5", priority=10)

        # Install a high-priority preset overriding the same command
        hi_data = {**valid_pack_data}
        hi_data["preset"] = {
            **valid_pack_data["preset"],
            "id": "hi-preset",
            "name": "Hi",
        }
        hi_data["provides"] = {
            "templates": [{
                "type": "command",
                "name": "speckit.specify",
                "file": "commands/speckit.specify.md",
            }]
        }
        hi_dir = temp_dir / "hi-preset"
        hi_dir.mkdir()
        with open(hi_dir / "preset.yml", "w") as f:
            yaml.dump(hi_data, f)
        (hi_dir / "commands").mkdir()
        (hi_dir / "commands" / "speckit.specify.md").write_text(
            "---\ndescription: hi\n---\nHi content\n"
        )
        manager.install_from_directory(hi_dir, "0.1.5", priority=1)

        # Verify the hi-preset's content is active in agent dir
        cmd_files = list(gemini_dir.glob("*specify*"))
        assert cmd_files, "Command file should exist in gemini dir"
        assert "Hi content" in cmd_files[0].read_text()

        # Remove the high-priority preset
        manager.remove("hi-preset")

        # The low-priority preset's command should now be in the resolution stack
        resolver = PresetResolver(project_dir)
        layers = resolver.collect_all_layers("speckit.specify", "command")
        assert len(layers) >= 1
        assert "lo-preset" in layers[0]["source"]

        # Verify on-disk agent command file switched to lo-preset content
        cmd_files = list(gemini_dir.glob("*specify*"))
        assert cmd_files, "Command file should still exist after removal"
        assert "Lo content" in cmd_files[0].read_text()


def _create_pack(temp_dir, valid_pack_data, pack_id, content,
                 strategy="replace", template_type="template",
                 template_name="spec-template"):
    """Helper to create a preset pack directory."""
    pack_data = {**valid_pack_data}
    pack_data["preset"] = {**valid_pack_data["preset"], "id": pack_id, "name": pack_id}

    tmpl_entry = {
        "type": template_type,
        "name": template_name,
    }
    if template_type == "script":
        tmpl_entry["file"] = f"scripts/{template_name}.sh"
    elif template_type == "command":
        tmpl_entry["file"] = f"commands/{template_name}.md"
    else:
        tmpl_entry["file"] = f"templates/{template_name}.md"
    if strategy != "replace":
        tmpl_entry["strategy"] = strategy
    pack_data["provides"] = {"templates": [tmpl_entry]}

    pack_dir = temp_dir / pack_id
    pack_dir.mkdir(exist_ok=True)
    with open(pack_dir / "preset.yml", 'w') as f:
        yaml.dump(pack_data, f)

    if template_type == "script":
        subdir = pack_dir / "scripts"
        subdir.mkdir(exist_ok=True)
        (subdir / f"{template_name}.sh").write_text(content)
    elif template_type == "command":
        subdir = pack_dir / "commands"
        subdir.mkdir(exist_ok=True)
        (subdir / f"{template_name}.md").write_text(content)
    else:
        subdir = pack_dir / "templates"
        subdir.mkdir(exist_ok=True)
        (subdir / f"{template_name}.md").write_text(content)

    return pack_dir


def test_preset_wrapper_resolves_ghes_asset_when_host_configured(tmp_path, monkeypatch):
    """End-to-end wiring for presets: auth.json github host → GHES asset resolution."""
    from specify_cli.authentication import http as _auth_http
    from specify_cli.authentication.config import AuthConfigEntry
    from specify_cli.presets import PresetCatalog

    monkeypatch.setattr(_auth_http, "_config_override", [
        AuthConfigEntry(hosts=("ghes.example",), provider="github",
                        auth="bearer", token="t"),
    ])
    catalog = PresetCatalog(tmp_path)

    captured = []

    @contextmanager
    def fake_open(url, timeout=None, extra_headers=None):
        captured.append(url)
        resp = MagicMock()
        resp.read.return_value = json.dumps({
            "assets": [{"name": "pack.zip",
                        "url": "https://ghes.example/api/v3/repos/o/r/releases/assets/9"}]
        }).encode()
        yield resp

    monkeypatch.setattr(catalog, "_open_url", fake_open)

    resolved = catalog._resolve_github_release_asset_api_url(
        "https://ghes.example/o/r/releases/download/v2/pack.zip"
    )
    assert resolved == "https://ghes.example/api/v3/repos/o/r/releases/assets/9"
    assert captured == ["https://ghes.example/api/v3/repos/o/r/releases/tags/v2"]


# ===== ensure_constitution_from_template resolver-awareness =====


class TestEnsureConstitutionResolverAware:
    """`ensure_constitution_from_template` must resolve through PresetResolver.

    The constitution is the only template materialized to a live file rather
    than resolved on demand. These tests pin the regression from issue #3272:
    a preset-provided ``constitution-template`` must seed memory, while the
    core template is used when no preset overrides it.
    """

    def _core_constitution(self, project_dir):
        templates_dir = project_dir / ".specify" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        (templates_dir / "constitution-template.md").write_text(
            "# [PROJECT_NAME] Constitution\n\n### [PRINCIPLE_1_NAME]\n"
        )

    def _wrap_constitution_preset(self, temp_dir):
        preset_dir = temp_dir / "ensure-wrap-preset"
        (preset_dir / "templates").mkdir(parents=True)
        (preset_dir / "templates" / "constitution-template.md").write_text(
            "# Ensure Wrapper\n\n{CORE_TEMPLATE}\n\n## Tail\n"
        )
        (preset_dir / "preset.yml").write_text(
            yaml.dump(
                {
                    "schema_version": "1.0",
                    "preset": {
                        "id": "ensure-wrap",
                        "name": "Ensure Wrap",
                        "version": "1.0.0",
                        "description": "Wrap strategy for ensure() coverage",
                    },
                    "requires": {"speckit_version": ">=0.1.0"},
                    "provides": {
                        "templates": [
                            {
                                "type": "template",
                                "name": "constitution-template",
                                "file": "templates/constitution-template.md",
                                "strategy": "wrap",
                                "description": "Wrapped constitution",
                            }
                        ]
                    },
                }
            )
        )
        return preset_dir

    def test_seeds_from_core_when_no_preset(self, project_dir):
        from specify_cli.commands.init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        ensure_constitution_from_template(project_dir)

        memory = project_dir / ".specify" / "memory" / "constitution.md"
        assert memory.exists()
        assert "[PROJECT_NAME]" in memory.read_text()
        assert (memory.parent / ".constitution-template.json").exists()

    def test_seeds_from_preset_when_installed(self, project_dir):
        from specify_cli.commands.init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        # Remove the memory file seeded during install to test ensure() in
        # isolation; it must re-seed from the preset, not the core template.
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.unlink()

        ensure_constitution_from_template(project_dir)

        assert memory.exists()
        content = memory.read_text()
        assert "preset:self-test" in content
        assert "[PROJECT_NAME]" not in content

    def test_preserves_existing_memory(self, project_dir):
        from specify_cli.commands.init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.parent.mkdir(parents=True, exist_ok=True)
        authored = "# Acme Constitution\nAuthored.\n"
        memory.write_text(authored)

        ensure_constitution_from_template(project_dir)

        assert memory.read_text() == authored

    def test_preserves_edited_generated_memory(self, project_dir):
        from specify_cli.commands.init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        ensure_constitution_from_template(project_dir)
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        authored = memory.read_text() + "\nAuthored amendment.\n"
        memory.write_text(authored)

        manager = PresetManager(project_dir)
        install_self_test_preset(manager)

        assert memory.read_text() == authored

    def test_composes_wrap_strategy_when_ensuring(self, project_dir, temp_dir):
        from specify_cli.commands.init import ensure_constitution_from_template

        self._core_constitution(project_dir)
        manager = PresetManager(project_dir)
        manager.install_from_directory(self._wrap_constitution_preset(temp_dir), "0.1.5")

        # Ensure we validate ensure() behavior directly.
        memory = project_dir / ".specify" / "memory" / "constitution.md"
        memory.unlink()
        ensure_constitution_from_template(project_dir)

        content = memory.read_text()
        assert "{CORE_TEMPLATE}" not in content
        assert "# Ensure Wrapper" in content
        assert "[PROJECT_NAME]" in content
