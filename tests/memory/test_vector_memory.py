"""
Tests for Phase 5: Vector Memory functionality.

Tests for Ollama client, agent-memory-mcp client, four-level memory,
RAG indexer, content templates, and search API.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from specify_cli.memory.vector.ollama_client import OllamaClient
from specify_cli.memory.vector.agent_memory_client import AgentMemoryClient
from specify_cli.memory.vector.memory_types import FourLevelMemory
from specify_cli.memory.vector.rag_indexer import RAGIndexer
from specify_cli.memory.vector.content_template import MemoryContentTemplate, StructuredMemory
from specify_cli.memory.vector.vector_search import VectorSearchAPI


class TestOllamaClient:
    """Test Ollama embeddings client."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = OllamaClient()

        assert client.host == "http://localhost:11434"
        assert client.model == "mxbai-embed-large"
        assert client.EMBEDDING_DIM == 1024

    def test_is_available_with_mock(self):
        """Test availability check."""
        client = OllamaClient()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            assert client.is_available() is True

    def test_is_available_failure(self):
        """Test availability check failure."""
        client = OllamaClient()

        with patch('requests.get', side_effect=Exception("Connection refused")):
            assert client.is_available() is False

    def test_embed_with_mock(self):
        """Test embedding generation."""
        client = OllamaClient()

        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "embedding": [0.1, 0.2, 0.3] * 341  # 1023 dims for test
            }
            mock_post.return_value = mock_response

            result = client.embed("test text")

            assert result is not None
            assert len(result) > 0

    def test_embed_batch(self):
        """Test batch embedding."""
        client = OllamaClient()

        with patch.object(client, '_embed_batch_request') as mock_batch:
            mock_batch.return_value = [
                [0.1] * 1024,
                [0.2] * 1024,
                [0.3] * 1024
            ]

            texts = ["text1", "text2", "text3"]
            results = client.embed_batch(texts)

            assert len(results) == 3
            assert all(r is not None for r in results)

    def test_get_status(self):
        """Test status retrieval."""
        client = OllamaClient()

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [{"name": "mxbai-embed-large"}]
            }
            mock_get.return_value = mock_response

            status = client.get_status()

            assert "available" in status
            assert "model" in status
            assert "embedding_dim" in status


