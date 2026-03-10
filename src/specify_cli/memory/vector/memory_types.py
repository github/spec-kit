"""
Four-level memory system implementation.

Level 1: Contextual (session-only)
Level 2: File-based (markdown)
Level 3: Vector-based (agent-memory-mcp + Ollama)
Level 4: Identity (AGENTS.md, SOUL.md, USER.md, MEMORY.md)
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import json

from ..logging import get_logger
from ..file_manager import FileMemoryManager
from .ollama_client import OllamaClient
from .agent_memory_client import AgentMemoryClient


class FourLevelMemory:
    """Implements the four-level memory hierarchy."""

    def __init__(
        self,
        project_id: str,
        global_home: Optional[Path] = None,
        enable_vector: bool = True
    ):
        """Initialize four-level memory system.

        Args:
            project_id: Current project identifier
            global_home: Path to global claude home
            enable_vector: Enable vector memory (Level 3)
        """
        self.logger = get_logger()
        self.project_id = project_id
        self.global_home = global_home or Path.home() / ".claude"

        # Level 2: File-based memory
        self.file_memory = FileMemoryManager(global_home=self.global_home)

        # Level 3: Vector memory (optional)
        self.enable_vector = enable_vector
        self.vector_client = None
        self.ollama_client = None

        if enable_vector:
            self.vector_client = AgentMemoryClient()
            self.ollama_client = OllamaClient()

        # Level 1: Session context (in-memory)
        self.session_context: Dict[str, Any] = {}

        # Level 4: Identity files
        self.identity_dir = self.global_home / "memory" / "projects" / ".global" / "identity"

    def store(
        self,
        content: str,
        level: str = "auto",
        memory_type: str = "semantic",
        tags: Optional[List[str]] = None,
        one_liner: Optional[str] = None
    ) -> bool:
        """Store content in appropriate memory level(s).

        Args:
            content: Content to store
            level: Memory level (1=session, 2=file, 3=vector, 4=identity, auto)
            memory_type: Type for vector memory
            tags: Optional tags
            one_liner: One-line summary for file memory

        Returns:
            True if successful
        """
        if not content or not content.strip():
            return False

        success = True

        # Level 1: Session context (always store)
        self._store_session(content)

        # Level 2: File-based memory
        if level in ["auto", "2", "file"]:
            file_type = self._determine_file_type(content, memory_type)
            self.file_memory.write_entry(
                file_type=file_type,
                title=self._extract_title(content),
                content=content,
                one_liner=one_liner
            )

        # Level 3: Vector memory
        if level in ["auto", "3", "vector"] and self.enable_vector:
            if self.vector_client and self.vector_client.is_available():
                success &= self.vector_client.store(
                    content=content,
                    memory_type=memory_type,
                    tags=tags
                )

        # Level 4: Identity (rare, manual)
        if level == "4" or level == "identity":
            self._store_identity(content, tags)

        return success

    def retrieve(
        self,
        query: str,
        levels: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve from memory levels.

        Args:
            query: Search query
            levels: Levels to search (default: all)
            limit: Results per level

        Returns:
            Dict mapping level to results
        """
        if levels is None:
            levels = ["1", "2", "3"]

        results = {}

        # Level 1: Session context
        if "1" in levels:
            results["session"] = self._search_session(query)

        # Level 2: File-based memory
        if "2" in levels:
            results["file"] = self._search_file_memory(query, limit)

        # Level 3: Vector memory
        if "3" in levels and self.enable_vector:
            if self.vector_client and self.vector_client.is_available():
                results["vector"] = self.vector_client.search(query, limit)

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get status of all memory levels.

        Returns:
            Status dict for each level
        """
        return {
            "level1_session": {
                "enabled": True,
                "entries": len(self.session_context)
            },
            "level2_file": {
                "enabled": True,
                "path": str(self.global_home / "memory" / "projects" / self.project_id)
            },
            "level3_vector": {
                "enabled": self.enable_vector,
                "agent_memory": self.vector_client.get_status() if self.vector_client else None,
                "ollama": self.ollama_client.get_status() if self.ollama_client else None
            },
            "level4_identity": {
                "enabled": True,
                "path": str(self.identity_dir)
            }
        }

    # Level 1: Session Context

    def _store_session(self, content: str) -> None:
        """Store in session context.

        Args:
            content: Content to store
        """
        timestamp = datetime.now().isoformat()
        self.session_context[timestamp] = {
            "content": content,
            "timestamp": timestamp
        }

        # Keep only last 100 entries
        if len(self.session_context) > 100:
            oldest = sorted(self.session_context.keys())[0]
            del self.session_context[oldest]

    def _search_session(self, query: str) -> List[Dict[str, Any]]:
        """Search session context.

        Args:
            query: Search query

        Returns:
            Matching entries
        """
        query_lower = query.lower()
        results = []

        for timestamp, entry in self.session_context.items():
            if query_lower in entry["content"].lower():
                results.append({
                    **entry,
                    "level": "session",
                    "timestamp": timestamp
                })

        return results[:10]

    # Level 2: File-based Memory

    def _determine_file_type(self, content: str, memory_type: str) -> str:
        """Determine which file type to use.

        Args:
            content: Content
            memory_type: Vector memory type

        Returns:
            File type (lessons, patterns, architecture, etc.)
        """
        # Map vector types to file types
        type_mapping = {
            "procedural": "patterns",
            "episodic": "lessons",
            "semantic": "architecture"
        }

        return type_mapping.get(memory_type, "lessons")

    def _extract_title(self, content: str) -> str:
        """Extract title from content.

        Args:
            content: Content

        Returns:
            Title string
        """
        lines = content.strip().split('\n')
        if lines:
            # First line, truncated
            return lines[0][:50]
        return "Untitled"

    def _search_file_memory(
        self,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search file-based memory.

        Args:
            query: Search query
            limit: Max results

        Returns:
            Matching entries
        """
        results = []

        # Search in each file type
        file_types = ["lessons", "patterns", "architecture"]

        for file_type in file_types:
            headers = self.file_memory.read_headers_first(
                file_type=file_type,
                limit=limit
            )

            for header in headers:
                query_lower = query.lower()
                title = header.get("title", "").lower()
                summary = header.get("summary", "").lower()

                if query_lower in title or query_lower in summary:
                    results.append({
                        "title": header["title"],
                        "summary": header["summary"],
                        "file_type": file_type,
                        "level": "file"
                    })

        return results[:limit]

    # Level 4: Identity

    def _store_identity(
        self,
        content: str,
        tags: Optional[List[str]] = None
    ) -> None:
        """Store in identity memory.

        Args:
            content: Content
            tags: Tags to determine which identity file
        """
        self.identity_dir.mkdir(parents=True, exist_ok=True)

        # Determine which identity file
        if tags and "agent" in tags:
            file_path = self.identity_dir / "AGENTS.md"
        elif tags and "user" in tags:
            file_path = self.identity_dir / "USER.md"
        else:
            file_path = self.identity_dir / "MEMORY.md"

        # Append
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"{content}\n")
