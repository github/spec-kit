"""
agent-memory-mcp client wrapper.

Interfaces with agent-memory-mcp CLI for vector memory operations.
"""

import subprocess
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..logging import get_logger


class AgentMemoryClient:
    """Client for agent-memory-mcp CLI."""

    # Memory types from agent-memory-mcp
    MEMORY_TYPES = {
        "semantic": "Semantic memory (facts, concepts)",
        "procedural": "Procedural memory (skills, how-to)",
        "episodic": "Episodic memory (events, experiences)",
        "working": "Working memory (temporary, session)"
    }

    def __init__(self, binary_path: Optional[str] = None):
        """Initialize agent-memory-mcp client.

        Args:
            binary_path: Path to agent-memory-mcp binary (default: search in PATH)
        """
        self.logger = get_logger()
        self.binary = binary_path or "agent-memory-mcp"

    def is_available(self) -> bool:
        """Check if agent-memory-mcp is installed.

        Returns:
            True if binary is available
        """
        try:
            result = subprocess.run(
                [self.binary, "--help"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def store(
        self,
        content: str,
        memory_type: str = "semantic",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store content in vector memory.

        Args:
            content: Content to store
            memory_type: Type of memory (semantic, procedural, episodic, working)
            tags: Optional list of tags
            metadata: Optional metadata dict

        Returns:
            True if successful
        """
        if not content or not content.strip():
            return False

        if memory_type not in self.MEMORY_TYPES:
            self.logger.warning(f"Invalid memory type: {memory_type}")
            return False

        try:
            cmd = [self.binary, "store",
                   "-content", content,
                   "-type", memory_type]

            if tags:
                cmd.extend(["-tags", ",".join(tags)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30
            )

            if result.returncode != 0:
                self.logger.warning(f"Store failed: {result.stderr.decode()}")
                return False

            return True

        except subprocess.TimeoutExpired:
            self.logger.warning("Store timeout")
            return False
        except Exception as e:
            self.logger.warning(f"Store error: {e}")
            return False

    def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Recall memories matching query.

        Args:
            query: Search query
            limit: Maximum results
            memory_type: Filter by memory type

        Returns:
            List of memory entries
        """
        try:
            cmd = [self.binary, "recall", query]

            if memory_type:
                cmd.extend(["-type", memory_type])

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                text=True
            )

            if result.returncode != 0:
                return []

            # Parse output
            return self._parse_recall_output(result.stdout, limit)

        except Exception as e:
            self.logger.warning(f"Recall error: {e}")
            return []

    def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching memories
        """
        try:
            cmd = [self.binary, "search", query]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                text=True
            )

            if result.returncode != 0:
                return []

            return self._parse_search_output(result.stdout, limit)

        except Exception as e:
            self.logger.warning(f"Search error: {e}")
            return []

    def list_memories(
        self,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List stored memories.

        Args:
            memory_type: Filter by memory type

        Returns:
            List of memory entries
        """
        try:
            cmd = [self.binary, "list"]

            if memory_type:
                cmd.extend(["-type", memory_type])

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                text=True
            )

            if result.returncode != 0:
                return []

            return self._parse_list_output(result.stdout)

        except Exception as e:
            self.logger.warning(f"List error: {e}")
            return []

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get memory statistics.

        Returns:
            Statistics dict or None
        """
        try:
            result = subprocess.run(
                [self.binary, "stats", "-json"],
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            return json.loads(result.stdout.decode())

        except Exception:
            return None

    def _parse_recall_output(
        self,
        output: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Parse recall command output.

        Args:
            output: Command output
            limit: Max results

        Returns:
            Parsed entries
        """
        # Simple parsing - assumes text output
        entries = []

        for line in output.strip().split('\n')[:limit]:
            if line.strip():
                entries.append({
                    "content": line.strip(),
                    "type": "unknown"
                })

        return entries

    def _parse_search_output(
        self,
        output: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Parse search command output.

        Args:
            output: Command output
            limit: Max results

        Returns:
            Parsed entries with scores
        """
        entries = []

        for line in output.strip().split('\n')[:limit]:
            if line.strip():
                entries.append({
                    "content": line.strip(),
                    "score": 1.0  # Default score if not parsed
                })

        return entries

    def _parse_list_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse list command output.

        Args:
            output: Command output

        Returns:
            Parsed entries
        """
        entries = []

        for line in output.strip().split('\n'):
            if line.strip():
                entries.append({
                    "content": line.strip()
                })

        return entries

    def get_status(self) -> Dict[str, Any]:
        """Get client status.

        Returns:
            Status dict
        """
        return {
            "available": self.is_available(),
            "binary": self.binary,
            "memory_types": list(self.MEMORY_TYPES.keys())
        }
