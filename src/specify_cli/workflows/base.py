"""Base classes for workflow step types.

Provides:
- ``StepBase`` — abstract base every step type must implement.
- ``StepContext`` — execution context passed to each step.
- ``StepResult`` — return value from step execution.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepStatus(str, Enum):
    """Status of a step execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class RunStatus(str, Enum):
    """Status of a workflow run."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class StepContext:
    """Execution context passed to each step.

    Contains everything the step needs to resolve expressions, dispatch
    commands, and record results.
    """

    #: Resolved workflow inputs (from user prompts / defaults).
    inputs: dict[str, Any] = field(default_factory=dict)

    #: Accumulated step results keyed by step ID.
    #: Each entry is ``{"integration": ..., "model": ..., "options": ...,
    #:   "input": ..., "output": ...}``.
    steps: dict[str, dict[str, Any]] = field(default_factory=dict)

    #: Current fan-out item (set only inside fan-out iterations).
    item: Any = None

    #: Fan-in aggregated results (set only for fan-in steps).
    fan_in: dict[str, Any] = field(default_factory=dict)

    #: Workflow-level default integration key.
    default_integration: str | None = None

    #: Workflow-level default model.
    default_model: str | None = None

    #: Workflow-level default options.
    default_options: dict[str, Any] = field(default_factory=dict)

    #: Project root path.
    project_root: str | None = None

    #: Current run ID.
    run_id: str | None = None


@dataclass
class StepResult:
    """Return value from a step execution."""

    #: Step status.
    status: StepStatus = StepStatus.COMPLETED

    #: Output data (stored as ``steps.<id>.output``).
    output: dict[str, Any] = field(default_factory=dict)

    #: Nested steps to execute (for control-flow steps like if/then).
    next_steps: list[dict[str, Any]] = field(default_factory=list)

    #: Error message if step failed.
    error: str | None = None


class StepBase(ABC):
    """Abstract base class for workflow step types.

    Every step type — built-in or extension-provided — implements this
    interface and registers in ``STEP_REGISTRY``.
    """

    #: Matches the ``type:`` value in workflow YAML.
    type_key: str = ""

    @abstractmethod
    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        """Execute the step with the given config and context.

        Parameters
        ----------
        config:
            The step configuration from workflow YAML.
        context:
            The execution context with inputs, accumulated step results, etc.

        Returns
        -------
        StepResult with status, output data, and optional nested steps.
        """

    def validate(self, config: dict[str, Any]) -> list[str]:
        """Validate step configuration and return a list of error messages.

        An empty list means the configuration is valid.
        """
        errors: list[str] = []
        if "id" not in config:
            errors.append("Step is missing required 'id' field.")
        return errors

    def can_resume(self, state: dict[str, Any]) -> bool:
        """Return whether this step can be resumed from the given state."""
        return True
