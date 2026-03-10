"""
Tests for graceful degradation when external dependencies are unavailable.
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

from specify_cli.memory.orchestrator import MemoryOrchestrator
from specify_cli.memory.file_manager import FileMemoryManager
from specify_cli.memory.logging import get_logger


class TestGracefulDegradation:
    """Test graceful degradation behavior."""

    def test_orchestrator_without_ollama(self):
        """Test orchestrator works when Ollama is unavailable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = MemoryOrchestrator(
                project_id="test",
                memory_root=Path(tmpdir),
                vector_enabled=True  # Requested but unavailable
            )

            # Check dependencies (should handle unavailable gracefully)
            status = orchestrator.check_dependencies()

            # Should not crash
            assert "ollama" in status
            assert "vector_memory" in status
            assert status["vector_memory"] is False  # Correctly detected as unavailable

    def test_orchestrator_search_without_vector(self):
        """Test search works when vector memory is unavailable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = MemoryOrchestrator(
                project_id="test",
                memory_root=Path(tmpdir),
                vector_enabled=False  # Explicitly disabled
            )

            # Create test data
            (Path(tmpdir) / "lessons.md").write_text(
                "## Error: Test - Test error\n"
                "### Solution: Test solution\n",
                encoding="utf-8"
            )

            # Search should work with local-only search
            results = orchestrator.search("test", scope="local")

            # Should find results from file-based search
            assert len(results) > 0
            assert results[0]["source"] == "lessons"
            assert "test" in results[0]["header"].lower()

    def test_file_manager_without_dependencies(self):
        """Test file manager works without any external dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileMemoryManager(
                project_id="test",
                memory_root=Path(tmpdir)
            )

            # Initialize memory files (should work without deps)
            success = manager.initialize_memory_files()

            assert success is True

            # Files should be created
            assert (Path(tmpdir) / "lessons.md").exists()
            assert (Path(tmpdir) / "patterns.md").exists()
            assert (Path(tmpdir) / "architecture.md").exists()
            assert (Path(tmpdir) / "projects-log.md").exists()

    def test_headers_first_context_optimization(self):
        """Test headers-first reading provides context optimization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileMemoryManager(
                project_id="test",
                memory_root=Path(tmpdir)
            )

            # Create test data with multiple headers
            (Path(tmpdir) / "lessons.md").write_text(
                "## Error: JWT - Token expires quickly\n"
                "### Solution: Implement refresh token flow\n"
                "\n"
                "## Error: CORS - Credentials issue\n"
                "### Solution: Set explicit origin\n"
                "\n"
                "## Pattern: Repository - Separate logic\n"
                "### When to use: Business logic separation\n"
            )

            # Read headers first
            headers = manager.read_headers_first(limit=10)

            # Should extract only headers (not full content)
            assert "lessons" in headers
            assert len(headers["lessons"]) == 3

            # Context optimization: all headers fit in ~200 chars
            total_chars = sum(len(h) for h in headers["lessons"])
            assert total_chars < 300  # Well under target ~80-120 tokens

    def test_importance_classifier_routing(self):
        """Test AI classifier routes to correct files based on importance."""
        from specify_cli.memory.classifier import AIImportanceClassifier

        classifier = AIImportanceClassifier()

        # High importance content (>0.7) → architecture.md
        high_importance = "This is a critical architecture decision for the database schema."
        result = classifier.calculate_importance(high_importance)
        assert result["score"] > 0.7
        assert result["routing_target"] == "architecture.md"

        # Medium importance (0.4-0.7) → patterns.md
        medium_importance = "This is a useful pattern for error handling that we can reuse."
        result = classifier.calculate_importance(medium_importance)
        assert 0.4 <= result["score"] <= 0.7
        assert result["routing_target"] == "patterns.md"

        # Low importance (<0.4) → projects-log.md
        low_importance = "Completed task X successfully."
        result = classifier.calculate_importance(low_importance)
        assert result["score"] < 0.4
        assert result["routing_target"] == "projects-log.md"

    def test_explicit_marker_override(self):
        """Test explicit user markers override AI classification."""
        from specify_cli.memory.classifier import AIImportanceClassifier

        classifier = AIImportanceClassifier()

        # Explicit marker should give score=1.0
        content = "Some content"
        result = classifier.calculate_importance(
            content,
            explicit_markers=["запомни это как паттерн"]
        )

        assert result["score"] == 1.0
        assert result["routing_target"] == "patterns.md"
        assert result["confidence"] == 1.0

    def test_logging_without_log_file(self):
        """Test logger works even if file handler fails."""
        # Get logger without file (console only)
        logger = get_logger(log_file=None)

        # Should not crash
        logger.logger.info("Test message")

        # Should also work with warning_once
        logger.warning_once("Test warning")
        logger.warning_once("Test warning")  # Should not repeat


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
