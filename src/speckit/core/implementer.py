"""
Implementation tracking for spec-kit.

This module provides tools to track progress of task implementation.
"""

from typing import Optional

from speckit.schemas import Task, TaskBreakdown, TaskStatus
from speckit.storage.base import StorageBase


class ImplementationTracker:
    """
    Tracks progress of task implementation.

    Provides methods to mark tasks as complete, get next available tasks,
    and report on overall progress.
    """

    def __init__(self, storage: StorageBase):
        """
        Initialize implementation tracker.

        Args:
            storage: Storage backend for persistence
        """
        self.storage = storage

    def mark_complete(
        self,
        breakdown: TaskBreakdown,
        task_id: str,
    ) -> TaskBreakdown:
        """
        Mark a task as completed.

        Args:
            breakdown: Task breakdown to update
            task_id: ID of the task to mark complete

        Returns:
            Updated TaskBreakdown
        """
        breakdown.mark_complete(task_id)
        return breakdown

    def mark_in_progress(
        self,
        breakdown: TaskBreakdown,
        task_id: str,
    ) -> TaskBreakdown:
        """
        Mark a task as in progress.

        Args:
            breakdown: Task breakdown to update
            task_id: ID of the task to mark in progress

        Returns:
            Updated TaskBreakdown
        """
        for task in breakdown.tasks:
            if task.id == task_id:
                task.status = TaskStatus.IN_PROGRESS
                break
        return breakdown

    def mark_blocked(
        self,
        breakdown: TaskBreakdown,
        task_id: str,
        reason: Optional[str] = None,
    ) -> TaskBreakdown:
        """
        Mark a task as blocked.

        Args:
            breakdown: Task breakdown to update
            task_id: ID of the task to mark blocked
            reason: Optional reason for blocking

        Returns:
            Updated TaskBreakdown
        """
        for task in breakdown.tasks:
            if task.id == task_id:
                task.status = TaskStatus.BLOCKED
                if reason:
                    task.description = f"{task.description}\n\nBLOCKED: {reason}"
                break
        return breakdown

    def get_next_tasks(self, breakdown: TaskBreakdown) -> list[Task]:
        """
        Get tasks that are ready to be executed.

        Returns tasks whose dependencies are all completed.

        Args:
            breakdown: Task breakdown to check

        Returns:
            List of tasks ready for execution
        """
        return breakdown.get_next_tasks()

    def get_progress(self, breakdown: TaskBreakdown) -> dict:
        """
        Get progress summary for a task breakdown.

        Args:
            breakdown: Task breakdown to summarize

        Returns:
            Dict with counts by status and percentage complete
        """
        counts = breakdown.get_progress()
        total = sum(counts.values())
        completed = counts.get("completed", 0)

        return {
            "counts": counts,
            "total": total,
            "completed": completed,
            "percent_complete": (completed / total * 100) if total > 0 else 0,
        }

    def get_blocked_tasks(self, breakdown: TaskBreakdown) -> list[Task]:
        """Get all blocked tasks."""
        return breakdown.get_tasks_by_status(TaskStatus.BLOCKED)

    def get_in_progress_tasks(self, breakdown: TaskBreakdown) -> list[Task]:
        """Get all in-progress tasks."""
        return breakdown.get_tasks_by_status(TaskStatus.IN_PROGRESS)
