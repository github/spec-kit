"""
Unit tests for the template pack system.

Tests cover:
- Template pack manifest validation
- Template pack registry operations
- Template pack manager installation/removal
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

from specify_cli.templates import (
    TemplatePackManifest,
    TemplatePackRegistry,
    TemplatePackManager,
    TemplateCatalog,
    TemplateResolver,
    TemplateError,
    TemplateValidationError,
    TemplateCompatibilityError,
    VALID_TEMPLATE_TYPES,
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
    """Valid template pack manifest data."""
    return {
        "schema_version": "1.0",
        "template_pack": {
            "id": "test-pack",
            "name": "Test Template Pack",
            "version": "1.0.0",
            "description": "A test template pack",
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
                    "type": "artifact",
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
    """Create a complete template pack directory structure."""
    p_dir = temp_dir / "test-pack"
    p_dir.mkdir()

    # Write manifest
    manifest_path = p_dir / "template-pack.yml"
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


# ===== TemplatePackManifest Tests =====


class TestTemplatePackManifest:
    """Test TemplatePackManifest validation and parsing."""

    def test_valid_manifest(self, pack_dir):
        """Test loading a valid manifest."""
        manifest = TemplatePackManifest(pack_dir / "template-pack.yml")
        assert manifest.id == "test-pack"
        assert manifest.name == "Test Template Pack"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test template pack"
        assert manifest.author == "Test Author"
        assert manifest.requires_speckit_version == ">=0.1.0"
        assert len(manifest.templates) == 1
        assert manifest.tags == ["testing", "example"]

    def test_missing_manifest(self, temp_dir):
        """Test that missing manifest raises error."""
        with pytest.raises(TemplateValidationError, match="Manifest not found"):
            TemplatePackManifest(temp_dir / "nonexistent.yml")

    def test_invalid_yaml(self, temp_dir):
        """Test that invalid YAML raises error."""
        bad_file = temp_dir / "bad.yml"
        bad_file.write_text(": invalid: yaml: {{{")
        with pytest.raises(TemplateValidationError, match="Invalid YAML"):
            TemplatePackManifest(bad_file)

    def test_missing_schema_version(self, temp_dir, valid_pack_data):
        """Test missing schema_version field."""
        del valid_pack_data["schema_version"]
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Missing required field: schema_version"):
            TemplatePackManifest(manifest_path)

    def test_wrong_schema_version(self, temp_dir, valid_pack_data):
        """Test unsupported schema version."""
        valid_pack_data["schema_version"] = "2.0"
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Unsupported schema version"):
            TemplatePackManifest(manifest_path)

    def test_missing_pack_id(self, temp_dir, valid_pack_data):
        """Test missing template_pack.id field."""
        del valid_pack_data["template_pack"]["id"]
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Missing template_pack.id"):
            TemplatePackManifest(manifest_path)

    def test_invalid_pack_id_format(self, temp_dir, valid_pack_data):
        """Test invalid pack ID format."""
        valid_pack_data["template_pack"]["id"] = "Invalid_ID"
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Invalid template pack ID"):
            TemplatePackManifest(manifest_path)

    def test_invalid_version(self, temp_dir, valid_pack_data):
        """Test invalid semantic version."""
        valid_pack_data["template_pack"]["version"] = "not-a-version"
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Invalid version"):
            TemplatePackManifest(manifest_path)

    def test_missing_speckit_version(self, temp_dir, valid_pack_data):
        """Test missing requires.speckit_version."""
        del valid_pack_data["requires"]["speckit_version"]
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Missing requires.speckit_version"):
            TemplatePackManifest(manifest_path)

    def test_no_templates_provided(self, temp_dir, valid_pack_data):
        """Test pack with no templates."""
        valid_pack_data["provides"]["templates"] = []
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="must provide at least one template"):
            TemplatePackManifest(manifest_path)

    def test_invalid_template_type(self, temp_dir, valid_pack_data):
        """Test template with invalid type."""
        valid_pack_data["provides"]["templates"][0]["type"] = "invalid"
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Invalid template type"):
            TemplatePackManifest(manifest_path)

    def test_valid_template_types(self):
        """Test that all expected template types are valid."""
        assert "artifact" in VALID_TEMPLATE_TYPES
        assert "command" in VALID_TEMPLATE_TYPES
        assert "script" in VALID_TEMPLATE_TYPES

    def test_template_missing_required_fields(self, temp_dir, valid_pack_data):
        """Test template missing required fields."""
        valid_pack_data["provides"]["templates"] = [{"type": "artifact"}]
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="missing 'type', 'name', or 'file'"):
            TemplatePackManifest(manifest_path)

    def test_invalid_template_name_format(self, temp_dir, valid_pack_data):
        """Test template with invalid name format."""
        valid_pack_data["provides"]["templates"][0]["name"] = "Invalid Name"
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        with pytest.raises(TemplateValidationError, match="Invalid template name"):
            TemplatePackManifest(manifest_path)

    def test_get_hash(self, pack_dir):
        """Test manifest hash calculation."""
        manifest = TemplatePackManifest(pack_dir / "template-pack.yml")
        hash_val = manifest.get_hash()
        assert hash_val.startswith("sha256:")
        assert len(hash_val) > 10

    def test_multiple_templates(self, temp_dir, valid_pack_data):
        """Test pack with multiple templates of different types."""
        valid_pack_data["provides"]["templates"] = [
            {"type": "artifact", "name": "spec-template", "file": "templates/spec-template.md"},
            {"type": "artifact", "name": "plan-template", "file": "templates/plan-template.md"},
            {"type": "command", "name": "specify", "file": "commands/specify.md"},
            {"type": "script", "name": "create-new-feature", "file": "scripts/create-new-feature.sh"},
        ]
        manifest_path = temp_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        manifest = TemplatePackManifest(manifest_path)
        assert len(manifest.templates) == 4


# ===== TemplatePackRegistry Tests =====


class TestTemplatePackRegistry:
    """Test TemplatePackRegistry operations."""

    def test_empty_registry(self, temp_dir):
        """Test empty registry initialization."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = TemplatePackRegistry(packs_dir)
        assert registry.list() == {}
        assert not registry.is_installed("test-pack")

    def test_add_and_get(self, temp_dir):
        """Test adding and retrieving a pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = TemplatePackRegistry(packs_dir)

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
        registry = TemplatePackRegistry(packs_dir)

        registry.add("test-pack", {"version": "1.0.0"})
        assert registry.is_installed("test-pack")

        registry.remove("test-pack")
        assert not registry.is_installed("test-pack")

    def test_remove_nonexistent(self, temp_dir):
        """Test removing a pack that doesn't exist."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = TemplatePackRegistry(packs_dir)
        registry.remove("nonexistent")  # Should not raise

    def test_list(self, temp_dir):
        """Test listing all packs."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = TemplatePackRegistry(packs_dir)

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
        registry1 = TemplatePackRegistry(packs_dir)
        registry1.add("test-pack", {"version": "1.0.0"})

        # Load with second instance
        registry2 = TemplatePackRegistry(packs_dir)
        assert registry2.is_installed("test-pack")

    def test_corrupted_registry(self, temp_dir):
        """Test recovery from corrupted registry file."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()

        registry_file = packs_dir / ".registry"
        registry_file.write_text("not valid json{{{")

        registry = TemplatePackRegistry(packs_dir)
        assert registry.list() == {}

    def test_get_nonexistent(self, temp_dir):
        """Test getting a nonexistent pack."""
        packs_dir = temp_dir / "packs"
        packs_dir.mkdir()
        registry = TemplatePackRegistry(packs_dir)
        assert registry.get("nonexistent") is None


