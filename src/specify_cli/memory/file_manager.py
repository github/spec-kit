"""
File Memory Manager - Manages markdown-based memory files.

Handles reading/writing memory files with one-line summary headers
and headers-first reading for context optimization.
"""

from typing import Optional, List, Dict
from pathlib import Path
import re
from datetime import datetime

from .logging import get_logger


class FileMemoryManager:
    """Manages file-based memory with headers-first reading."""

    def __init__(self, project_id: str, memory_root: Optional[Path] = None):
        """Initialize file memory manager.

        Args:
            project_id: Project identifier
            memory_root: Root directory for memory files
        """
        self.project_id = project_id
        self.logger = get_logger()

        if memory_root is None:
            from .config import MemoryConfigManager
            config = MemoryConfigManager()
            memory_root = config.global_home / "memory" / "projects" / project_id

        self.memory_root = Path(memory_root)
        self.memory_root.mkdir(parents=True, exist_ok=True)

    def read_headers_first(
        self,
        file_type: str = "all",
        limit: int = 10
    ) -> Dict[str, List[str]]:
        """Read only headers from memory files (context optimization).

        Args:
            file_type: "lessons", "patterns", "architecture", or "all"
            limit: Maximum headers per file

        Returns:
            Dict mapping file names to header lists
        """
        result = {}

        if file_type == "all" or file_type == "lessons":
            result["lessons"] = self._extract_headers(
                self.memory_root / "lessons.md", limit
            )

        if file_type == "all" or file_type == "patterns":
            result["patterns"] = self._extract_headers(
                self.memory_root / "patterns.md", limit
            )

        if file_type == "all" or file_type == "architecture":
            result["architecture"] = self._extract_headers(
                self.memory_root / "architecture.md", limit
            )

        return result

    def _extract_headers(self, file_path: Path, limit: int) -> List[str]:
        """Extract headers from markdown file.

        Args:
            file_path: Path to file
            limit: Maximum headers to extract

        Returns:
            List of header lines with one-line summary
        """
        headers = []

        if not file_path.exists():
            return headers

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line in lines:
                if line.startswith("## "):
                    headers.append(line.strip())
                    if len(headers) >= limit:
                        break

        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")

        return headers

    def read_section(self, file_type: str, header_match: str) -> Optional[str]:
        """Read full section content based on header match.

        Args:
            file_type: Type of memory file
            header_match: Text to match in header

        Returns:
            Section content or None
        """
        file_map = {
            "lessons": "lessons.md",
            "patterns": "patterns.md",
            "architecture": "architecture.md",
        }

        if file_type not in file_map:
            return None

        file_path = self.memory_root / file_map[file_type]

        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Find matching header
            start_idx = None
            for i, line in enumerate(lines):
                if line.startswith("## ") and header_match.lower() in line.lower():
                    start_idx = i
                    break

            if start_idx is None:
                return None

            # Find end of section (next header or EOF)
            end_idx = len(lines)
            for i in range(start_idx + 1, len(lines)):
                if lines[i].startswith("## "):
                    end_idx = i
                    break

            return "\n".join(lines[start_idx:end_idx])

        except Exception as e:
            self.logger.error(f"Error reading section from {file_path}: {e}")
            return None

    def write_entry(
        self,
        file_type: str,
        title: str,
        content: str,
        one_liner: Optional[str] = None
    ) -> bool:
        """Write an entry to a memory file with one-line summary header.

        Args:
            file_type: Type of memory file ("lessons", "patterns", etc.)
            title: Entry title
            content: Entry content
            one_liner: One-line summary (appended to title)

        Returns:
            True if written successfully
        """
        file_map = {
            "lesson": "lessons.md",
            "pattern": "patterns.md",
            "architecture": "architecture.md",
            "log": "projects-log.md",
        }

        if file_type not in file_map:
            self.logger.error(f"Unknown file type: {file_type}")
            return False

        file_path = self.memory_root / file_map[file_type]
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if doesn't exist
        if not file_path.exists():
            file_path.write_text("", encoding="utf-8")

        # Format header with one-line summary
        if one_liner:
            header = f"## {title} - {one_liner}"
        else:
            header = f"## {title}"

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Append entry
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n{header}\n")
                f.write(f"> **Date**: {timestamp}\n")
                f.write(f"\n{content}\n")

            self.logger.info(f"Wrote to {file_path.name}: {title}")
            return True

        except Exception as e:
            self.logger.error(f"Error writing to {file_path}: {e}")
            return False

    def initialize_memory_files(self, template_dir: Optional[Path] = None) -> bool:
        """Initialize memory files from templates.

        Args:
            template_dir: Directory containing memory file templates

        Returns:
            True if initialized successfully
        """
        templates = {
            "lessons.md": """# Lessons Learned

> Accumulated lessons and corrections from project development.

## Format
## Error: [Title] - [One-line summary]
### Solution: What was done
### Lesson: What was learned
### Project: {self.project_id}
### Date: {date}
""",
            "patterns.md": """# Patterns and Reusable Solutions

> Repeating patterns and auto-improvement insights.

## Format
## Pattern: [Title] - [One-line summary]
### When to use: Context
### Implementation: Code/approach
### Examples: Where used
""",
            "architecture.md": """# Project Architecture: {self.project_id}

> Architecture and design decisions.

## Format
## [Layer]: [Title] - [Description]
### Component: [Path] - [Purpose]
""",
            "projects-log.md": """# Projects Log

> History of completed tasks and achievements.

## Format
## [Date]: [Task] - [Summary]
### What was done: Brief description
### Result: Outcome
""",
            "handoff.md": """# Session Handoff

> Context for continuing work across sessions.

## Current Topic
{topic}

## Recent Decisions
{decisions}

## Unfinished Tasks
- [ ] {task}
""",
        }

        try:
            for filename, template in templates.items():
                file_path = self.memory_root / filename
                if not file_path.exists():
                    # Apply template variables
                    content = template.format(
                        project_id=self.project_id,
                        date=datetime.now().strftime("%Y-%m-%d"),
                        topic="Starting new session",
                        decisions="No recent decisions",
                        task="Initial setup"
                    )
                    file_path.write_text(content, encoding="utf-8")
                    self.logger.info(f"Initialized {filename}")

            return True

        except Exception as e:
            self.logger.error(f"Error initializing memory files: {e}")
            return False
