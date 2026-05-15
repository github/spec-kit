"""Switch step — multi-branch dispatch."""

from __future__ import annotations

from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


class SwitchStep(StepBase):
    """Multi-branch dispatch on an expression.

    Evaluates ``expression:`` once, matches against ``cases:`` keys
    (exact match, string-coerced).  Falls through to ``default:`` if
    no case matches.
    """

    type_key = "switch"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        expression = config.get("expression", "")
        value = evaluate_expression(expression, context)

        # String-coerce for matching
        str_value = str(value) if value is not None else ""

        cases = config.get("cases", {})
        for case_key, case_steps in cases.items():
            if str(case_key) == str_value:
                return StepResult(
                    status=StepStatus.COMPLETED,
                    output={"matched_case": str(case_key), "expression_value": value},
                    next_steps=case_steps,
                )

        # Default fallback
        default_steps = config.get("default", [])
        return StepResult(
            status=StepStatus.COMPLETED,
            output={"matched_case": "__default__", "expression_value": value},
            next_steps=default_steps,
        )

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "expression" not in config:
            errors.append(
                f"Switch step {config.get('id', '?')!r} is missing "
                f"'expression' field."
            )
        cases = config.get("cases", {})
        if not isinstance(cases, dict):
            errors.append(
                f"Switch step {config.get('id', '?')!r}: 'cases' must be a mapping."
            )
        else:
            for key, val in cases.items():
                if not isinstance(val, list):
                    errors.append(
                        f"Switch step {config.get('id', '?')!r}: "
                        f"case {key!r} must be a list of steps."
                    )
        default = config.get("default")
        if default is not None and not isinstance(default, list):
            errors.append(
                f"Switch step {config.get('id', '?')!r}: "
                f"'default' must be a list of steps."
            )
        return errors
