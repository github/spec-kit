"""
Auto-save trigger for memory accumulation.

Automatically saves context after significant events.
"""

import atexit
import threading
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime
from collections import deque

from ..logging import get_logger
from .file_manager import FileMemoryManager
from .classifier import AIImportanceClassifier


class AutoSaveTrigger:
    """Automatically saves memory after significant events."""

    def __init__(
        self,
        project_id: str,
        global_home: Optional[Path] = None,
        enabled: bool = True
    ):
        """Initialize auto-save trigger.

        Args:
            project_id: Current project identifier
            global_home: Path to global claude home
            enabled: Whether auto-save is enabled
        """
        self.logger = get_logger()
        self.project_id = project_id
        self.global_home = global_home or Path.home() / ".claude"
        self.enabled = enabled

        self.file_manager = FileMemoryManager(global_home=self.global_home)
        self.classifier = AIImportanceClassifier()

        # Event tracking
        self._events = deque(maxlen=100)
        self._lock = threading.Lock()

        # Register cleanup on exit
        atexit.register(self._cleanup)

    def track_event(
        self,
        event_type: str,
        data: dict[str, Any],
        auto_save: bool = False
    ) -> str:
        """Track an event for potential auto-save.

        Args:
            event_type: Type of event (e.g., "task_complete", "error_fixed")
            data: Event data
            auto_save: Whether to immediately save to memory

        Returns:
            Event ID
        """
        import uuid

        event_id = str(uuid.uuid4())[:8]

        event = {
            "id": event_id,
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        with self._lock:
            self._events.append(event)

        # Auto-save if requested
        if auto_save and self.enabled:
            self._save_event_to_memory(event)

        return event_id

    def task_completed(
        self,
        task_name: str,
        success: bool,
        lessons: Optional[str] = None
    ) -> str:
        """Track task completion.

        Args:
            task_name: Name of completed task
            success: Whether task was successful
            lessons: Lessons learned (optional)

        Returns:
            Event ID
        """
        return self.track_event(
            "task_complete",
            {
                "task": task_name,
                "success": success,
                "lessons": lessons
            },
            auto_save=lessons is not None
        )

    def error_fixed(
        self,
        error: str,
        solution: str,
        context: Optional[str] = None
    ) -> str:
        """Track error fix.

        Args:
            error: Error description
            solution: How it was fixed
            context: Additional context

        Returns:
            Event ID
        """
        return self.track_event(
            "error_fixed",
            {
                "error": error,
                "solution": solution,
                "context": context
            },
            auto_save=True
        )

    def pattern_discovered(
        self,
        pattern_name: str,
        description: str,
        code_example: Optional[str] = None
    ) -> str:
        """Track pattern discovery.

        Args:
            pattern_name: Name of pattern
            description: Pattern description
            code_example: Code example (optional)

        Returns:
            Event ID
        """
        return self.track_event(
            "pattern_discovered",
            {
                "pattern": pattern_name,
                "description": description,
                "code": code_example
            },
            auto_save=True
        )

    def _save_event_to_memory(self, event: dict[str, Any]) -> bool:
        """Save event to appropriate memory file.

        Args:
            event: Event data

        Returns:
            True if successful
        """
        try:
            event_type = event["type"]
            data = event["data"]

            if event_type == "error_fixed":
                # Calculate importance for routing
                importance = self.classifier.calculate_importance(
                    data.get("error", "") + " " + data.get("solution", "")
                )

                score = importance.get("overall_score", 0.5)

                # Route based on importance
                if score > 0.7:
                    # High importance → architecture.md
                    self.file_manager.write_entry(
                        file_type="architecture",
                        title=data.get("error", "Error"),
                        content=data.get("solution", ""),
                        one_liner=f"## Error: {data.get('error', '')[:50]} - {data.get('solution', '')[:50]}"
                    )
                elif score > 0.4:
                    # Medium importance → patterns.md
                    self.file_manager.write_entry(
                        file_type="patterns",
                        title=data.get("error", "Error Pattern"),
                        content=data.get("solution", ""),
                        one_liner=f"## Pattern: {data.get('error', '')[:50]}"
                    )
                else:
                    # Low importance → lessons.md
                    self.file_manager.write_entry(
                        file_type="lessons",
                        title=data.get("error", "Error"),
                        content=data.get("solution", "")
                    )

            elif event_type == "pattern_discovered":
                self.file_manager.write_entry(
                    file_type="patterns",
                    title=data.get("pattern", "Pattern"),
                    content=data.get("description", ""),
                    one_liner=f"## Pattern: {data.get('pattern', '')[:50]}"
                )

            elif event_type == "task_complete" and data.get("lessons"):
                self.file_manager.write_entry(
                    file_type="lessons",
                    title=f"Task: {data.get('task', 'Unknown')}",
                    content=data.get("lessons", "")
                )

            return True

        except Exception as e:
            self.logger.error(f"Error saving event to memory: {e}")
            return False

    def get_recent_events(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        with self._lock:
            events = list(self._events)

        return events[-limit:]

    def _cleanup(self) -> None:
        """Cleanup on exit."""
        # Save any pending events
        if not self.enabled:
            return

        with self._lock:
            events = list(self._events)

        # Process unsaved events
        for event in events:
            if event["type"] in ["error_fixed", "pattern_discovered"]:
                self._save_event_to_memory(event)

    def enable(self) -> None:
        """Enable auto-save."""
        self.enabled = True

    def disable(self) -> None:
        """Disable auto-save."""
        self.enabled = False