# ===== TemplatePackManager Tests =====


class TestTemplatePackManager:
    """Test TemplatePackManager installation and removal."""

    def test_install_from_directory(self, project_dir, pack_dir):
        """Test installing a template pack from a directory."""
        manager = TemplatePackManager(project_dir)
        manifest = manager.install_from_directory(pack_dir, "0.1.5")

        assert manifest.id == "test-pack"
        assert manager.registry.is_installed("test-pack")

        # Verify files are copied
        installed_dir = project_dir / ".specify" / "templates" / "packs" / "test-pack"
        assert installed_dir.exists()
        assert (installed_dir / "template-pack.yml").exists()
        assert (installed_dir / "templates" / "spec-template.md").exists()

    def test_install_already_installed(self, project_dir, pack_dir):
        """Test installing an already-installed pack raises error."""
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        with pytest.raises(TemplateError, match="already installed"):
            manager.install_from_directory(pack_dir, "0.1.5")

    def test_install_incompatible(self, project_dir, temp_dir, valid_pack_data):
        """Test installing an incompatible pack raises error."""
        valid_pack_data["requires"]["speckit_version"] = ">=99.0.0"
        incompat_dir = temp_dir / "incompat-pack"
        incompat_dir.mkdir()
        manifest_path = incompat_dir / "template-pack.yml"
        with open(manifest_path, 'w') as f:
            yaml.dump(valid_pack_data, f)
        (incompat_dir / "templates").mkdir()
        (incompat_dir / "templates" / "spec-template.md").write_text("test")

        manager = TemplatePackManager(project_dir)
        with pytest.raises(TemplateCompatibilityError):
            manager.install_from_directory(incompat_dir, "0.1.5")

    def test_install_from_zip(self, project_dir, pack_dir, temp_dir):
        """Test installing from a ZIP file."""
        zip_path = temp_dir / "test-pack.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for file_path in pack_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(pack_dir)
                    zf.write(file_path, arcname)

        manager = TemplatePackManager(project_dir)
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

        manager = TemplatePackManager(project_dir)
        manifest = manager.install_from_zip(zip_path, "0.1.5")
        assert manifest.id == "test-pack"

    def test_install_from_zip_no_manifest(self, project_dir, temp_dir):
        """Test installing from ZIP without manifest raises error."""
        zip_path = temp_dir / "bad.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("readme.txt", "no manifest here")

        manager = TemplatePackManager(project_dir)
        with pytest.raises(TemplateValidationError, match="No template-pack.yml found"):
            manager.install_from_zip(zip_path, "0.1.5")

    def test_remove(self, project_dir, pack_dir):
        """Test removing a template pack."""
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")
        assert manager.registry.is_installed("test-pack")

        result = manager.remove("test-pack")
        assert result is True
        assert not manager.registry.is_installed("test-pack")

        installed_dir = project_dir / ".specify" / "templates" / "packs" / "test-pack"
        assert not installed_dir.exists()

    def test_remove_nonexistent(self, project_dir):
        """Test removing a pack that doesn't exist."""
        manager = TemplatePackManager(project_dir)
        result = manager.remove("nonexistent")
        assert result is False

    def test_list_installed(self, project_dir, pack_dir):
        """Test listing installed packs."""
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-pack"
        assert installed[0]["name"] == "Test Template Pack"
        assert installed[0]["version"] == "1.0.0"
        assert installed[0]["template_count"] == 1

    def test_list_installed_empty(self, project_dir):
        """Test listing when no packs installed."""
        manager = TemplatePackManager(project_dir)
        assert manager.list_installed() == []

    def test_get_pack(self, project_dir, pack_dir):
        """Test getting a specific installed pack."""
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        pack = manager.get_pack("test-pack")
        assert pack is not None
        assert pack.id == "test-pack"

    def test_get_pack_not_installed(self, project_dir):
        """Test getting a non-installed pack returns None."""
        manager = TemplatePackManager(project_dir)
        assert manager.get_pack("nonexistent") is None

    def test_check_compatibility_valid(self, pack_dir):
        """Test compatibility check with valid version."""
        manager = TemplatePackManager(Path(tempfile.mkdtemp()))
        manifest = TemplatePackManifest(pack_dir / "template-pack.yml")
        assert manager.check_compatibility(manifest, "0.1.5") is True

    def test_check_compatibility_invalid(self, pack_dir):
        """Test compatibility check with invalid specifier."""
        manager = TemplatePackManager(Path(tempfile.mkdtemp()))
        manifest = TemplatePackManifest(pack_dir / "template-pack.yml")
        manifest.data["requires"]["speckit_version"] = "not-a-specifier"
        with pytest.raises(TemplateCompatibilityError, match="Invalid version specifier"):
            manager.check_compatibility(manifest, "0.1.5")


