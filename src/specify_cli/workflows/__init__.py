"""Workflow engine for multi-step, resumable automation workflows.

Provides:
- ``StepBase`` — abstract base every step type must implement.
- ``StepContext`` — execution context passed to each step.
- ``StepResult`` — return value from step execution.
- ``STEP_REGISTRY`` — maps ``type_key`` to ``StepBase`` subclass instances.
- ``WorkflowEngine`` — orchestrator that loads, validates, and executes
  workflow YAML definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import StepBase

# Maps step type_key → StepBase instance.
STEP_REGISTRY: dict[str, StepBase] = {}


def _register_step(step: StepBase) -> None:
    """Register a step type instance in the global registry.

    Raises ``ValueError`` for falsy keys and ``KeyError`` for duplicates.
    """
    key = step.type_key
    if not key:
        raise ValueError("Cannot register step type with an empty type_key.")
    if key in STEP_REGISTRY:
        raise KeyError(f"Step type with key {key!r} is already registered.")
    STEP_REGISTRY[key] = step


def get_step_type(type_key: str) -> StepBase | None:
    """Return the step type for *type_key*, or ``None`` if not registered."""
    return STEP_REGISTRY.get(type_key)


# -- Register built-in step types ----------------------------------------

def _register_builtin_steps() -> None:
    """Register all built-in step types."""
    from .steps.command import CommandStep
    from .steps.do_while import DoWhileStep
    from .steps.fan_in import FanInStep
    from .steps.fan_out import FanOutStep
    from .steps.gate import GateStep
    from .steps.if_then import IfThenStep
    from .steps.prompt import PromptStep
    from .steps.shell import ShellStep
    from .steps.switch import SwitchStep
    from .steps.while_loop import WhileStep

    _register_step(CommandStep())
    _register_step(DoWhileStep())
    _register_step(FanInStep())
    _register_step(FanOutStep())
    _register_step(GateStep())
    _register_step(IfThenStep())
    _register_step(PromptStep())
    _register_step(ShellStep())
    _register_step(SwitchStep())
    _register_step(WhileStep())


_register_builtin_steps()
