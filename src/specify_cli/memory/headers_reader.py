"""
Headers-First reading for context optimization.

Reads only file headers with one-line summaries to minimize context usage.
Target: ~80-120 tokens vs ~2000 tokens for full content (95% savings).
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from collections import OrderedDict

from ..logging import get_logger


class HeadersFirstReader:
    """Implements headers-first reading strategy for context optimization."""

    # Maximum headers to read per file type
    DEFAULT_LIMITS = {
        "lessons": 10,
        "patterns": 10,
        "architecture": 5,
        "projects-log": 5,
        "handoff": 5
    }

    # Pattern to extract one-line summary from header
    ONE_LINER_PATTERN = re.compile(r'^##+\s+(.+?)(?:\s+-\s+(.+))?$')

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize headers-first reader.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.global_home = global_home or Path.home() / ".claude"

    def read_headers(
        self,
        project_id: str,
        file_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """Read headers from memory files.

        Args:
            project_id: Project identifier
            file_types: List of file types to read (default: all)
            limit: Max headers per file type (default: from DEFAULT_LIMITS)

        Returns:
            Dict mapping file_type to list of headers:
            {
                "lessons": [
                    {"title": "Error: JWT", "summary": "expire через 15 мин"},
                    ...
                ],
                "patterns": [...],
                ...
            }
        """
        if file_types is None:
            file_types = ["lessons", "patterns", "architecture", "projects-log", "handoff"]

        result = {}

        for file_type in file_types:
            file_limit = limit or self.DEFAULT_LIMITS.get(file_type, 10)
            headers = self._read_headers_from_file(project_id, file_type, file_limit)
            result[file_type] = headers

        return result

    def _read_headers_from_file(
        self,
        project_id: str,
        file_type: str,
        limit: int
    ) -> List[Dict[str, str]]:
        """Read headers from a single file.

        Args:
            project_id: Project identifier
            file_type: Type of memory file
            limit: Maximum headers to read

        Returns:
            List of header dicts with 'title' and 'summary'
        """
        # Determine file path
        if project_id == ".global":
            file_path = self.global_home / "memory" / "projects" / ".global" / f"{self._get_filename(file_type)}"
        else:
            file_path = self.global_home / "memory" / "projects" / project_id / f"{self._get_filename(file_type)}"

        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding='utf-8')
            return self._extract_headers(content, limit)

        except Exception as e:
            self.logger.warning(f"Error reading headers from {file_path}: {e}")
            return []

    def _extract_headers(
        self,
        content: str,
        limit: int
    ) -> List[Dict[str, str]]:
        """Extract headers from markdown content.

        Args:
            content: Markdown content
            limit: Maximum headers to extract

        Returns:
            List of header dicts
        """
        headers = []

        for line in content.split('\n'):
            if len(headers) >= limit:
                break

            # Match markdown headers (## or ###)
            match = self.ONE_LINER_PATTERN.match(line.strip())

            if match:
                title = match.group(1).strip()
                summary = match.group(2).strip() if match.group(2) else ""

                headers.append({
                    "title": title,
                    "summary": summary
                })

        return headers

    def read_section(
        self,
        project_id: str,
        file_type: str,
        header_match: str
    ) -> Optional[str]:
        """Read full section content for a specific header.

        Args:
            project_id: Project identifier
            file_type: Type of memory file
            header_match: Header title to match (partial match OK)

        Returns:
            Section content or None if not found
        """
        file_path = self._get_file_path(project_id, file_type)

        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            return self._extract_section(content, header_match)

        except Exception as e:
            self.logger.warning(f"Error reading section from {file_path}: {e}")
            return None

    def _extract_section(
        self,
        content: str,
        header_match: str
    ) -> Optional[str]:
        """Extract section content between matching headers.

        Args:
            content: Full markdown content
            header_match: Header title to find

        Returns:
            Section content or None
        """
        lines = content.split('\n')
        section_lines = []
        capturing = False

        for i, line in enumerate(lines):
            # Check if this is our target header
            if header_match.lower() in line.lower() and line.strip().startswith('#'):
                capturing = True
                section_lines = [line]
                continue

            # If capturing and hit next header, stop
            if capturing and line.strip().startswith('#') and len(section_lines) > 1:
                break

            # Capture content
            if capturing:
                section_lines.append(line)

        return '\n'.join(section_lines) if section_lines else None

    def format_headers_context(
        self,
        headers: Dict[str, List[Dict[str, str]]],
        format: str = "compact"
    ) -> str:
        """Format headers into context string.

        Args:
            headers: Headers dict from read_headers()
            format: "compact" or "detailed"

        Returns:
            Formatted context string
        """
        if format == "compact":
            return self._format_compact(headers)
        else:
            return self._format_detailed(headers)

    def _format_compact(self, headers: Dict[str, List[Dict[str, str]]]) -> str:
        """Format headers in compact format (~80-120 tokens)."""
        lines = []

        for file_type, items in headers.items():
            if items:
                lines.append(f"## {file_type.title()} ({len(items)} items)")

                for item in items[:5]:  # Max 5 per type in compact
                    if item.get("summary"):
                        lines.append(f"- {item['title']}: {item['summary']}")
                    else:
                        lines.append(f"- {item['title']}")

        return '\n'.join(lines)

    def _format_detailed(self, headers: Dict[str, List[Dict[str, str]]]) -> str:
        """Format headers in detailed format."""
        lines = []

        for file_type, items in headers.items():
            if items:
                lines.append(f"## {file_type.title()}")

                for item in items:
                    if item.get("summary"):
                        lines.append(f"### {item['title']}")
                        lines.append(f"{item['summary']}")
                    else:
                        lines.append(f"### {item['title']}")

                lines.append("")  # Blank line between sections

        return '\n'.join(lines)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def _get_file_path(self, project_id: str, file_type: str) -> Path:
        """Get file path for memory file.

        Args:
            project_id: Project identifier
            file_type: Type of memory file

        Returns:
            Path to file
        """
        filename = self._get_filename(file_type)

        if project_id == ".global":
            return self.global_home / "memory" / "projects" / ".global" / filename
        else:
            return self.global_home / "memory" / "projects" / project_id / filename

    def _get_filename(self, file_type: str) -> str:
        """Get filename for file type.

        Args:
            file_type: Type of memory file

        Returns:
            Filename
        """
        filenames = {
            "lessons": "lessons.md",
            "patterns": "patterns.md",
            "architecture": "architecture.md",
            "projects-log": "projects-log.md",
            "handoff": "handoff.md"
        }

        return filenames.get(file_type, f"{file_type}.md")


class ContextOptimizer:
    """Optimizes context usage using headers-first reading."""

    def __init__(self, global_home: Optional[Path] = None):
        """Initialize context optimizer.

        Args:
            global_home: Path to global claude home
        """
        self.logger = get_logger()
        self.reader = HeadersFirstReader(global_home)

    def get_before_task_context(
        self,
        project_id: str,
        token_budget: int = 100
    ) -> Dict[str, any]:
        """Get context before task (headers only, minimal tokens).

        Args:
            project_id: Project identifier
            token_budget: Target token budget (default: 100)

        Returns:
            Context dict with headers and token count
        """
        # Read headers from all files
        headers = self.reader.read_headers(project_id)

        # Format compactly
        context = self.reader.format_headers_context(headers, format="compact")

        # Estimate tokens
        estimated = self.reader.estimate_tokens(context)

        return {
            "context": context,
            "estimated_tokens": estimated,
            "headers": headers,
            "within_budget": estimated <= token_budget
        }

    def get_deep_dive_context(
        self,
        project_id: str,
        file_type: str,
        header_match: str
    ) -> str:
        """Get deep dive context for specific section.

        Args:
            project_id: Project identifier
            file_type: Type of memory file
            header_match: Header to match

        Returns:
            Full section content
        """
        return self.reader.read_section(project_id, file_type, header_match) or ""