# ===== TemplateResolver Tests =====


class TestTemplateResolver:
    """Test TemplateResolver priority stack."""

    def test_resolve_core_template(self, project_dir):
        """Test resolving a core template."""
        resolver = TemplateResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert result.name == "spec-template.md"
        assert "Core Spec Template" in result.read_text()

    def test_resolve_nonexistent(self, project_dir):
        """Test resolving a nonexistent template returns None."""
        resolver = TemplateResolver(project_dir)
        result = resolver.resolve("nonexistent-template")
        assert result is None

    def test_resolve_override_takes_priority(self, project_dir):
        """Test that project overrides take priority over core."""
        # Create override
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override Spec Template\n")

        resolver = TemplateResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Override Spec Template" in result.read_text()

    def test_resolve_pack_takes_priority_over_core(self, project_dir, pack_dir):
        """Test that installed packs take priority over core templates."""
        # Install the pack
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = TemplateResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()

    def test_resolve_override_takes_priority_over_pack(self, project_dir, pack_dir):
        """Test that overrides take priority over installed packs."""
        # Install the pack
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        # Create override
        overrides_dir = project_dir / ".specify" / "templates" / "overrides"
        overrides_dir.mkdir(parents=True)
        override = overrides_dir / "spec-template.md"
        override.write_text("# Override Spec Template\n")

        resolver = TemplateResolver(project_dir)
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

        resolver = TemplateResolver(project_dir)
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
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = TemplateResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        # Pack should win over extension
        assert "Custom Spec Template" in result.read_text()

    def test_resolve_with_source_core(self, project_dir):
        """Test resolve_with_source for core template."""
        resolver = TemplateResolver(project_dir)
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

        resolver = TemplateResolver(project_dir)
        result = resolver.resolve_with_source("spec-template")
        assert result is not None
        assert result["source"] == "project override"

    def test_resolve_with_source_pack(self, project_dir, pack_dir):
        """Test resolve_with_source for pack template."""
        manager = TemplatePackManager(project_dir)
        manager.install_from_directory(pack_dir, "0.1.5")

        resolver = TemplateResolver(project_dir)
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

        resolver = TemplateResolver(project_dir)
        result = resolver.resolve_with_source("unique-template")
        assert result is not None
        assert result["source"] == "extension:my-ext"

    def test_resolve_with_source_not_found(self, project_dir):
        """Test resolve_with_source for nonexistent template."""
        resolver = TemplateResolver(project_dir)
        result = resolver.resolve_with_source("nonexistent")
        assert result is None

    def test_resolve_skips_hidden_extension_dirs(self, project_dir):
        """Test that hidden directories in extensions are skipped."""
        ext_dir = project_dir / ".specify" / "extensions" / ".backup"
        ext_templates_dir = ext_dir / "templates"
        ext_templates_dir.mkdir(parents=True)
        ext_template = ext_templates_dir / "hidden-template.md"
        ext_template.write_text("# Hidden\n")

        resolver = TemplateResolver(project_dir)
        result = resolver.resolve("hidden-template")
        assert result is None


