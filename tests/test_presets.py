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

        resolver = PresetResolver(project_dir)
        result = resolver.resolve("custom-template")
        assert result is not None
        assert "Extension Custom Template" in result.read_text()

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

        resolver = PresetResolver(project_dir)
        result = resolver.resolve_with_source("unique-template")
        assert result is not None
        assert result["source"] == "extension:my-ext"

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

    def test_search_with_cached_data(self, project_dir):
        """Test search with cached catalog data."""
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

        result = resolver.resolve_with_source("spec-template")
        assert result["source"] == "extension:my-ext"

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
    "agent-file-template",
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
        assert len(manifest.templates) == 7  # 6 templates + 1 command

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
        """Test that installing self-test registers commands in .claude/commands/."""
        # Create Claude agent directory to simulate Claude being set up
        claude_dir = project_dir / ".claude" / "commands"
        claude_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        # Check the command was registered
        cmd_file = claude_dir / "speckit.specify.md"
        assert cmd_file.exists(), "Command not registered in .claude/commands/"
        content = cmd_file.read_text()
        assert "preset:self-test" in content

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
        claude_dir = project_dir / ".claude" / "commands"
        claude_dir.mkdir(parents=True)

        manager = PresetManager(project_dir)
        manager.install_from_directory(SELF_TEST_PRESET_DIR, "0.1.5")

        cmd_file = claude_dir / "speckit.specify.md"
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
        claude_dir = project_dir / ".claude" / "commands"
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
        claude_dir = project_dir / ".claude" / "commands"
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

        cmd_file = claude_dir / "speckit.fakeext.cmd.md"
        assert cmd_file.exists(), "Command not registered despite extension being present"


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

    def _write_init_options(self, project_dir, ai="claude", ai_skills=True):
        from specify_cli import save_init_options

        save_init_options(project_dir, {"ai": ai, "ai_skills": ai_skills})

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
        (project_dir / ".claude" / "commands").mkdir(parents=True, exist_ok=True)

        # Install self-test preset (has a command override for speckit.specify)
        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:self-test" in content, "Skill should reference preset source"

        # Verify it was recorded in registry
        metadata = manager.registry.get("self-test")
        assert "speckit-specify" in metadata.get("registered_skills", [])

    def test_skill_not_updated_when_ai_skills_disabled(self, project_dir, temp_dir):
        """When --ai-skills was NOT used, preset install should not touch skills."""
        self._write_init_options(project_dir, ai="claude", ai_skills=False)
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        (project_dir / ".claude" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()
        assert "untouched" in content, "Skill should not be modified when ai_skills=False"

    def test_skill_not_updated_without_init_options(self, project_dir, temp_dir):
        """When no init-options.json exists, preset install should not touch skills."""
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify", body="untouched")

        (project_dir / ".claude" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        skill_file = skills_dir / "speckit-specify" / "SKILL.md"
        content = skill_file.read_text()
        assert "untouched" in content

    def test_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """When a preset is removed, skills should be restored from core templates."""
        self._write_init_options(project_dir, ai="claude")
        skills_dir = project_dir / ".claude" / "skills"
        self._create_skill(skills_dir, "speckit-specify")

        (project_dir / ".claude" / "commands").mkdir(parents=True, exist_ok=True)

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

    def test_no_skills_registered_when_no_skill_dir_exists(self, project_dir, temp_dir):
        """Skills should not be created when no existing skill dir is found."""
        self._write_init_options(project_dir, ai="claude")
        # Don't create skills dir — simulate --ai-skills never created them

        (project_dir / ".claude" / "commands").mkdir(parents=True, exist_ok=True)

        manager = PresetManager(project_dir)
        SELF_TEST_DIR = Path(__file__).parent.parent / "presets" / "self-test"
        manager.install_from_directory(SELF_TEST_DIR, "0.1.5")

        metadata = manager.registry.get("self-test")
        assert metadata.get("registered_skills", []) == []
