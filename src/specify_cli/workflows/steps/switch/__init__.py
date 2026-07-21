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
        if not isinstance(cases, dict):
            # The engine does not auto-validate step config, so an unvalidated
            # run with a non-mapping ``cases`` (a list/scalar authoring mistake)
            # would otherwise raise AttributeError from ``.items()`` below and
            # crash the whole run. Fail this step loudly instead, mirroring the
            # fan-out step's non-list ``items`` handling.
            return StepResult(
                status=StepStatus.FAILED,
                error=(
                    f"Switch step {config.get('id', '?')!r}: 'cases' must be a "
                    f"mapping, got {type(cases).__name__}."
                ),
                output={"matched_case": None, "expression_value": value},
            )
        for case_key, case_steps in cases.items():
            if str(case_key) == str_value:
                if not isinstance(case_steps, list):
                    return self._non_list_branch_failure(
                        config, f"case {str(case_key)!r}", case_steps, value
                    )
                return StepResult(
                    status=StepStatus.COMPLETED,
                    output={"matched_case": str(case_key), "expression_value": value},
                    next_steps=case_steps,
                )

        # Default fallback
        default_steps = config.get("default", [])
        if default_steps is None:
            default_steps = []
        elif not isinstance(default_steps, list):
            return self._non_list_branch_failure(
                config, "'default'", default_steps, value
            )
        return StepResult(
            status=StepStatus.COMPLETED,
            output={"matched_case": "__default__", "expression_value": value},
            next_steps=default_steps,
        )

    @staticmethod
    def _non_list_branch_failure(
        config: dict[str, Any], branch_label: str, branch: Any, value: Any
    ) -> StepResult:
        """Fail the step for a non-list branch instead of crashing the run.

        ``validate`` rejects a non-list case/default branch, but the engine does
        not auto-validate and feeds ``next_steps`` straight into
        ``_execute_steps``, which iterates them as step mappings. A non-list
        branch would be iterated element-wise (a dict yields its keys, a str its
        characters) and crash the whole run with AttributeError on ``.get()``.
        Fail this step loudly on an unvalidated run instead, mirroring the
        non-mapping ``cases`` guard above.
        """
        return StepResult(
            status=StepStatus.FAILED,
            output={"matched_case": None, "expression_value": value},
            error=(
                f"Switch step {config.get('id', '?')!r}: {branch_label} must be "
                f"a list of steps, got {type(branch).__name__}."
            ),
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