# ===== TemplateCatalog Tests =====


class TestTemplateCatalog:
    """Test template catalog functionality."""

    def test_default_catalog_url(self, project_dir):
        """Test default catalog URL."""
        catalog = TemplateCatalog(project_dir)
        assert "githubusercontent.com" in catalog.DEFAULT_CATALOG_URL
        assert "templates/catalog.json" in catalog.DEFAULT_CATALOG_URL

    def test_community_catalog_url(self, project_dir):
        """Test community catalog URL."""
        catalog = TemplateCatalog(project_dir)
        assert "templates/catalog.community.json" in catalog.COMMUNITY_CATALOG_URL

    def test_cache_validation_no_cache(self, project_dir):
        """Test cache validation when no cache exists."""
        catalog = TemplateCatalog(project_dir)
        assert catalog.is_cache_valid() is False

    def test_cache_validation_valid(self, project_dir):
        """Test cache validation with valid cache."""
        catalog = TemplateCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text(json.dumps({
            "schema_version": "1.0",
            "template_packs": {},
        }))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }))

        assert catalog.is_cache_valid() is True

    def test_cache_validation_expired(self, project_dir):
        """Test cache validation with expired cache."""
        catalog = TemplateCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text(json.dumps({
            "schema_version": "1.0",
            "template_packs": {},
        }))
        catalog.cache_metadata_file.write_text(json.dumps({
            "cached_at": "2020-01-01T00:00:00+00:00",
        }))

        assert catalog.is_cache_valid() is False

    def test_cache_validation_corrupted(self, project_dir):
        """Test cache validation with corrupted metadata."""
        catalog = TemplateCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog.cache_file.write_text("not json")
        catalog.cache_metadata_file.write_text("not json")

        assert catalog.is_cache_valid() is False

    def test_clear_cache(self, project_dir):
        """Test clearing the cache."""
        catalog = TemplateCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)
        catalog.cache_file.write_text("{}")
        catalog.cache_metadata_file.write_text("{}")

        catalog.clear_cache()

        assert not catalog.cache_file.exists()
        assert not catalog.cache_metadata_file.exists()

    def test_search_with_cached_data(self, project_dir):
        """Test search with cached catalog data."""
        catalog = TemplateCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog_data = {
            "schema_version": "1.0",
            "template_packs": {
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
        catalog = TemplateCatalog(project_dir)
        catalog.cache_dir.mkdir(parents=True, exist_ok=True)

        catalog_data = {
            "schema_version": "1.0",
            "template_packs": {
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
        catalog = TemplateCatalog(project_dir)
        catalog._validate_catalog_url("https://example.com/catalog.json")

    def test_validate_catalog_url_http_rejected(self, project_dir):
        """Test that HTTP URLs are rejected."""
        catalog = TemplateCatalog(project_dir)
        with pytest.raises(TemplateValidationError, match="must use HTTPS"):
            catalog._validate_catalog_url("http://example.com/catalog.json")

    def test_validate_catalog_url_localhost_http_allowed(self, project_dir):
        """Test that HTTP is allowed for localhost."""
        catalog = TemplateCatalog(project_dir)
        catalog._validate_catalog_url("http://localhost:8080/catalog.json")
        catalog._validate_catalog_url("http://127.0.0.1:8080/catalog.json")

    def test_env_var_catalog_url(self, project_dir, monkeypatch):
        """Test catalog URL from environment variable."""
        monkeypatch.setenv("SPECKIT_TEMPLATE_CATALOG_URL", "https://custom.example.com/catalog.json")
        catalog = TemplateCatalog(project_dir)
        assert catalog.get_catalog_url() == "https://custom.example.com/catalog.json"


# ===== Integration Tests =====


class TestIntegration:
    """Integration tests for complete template pack workflows."""

    def test_full_install_resolve_remove_cycle(self, project_dir, pack_dir):
        """Test complete lifecycle: install → resolve → remove."""
        # Install
        manager = TemplatePackManager(project_dir)
        manifest = manager.install_from_directory(pack_dir, "0.1.5")
        assert manifest.id == "test-pack"

        # Resolve — pack template should win over core
        resolver = TemplateResolver(project_dir)
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
        resolver = TemplateResolver(project_dir)

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
        manager = TemplatePackManager(project_dir)
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
        manager = TemplatePackManager(project_dir)
        manager.install_from_zip(zip_path, "0.1.5")

        # Resolve
        resolver = TemplateResolver(project_dir)
        result = resolver.resolve("spec-template")
        assert result is not None
        assert "Custom Spec Template" in result.read_text()
