"""
Auto Handoff System - Weekly session analysis and context preservation.

Creates memory/handoff.md for context recovery between sessions.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

from ..logging import get_logger
from ..file_manager import FileMemoryManager
from ..headers_reader import HeadersFirstReader


class AutoHandoffSystem:
    """Auto handoff system for session context preservation.

    Analyzes recent activity and creates handoff.md for:
    - Active tasks
    - Blocked issues
    - Next session focus
    - Context restoration
    """

    def __init__(self, project_id: str, memory_root: Optional[Path] = None):
        """Initialize auto handoff system.

        Args:
            project_id: Agent/project identifier
            memory_root: Root directory for memory files
        """
        self.project_id = project_id
        self.logger = get_logger()

        # For agents, memory is in ~/.claude/agents/{name}/memory/
        if memory_root and memory_root.name == project_id:
            # Agent mode: memory is in agent_name/memory/
            self.memory_path = memory_root / "memory"
            self.file_manager = None
        elif memory_root and "agents" in str(memory_root):
            # Also in agents directory
            self.memory_path = memory_root / "memory" if (memory_root / "memory").exists() else memory_root
            self.file_manager = None
        else:
            # Project mode: use FileMemoryManager structure  
            self.file_manager = FileMemoryManager(
                project_id=project_id,
                memory_root=memory_root
            )
            self.memory_path = self.file_manager.memory_root

        # Ensure memory directory exists
        self.memory_path.mkdir(parents=True, exist_ok=True)

        self.headers_reader = HeadersFirstReader(
            global_home=memory_root or Path.home() / ".claude"
        )

    def create_handoff(
        self,
        active_tasks: Optional[List[Dict[str, Any]]] = None,
        blocked_issues: Optional[List[Dict[str, Any]]] = None,
        notes: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """Create handoff file with current session context.

        Args:
            active_tasks: List of active tasks (default: read from projects-log.md)
            blocked_issues: List of blocked issues
            notes: Additional session notes
            force: Force creation even if recent handoff exists

        Returns:
            True if handoff created successfully
        """
        self.logger.info("=== Creating Session Handoff ===")

        handoff_file = self.memory_path / "handoff.md"

        # Check if recent handoff exists (within 24 hours)
        if not force and handoff_file.exists():
            content = handoff_file.read_text(encoding="utf-8")
            if "Last Updated:" in content:
                # Extract date
                for line in content.split("\n"):
                    if "**Last Updated**:" in line:
                        try:
                            date_str = line.split(":**", 1)[1].strip()
                            last_date = datetime.fromisoformat(date_str)
                            if datetime.now() - last_date < timedelta(hours=24):
                                self.logger.info("Recent handoff exists (<24h), skipping")
                                return True
                        except:
                            pass

        # Build handoff content
        content = self._build_handoff_content(
            active_tasks=active_tasks,
            blocked_issues=blocked_issues,
            notes=notes
        )

        # Write handoff
        handoff_file.write_text(content, encoding="utf-8")

        self.logger.info(f"Handoff created: {handoff_file}")

        return True

    def restore_context(self) -> Dict[str, Any]:
        """Restore context from handoff file.

        Returns:
            Dict with restored context data
        """
        handoff_file = self.memory_path / "handoff.md"

        if not handoff_file.exists():
            self.logger.warning("No handoff file found")
            return {
                "active_tasks": [],
                "blocked_issues": [],
                "last_session": None,
                "next_focus": "No previous context found"
            }

        content = handoff_file.read_text(encoding="utf-8")

        # Parse handoff
        context = {
            "active_tasks": self._extract_tasks(content),
            "blocked_issues": self._extract_issues(content),
            "last_session": self._extract_date(content),
            "next_focus": self._extract_focus(content)
        }

        self.logger.info(f"Restored context from {context['last_session']}")

        return context

    def _build_handoff_content(
        self,
        active_tasks: Optional[List[Dict[str, Any]]],
        blocked_issues: Optional[List[Dict[str, Any]]],
        notes: Optional[str]
    ) -> str:
        """Build handoff file content.

        Args:
            active_tasks: Active tasks list
            blocked_issues: Blocked issues list
            notes: Session notes

        Returns:
            Handoff markdown content
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Get active tasks from projects-log if not provided
        if active_tasks is None:
            active_tasks = self._get_recent_tasks(limit=5)

        # Get blocked issues from patterns if not provided
        if blocked_issues is None:
            blocked_issues = self._get_blocked_issues()

        content = f"""# Session Handoff

**Last Updated**: {now}
**Project**: {self.project_id}

---

## Session Summary

**Date**: {datetime.now().strftime("%Y-%m-%d")}
**Time**: {datetime.now().strftime("%H:%M")}

---

## Active Tasks

"""

        if active_tasks:
            for i, task in enumerate(active_tasks, 1):
                title = task.get("title", "Unnamed task")
                status = task.get("status", "in_progress")
                desc = task.get("description", "")

                content += f"{i}. **{title}** ({status})\n"
                if desc:
                    content += f"   {desc}\n"
                content += "\n"
        else:
            content += "_No active tasks recorded_\n\n"

        content += "---\n\n## Blocked Issues\n\n"

        if blocked_issues:
            for i, issue in enumerate(blocked_issues, 1):
                issue_type = issue.get("type", "Unknown")
                description = issue.get("description", "")

                content += f"{i}. **{issue_type}**\n"
                content += f"   {description}\n\n"
        else:
            content += "_No blocked issues_\n\n"

        content += "---\n\n## Next Session Focus\n\n"

        # Determine focus based on active tasks and blocks
        if blocked_issues:
            content += "**Priority**: Resolve blocked issues\n\n"
            for issue in blocked_issues[:2]:
                content += f"- {issue.get('type', 'Unknown')}: {issue.get('description', '')[:50]}...\n"
        elif active_tasks:
            content += "**Priority**: Continue active tasks\n\n"
            for task in active_tasks[:2]:
                content += f"- {task.get('title', 'Unnamed')}: {task.get('description', '')[:50]}...\n"
        else:
            content += "_No specific focus defined_\n"

        content += "\n---\n\n## Quick Context (Headers-First)\n\n"

        # Add headers from recent memory files
        headers = self.headers_reader.read_all_headers(project_id=self.project_id, limit=5)

        if headers.get("lessons"):
            content += "### Recent Lessons\n"
            for header in headers["lessons"][:3]:
                content += f"- {header}\n"

        if headers.get("patterns"):
            content += "\n### Active Patterns\n"
            for header in headers["patterns"][:3]:
                content += f"- {header}\n"

        if notes:
            content += "\n---\n\n## Session Notes\n\n"
            content += notes + "\n"

        content += "\n---\n\n## Memory Access\n\n"
        content += "Full context available in:\n"
        content += f"- `memory/lessons.md` - {self._count_entries('lessons')} entries\n"
        content += f"- `memory/patterns.md` - {self._count_entries('patterns')} entries\n"
        content += f"- `memory/projects-log.md` - {self._count_entries('projects-log')} entries\n"

        return content

    def _get_recent_tasks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent tasks from projects-log.

        Args:
            limit: Max tasks to return

        Returns:
            List of recent tasks
        """
        log_file = self.memory_path / "projects-log.md"

        if not log_file.exists():
            return []

        content = log_file.read_text(encoding="utf-8")

        # Parse recent tasks (simple format: ## Task - date)
        tasks = []
        for line in content.split("\n"):
            if line.startswith("## "):
                # Extract task info
                parts = line[3:].strip().split(" - ", 1)
                if len(parts) == 2:
                    title, date = parts
                    tasks.append({
                        "title": title.strip(),
                        "date": date.strip(),
                        "status": "in_progress",
                        "description": ""
                    })
                elif len(parts) == 1:
                    tasks.append({
                        "title": parts[0].strip(),
                        "status": "in_progress",
                        "description": ""
                    })

                if len(tasks) >= limit:
                    break

        return tasks

    def _get_blocked_issues(self) -> List[Dict[str, Any]]:
        """Get blocked issues from patterns.

        Returns:
            List of blocked issues
        """
        patterns_file = self.memory_path / "patterns.md"

        if not patterns_file.exists():
            return []

        content = patterns_file.read_text(encoding="utf-8")

        issues = []
        for line in content.split("\n"):
            if line.startswith("## Error:"):
                # Extract error type
                error_text = line[8:].split("(")[0].strip()
                issues.append({
                    "type": error_text.split("-")[0].strip(),
                    "description": error_text
                })

        return issues[:5]  # Limit to top 5

    def _extract_tasks(self, content: str) -> List[Dict[str, Any]]:
        """Extract tasks from handoff content.

        Args:
            content: Handoff file content

        Returns:
            List of tasks
        """
        tasks = []
        in_active_section = False

        for line in content.split("\n"):
            if "## Active Tasks" in line:
                in_active_section = True
                continue
            if in_active_section and line.startswith("---"):
                break
            if in_active_section and line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                # Parse task line: "1. **Title** (status)"
                title_match = line.split("**")[1].split("**")[0] if "**" in line else "Unknown"
                status_match = line.split("(")[1].split(")")[0] if "(" in line else "unknown"

                tasks.append({
                    "title": title_match.strip(),
                    "status": status_match.strip()
                })

        return tasks

    def _extract_issues(self, content: str) -> List[Dict[str, Any]]:
        """Extract blocked issues from handoff content.

        Args:
            content: Handoff file content

        Returns:
            List of issues
        """
        issues = []
        in_blocked_section = False

        for line in content.split("\n"):
            if "## Blocked Issues" in line:
                in_blocked_section = True
                continue
            if in_blocked_section and line.startswith("---"):
                break
            if in_blocked_section and line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                # Parse issue line: "1. **Type**"
                if "**" in line:
                    issue_type = line.split("**")[1].split("**")[0]
                    issues.append({"type": issue_type.strip()})

        return issues

    def _extract_date(self, content: str) -> Optional[str]:
        """Extract last session date from handoff.

        Args:
            content: Handoff content

        Returns:
            Date string or None
        """
        for line in content.split("\n"):
            if "**Date**:" in line or "**Last Updated**:" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
        return None

    def _extract_focus(self, content: str) -> str:
        """Extract next session focus from handoff.

        Args:
            content: Handoff content

        Returns:
            Focus description
        """
        in_focus_section = False
        focus_lines = []

        for line in content.split("\n"):
            if "## Next Session Focus" in line:
                in_focus_section = True
                continue
            if in_focus_section and line.startswith("---"):
                break
            if in_focus_section and line.strip() and not line.startswith("#"):
                focus_lines.append(line.strip())

        return "\n".join(focus_lines) if focus_lines else "No specific focus"

    def _count_entries(self, file_type: str) -> int:
        """Count entries in memory file.

        Args:
            file_type: Type of memory file

        Returns:
            Number of entries
        """
        mem_file = self.memory_path / f"{file_type}.md"

        if not mem_file.exists():
            return 0

        content = mem_file.read_text(encoding="utf-8")
        return content.count("## ") - 1  # Subtract title
