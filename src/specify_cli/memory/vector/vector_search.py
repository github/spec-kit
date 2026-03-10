"""
Unified search API for vector memory.

Provides search across all memory types with fallback.
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from ..logging import get_logger
from ..file_manager import FileMemoryManager
from ..headers_reader import HeadersFirstReader
from .ollama_client import OllamaClient
from .agent_memory_client import AgentMemoryClient
from .memory_types import FourLevelMemory


class VectorSearchAPI:
    """Unified search API for vector memory system."""

    def __init__(
        self,
        project_id: str,
        global_home: Optional[Path] = None,
        enable_vector: bool = True
    ):
        """Initialize search API.

        Args:
            project_id: Project identifier
            global_home: Path to global claude home
            enable_vector: Enable vector memory search
        """
        self.logger = get_logger()
        self.project_id = project_id
        self.global_home = global_home or Path.home() / ".claude"

        # Memory components
        self.file_memory = FileMemoryManager(global_home=self.global_home)
        self.headers_reader = HeadersFirstReader(global_home=self.global_home)
        self.four_level = FourLevelMemory(
            project_id=project_id,
            global_home=self.global_home,
            enable_vector=enable_vector
        )

        # Vector clients (optional)
        self.enable_vector = enable_vector
        self.ollama = None
        self.agent_memory = None

        if enable_vector:
            self.ollama = OllamaClient()
            self.agent_memory = AgentMemoryClient()

    def search(
        self,
        query: str,
        scope: str = "all",
        levels: Optional[List[str]] = None,
        limit: int = 10,
        min_score: float = 0.3
    ) -> Dict[str, Any]:
        """Unified search across all memory types.

        Args:
            query: Search query
            scope: "local", "global", or "all"
            levels: Memory levels to search ["1", "2", "3", "4"]
            limit: Max results per source
            min_score: Minimum relevance score

        Returns:
            Search results dict
        """
        if levels is None:
            levels = ["2", "3"] if self.enable_vector else ["2"]

        results = {
            "query": query,
            "scope": scope,
            "total": 0,
            "results": {}
        }

        # Search file-based memory (Level 2)
        if "2" in levels:
            file_results = self._search_file_memory(query, limit, min_score)
            results["results"]["file"] = file_results
            results["total"] += len(file_results)

        # Search vector memory (Level 3)
        if "3" in levels and self.enable_vector:
            vector_results = self._search_vector_memory(query, limit)
            results["results"]["vector"] = vector_results
            results["total"] += len(vector_results)

        # Search session context (Level 1)
        if "1" in levels:
            session_results = self.four_level._search_session(query)
            results["results"]["session"] = session_results
            results["total"] += len(session_results)

        # Sort by relevance and limit total
        results = self._sort_and_limit(results, limit * 2)

        return results

    def _search_file_memory(
        self,
        query: str,
        limit: int,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Search file-based memory.

        Args:
            query: Search query
            limit: Max results
            min_score: Minimum relevance score

        Returns:
            List of results
        """
        results = []

        # Search headers first (fast)
        headers = self.headers_reader.read_headers(
            project_id=self.project_id,
            limit=limit * 2
        )

        query_lower = query.lower()

        for file_type, items in headers.items():
            for item in items:
                title = item.get("title", "").lower()
                summary = item.get("summary", "").lower()

                # Calculate relevance
                score = self._calculate_relevance(query_lower, title, summary)

                if score >= min_score:
                    # Get full content if high relevance
                    if score > 0.7:
                        content = self.headers_reader.read_section(
                            project_id=self.project_id,
                            file_type=file_type,
                            header_match=item["title"]
                        )
                    else:
                        content = None

                    results.append({
                        "title": item["title"],
                        "summary": item["summary"],
                        "file_type": file_type,
                        "score": score,
                        "content": content,
                        "source": "file"
                    })

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:limit]

    def _search_vector_memory(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search vector memory.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of results
        """
        if not self.agent_memory or not self.agent_memory.is_available():
            return []

        try:
            results = self.agent_memory.search(query, limit)

            # Normalize to standard format
            normalized = []
            for item in results:
                normalized.append({
                    "content": item.get("content", ""),
                    "score": item.get("score", 1.0),
                    "source": "vector"
                })

            return normalized

        except Exception as e:
            self.logger.warning(f"Vector search error: {e}")
            return []

    def _calculate_relevance(
        self,
        query: str,
        title: str,
        summary: str
    ) -> float:
        """Calculate relevance score.

        Args:
            query: Search query (lowercase)
            title: Entry title (lowercase)
            summary: Entry summary (lowercase)

        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0

        # Exact match in title
        if query in title:
            score += 1.0
            return score

        # Word overlap in title
        query_words = set(query.split())
        title_words = set(title.split())

        overlap = query_words & title_words
        if overlap:
            score += len(overlap) / len(query_words) * 0.8

        # Match in summary
        if query in summary:
            score += 0.5

        return min(score, 1.0)

    def _sort_and_limit(
        self,
        results: Dict[str, Any],
        limit: int
    ) -> Dict[str, Any]:
        """Sort all results by score and limit.

        Args:
            results: Results dict
            limit: Max total results

        Returns:
            Sorted and limited results
        """
        # Collect all results with source
        all_results = []

        for source, items in results.get("results", {}).items():
            for item in items:
                item["source_type"] = source
                all_results.append(item)

        # Sort by score
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Limit
        all_results = all_results[:limit]

        # Reconstruct results dict
        results["results"] = all_results
        results["total"] = len(all_results)

        return results

    def semantic_search(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Pure semantic search using vector embeddings.

        Args:
            query: Search query
            limit: Max results

        Returns:
            Semantic search results
        """
        if not self.agent_memory or not self.agent_memory.is_available():
            return []

        return self.agent_memory.search(query, limit)

    def hybrid_search(
        self,
        query: str,
        alpha: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining semantic and keyword.

        Args:
            query: Search query
            alpha: Weight for semantic (0=keyword only, 1=semantic only)
            limit: Max results

        Returns:
            Combined results
        """
        # Get semantic results
        semantic_results = []
        if self.agent_memory and self.agent_memory.is_available():
            semantic_results = self.agent_memory.search(query, limit)

        # Get keyword results
        keyword_results = self._search_file_memory(query, limit, 0.0)

        # Combine with weighted scores
        combined = []

        # Add semantic results
        for item in semantic_results:
            combined.append({
                **item,
                "combined_score": item.get("score", 1.0) * alpha
            })

        # Add keyword results
        for item in keyword_results:
            combined.append({
                **item,
                "combined_score": item.get("score", 0) * (1 - alpha)
            })

        # Sort and limit
        combined.sort(key=lambda x: x["combined_score"], reverse=True)

        return combined[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get search system statistics.

        Returns:
            Statistics dict
        """
        return {
            "project_id": self.project_id,
            "vector_enabled": self.enable_vector,
            "ollama_available": self.ollama.is_available() if self.ollama else False,
            "agent_memory_available": self.agent_memory.is_available() if self.agent_memory else False,
            "memory_status": self.four_level.get_status()
        }
