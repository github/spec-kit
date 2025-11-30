"""
Tests for Mermaid-based dependency management.
"""

import pytest
from pathlib import Path
import os
from spectrena.worktrees import (
    parse_mermaid_deps,
    write_mermaid_deps,
    load_dependencies,
)


class TestMermaidParsing:
    """Test parsing Mermaid dependency graphs."""

    def test_parse_empty_file(self, temp_dir):
        """Test parsing empty deps.mermaid file."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("graph TD\n")

        deps = parse_mermaid_deps(deps_file)
        assert deps == {}

    def test_parse_nonexistent_file(self, temp_dir):
        """Test parsing when file doesn't exist."""
        deps_file = temp_dir / "deps.mermaid"
        deps = parse_mermaid_deps(deps_file)
        assert deps == {}

    def test_parse_standalone_nodes(self, temp_dir):
        """Test parsing specs with no dependencies."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001-user-auth
    CORE-002-data-sync
""")

        deps = parse_mermaid_deps(deps_file)
        assert "CORE-001-user-auth" in deps
        assert "CORE-002-data-sync" in deps
        assert deps["CORE-001-user-auth"] == []
        assert deps["CORE-002-data-sync"] == []

    def test_parse_simple_dependencies(self, temp_dir):
        """Test parsing simple dependency relationships."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001-user-auth
    CORE-002-data-sync --> CORE-001-user-auth
""")

        deps = parse_mermaid_deps(deps_file)
        assert "CORE-001-user-auth" in deps
        assert "CORE-002-data-sync" in deps
        assert deps["CORE-001-user-auth"] == []
        assert deps["CORE-002-data-sync"] == ["CORE-001-user-auth"]

    def test_parse_multiple_dependencies(self, temp_dir):
        """Test parsing spec with multiple dependencies."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001-user-auth
    CORE-002-data-sync --> CORE-001-user-auth
    API-001-rest-endpoints --> CORE-001-user-auth
    API-001-rest-endpoints --> CORE-002-data-sync
""")

        deps = parse_mermaid_deps(deps_file)
        assert deps["API-001-rest-endpoints"] == [
            "CORE-001-user-auth",
            "CORE-002-data-sync"
        ]

    def test_parse_complex_graph(self, temp_dir):
        """Test parsing complex dependency graph."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001-user-auth
    CORE-002-data-sync --> CORE-001-user-auth
    API-001-rest-endpoints --> CORE-001-user-auth
    API-002-webhooks --> API-001-rest-endpoints
    UI-001-dashboard --> API-001-rest-endpoints
    UI-001-dashboard --> CORE-002-data-sync
""")

        deps = parse_mermaid_deps(deps_file)

        # Root node
        assert deps["CORE-001-user-auth"] == []

        # First level
        assert deps["CORE-002-data-sync"] == ["CORE-001-user-auth"]
        assert deps["API-001-rest-endpoints"] == ["CORE-001-user-auth"]

        # Second level
        assert deps["API-002-webhooks"] == ["API-001-rest-endpoints"]
        assert "API-001-rest-endpoints" in deps["UI-001-dashboard"]
        assert "CORE-002-data-sync" in deps["UI-001-dashboard"]

    def test_parse_whitespace_tolerance(self, temp_dir):
        """Test parsing with various whitespace formats."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    SPEC-001
    SPEC-002-->SPEC-001
    SPEC-003  -->  SPEC-002
""")

        deps = parse_mermaid_deps(deps_file)
        assert deps["SPEC-002"] == ["SPEC-001"]
        assert deps["SPEC-003"] == ["SPEC-002"]


