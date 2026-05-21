"""Gate-on-condition step — auto-firing review gate."""

from __future__ import annotations

import sys
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import (
    evaluate_condition,
    evaluate_expression,
)


class GateOnConditionStep(StepBase):
    """Review gate that auto-fires a verdict when a condition matches.

    Evaluates each ``conditions:`` entry's ``if:`` expression in
    declaration order; the first truthy condition's ``then_route`` is
    recorded as ``output.choice`` and the step completes without
    operator interaction. When no condition matches, the step falls
    back to interactive prompt behaviour (``fallback_prompt:``) — or
    aborts the run if no ``fallback_prompt`` is declared.

    Example YAML::

        - id: review-overview
          type: gate-on-condition
          conditions:
            - if: "{{ steps.detect.output.has_pending_work }}"
              then_route: regenerate
            - if: "{{ steps.detect.output.is_clean }}"
              then_route: continue
          fallback_prompt:
            message: "Ambiguous — approve, regenerate, or abort?"
            options: [approve, regenerate, abort]
            on_reject: abort

    The ``fallback_prompt`` schema mirrors the regular ``gate`` step's
    fields (``message``, ``options``, ``on_reject``) so authors writing
    both kinds use the same vocabulary.

    The recorded ``output.choice`` is the matched route name, so
    downstream ``switch``/``if`` steps branch on it exactly the same
    way they branch on a regular ``gate`` step's choice. The output
    also includes ``output.auto_fired`` (``True`` when a condition
    matched, ``False`` when the operator chose) so workflow authors
    can distinguish automatic vs. interactive verdicts.
    """

    type_key = "gate-on-condition"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        conditions = config.get("conditions") or []

        for index, cond_spec in enumerate(conditions):
            expr = cond_spec.get("if", "")
            route = cond_spec.get("then_route", "")
            if evaluate_condition(expr, context):
                return StepResult(
                    status=StepStatus.COMPLETED,
                    output={
                        "choice": route,
                        "auto_fired": True,
                        "matched_condition_index": index,
                    },
                )

        # No condition matched — defer to the fallback prompt.
        fallback = config.get("fallback_prompt") or {}
        message = fallback.get("message", "Review required.")
        if isinstance(message, str) and "{{" in message:
            message = evaluate_expression(message, context)
        options = fallback.get("options", ["approve", "reject"])
        on_reject = fallback.get("on_reject", "abort")

        output: dict[str, Any] = {
            "choice": None,
            "auto_fired": False,
            "matched_condition_index": None,
            "message": message,
            "options": options,
            "on_reject": on_reject,
        }

        if not fallback:
            output["aborted"] = True
            return StepResult(
                status=StepStatus.FAILED,
                output=output,
                error=(
                    f"gate-on-condition step {config.get('id', '?')!r}: "
                    f"no condition matched and no fallback_prompt declared."
                ),
            )

        # Non-interactive: pause for later resume (same contract as `gate`).
        if not sys.stdin.isatty():
            return StepResult(status=StepStatus.PAUSED, output=output)

        # Interactive: prompt the operator.
        choice = self._prompt(message, options)
        output["choice"] = choice

        if choice in ("reject", "abort"):
            if on_reject == "abort":
                output["aborted"] = True
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=(
                        f"gate-on-condition fallback rejected by user at step "
                        f"{config.get('id', '?')!r}"
                    ),
                )
            if on_reject == "retry":
                return StepResult(status=StepStatus.PAUSED, output=output)
            # on_reject == "skip" → completed, downstream steps decide.

        return StepResult(status=StepStatus.COMPLETED, output=output)

    @staticmethod
    def _prompt(message: str, options: list[str]) -> str:
        """Display the fallback prompt and read a choice from the operator.

        Matches the visual style and selection semantics of the
        regular ``gate`` step's prompt so operators see a consistent
        UX when either kind fires interactively.
        """
        print("\n  ┌─ Gate (auto-condition fallback) ───────────")
        print(f"  │ {message}")
        print("  │")
        for i, opt in enumerate(options, 1):
            print(f"  │  [{i}] {opt}")
        print("  └────────────────────────────────────────────")

        while True:
            try:
                raw = input(f"  Choose [1-{len(options)}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return options[-1]
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1]
            if raw.lower() in [o.lower() for o in options]:
                return next(o for o in options if o.lower() == raw.lower())
            print(f"  Invalid choice. Enter 1-{len(options)} or an option name.")

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        step_id = config.get("id", "?")

        conditions = config.get("conditions")
        if conditions is None:
            errors.append(
                f"gate-on-condition step {step_id!r} is missing "
                f"'conditions' field."
            )
        elif not isinstance(conditions, list):
            errors.append(
                f"gate-on-condition step {step_id!r}: 'conditions' must "
                f"be a list of mappings."
            )
        elif not conditions:
            errors.append(
                f"gate-on-condition step {step_id!r}: 'conditions' must "
                f"be a non-empty list."
            )
        else:
            for index, cond in enumerate(conditions):
                if not isinstance(cond, dict):
                    errors.append(
                        f"gate-on-condition step {step_id!r}: condition "
                        f"at index {index} must be a mapping with 'if' "
                        f"and 'then_route'."
                    )
                    continue
                # 'if' must be present and a string. Without this check
                # a YAML authoring mistake (`if: 42`) would coerce
                # through `evaluate_condition` and trigger only at
                # runtime — better to fail at validation time.
                if "if" not in cond:
                    errors.append(
                        f"gate-on-condition step {step_id!r}: condition "
                        f"at index {index} is missing 'if'."
                    )
                elif not isinstance(cond["if"], str):
                    errors.append(
                        f"gate-on-condition step {step_id!r}: condition "
                        f"at index {index}: 'if' must be a string "
                        f"(got {type(cond['if']).__name__})."
                    )
                # 'then_route' must be a non-empty string. An empty
                # route silently matches an empty `switch case: ""`
                # which is almost always an authoring mistake; reject
                # it eagerly.
                if "then_route" not in cond:
                    errors.append(
                        f"gate-on-condition step {step_id!r}: condition "
                        f"at index {index} is missing 'then_route'."
                    )
                elif not isinstance(cond["then_route"], str):
                    errors.append(
                        f"gate-on-condition step {step_id!r}: condition "
                        f"at index {index}: 'then_route' must be a "
                        f"string (got {type(cond['then_route']).__name__})."
                    )
                elif not cond["then_route"]:
                    errors.append(
                        f"gate-on-condition step {step_id!r}: condition "
                        f"at index {index}: 'then_route' must be a "
                        f"non-empty string."
                    )

        fallback = config.get("fallback_prompt")
        if fallback is not None:
            if not isinstance(fallback, dict):
                errors.append(
                    f"gate-on-condition step {step_id!r}: "
                    f"'fallback_prompt' must be a mapping."
                )
            else:
                fb_options = fallback.get("options", ["approve", "reject"])
                if not isinstance(fb_options, list) or not fb_options:
                    errors.append(
                        f"gate-on-condition step {step_id!r}: "
                        f"'fallback_prompt.options' must be a non-empty list."
                    )
                elif not all(isinstance(c, str) for c in fb_options):
                    errors.append(
                        f"gate-on-condition step {step_id!r}: all "
                        f"'fallback_prompt.options' must be strings."
                    )
                fb_on_reject = fallback.get("on_reject", "abort")
                if fb_on_reject not in ("abort", "skip", "retry"):
                    errors.append(
                        f"gate-on-condition step {step_id!r}: "
                        f"'fallback_prompt.on_reject' must be 'abort', "
                        f"'skip', or 'retry'."
                    )

        return errors