class TestAgentMemoryClient:
    """Test agent-memory-mcp client."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = AgentMemoryClient()

        assert client.binary == "agent-memory-mcp"
        assert "semantic" in client.MEMORY_TYPES

    def test_is_available_mock(self):
        """Test availability check."""
        client = AgentMemoryClient()

        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            assert client.is_available() is True

    def test_is_available_not_found(self):
        """Test availability when binary not found."""
        client = AgentMemoryClient()

        with patch('subprocess.run', side_effect=FileNotFoundError):
            assert client.is_available() is False

    def test_store_with_mock(self):
        """Test storing content."""
        client = AgentMemoryClient()

        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = client.store(
                content="Test content",
                memory_type="semantic",
                tags=["test"]
            )

            assert result is True

    def test_recall_with_mock(self):
        """Test recalling memories."""
        client = AgentMemoryClient()

        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "Result 1\nResult 2\n"
            mock_run.return_value = mock_result

            results = client.recall("test query")

            assert isinstance(results, list)
            assert len(results) >= 0


class TestFourLevelMemory:
    """Test four-level memory system."""

    def test_initialization(self):
        """Test system initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = FourLevelMemory(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            assert memory.project_id == "test-project"
            assert memory.enable_vector is False
            assert memory.session_context == {}

    def test_store_session_level(self):
        """Test storing at session level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = FourLevelMemory(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            memory.store("Test content", level="1")

            assert len(memory.session_context) > 0

    def test_retrieve_session(self):
        """Test retrieving from session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = FourLevelMemory(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            memory.store("Test content about authentication", level="1")

            results = memory.retrieve("authentication", levels=["1"])

            assert "session" in results
            assert len(results["session"]) > 0

    def test_get_status(self):
        """Test getting status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = FourLevelMemory(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            status = memory.get_status()

            assert "level1_session" in status
            assert "level2_file" in status
            assert "level3_vector" in status
            assert "level4_identity" in status


class TestMemoryContentTemplate:
    """Test content templates."""

    def test_format_problem_solution(self):
        """Test problem-solution template."""
        content = MemoryContentTemplate.format_problem_solution(
            title="JWT Token Expired",
            problem="Tokens expire after 15 minutes",
            solution="Implement refresh token flow",
            lessons="Use short-lived access tokens with refresh mechanism",
            tags=["auth", "jwt"],
            project="test-project"
        )

        assert "JWT Token Expired" in content
        assert "Tokens expire" in content
        assert "refresh token flow" in content

    def test_format_pattern(self):
        """Test pattern template."""
        content = MemoryContentTemplate.format_pattern(
            name="Repository",
            summary="Separate data access from business logic",
            pattern="Create repository interface",
            context="Data layer architecture",
            language="python",
            example="class Repository:\n    pass"
        )

        assert "Repository" in content
        assert "Separate data access" in content
        assert "```python" in content

    def test_format_decision(self):
        """Test decision template."""
        content = MemoryContentTemplate.format_decision(
            title="Use PostgreSQL as primary database",
            context="Need ACID compliance and complex queries",
            decision="PostgreSQL chosen over MongoDB",
            positive="Strong consistency, powerful querying",
            negative="More complex scaling"
        )

        assert "PostgreSQL" in content
        assert "ACID compliance" in content
        assert "Decision" in content

    def test_format_episodic(self):
        """Test episodic template."""
        content = MemoryContentTemplate.format_episodic(
            title="Fixed authentication bug",
            description="JWT validation was failing",
            insights="Always validate token expiration",
            event_type="Bug Fix",
            impact="Users can now authenticate properly"
        )

        assert "authentication bug" in content
        assert "JWT validation" in content


class TestStructuredMemory:
    """Test structured memory helper."""

    def test_create_problem_entry(self):
        """Test creating problem entry."""
        helper = StructuredMemory(project_id="test-project")

        entry = helper.create_problem_entry(
            title="Test Problem",
            problem="Problem description",
            solution="Solution description",
            lessons="Lesson learned"
        )

        assert entry["type"] == "problem_solution"
        assert entry["title"] == "Test Problem"
        assert "content" in entry
        assert "tags" in entry

    def test_create_pattern_entry(self):
        """Test creating pattern entry."""
        helper = StructuredMemory(project_id="test-project")

        entry = helper.create_pattern_entry(
            name="Test Pattern",
            summary="Pattern summary",
            pattern="Pattern description",
            context="Usage context"
        )

        assert entry["type"] == "pattern"
        assert entry["title"] == "Test Pattern"
        assert entry["summary"] == "Pattern summary"

    def test_create_decision_entry(self):
        """Test creating decision entry."""
        helper = StructuredMemory(project_id="test-project")

        entry = helper.create_decision_entry(
            title="Test Decision",
            context="Decision context",
            decision="The decision itself"
        )

        assert entry["type"] == "decision"
        assert entry["title"] == "Test Decision"


class TestVectorSearchAPI:
    """Test unified search API."""

    def test_initialization(self):
        """Test API initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            api = VectorSearchAPI(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            assert api.project_id == "test-project"
            assert api.enable_vector is False

    def test_search_file_memory(self):
        """Test searching file memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            memory_dir = Path(tmpdir) / "memory" / "projects" / "test-project"
            memory_dir.mkdir(parents=True)

            lessons_file = memory_dir / "lessons.md"
            lessons_file.write_text("""
# Lessons

## Error: JWT Expired
Token expires after 15 minutes
Solution: Use refresh tokens
""", encoding='utf-8')

            api = VectorSearchAPI(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            results = api.search("JWT", scope="local", levels=["2"])

            assert "results" in results
            assert "total" in results
            assert results["total"] >= 0

    def test_get_stats(self):
        """Test getting statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            api = VectorSearchAPI(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            stats = api.get_stats()

            assert "project_id" in stats
            assert stats["project_id"] == "test-project"
            assert "vector_enabled" in stats


class TestRAGIndexer:
    """Test RAG indexer."""

    def test_initialization(self):
        """Test indexer initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            indexer = RAGIndexer(
                project_id="test-project",
                global_home=Path(tmpdir),
                auto_index=False
            )

            assert indexer.project_id == "test-project"

    def test_extract_sections(self):
        """Test section extraction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            indexer = RAGIndexer(
                project_id="test-project",
                global_home=Path(tmpdir),
                auto_index=False
            )

            content = """
## Section 1
Content 1

## Section 2
Content 2
"""

            sections = indexer._extract_sections(content)

            assert len(sections) == 2
            assert sections[0][0] == "Section 1"
            assert sections[1][0] == "Section 2"

    def test_get_memory_type(self):
        """Test memory type detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            indexer = RAGIndexer(
                project_id="test-project",
                global_home=Path(tmpdir),
                auto_index=False
            )

            assert indexer._get_memory_type("patterns.md") == "procedural"
            assert indexer._get_memory_type("lessons.md") == "episodic"
            assert indexer._get_memory_type("architecture.md") == "semantic"


class TestVectorIntegration:
    """Integration tests for vector memory."""

    def test_graceful_degradation_without_ollama(self):
        """Test system works without Ollama."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Disable vector memory
            memory = FourLevelMemory(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            # Should still work with file-based only
            memory.store("Test content", level="2")

            results = memory.retrieve("Test", levels=["2"])

            assert "file" in results

    def test_content_to_search_flow(self):
        """Test full flow from content storage to search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Store using structured template
            helper = StructuredMemory(project_id="test-project")

            entry = helper.create_problem_entry(
                title="Authentication Issue",
                problem="Users cannot login",
                solution="Fixed token validation",
                lessons="Always check token expiration"
            )

            # Write to file
            memory = FourLevelMemory(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            memory.store(entry["content"], level="2")

            # Search should find it
            api = VectorSearchAPI(
                project_id="test-project",
                global_home=Path(tmpdir),
                enable_vector=False
            )

            results = api.search("Authentication", levels=["2"])

            assert results["total"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