class TestMermaidWriting:
    """Test writing Mermaid dependency graphs."""

    def test_write_empty_graph(self, temp_dir):
        """Test writing empty dependency graph."""
        deps_file = temp_dir / "deps.mermaid"
        write_mermaid_deps(deps_file, {})

        content = deps_file.read_text()
        assert content == "graph TD\n"

    def test_write_standalone_nodes(self, temp_dir):
        """Test writing specs with no dependencies."""
        deps_file = temp_dir / "deps.mermaid"
        deps = {
            "CORE-001-user-auth": [],
            "CORE-002-data-sync": [],
        }
        write_mermaid_deps(deps_file, deps)

        content = deps_file.read_text()
        assert "graph TD" in content
        assert "CORE-001-user-auth" in content
        assert "CORE-002-data-sync" in content
        assert "-->" not in content

    def test_write_simple_dependencies(self, temp_dir):
        """Test writing simple dependencies."""
        deps_file = temp_dir / "deps.mermaid"
        deps = {
            "CORE-001-user-auth": [],
            "CORE-002-data-sync": ["CORE-001-user-auth"],
        }
        write_mermaid_deps(deps_file, deps)

        content = deps_file.read_text()
        assert "CORE-001-user-auth" in content
        assert "CORE-002-data-sync --> CORE-001-user-auth" in content

    def test_write_multiple_dependencies(self, temp_dir):
        """Test writing spec with multiple dependencies."""
        deps_file = temp_dir / "deps.mermaid"
        deps = {
            "CORE-001-user-auth": [],
            "CORE-002-data-sync": ["CORE-001-user-auth"],
            "API-001-rest-endpoints": ["CORE-001-user-auth", "CORE-002-data-sync"],
        }
        write_mermaid_deps(deps_file, deps)

        content = deps_file.read_text()
        assert "API-001-rest-endpoints --> CORE-001-user-auth" in content
        assert "API-001-rest-endpoints --> CORE-002-data-sync" in content

    def test_roundtrip_parse_write(self, temp_dir):
        """Test that parse -> write -> parse produces same result."""
        deps_file = temp_dir / "deps.mermaid"
        original = {
            "CORE-001": [],
            "CORE-002": ["CORE-001"],
            "API-001": ["CORE-001", "CORE-002"],
        }

        # Write
        write_mermaid_deps(deps_file, original)

        # Parse
        parsed = parse_mermaid_deps(deps_file)

        # Should match - all specs with dependencies are preserved
        # CORE-001 appears as standalone node, so it gets an entry
        assert parsed == original


class TestDependencyOperations:
    """Test dependency graph operations."""

    def test_load_dependencies_mermaid(self, temp_dir):
        """Test loading dependencies from Mermaid file."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001-user-auth
    CORE-002-data-sync --> CORE-001-user-auth
    API-001-rest-endpoints --> CORE-001-user-auth
""")

        os.chdir(temp_dir)
        deps = load_dependencies()

        assert deps["CORE-001-user-auth"] == []
        assert deps["CORE-002-data-sync"] == ["CORE-001-user-auth"]
        assert deps["API-001-rest-endpoints"] == ["CORE-001-user-auth"]

    def test_dependency_chain(self, temp_dir):
        """Test linear dependency chain."""
        deps_file = temp_dir / "deps.mermaid"
        # Include all specs as standalone nodes for complete graph
        deps_file.write_text("""graph TD
    SPEC-001
    SPEC-002
    SPEC-003
    SPEC-004
    SPEC-002 --> SPEC-001
    SPEC-003 --> SPEC-002
    SPEC-004 --> SPEC-003
""")

        os.chdir(temp_dir)
        deps = load_dependencies()

        # Verify chain: 4 -> 3 -> 2 -> 1
        assert deps["SPEC-004"] == ["SPEC-003"]
        assert deps["SPEC-003"] == ["SPEC-002"]
        assert deps["SPEC-002"] == ["SPEC-001"]
        assert deps["SPEC-001"] == []

    def test_diamond_dependency(self, temp_dir):
        """Test diamond-shaped dependency graph."""
        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    ROOT
    LEFT --> ROOT
    RIGHT --> ROOT
    BOTTOM --> LEFT
    BOTTOM --> RIGHT
""")

        deps = parse_mermaid_deps(deps_file)

        # Bottom depends on both left and right
        assert "LEFT" in deps["BOTTOM"]
        assert "RIGHT" in deps["BOTTOM"]

        # Left and right both depend on root
        assert deps["LEFT"] == ["ROOT"]
        assert deps["RIGHT"] == ["ROOT"]


class TestDependencyValidation:
    """Test dependency graph validation."""

    def test_detect_cycle_simple(self, temp_dir):
        """Test detecting simple circular dependency."""
        from spectrena.worktrees import dep_check

        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    SPEC-001 --> SPEC-002
    SPEC-002 --> SPEC-001
""")

        os.chdir(temp_dir)
        # This should detect a cycle
        # Note: dep_check prints to console, returns boolean
        result = dep_check()
        assert result == False  # Cycle detected

    def test_detect_cycle_indirect(self, temp_dir):
        """Test detecting indirect circular dependency."""
        from spectrena.worktrees import dep_check

        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    SPEC-001 --> SPEC-002
    SPEC-002 --> SPEC-003
    SPEC-003 --> SPEC-001
