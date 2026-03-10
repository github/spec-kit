"""
Auto-Improvement System - Error → Pattern → Rule workflow.

Tracks errors and promotes patterns to lessons after 3 repeats.
"""

import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from ..logging import get_logger
from ..file_manager import FileMemoryManager


class AutoImprovementSystem:
    """Auto-improvement system for agents.

    Workflow:
    1. Error occurs → Record in patterns.md
    2. 3 repeats → Promote to lessons.md as rule
    3. Weekly review → Consolidate related patterns
    """

    def __init__(self, project_id: str, memory_root: Optional[Path] = None):
        """Initialize auto-improvement system.

        Args:
            project_id: Agent/project identifier
            memory_root: Root directory for memory files
        """
        self.project_id = project_id
        self.logger = get_logger()

        # For agents, memory is in ~/.claude/agents/{name}/memory/
        # For projects, memory is in ~/.claude/memory/projects/{name}/
        if memory_root and (memory_root.name == project_id or "agents" in str(memory_root)):
            # Agent mode: use provided path directly (already has agent name in path)
            self.memory_path = memory_root / "memory" if (memory_root / "memory").exists() else memory_root
        else:
            # Project mode: use FileMemoryManager structure  
            self.file_manager = FileMemoryManager(
                project_id=project_id,
                memory_root=memory_root
            )
            self.memory_path = self.file_manager.memory_root

        # Ensure memory directory exists
        self.memory_path.mkdir(parents=True, exist_ok=True)

    def record_error(
        self,
        error_type: str,
        error_message: str,
        solution: str,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Record error in patterns.md.

        Args:
            error_type: Type of error (e.g., "CORS", "JWT", "Database")
            error_message: Error description
            solution: How to fix it
            context: Additional context (file, function, etc.)
            tags: Search tags

        Returns:
            True if recorded successfully
        """
        self.logger.info(f"=== Recording Error: {error_type} ===")

        # Check if similar pattern exists
        similar = self._find_similar_patterns(error_type, error_message)

        # Increment repeat count or create new pattern
        if similar:
            # Update existing pattern
            new_count = similar["count"] + 1
            self._update_pattern_count(similar["id"], new_count)

            # If 3+ repeats, promote to lessons
            if new_count >= 3:
                self._promote_to_lesson(
                    error_type=error_type,
                    error_message=error_message,
                    solution=solution,
                    repeat_count=new_count
                )
        else:
            # Create new pattern
            self._create_pattern(
                error_type=error_type,
                error_message=error_message,
                solution=solution,
                context=context,
                tags=tags
            )

        return True

    def _find_similar_patterns(
        self,
        error_type: str,
        error_message: str
    ) -> Optional[Dict[str, Any]]:
        """Find similar existing patterns.

        Args:
            error_type: Type of error
            error_message: Error message

        Returns:
            Similar pattern dict or None
        """
        patterns_file = self.memory_path / "patterns.md"

        if not patterns_file.exists():
            return None

        content = patterns_file.read_text(encoding="utf-8")

        # Look for similar error type or message
        # Pattern format: ## Error: {type} - {message} (repeat: {count})
        pattern_re = r"## Error: (.+?) - (.+?) \(repeat: (\d+)\)"

        for match in re.finditer(pattern_re, content):
            p_type, p_msg, p_count = match.groups()
            count = int(p_count)

            # Check similarity
            type_match = error_type.lower() in p_type.lower() or p_type.lower() in error_type.lower()

            if type_match:
                return {
                    "id": match.group(0),
                    "type": p_type,
                    "message": p_msg,
                    "count": count
                }

        return None

    def _update_pattern_count(self, pattern_id: str, new_count: int) -> None:
        """Update repeat count for existing pattern.

        Args:
            pattern_id: Pattern identifier (old text)
            new_count: New repeat count
        """
        patterns_file = self.memory_path / "patterns.md"
        content = patterns_file.read_text(encoding="utf-8")

        # Update count in pattern header
        new_id = pattern_id.replace(
            f"(repeat: {new_count - 1})",
            f"(repeat: {new_count})"
        )

        content = content.replace(pattern_id, new_id)
        patterns_file.write_text(content, encoding="utf-8")

        self.logger.info(f"Updated pattern count: {new_count}")

    def _create_pattern(
        self,
        error_type: str,
        error_message: str,
        solution: str,
        context: Optional[str],
        tags: Optional[List[str]]
    ) -> None:
        """Create new pattern entry.

        Args:
            error_type: Type of error
            error_message: Error message
            solution: Solution description
            context: Additional context
            tags: Search tags
        """
        patterns_file = self.memory_path / "patterns.md"

        # Build pattern entry
        entry = f"\n## Error: {error_type} - {error_message} (repeat: 1)\n\n"
        entry += f"**Solution**: {solution}\n\n"

        if context:
            entry += f"**Context**: {context}\n\n"

        if tags:
            entry += f"**Tags**: {', '.join(tags)}\n\n"

        entry += f"**First Occurred**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        entry += "\n---\n"

        # Append to patterns file
        if patterns_file.exists():
            content = patterns_file.read_text(encoding="utf-8")
            # Insert before the end
            content = content.rstrip() + "\n" + entry
        else:
            content = "# Improvement Patterns\n\n" + entry

        patterns_file.write_text(content, encoding="utf-8")

        self.logger.info(f"Created new pattern: {error_type}")

    def _promote_to_lesson(
        self,
        error_type: str,
        error_message: str,
        solution: str,
        repeat_count: int
    ) -> None:
        """Promote pattern to lesson after 3 repeats.

        Args:
            error_type: Type of error
            error_message: Error message
            solution: Solution
            repeat_count: Number of repeats
        """
        lessons_file = self.memory_path / "lessons.md"

        # Build lesson entry
        title = f"Rule: {error_type}"
        one_liner = f"{error_message} (occurred {repeat_count} times)"

        entry = f"\n## {title}\n\n"
        entry += f"**{one_liner}**\n\n"
        entry += f"### Solution\n{solution}\n\n"
        entry += f"**Promoted**: {datetime.now().strftime('%Y-%m-%d')}\n"
        entry += f"**Repeat Count**: {repeat_count}\n"
        entry += "\n---\n"

        # Append to lessons file
        if lessons_file.exists():
            content = lessons_file.read_text(encoding="utf-8")
            content = content.rstrip() + "\n" + entry
        else:
            content = "# Lessons Learned\n\n" + entry

        lessons_file.write_text(content, encoding="utf-8")

        self.logger.info(f"Promoted to lesson: {title}")

    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of patterns and repeats.

        Returns:
            Dict with pattern statistics
        """
        patterns_file = self.memory_path / "patterns.md"

        if not patterns_file.exists():
            return {
                "total_patterns": 0,
                "ready_for_promotion": [],
                "by_type": {}
            }

        content = patterns_file.read_text(encoding="utf-8")

        # Parse patterns
        pattern_re = r"## Error: (.+?) - (.+?) \(repeat: (\d+)\)"
        patterns = list(re.finditer(pattern_re, content))

        by_type = defaultdict(int)
        ready_for_promotion = []

        for match in patterns:
            p_type, p_msg, p_count = match.groups()
            count = int(p_count)
            by_type[p_type] += 1

            if count >= 3:
                ready_for_promotion.append({
                    "type": p_type,
                    "message": p_msg,
                    "count": count
                })

        return {
            "total_patterns": len(patterns),
            "ready_for_promotion": ready_for_promotion,
            "by_type": dict(by_type)
        }

    def consolidate_patterns(self) -> int:
        """Consolidate related patterns (weekly maintenance).

        Returns:
            Number of consolidations made
        """
        self.logger.info("=== Consolidating Patterns ===")

        summary = self.get_pattern_summary()
        consolidations = 0

        # Find patterns ready for promotion but not yet promoted
        for pattern in summary["ready_for_promotion"]:
            # Check if already promoted
            lessons_file = self.memory_path / "lessons.md"
            if lessons_file.exists():
                content = lessons_file.read_text(encoding="utf-8")
                if pattern["type"] in content:
                    # Already promoted, skip
                    continue

            # Promote now
            self._promote_to_lesson(
                error_type=pattern["type"],
                error_message=pattern["message"],
                solution="_See patterns.md for solution_",
                repeat_count=pattern["count"]
            )
            consolidations += 1

        self.logger.info(f"Consolidated {consolidations} patterns")

        return consolidations
