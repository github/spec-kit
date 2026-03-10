"""
RAG (Retrieval-Augmented Generation) indexer.

Automatically indexes memory files for vector search.
"""

import time
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from threading import Thread, Event

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from ..logging import get_logger
from .ollama_client import OllamaClient
from .agent_memory_client import AgentMemoryClient


class MemoryFileHandler(FileSystemEventHandler):
    """Handler for memory file changes."""

    def __init__(self, indexer: 'RAGIndexer'):
        """Initialize handler.

        Args:
            indexer: RAGIndexer instance
        """
        self.indexer = indexer
        self.logger = get_logger()
        self._last_event = {}
        self._debounce_seconds = 2.0

    def on_modified(self, event):
        """Handle file modification.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Only process .md files
        if not event.src_path.endswith('.md'):
            return

        # Debounce: ignore rapid successive events
        path = event.src_path
        now = time.time()

        if path in self._last_event:
            if now - self._last_event[path] < self._debounce_seconds:
                return

        self._last_event[path] = now

        # Queue for indexing
        self.indexer.queue_indexing(path)


class RAGIndexer:
    """Automatic RAG indexer for memory files."""

    def __init__(
        self,
        project_id: str,
        global_home: Optional[Path] = None,
        auto_index: bool = True
    ):
        """Initialize RAG indexer.

        Args:
            project_id: Project identifier
            global_home: Path to global claude home
            auto_index: Enable automatic file watching
        """
        self.logger = get_logger()
        self.project_id = project_id
        self.global_home = global_home or Path.home() / ".claude"
        self.auto_index = auto_index

        # Memory clients
        self.ollama = OllamaClient()
        self.agent_memory = AgentMemoryClient()

        # Indexing queue
        self._index_queue: List[Path] = []
        self._processing = False
        self._stop_event = Event()

        # File watcher
        self.observer = None

        if auto_index and WATCHDOG_AVAILABLE:
            self._setup_file_watcher()

    def _setup_file_watcher(self) -> None:
        """Setup file system watcher."""
        try:
            memory_path = self.global_home / "memory" / "projects" / self.project_id

            if not memory_path.exists():
                return

            event_handler = MemoryFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                event_handler,
                str(memory_path),
                recursive=False
            )
            self.observer.start()

            self.logger.info(f"File watcher started for {memory_path}")

        except Exception as e:
            self.logger.warning(f"Failed to setup file watcher: {e}")

    def queue_indexing(self, file_path: str) -> None:
        """Queue file for indexing.

        Args:
            file_path: Path to file
        """
        path = Path(file_path)

        if path not in self._index_queue:
            self._index_queue.append(path)

        # Trigger processing
        if not self._processing:
            self._processing = True
            Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self) -> None:
        """Process indexing queue."""
        while self._index_queue and not self._stop_event.is_set():
            path = self._index_queue.pop(0)

            try:
                self._index_file(path)
            except Exception as e:
                self.logger.warning(f"Indexing error for {path}: {e}")

            # Small delay between files
            time.sleep(0.5)

        self._processing = False

    def _index_file(self, file_path: Path) -> bool:
        """Index a single file.

        Args:
            file_path: Path to file

        Returns:
            True if successful
        """
        if not file_path.exists():
            return False

        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return False

        # Determine memory type from file name
        memory_type = self._get_memory_type(file_path.name)

        # Extract sections
        sections = self._extract_sections(content)

        # Index each section
        indexed = 0
        for title, section_content in sections:
            if self._index_section(title, section_content, memory_type):
                indexed += 1

        self.logger.debug(f"Indexed {indexed} sections from {file_path.name}")
        return indexed > 0

    def _get_memory_type(self, filename: str) -> str:
        """Determine memory type from filename.

        Args:
            filename: File name

        Returns:
            Memory type
        """
        mapping = {
            "patterns.md": "procedural",
            "lessons.md": "episodic",
            "architecture.md": "semantic",
            "projects-log.md": "episodic"
        }

        return mapping.get(filename, "semantic")

    def _extract_sections(self, content: str) -> List[tuple[str, str]]:
        """Extract sections from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of (title, content) tuples
        """
        sections = []
        current_title = None
        current_content = []

        for line in content.split('\n'):
            if line.strip().startswith('##'):
                # Save previous section
                if current_title:
                    sections.append((
                        current_title,
                        '\n'.join(current_content).strip()
                    ))

                # Start new section
                current_title = line.strip().replace('##', '').strip()
                current_content = []
            elif current_title:
                current_content.append(line)

        # Don't forget last section
        if current_title:
            sections.append((
                current_title,
                '\n'.join(current_content).strip()
            ))

        return sections

    def _index_section(
        self,
        title: str,
        content: str,
        memory_type: str
    ) -> bool:
        """Index a section in vector memory.

        Args:
            title: Section title
            content: Section content
            memory_type: Memory type

        Returns:
            True if successful
        """
        if not content or len(content.strip()) < 20:
            return False

        # Combine title and content
        full_content = f"{title}\n\n{content}"

        # Store in vector memory
        return self.agent_memory.store(
            content=full_content,
            memory_type=memory_type,
            tags=["indexed", "auto"]
        )

    def index_all(self) -> Dict[str, int]:
        """Index all memory files.

        Returns:
            Dict with file -> section count
        """
        results = {}

        memory_path = self.global_home / "memory" / "projects" / self.project_id

        if not memory_path.exists():
            return results

        # Index each .md file
        for file_path in memory_path.glob("*.md"):
            try:
                sections = self._extract_sections(
                    file_path.read_text(encoding='utf-8')
                )
                results[file_path.name] = len(sections)

                # Index file
                self._index_file(file_path)

            except Exception as e:
                self.logger.warning(f"Error indexing {file_path.name}: {e}")

        return results

    def search(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search indexed memory.

        Args:
            query: Search query
            limit: Max results

        Returns:
            Search results
        """
        return self.agent_memory.search(query, limit)

    def stop(self) -> None:
        """Stop file watcher."""
        self._stop_event.set()

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def __del__(self):
        """Cleanup on deletion."""
        self.stop()