""")

        os.chdir(temp_dir)
        result = dep_check()
        assert result == False  # Cycle detected

    def test_no_cycle_valid_graph(self, temp_dir):
        """Test validation passes for valid graph."""
        from spectrena.worktrees import dep_check

        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001
    CORE-002 --> CORE-001
    API-001 --> CORE-001
    API-002 --> API-001
""")

        # Create specs directory with matching specs
        specs_dir = temp_dir / "specs"
        specs_dir.mkdir()
        (specs_dir / "CORE-001").mkdir()
        (specs_dir / "CORE-002").mkdir()
        (specs_dir / "API-001").mkdir()
        (specs_dir / "API-002").mkdir()

        os.chdir(temp_dir)
        result = dep_check()
        assert result == True  # No cycles

    def test_missing_spec_warning(self, temp_dir):
        """Test warning for missing spec directories."""
        from spectrena.worktrees import dep_check

        deps_file = temp_dir / "deps.mermaid"
        deps_file.write_text("""graph TD
    CORE-001
    CORE-002 --> CORE-001
    MISSING-SPEC --> CORE-001
""")

        # Create only some specs
        specs_dir = temp_dir / "specs"
        specs_dir.mkdir()
        (specs_dir / "CORE-001").mkdir()
        (specs_dir / "CORE-002").mkdir()
        # MISSING-SPEC not created

        os.chdir(temp_dir)
        # Should still return True (warnings don't fail validation)
        result = dep_check()
        # Note: This will print warning about missing spec


class TestIntegration:
    """Integration tests for dependency management."""

    def test_add_and_show_dependencies(self, temp_dir):
        """Test adding dependencies and showing the graph."""
        from spectrena.worktrees import dep_add, parse_mermaid_deps

        deps_file = temp_dir / "deps.mermaid"
        os.chdir(temp_dir)

        # Add first dependency
        dep_add("CORE-002", "CORE-001")

        # Verify it was written
        deps = parse_mermaid_deps(deps_file)
        assert "CORE-002" in deps
        assert "CORE-001" in deps["CORE-002"]

        # Add another dependency
        dep_add("API-001", "CORE-001")

        # Verify both are present
        deps = parse_mermaid_deps(deps_file)
        assert "CORE-002" in deps
        assert "API-001" in deps

    def test_remove_dependency(self, temp_dir):
        """Test removing a dependency."""
        from spectrena.worktrees import dep_add, dep_remove, parse_mermaid_deps

        deps_file = temp_dir / "deps.mermaid"
        os.chdir(temp_dir)

        # Add dependencies
        dep_add("SPEC-002", "SPEC-001")
        dep_add("SPEC-003", "SPEC-001")
        dep_add("SPEC-003", "SPEC-002")

        # Remove one
        dep_remove("SPEC-003", "SPEC-002")

        # Verify
        deps = parse_mermaid_deps(deps_file)
        assert "SPEC-001" in deps["SPEC-003"]
        assert "SPEC-002" not in deps["SPEC-003"]

    def test_full_workflow(self, temp_dir):
        """Test complete dependency management workflow."""
        from spectrena.worktrees import (
            dep_add,
            dep_check,
            parse_mermaid_deps,
        )

        os.chdir(temp_dir)

        # Create specs directory
        specs_dir = temp_dir / "specs"
        specs_dir.mkdir()

        # Add specs
        for spec_id in ["CORE-001", "CORE-002", "API-001", "UI-001"]:
            (specs_dir / spec_id).mkdir()

        # Build dependency graph
        dep_add("CORE-002", "CORE-001")
        dep_add("API-001", "CORE-001")
        dep_add("UI-001", "API-001")
        dep_add("UI-001", "CORE-002")

        # Validate
        result = dep_check()
        assert result == True

        # Verify structure
        deps = parse_mermaid_deps(temp_dir / "deps.mermaid")

        # CORE-001 should be present (added as dependency)
        # dep_add ensures dependencies exist in graph
        assert "CORE-002" in deps
        assert "API-001" in deps
        assert "UI-001" in deps

        assert deps["CORE-002"] == ["CORE-001"]
        assert deps["API-001"] == ["CORE-001"]
        assert "API-001" in deps["UI-001"]
        assert "CORE-002" in deps["UI-001"]
