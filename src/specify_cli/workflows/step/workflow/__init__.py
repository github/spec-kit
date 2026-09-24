"""Workflow step — execute an installed workflow as a scoped subtree.

The step itself performs caller-side resolution only: it evaluates the
``workflow`` target expression, resolves the installed/enabled target
definition, and evaluates the input mapping. The engine special-cases
``type: workflow`` and runs the resulting subtree in a nested
``ExecutionScope``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.composition import (
    evaluate_input_mapping,
    resolve_composed_workflow,
    validate_workflow_call_config,
)
from specify_cli.workflows.expressions import evaluate_expression


class WorkflowStep(StepBase):
    """Compose an installed workflow into the current run."""

    type_key = "workflow"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        step_id = config.get("id", "?")
        try:
            from specify_cli.workflows.engine import _ID_PATTERN
            from specify_cli.workflows.overlay.schema import (
                _RESERVED_WORKFLOW_IDS,
            )

            target_expr = config.get("workflow")
            if not isinstance(target_expr, str):
                return StepResult(
                    status=StepStatus.FAILED,
                    output={"workflow": target_expr, "status": StepStatus.FAILED.value},
                    error=(
                        f"Workflow step {step_id!r}: 'workflow' must be a string."
                    ),
                )

            target = evaluate_expression(target_expr, context)
            if not isinstance(target, str):
                return StepResult(
                    status=StepStatus.FAILED,
                    output={"workflow": target, "status": StepStatus.FAILED.value},
                    error=(
                        f"Workflow step {step_id!r}: 'workflow' expression "
                        f"resolved to {type(target).__name__}, expected a string."
                    ),
                )
            if (
                not _ID_PATTERN.fullmatch(target)
                or target in _RESERVED_WORKFLOW_IDS
            ):
                return StepResult(
                    status=StepStatus.FAILED,
                    output={"workflow": target, "status": StepStatus.FAILED.value},
                    error=(
                        f"Workflow step {step_id!r}: {target!r} is not a valid "
                        "workflow ID."
                    ),
                )

            project_root = (
                Path(context.project_root) if context.project_root else Path(".")
            )
            definition = resolve_composed_workflow(project_root, target)
            raw_inputs = evaluate_input_mapping(config.get("input", {}), context)
            workflow_dir = (
                str(definition.source_path.resolve().parent)
                if definition.source_path is not None
                else None
            )
            return StepResult(
                status=StepStatus.COMPLETED,
                output={
                    "workflow": target,
                    "definition": definition,
                    "inputs": raw_inputs,
                    "workflow_dir": workflow_dir,
                },
            )
        except Exception as exc:  # noqa: BLE001
            # Runtime resolution failures become a failed step result so the
            # caller's normal continue_on_error handling applies.
            return StepResult(
                status=StepStatus.FAILED,
                output={
                    "workflow": config.get("workflow"),
                    "status": StepStatus.FAILED.value,
                },
                error=f"Workflow step {step_id!r}: {exc}",
            )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        errors.extend(validate_workflow_call_config(config))
        return errors
