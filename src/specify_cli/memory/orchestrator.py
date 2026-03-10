"""
Memory Orchestrator - Coordinates all memory operations.

Provides unified API for file-based and vector-based memory with graceful degradation.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

from .logging import get_logger
from .config import MemoryConfigManager


class MemoryOrchestrator:
    """Orchestrates all memory operations with smart search and graceful degradation."""

    def __init__(
        self,
        project_id: str,
        memory_root: Optional[Path] = None,
        vector_enabled: bool = False
    ):
        """Initialize memory orchestrator.

        Args:
            project_id: Project identifier
            memory_root: Root directory for memory files
            vector_enabled: Whether vector memory is available
        """
        self.project_id = project_id
        self.logger = get_logger()
        self.vector_enabled = vector_enabled

        # Setup paths
        if memory_root is None:
            config = MemoryConfigManager()
            memory_root = config.global_home / "memory" / "projects" / project_id

        self.memory_root = Path(memory_root)
        self.memory_root.mkdir(parents=True, exist_ok=True)

        # Memory file paths
        self.lessons_file = self.memory_root / "lessons.md"
        self.patterns_file = self.memory_root / "patterns.md"
        self.architecture_file = self.memory_root / "architecture.md"
        self.projects_log_file = self.memory_root / "projects-log.md"
        self.handoff_file = self.memory_root / "handoff.md"

        # Graceful degradation tracking
        self._vector_available = vector_enabled
        self._vector_warning_shown = False

    def check_dependencies(self) -> Dict[str, bool]:
        """Check availability of external dependencies.

        Returns:
            Dict with availability status
        """
        status = {
            "vector_memory": False,
            "ollama": False,
            "agent_memory_mcp": False,
        }

        # Check Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            status["ollama"] = response.status_code == 200
        except Exception:
            pass

        # Check agent-memory-mcp
        try:
            import shutil
            status["agent_memory_mcp"] = shutil.which("agent-memory-mcp") is not None
        except Exception:
            pass

        # Vector memory available if both dependencies present
        status["vector_memory"] = status["ollama"] and status["agent_memory_mcp"]

        self._vector_available = status["vector_memory"]

        # Show warning once per session
        if self.vector_enabled and not self._vector_available and not self._vector_warning_shown:
            self.logger.warning_once(
                "Vector memory unavailable (Ollama or agent-memory-mcp not found). "
                "Using file-based memory only.",
                warning_key="_vector_warning_shown"
            )
            self._vector_warning_shown = True

        return status

    def search(
        self,
        query: str,
        scope: str = "auto",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memory with smart scope determination.

        Args:
            query: Search query
            scope: "local", "global", or "auto"
            limit: Maximum results

        Returns:
            List of search results
        """
        # Determine scope
        if scope == "auto":
            scope = self._determine_search_scope(query)

        # Local search (always available)
        results = self._search_local(query, limit)

        # Global search if needed
        if scope == "global" or (scope == "auto" and len(results) < 3):
            if self._vector_available:
                results.extend(self._search_vector(query, limit))
            else:
                self.logger.debug("Vector memory unavailable, using local search only")

        return results[:limit]

    def _determine_search_scope(self, query: str) -> str:
        """Determine search scope based on query content.

        Args:
            query: Search query

        Returns:
            "local" or "global"
        """
        # Explicit markers
        global_markers = ["вообще", "везде", "в других проектах", "во всех", "best practice"]
        local_markers = ["здесь", "в этом проекте", "локально", "у нас", "наш код", "наша база"]

        query_lower = query.lower()

        if any(marker in query_lower for marker in global_markers):
            return "global"
        if any(marker in query_lower for marker in local_markers):
            return "local"

        # Intent classification
        fix_keywords = ["как исправить", "как решить", "как устранить", "оптимальный подход"]
        find_keywords = ["где находится", "как мы делали", "найти в коде"]

        if any(kw in query_lower for kw in fix_keywords):
            return "global"
        if any(kw in query_lower for kw in find_keywords):
            return "local"

        # Default: local first, fall back to global if <3 results
        return "auto"

    def _search_local(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search local file-based memory.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        results = []
        query_lower = query.lower()

        # Search in lessons.md
        if self.lessons_file.exists():
            results.extend(self._search_headers(self.lessons_file, query_lower, "lessons", limit))

        # Search in patterns.md
        if self.patterns_file.exists():
            results.extend(self._search_headers(self.patterns_file, query_lower, "patterns", limit))

        return results[:limit]

    def _search_headers(self, file_path: Path, query: str, source: str, limit: int) -> List[Dict[str, Any]]:
        """Search headers in markdown file.

        Args:
            file_path: Path to markdown file
            query: Search query
            source: Source name for results
            limit: Maximum results

        Returns:
            List of matching headers
        """
        results = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line in lines:
                if line.startswith("## "):
                    # Extract header text
                    header_text = line[3:].strip()
                    if query in header_text.lower():
                        results.append({
                            "source": source,
                            "file": str(file_path.relative_to(self.memory_root)),
                            "header": header_text,
                            "type": "file_memory"
                        })
                        if len(results) >= limit:
                            break
        except Exception as e:
            self.logger.error(f"Error searching headers in {file_path}: {e}")

        return results

    def _search_vector(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search vector memory (if available).

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        if not self._vector_available:
            return []

        # TODO: Implement vector search via agent-memory-mcp
        # For now, return empty results
        return []

    def save_memory(
        self,
        content: str,
        memory_type: str = "log",
        importance: float = 0.5
    ) -> bool:
        """Save content to appropriate memory file based on AI classification.

        Args:
            content: Content to save
            memory_type: "lesson", "pattern", "architecture", or "log"
            importance: Importance score (0.0-1.0) for routing

        Returns:
            True if saved successfully
        """
        try:
            if memory_type == "lesson":
                target_file = self.lessons_file
            elif memory_type == "pattern":
                target_file = self.patterns_file
            elif memory_type == "architecture" or importance > 0.7:
                target_file = self.architecture_file
            else:
                target_file = self.projects_log_file

            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Append to file
            with open(target_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n{content}")

            self.logger.info(f"Saved to {target_file.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving memory: {e}")
            return False

    def get_headers_first(self, limit: int = 10) -> Dict[str, List[str]]:
        """Get headers from all memory files (headers-first reading).

        Args:
            limit: Maximum headers per file

        Returns:
            Dict mapping file names to header lists
        """
        result = {}

        files = [
            ("lessons", self.lessons_file),
            ("patterns", self.patterns_file),
            ("architecture", self.architecture_file),
        ]

        for name, file_path in files:
            if file_path.exists():
                headers = self._extract_headers(file_path, limit)
                result[name] = headers

        return result

    def _extract_headers(self, file_path: Path, limit: int) -> List[str]:
        """Extract headers from markdown file.

        Args:
            file_path: Path to file
            limit: Maximum headers to extract

        Returns:
            List of header lines
        """
        headers = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line in lines:
                if line.startswith("## "):
                    headers.append(line)
                    if len(headers) >= limit:
                        break

        except Exception as e:
            self.logger.error(f"Error extracting headers from {file_path}: {e}")

        return headers
