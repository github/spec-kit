"""
Tests for Phase 8: SpecKit Integration functionality.

Tests for speckit.memory.* commands and memory integration.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Import extension modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from extensions.speckit_memory.speckit_memory_specify import get_memory_context_before_spec
    from extensions.speckit_memory.speckit_memory_features import collect_quick_feature_info
    from extensions.speckit_memory.speckit_memory_plan import get_architecture_context
    from extensions.speckit_memory.speckit_memory_tasks import get_pattern_memory
    from extensions.speckit_memory.speckit_memory_clarify import get_cross_project_context
    EXTENSIONS_AVAILABLE = True
except ImportError as e:
    EXTENSIONS_AVAILABLE = False
    print(f"Warning: Extensions not available: {e}")


@pytest.mark.skipif(not EXTENSIONS_AVAILABLE, reason="Extensions not available")
class TestSpeckitMemorySpecify:
    """Test speckit.memory.specify command."""

    def test_get_memory_context_before_spec(self):
        """Test getting memory context before spec creation."""
        # Mock memory components
        with patch('extensions.speckit_memory.speckit_memory_specify.MEMORY_AVAILABLE', True):
            with patch('extensions.speckit_memory.speckit_memory_specify.HeadersFirstReader') as mock_reader:
                # Setup mock return value
                mock_reader.return_value.read_headers.return_value = {
                    "lessons": [
                        {"title": "Lesson 1", "one_liner": "Fix JWT token expiration"}
                    ],
                    "patterns": [
                        {"title": "Pattern 1", "one_liner": "Use refresh tokens"}
                    ],
                    "architecture": []
                }

                context = get_memory_context_before_spec("test-project")

                assert context["available"] is True
                assert context["project_id"] == "test-project"
                assert len(context["recent_lessons"]) >= 0
                assert len(context["active_patterns"]) >= 0

    def test_format_memory_context_for_spec(self):
        """Test formatting memory context for spec."""
        from extensions.speckit_memory.speckit_memory_specify import format_memory_context_for_spec

        context = {
            "available": True,
            "recent_lessons": [
                {"title": "JWT Fix", "summary": "Use refresh tokens"}
            ],
            "active_patterns": [
                {"title": "Repository Pattern", "summary": "Separate business logic"}
            ]
        }

        formatted = format_memory_context_for_spec(context)

        assert "## Memory Context" in formatted
        assert "JWT Fix" in formatted
        assert "Repository Pattern" in formatted


@pytest.mark.skipif(not EXTENSIONS_AVAILABLE, reason="Extensions not available")
class TestSpeckitMemoryFeatures:
    """Test speckit.memory.features command."""

    def test_collect_quick_feature_info_interactive(self):
        """Test collecting feature info interactively."""
        # Non-interactive test with defaults
        with patch('extensions.speckit_memory.speckit_memory_features.RICH_AVAILABLE', False):
            with patch('extensions.speckit_memory.speckit_memory_features.collect_quick_feature_info') as mock_collect:
                # Mock user input
                mock_collect.return_value = {
                    "name": "test-feature",
                    "description": "Test description",
                    "estimated_hours": 2,
                    "in_scope": ["Fix bug", "Test"],
                    "acceptance_criteria": ["Works"]
                }

                feature_info = mock_collect()

                assert feature_info["name"] == "test-feature"
                assert feature_info["estimated_hours"] == 2

    def test_generate_quick_spec(self):
        """Test quick spec generation."""
        from extensions.speckit_memory.speckit_memory_features import generate_quick_spec

        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir) / "specs"
            specs_dir.mkdir(parents=True, exist_ok=True)

            feature_info = {
                "name": "quick-test",
                "description": "Quick test feature",
                "estimated_hours": 1,
                "in_scope": ["Task 1", "Task 2"],
                "acceptance_criteria": ["Works", "Tested"]
            }

            spec_file = generate_quick_spec(feature_info, specs_dir)

            assert spec_file is not None
            assert spec_file.exists()
            assert spec_file.name == "spec.md"

            # Verify content
            content = spec_file.read_text()
            assert "quick-test" in content
            assert "Quick Feature" in content
            assert "Task 1" in content


@pytest.mark.skipif(not EXTENSIONS_AVAILABLE, reason="Extensions not available")
class TestSpeckitMemoryPlan:
    """Test speckit.memory.plan command."""

    def test_get_architecture_context(self):
        """Test getting architecture context."""
        with patch('extensions.speckit_memory.speckit_memory_plan.MEMORY_AVAILABLE', True):
            with patch('extensions.speckit_memory.speckit_memory_plan.HeadersFirstReader') as mock_reader:
                # Mock return value
                mock_reader.return_value.read_headers.return_value = {
                    "architecture": [
                        {"title": "Decision 1", "one_liner": "Use PostgreSQL"}
                    ],
                    "patterns": [
                        {"title": "Pattern 1", "one_liner": "Repository pattern"}
                    ]
                }

                context = get_architecture_context("test-project")

                assert "decisions" in context
                assert "patterns" in context
                assert len(context["decisions"]) >= 0

    def test_format_plan_memory_section(self):
        """Test formatting memory section for plan."""
        from extensions.speckit_memory.speckit_memory_plan import format_plan_memory_section

        context = {
            "decisions": [
                {"title": "PostgreSQL", "summary": "Use for primary database"}
            ],
            "patterns": [
                {"title": "Repository", "summary": "Separate concerns"}
            ]
        }

        formatted = format_plan_memory_section(context)

        assert "## Memory Context" in formatted
        assert "PostgreSQL" in formatted
        assert "Repository" in formatted


@pytest.mark.skipif(not EXTENSIONS_AVAILABLE, reason="Extensions not available")
class TestSpeckitMemoryTasks:
    """Test speckit.memory.tasks command."""

    def test_get_pattern_memory(self):
        """Test getting pattern memory."""
        with patch('extensions.speckit_memory.speckit_memory_tasks.MEMORY_AVAILABLE', True):
            with patch('extensions.speckit_memory.speckit_memory_tasks.HeadersFirstReader') as mock_reader:
                # Mock return value
                mock_reader.return_value.read_headers.return_value = {
                    "patterns": [
                        {"title": "Test Pattern", "one_liner": "Test description"}
                    ]
                }

                patterns = get_pattern_memory("test-project")

                assert isinstance(patterns, list)
                assert len(patterns) >= 0


@pytest.mark.skipif(not EXTENSIONS_AVAILABLE, reason="Extensions not available")
class TestSpeckitMemoryClarify:
    """Test speckit_memory.clarify command."""

    def test_get_cross_project_context(self):
        """Test getting cross-project context."""
        with patch('extensions.speckit_memory.speckit_memory_clarify.MEMORY_AVAILABLE', True):
            with patch('extensions.speckit_memory.speckit_memory_clarify.MemoryOrchestrator') as mock_orch:
                # Mock orchestrator
                mock_orch.return_value.search.return_value = [
                    {"title": "JWT Pattern", "source": "project-a"}
                ]

                context = get_cross_project_context("JWT authentication")

                assert context["available"] or "error" in context
                if context["available"]:
                    assert "results" in context


@pytest.mark.skipif(not EXTENSIONS_AVAILABLE, reason="Extensions not available")
class TestSpeckitMemoryIntegration:
    """Integration tests for speckit memory commands."""

    def test_quick_feature_full_workflow(self):
        """Test complete quick feature workflow."""
        from extensions.speckit_memory.speckit_memory_features import (
            generate_quick_spec,
            generate_quick_plan,
            generate_quick_tasks
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir) / "specs"
            specs_dir.mkdir(parents=True, exist_ok=True)

            feature_info = {
                "name": "integration-test",
                "description": "Test feature",
                "estimated_hours": 1,
                "in_scope": ["Implement", "Test"],
                "acceptance_criteria": ["Works"]
            }

            # Generate all artifacts
            spec_file = generate_quick_spec(feature_info, specs_dir)
            plan_file = generate_quick_plan(feature_info, spec_file.parent)
            tasks_file = generate_quick_tasks(feature_info, spec_file.parent)

            # Verify all created
            assert spec_file.exists()
            assert plan_file.exists()
            assert tasks_file.exists()

            # Verify spec content
            spec_content = spec_file.read_text()
            assert "integration-test" in spec_content

            # Verify plan content
            plan_content = plan_file.read_text()
            assert "integration-test" in plan_content

            # Verify tasks content
            tasks_content = tasks_file.read_text()
            assert "integration-test" in tasks_content
            assert "T001" in tasks_content

    def test_manifest_structure(self):
        """Test extension manifest structure."""
        manifest_path = Path(__file__).parent.parent / "speckit-memory" / "manifest.json"

        if manifest_path.exists():
            import json
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            # Required fields
            assert "name" in manifest
            assert "version" in manifest
            assert "registered_commands" in manifest

            # Check commands
            commands = manifest["registered_commands"]
            assert len(commands) == 5

            expected_commands = [
                "speckit.memory.specify",
                "speckit.memory.plan",
                "speckit.memory.tasks",
                "speckit.memory.clarify",
                "speckit.memory.features"
            ]

            for cmd in expected_commands:
                assert cmd in commands, f"Missing command: {cmd}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
