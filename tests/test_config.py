"""
Tests for spectrena.config module.
"""

import pytest
from pathlib import Path
from spectrena.config import Config, SpecIdConfig


class TestSpecIdConfig:
    """Test SpecIdConfig class."""

    def test_simple_template(self):
        """Test simple spec ID template."""
        config = SpecIdConfig(template="{NNN}-{slug}")
        spec_id = config.generate_spec_id(1, "user-auth")
        assert spec_id == "001-user-auth"

    def test_component_template(self):
        """Test component-based spec ID template."""
        config = SpecIdConfig(template="{component}-{NNN}-{slug}")
        spec_id = config.generate_spec_id(1, "user-auth", component="CORE")
        assert spec_id == "CORE-001-user-auth"

    def test_project_template(self):
        """Test project-based spec ID template."""
        config = SpecIdConfig(
            template="{project}-{NNN}-{slug}",
            project="MYAPP"
        )
        spec_id = config.generate_spec_id(1, "user-auth")
        assert spec_id == "MYAPP-001-user-auth"

    def test_full_template(self):
        """Test full spec ID template."""
        config = SpecIdConfig(
            template="{project}-{component}-{NNN}-{slug}",
            project="MYAPP"
        )
        spec_id = config.generate_spec_id(1, "user-auth", component="CORE")
        assert spec_id == "MYAPP-CORE-001-user-auth"

    def test_requires_component(self):
        """Test requires_component property."""
        config = SpecIdConfig(template="{component}-{NNN}-{slug}")
        assert config.requires_component is True

        config = SpecIdConfig(template="{NNN}-{slug}")
        assert config.requires_component is False

    def test_requires_project(self):
        """Test requires_project property."""
        config = SpecIdConfig(template="{project}-{NNN}-{slug}")
        assert config.requires_project is True

        config = SpecIdConfig(template="{NNN}-{slug}")
        assert config.requires_project is False

    def test_padding(self):
        """Test number padding."""
        config = SpecIdConfig(template="{NNN}-{slug}", padding=3)
        spec_id = config.generate_spec_id(5, "test")
        assert "005" in spec_id

        config = SpecIdConfig(template="{NNN}-{slug}", padding=4)
        spec_id = config.generate_spec_id(5, "test")
        assert "0005" in spec_id

    def test_validate_component(self):
        """Test component validation."""
        config = SpecIdConfig(components=["CORE", "API", "UI"])

        assert config.validate_component("CORE") is True
        assert config.validate_component("core") is True  # Case insensitive
        assert config.validate_component("INVALID") is False

        # Empty components list means all are valid
        config = SpecIdConfig(components=[])
        assert config.validate_component("ANYTHING") is True


class TestConfig:
    """Test Config class."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.spec_id.template == "{NNN}-{slug}"
        assert config.spec_id.padding == 3
        assert config.spectrena.enabled is False

    def test_save_and_load(self, temp_dir):
        """Test saving and loading configuration."""
        config = Config()
        config.spec_id.template = "{component}-{NNN}-{slug}"
        config.spec_id.components = ["CORE", "API"]
        config.spec_id.project = "MYAPP"

        config.save(temp_dir)

        # Load it back
        loaded = Config.load(temp_dir)
        assert loaded.spec_id.template == "{component}-{NNN}-{slug}"
        assert "CORE" in loaded.spec_id.components
        assert "API" in loaded.spec_id.components
        assert loaded.spec_id.project == "MYAPP"

    def test_load_nonexistent(self, temp_dir):
        """Test loading when config doesn't exist."""
        config = Config.load(temp_dir)
        # Should return defaults
        assert config.spec_id.template == "{NNN}-{slug}"

    def test_yaml_generation(self):
        """Test YAML generation."""
        config = Config()
        config.spec_id.template = "{component}-{NNN}-{slug}"
        config.spec_id.components = ["CORE", "API"]
        config.spec_id.project = "TEST"
        config.spectrena.enabled = True

        yaml = config._generate_yaml()

        assert "template:" in yaml
        assert "{component}-{NNN}-{slug}" in yaml
        assert "- CORE" in yaml
        assert "- API" in yaml
        assert "project: \"TEST\"" in yaml
        assert "enabled: true" in yaml
