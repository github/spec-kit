"""Progress tracking with Rich tree visualization and live updates."""

import contextlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

from rich.console import Console
from rich.live import Live
from rich.tree import Tree


class StepStatus(Enum):
    """Step status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class StepNode:
    """Individual step in the progress tree."""

    key: str
    label: str
    status: StepStatus = StepStatus.PENDING
    detail: str = ""
    children: Dict[str, "StepNode"] = field(default_factory=dict)
    parent: Optional[str] = None


class StepTracker:
    """Track and render hierarchical steps with Rich tree visualization.

    Supports live auto-refresh via an attached refresh callback and provides
    a fluent interface for step management.
    """

    def __init__(self, title: str, console: Optional[Console] = None):
        """Initialize step tracker.

        Args:
            title: Main title for the progress tree
            console: Rich console instance (creates new if None)
        """
        self.title = title
        self._console = console or Console()
        self._steps: Dict[str, StepNode] = {}
        self._refresh_cb: Optional[Callable[[], None]] = None
        self._live_display: Optional[Live] = None
        self._root_steps = []  # Track top-level step order

    @classmethod
    def create_default(cls, title: str = "Progress") -> "StepTracker":
        """Factory method for default configuration.

        Args:
            title: Title for the progress tree

        Returns:
            StepTracker instance with default console
        """
        return cls(title)

    def attach_refresh(self, callback: Callable[[], None]) -> "StepTracker":
        """Attach refresh callback for live updates.

        Args:
            callback: Function to call when display needs refreshing

        Returns:
            Self for method chaining
        """
        self._refresh_cb = callback
        return self

    def add_step(
        self, key: str, label: str, parent: Optional[str] = None
    ) -> "StepTracker":
        """Add a step to the tracking tree.

        Args:
            key: Unique identifier for the step
            label: Display label for the step
            parent: Parent step key (None for root level)

        Returns:
            Self for method chaining
        """
        if key in self._steps:
            return self

        step = StepNode(key=key, label=label, parent=parent)
        self._steps[key] = step

        if parent is None:
            self._root_steps.append(key)
        else:
            if parent in self._steps:
                self._steps[parent].children[key] = step

        self._maybe_refresh()
        return self

    def start_step(self, key: str, detail: str = "") -> "StepTracker":
        """Mark step as in progress with live updates.

        Args:
            key: Step identifier
            detail: Optional detail message

        Returns:
            Self for method chaining
        """
        return self._update_step(key, StepStatus.RUNNING, detail)

    def complete_step(self, key: str, detail: str = "") -> "StepTracker":
        """Mark step as completed successfully.

        Args:
            key: Step identifier
            detail: Optional completion message

        Returns:
            Self for method chaining
        """
        return self._update_step(key, StepStatus.DONE, detail)

    def error_step(self, key: str, detail: str = "") -> "StepTracker":
        """Mark step as failed with error.

        Args:
            key: Step identifier
            detail: Error message

        Returns:
            Self for method chaining
        """
        return self._update_step(key, StepStatus.ERROR, detail)

    def skip_step(self, key: str, detail: str = "") -> "StepTracker":
        """Mark step as skipped.

        Args:
            key: Step identifier
            detail: Skip reason

        Returns:
            Self for method chaining
        """
        return self._update_step(key, StepStatus.SKIPPED, detail)

    def update_step(self, key: str, detail: str) -> "StepTracker":
        """Update step detail message without changing status.

        Args:
            key: Step identifier
            detail: New detail message

        Returns:
            Self for method chaining
        """
        if key in self._steps:
            self._steps[key].detail = detail
            self._maybe_refresh()
        return self

    def start_live_display(
        self, refresh_per_second: float = 4, transient: bool = True
    ) -> "StepTracker":
        """Start live updating display.

        Args:
            refresh_per_second: Update frequency
            transient: Whether display disappears when stopped

        Returns:
            Self for method chaining
        """
        if self._live_display is None:
            self._live_display = Live(
                self.render(),
                console=self._console,
                refresh_per_second=refresh_per_second,
                transient=transient,
            )
            self._live_display.start()
            self.attach_refresh(lambda: self._live_display.update(self.render()))
        return self

    def stop_live_display(self, show_final: bool = True) -> "StepTracker":
        """Stop live display and optionally show final state.

        Args:
            show_final: Whether to print final tree state

        Returns:
            Self for method chaining
        """
        if self._live_display:
            self._live_display.stop()
            self._live_display = None
            self._refresh_cb = None

            if show_final:
                self._console.print(self.render())
        return self

    def render(self) -> Tree:
        """Render current state as Rich tree.

        Returns:
            Rich Tree object for display
        """
        tree = Tree(f"[bold cyan]{self.title}[/bold cyan]", guide_style="grey50")

        for root_key in self._root_steps:
            if root_key in self._steps:
                self._add_step_to_tree(tree, self._steps[root_key])

        return tree

    def _add_step_to_tree(self, parent: Tree, step: StepNode) -> None:
        """Recursively add step and children to tree.

        Args:
            parent: Parent tree node
            step: Step to add
        """
        symbol, style = self._get_step_display_info(step.status)

        # Build display text
        if step.detail:
            if step.status == StepStatus.PENDING:
                text = f"{symbol} [bright_black]{step.label} ({step.detail})[/bright_black]"
            else:
                text = f"{symbol} [white]{step.label}[/white] [bright_black]({step.detail})[/bright_black]"
        else:
            if step.status == StepStatus.PENDING:
                text = f"{symbol} [bright_black]{step.label}[/bright_black]"
            else:
                text = f"{symbol} [white]{step.label}[/white]"

        node = parent.add(text)

        # Add children
        for child in step.children.values():
            self._add_step_to_tree(node, child)

    def _update_step(
        self, key: str, status: StepStatus, detail: str = ""
    ) -> "StepTracker":
        """Internal method to update step status.

        Args:
            key: Step identifier
            status: New status
            detail: Detail message

        Returns:
            Self for method chaining
        """
        if key in self._steps:
            self._steps[key].status = status
            if detail:
                self._steps[key].detail = detail
            self._maybe_refresh()
        else:
            # Auto-add step if it doesn't exist
            self.add_step(key, key).start_step(key, detail)

        return self

    def _get_step_display_info(self, status: StepStatus) -> tuple[str, str]:
        """Get display symbol and style for status.

        Args:
            status: Step status

        Returns:
            Tuple of (symbol, style)
        """
        if status == StepStatus.DONE:
            return "[green]●[/green]", "green"
        elif status == StepStatus.PENDING:
            return "[green dim]○[/green dim]", "dim"
        elif status == StepStatus.RUNNING:
            return "[cyan]○[/cyan]", "cyan"
        elif status == StepStatus.ERROR:
            return "[red]●[/red]", "red"
        elif status == StepStatus.SKIPPED:
            return "[yellow]○[/yellow]", "yellow"
        else:
            return " ", ""

    def _maybe_refresh(self) -> None:
        """Trigger refresh if callback is attached."""
        if self._refresh_cb:
            with contextlib.suppress(Exception):
                self._refresh_cb()

    def __enter__(self) -> "StepTracker":
        """Context manager entry."""
        self.start_live_display()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop_live_display(show_final=True)
