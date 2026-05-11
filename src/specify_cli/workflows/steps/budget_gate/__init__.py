"""Budget gate step — LLM spend circuit breaker."""

from __future__ import annotations

import sys
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression

_VALID_ON_WARNING = frozenset({"pause", "notify", "continue"})
_VALID_ON_EXCEEDED = frozenset({"abort", "pause"})


class BudgetGateStep(StepBase):
    """LLM spend circuit breaker.

    Compares ``current_spend_usd`` against ``threshold_usd`` and takes
    action before spending runs away:

    * ``< 80 %`` — completes silently (no interruption to the workflow).
    * ``>= 80 %`` — emits a warning; behaviour controlled by ``on_warning``
      (``pause`` / ``notify`` / ``continue``).
    * ``>= 100 %`` — emits an error; behaviour controlled by ``on_exceeded``
      (``abort`` / ``pause``).

    Both ``threshold_usd`` and ``current_spend_usd`` support ``{{ }}``
    template expressions so they can read from previous step outputs
    (e.g. ``{{ steps.cost_tracker.output.total_spend }}``).
    """

    type_key = "budget-gate"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        threshold_raw = config.get("threshold_usd", 0)
        if isinstance(threshold_raw, str) and "{{" in threshold_raw:
            threshold_raw = evaluate_expression(threshold_raw, context)
        threshold = float(threshold_raw) if threshold_raw else 0.0

        spend_raw = config.get("current_spend_usd", 0)
        if isinstance(spend_raw, str) and "{{" in spend_raw:
            spend_raw = evaluate_expression(spend_raw, context)
        current_spend = float(spend_raw) if spend_raw else 0.0

        on_warning = config.get("on_warning", "pause")
        on_exceeded = config.get("on_exceeded", "abort")

        pct = (current_spend / threshold * 100) if threshold > 0 else 0.0

        output: dict[str, Any] = {
            "threshold_usd": threshold,
            "current_spend_usd": current_spend,
            "pct_used": round(pct, 1),
            "status": "ok",
        }

        if threshold > 0 and current_spend >= threshold:
            output["status"] = "exceeded"
            self._print_exceeded(current_spend, threshold, pct)
            if on_exceeded == "abort":
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=(
                        f"Budget gate: LLM spend ${current_spend:.2f} exceeded "
                        f"threshold ${threshold:.2f} ({pct:.1f}%)"
                    ),
                )
            # on_exceeded == "pause"
            return StepResult(status=StepStatus.PAUSED, output=output)

        if threshold > 0 and current_spend >= threshold * 0.8:
            output["status"] = "warning"
            self._print_warning(current_spend, threshold, pct)
            if on_warning == "continue":
                return StepResult(status=StepStatus.COMPLETED, output=output)
            if on_warning == "notify":
                # Emit the warning but don't block execution
                return StepResult(status=StepStatus.COMPLETED, output=output)
            # on_warning == "pause" — pause if not interactive, else prompt
            if not sys.stdin.isatty():
                return StepResult(status=StepStatus.PAUSED, output=output)
            choice = self._prompt_warning(current_spend, threshold)
            if choice == "abort":
                output["status"] = "exceeded"
                return StepResult(
                    status=StepStatus.FAILED,
                    output=output,
                    error=(
                        f"Budget gate: user aborted at ${current_spend:.2f} "
                        f"/ ${threshold:.2f} ({pct:.1f}%)"
                    ),
                )
            return StepResult(status=StepStatus.COMPLETED, output=output)

        return StepResult(status=StepStatus.COMPLETED, output=output)

    @staticmethod
    def _print_warning(spend: float, threshold: float, pct: float) -> None:
        print("\n  ┌─ Budget Gate ───────────────────────────────")
        print(f"  │  ⚠  WARNING: {pct:.1f}% of LLM budget used")
        print(f"  │     Spent:     ${spend:.2f}")
        print(f"  │     Threshold: ${threshold:.2f}")
        print("  └────────────────────────────────────────────")

    @staticmethod
    def _print_exceeded(spend: float, threshold: float, pct: float) -> None:
        print("\n  ┌─ Budget Gate ───────────────────────────────")
        print(f"  │  ✗  EXCEEDED: {pct:.1f}% of LLM budget used")
        print(f"  │     Spent:     ${spend:.2f}")
        print(f"  │     Threshold: ${threshold:.2f}")
        print("  └────────────────────────────────────────────")

    @staticmethod
    def _prompt_warning(spend: float, threshold: float) -> str:
        """Prompt user to continue or abort after a budget warning."""
        print(f"  Continue workflow with ${spend:.2f} / ${threshold:.2f} spent?")
        print("  [1] continue")
        print("  [2] abort")
        while True:
            try:
                raw = input("  Choose [1-2]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return "abort"
            if raw == "1" or raw.lower() == "continue":
                return "continue"
            if raw == "2" or raw.lower() == "abort":
                return "abort"
            print("  Enter 1 (continue) or 2 (abort).")

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        if "threshold_usd" not in config:
            errors.append(
                f"Budget gate step {config.get('id', '?')!r} is missing "
                f"'threshold_usd' field."
            )
        if "current_spend_usd" not in config:
            errors.append(
                f"Budget gate step {config.get('id', '?')!r} is missing "
                f"'current_spend_usd' field."
            )
        on_warning = config.get("on_warning", "pause")
        if on_warning not in _VALID_ON_WARNING:
            errors.append(
                f"Budget gate step {config.get('id', '?')!r}: 'on_warning' must be "
                f"one of {sorted(_VALID_ON_WARNING)}."
            )
        on_exceeded = config.get("on_exceeded", "abort")
        if on_exceeded not in _VALID_ON_EXCEEDED:
            errors.append(
                f"Budget gate step {config.get('id', '?')!r}: 'on_exceeded' must be "
                f"one of {sorted(_VALID_ON_EXCEEDED)}."
            )
        return errors
