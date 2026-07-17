"""If/Then/Else step — conditional branching."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_condition


class IfThenStep(StepBase):
    """Branch based on a boolean condition expression.

    Both ``then:`` and ``else:`` contain inline step arrays — full step
    definitions, not ID references.
    """

    type_key = "if"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        condition = config.get("condition", False)
        result = evaluate_condition(condition, context)

        if result:
            branch_name = "then"
            branch = config.get("then", [])
        else:
            branch_name = "else"
            branch = config.get("else", [])

        # The engine does not auto-validate step config (see
        # ``WorkflowEngine.load_workflow``), and it feeds ``next_steps`` straight
        # into ``_execute_steps`` which iterates them as step mappings. A
        # non-list branch (a single mapping or scalar authoring mistake) would
        # otherwise be iterated element-wise — a dict yields its string keys, a
        # str its characters — and crash the whole run with AttributeError on
        # ``.get()``. ``validate`` already rejects a non-list branch; fail this
        # step loudly on an unvalidated run instead, mirroring the switch/fan-out
        # steps. A missing ``else`` defaults to ``[]`` and stays valid.
        if branch is None and branch_name == "else":
            branch = []
        elif not isinstance(branch, list):
            return StepResult(
                status=StepStatus.FAILED,
                output={"condition_result": result},
                error=(
                    f"If step {config.get('id', '?')!r}: {branch_name!r} must be "
                    f"a list of steps, got {type(branch).__name__}."
                ),
            )

        return StepResult(
            status=StepStatus.COMPLETED,
            output={"condition_result": result},
            next_steps=branch,
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "condition" not in config:
            errors.append(
                f"If step {config.get('id', '?')!r} is missing 'condition' field."
            )
        if "then" not in config:
            errors.append(
                f"If step {config.get('id', '?')!r} is missing 'then' field."
            )
        then_branch = config.get("then", [])
        if not isinstance(then_branch, list):
            errors.append(
                f"If step {config.get('id', '?')!r}: 'then' must be a list of steps."
            )
        else_branch = config.get("else")
        if else_branch is not None and not isinstance(else_branch, list):
            errors.append(
                f"If step {config.get('id', '?')!r}: 'else' must be a list of steps."
            )
        return errors
