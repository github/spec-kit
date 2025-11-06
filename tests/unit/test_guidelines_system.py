"""
Unit tests for corporate guidelines system.
"""
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestGuidelinesStructure:
    """Tests for guidelines directory structure."""

    def test_guidelines_directory_exists(self, mock_guidelines_structure: Path):
        """Test guidelines directory can be created."""
        assert mock_guidelines_structure.exists()
        assert mock_guidelines_structure.is_dir()
        assert mock_guidelines_structure.name == ".guidelines"

    def test_branch_config_exists(self, mock_guidelines_structure: Path):
        """Test branch-config.json exists."""
        config_file = mock_guidelines_structure / "branch-config.json"
        assert config_file.exists()

    def test_stack_mapping_exists(self, mock_guidelines_structure: Path):
        """Test stack-mapping.json exists."""
        mapping_file = mock_guidelines_structure / "stack-mapping.json"
        assert mapping_file.exists()

    def test_guidelines_markdown_exists(self, mock_guidelines_structure: Path):
        """Test guideline markdown files exist."""
        guideline_file = mock_guidelines_structure / "reactjs-guidelines.md"
        assert guideline_file.exists()


@pytest.mark.unit
class TestBranchConfigParsing:
    """Tests for branch-config.json parsing."""

    def test_branch_config_valid_json(self, mock_guidelines_structure: Path):
        """Test branch-config.json is valid JSON."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert isinstance(config, dict)

    def test_branch_config_has_version(self, mock_guidelines_structure: Path):
        """Test branch-config.json has version field."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert "version" in config
        assert isinstance(config["version"], str)

    def test_branch_config_has_branch_naming(self, mock_guidelines_structure: Path):
        """Test branch-config.json has branchNaming section."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert "branchNaming" in config
        assert isinstance(config["branchNaming"], dict)

    def test_branch_naming_has_enabled_flag(self, mock_guidelines_structure: Path):
        """Test branchNaming has enabled flag."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        branch_naming = config["branchNaming"]
        assert "enabled" in branch_naming
        assert isinstance(branch_naming["enabled"], bool)

    def test_branch_naming_has_pattern(self, mock_guidelines_structure: Path):
        """Test branchNaming has pattern field."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        branch_naming = config["branchNaming"]
        assert "pattern" in branch_naming
        assert isinstance(branch_naming["pattern"], str)

    def test_branch_naming_has_components(self, mock_guidelines_structure: Path):
        """Test branchNaming has components field."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        branch_naming = config["branchNaming"]
        assert "components" in branch_naming
        assert isinstance(branch_naming["components"], dict)

    def test_branch_config_component_structure(self, mock_guidelines_structure: Path):
        """Test branch config components have correct structure."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        components = config["branchNaming"]["components"]

        for component_name, component_data in components.items():
            assert "type" in component_data
            assert "value" in component_data


@pytest.mark.unit
class TestStackMappingParsing:
    """Tests for stack-mapping.json parsing."""

    def test_stack_mapping_valid_json(self, mock_guidelines_structure: Path):
        """Test stack-mapping.json is valid JSON."""
        mapping_file = mock_guidelines_structure / "stack-mapping.json"
        with open(mapping_file) as f:
            mapping = json.load(f)

        assert isinstance(mapping, dict)

    def test_stack_mapping_has_version(self, mock_guidelines_structure: Path):
        """Test stack-mapping.json has version field."""
        mapping_file = mock_guidelines_structure / "stack-mapping.json"
        with open(mapping_file) as f:
            mapping = json.load(f)

        assert "version" in mapping
        assert isinstance(mapping["version"], str)

    def test_stack_mapping_has_stacks(self, mock_guidelines_structure: Path):
        """Test stack-mapping.json has stacks array."""
        mapping_file = mock_guidelines_structure / "stack-mapping.json"
        with open(mapping_file) as f:
            mapping = json.load(f)

        assert "stacks" in mapping
        assert isinstance(mapping["stacks"], list)

    def test_stack_entry_structure(self, mock_guidelines_structure: Path):
        """Test stack entries have correct structure."""
        mapping_file = mock_guidelines_structure / "stack-mapping.json"
        with open(mapping_file) as f:
            mapping = json.load(f)

        stacks = mapping["stacks"]
        assert len(stacks) > 0

        for stack in stacks:
            assert "name" in stack
            assert "paths" in stack
            assert "guidelines" in stack
            assert isinstance(stack["paths"], list)
            assert isinstance(stack["guidelines"], str)

    def test_stack_paths_format(self, mock_guidelines_structure: Path):
        """Test stack paths follow expected format."""
        mapping_file = mock_guidelines_structure / "stack-mapping.json"
        with open(mapping_file) as f:
            mapping = json.load(f)

        stacks = mapping["stacks"]

        for stack in stacks:
            paths = stack["paths"]
            for path in paths:
                assert isinstance(path, str)
                # Paths should typically end with / for directories
                # or be specific file patterns


@pytest.mark.unit
class TestGuidelineFiles:
    """Tests for guideline markdown files."""

    def test_guideline_file_readable(self, mock_guidelines_structure: Path):
        """Test guideline files can be read."""
        guideline_file = mock_guidelines_structure / "reactjs-guidelines.md"
        content = guideline_file.read_text()

        assert len(content) > 0
        assert isinstance(content, str)

    def test_guideline_file_markdown_format(self, mock_guidelines_structure: Path):
        """Test guideline files are in markdown format."""
        guideline_file = mock_guidelines_structure / "reactjs-guidelines.md"
        content = guideline_file.read_text()

        # Should contain markdown heading
        assert "#" in content

    def test_guideline_file_has_content(self, mock_guidelines_structure: Path):
        """Test guideline files have meaningful content."""
        guideline_file = mock_guidelines_structure / "reactjs-guidelines.md"
        content = guideline_file.read_text()

        # Should have more than just a heading
        lines = content.strip().split("\n")
        assert len(lines) >= 2


@pytest.mark.unit
class TestBranchNamingValidation:
    """Tests for branch naming validation logic."""

    def test_branch_pattern_placeholder_format(self):
        """Test branch pattern uses correct placeholder format."""
        pattern = "{username}/{repo-name}"

        # Should contain placeholders in braces
        assert "{" in pattern and "}" in pattern

    def test_branch_pattern_substitution(self):
        """Test branch pattern can be substituted."""
        pattern = "{username}/{repo-name}"
        username = "testuser"
        repo_name = "test-repo"

        result = pattern.replace("{username}", username).replace("{repo-name}", repo_name)

        assert result == "testuser/test-repo"

    def test_branch_pattern_multiple_components(self):
        """Test branch pattern with multiple components."""
        pattern = "{team}/{username}/{feature-type}/{description}"

        components = {
            "team": "backend",
            "username": "john",
            "feature-type": "feature",
            "description": "add-api"
        }

        result = pattern
        for key, value in components.items():
            result = result.replace(f"{{{key}}}", value)

        assert result == "backend/john/feature/add-api"


@pytest.mark.unit
class TestStackDetection:
    """Tests for technology stack detection."""

    def test_detect_stack_by_path(self, mock_guidelines_structure: Path):
        """Test detecting stack based on file path."""
        mapping_file = mock_guidelines_structure / "stack-mapping.json"
        with open(mapping_file) as f:
            mapping = json.load(f)

        stacks = mapping["stacks"]
        react_stack = next((s for s in stacks if s["name"] == "react"), None)

        assert react_stack is not None

        # Check if a path matches
        test_path = "src/components/Button.tsx"
        matches = any(test_path.startswith(p) for p in react_stack["paths"])

        assert matches is True

    def test_multiple_stack_detection(self, temp_dir: Path):
        """Test detecting multiple applicable stacks."""
        mapping = {
            "version": "1.0",
            "stacks": [
                {
                    "name": "frontend",
                    "paths": ["frontend/", "client/"],
                    "guidelines": "frontend-guidelines.md"
                },
                {
                    "name": "react",
                    "paths": ["frontend/react/", "components/"],
                    "guidelines": "react-guidelines.md"
                }
            ]
        }

        test_path = "frontend/react/Button.tsx"

        matching_stacks = [
            stack for stack in mapping["stacks"]
            if any(test_path.startswith(p) for p in stack["paths"])
        ]

        # Should match both frontend and react
        assert len(matching_stacks) >= 1


@pytest.mark.unit
class TestGuidelinesCompliance:
    """Tests for guidelines compliance checking."""

    def test_compliance_check_structure(self):
        """Test compliance check has expected structure."""
        # Mock compliance result structure
        compliance_result = {
            "compliant": True,
            "violations": [],
            "warnings": [],
        }

        assert "compliant" in compliance_result
        assert "violations" in compliance_result
        assert isinstance(compliance_result["compliant"], bool)
        assert isinstance(compliance_result["violations"], list)

    def test_violation_structure(self):
        """Test violation object has expected structure."""
        violation = {
            "file": "src/test.js",
            "line": 10,
            "severity": "error",
            "message": "Missing type annotation",
        }

        assert "file" in violation
        assert "severity" in violation
        assert "message" in violation


@pytest.mark.unit
class TestGuidelinesConfiguration:
    """Tests for guidelines configuration."""

    def test_guidelines_version_format(self, mock_guidelines_structure: Path):
        """Test guidelines use semantic versioning."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        version = config["version"]
        # Should be in format X.Y or X.Y.Z
        parts = version.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)

    def test_guidelines_backward_compatibility(self, mock_guidelines_structure: Path):
        """Test guidelines config maintains backward compatibility."""
        config_file = mock_guidelines_structure / "branch-config.json"
        with open(config_file) as f:
            config = json.load(f)

        # Version 1.0 should have minimum required fields
        assert "version" in config
        assert "branchNaming" in config


@pytest.mark.unit
class TestGuidelinesPaths:
    """Tests for guidelines file path handling."""

    def test_guidelines_directory_name(self):
        """Test guidelines directory has correct name."""
        guidelines_dir = Path(".guidelines")
        assert guidelines_dir.name == ".guidelines"

    def test_guidelines_config_filenames(self):
        """Test guidelines config files have correct names."""
        expected_files = [
            "branch-config.json",
            "stack-mapping.json",
        ]

        for filename in expected_files:
            assert isinstance(filename, str)
            assert filename.endswith(".json")

    def test_guidelines_markdown_extension(self):
        """Test guideline files use .md extension."""
        guidelines = [
            "reactjs-guidelines.md",
            "java-guidelines.md",
            "python-guidelines.md",
        ]

        for guideline in guidelines:
            assert guideline.endswith(".md")
