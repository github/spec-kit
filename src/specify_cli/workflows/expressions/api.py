"""Public evaluation API for workflow expression templates.

The API layer owns namespace construction and nothing else: the whole
single-expression-vs-interpolation decision lives in the engine contract
(``_evaluate_template``), reached only through ``engine.py``.
"""

from __future__ import annotations

from typing import Any

from .engine import _evaluate_template
from .namespace import _build_namespace


def evaluate_expression(template: str, context: Any) -> Any:
    """Evaluate a template string with ``{{ ... }}`` expressions.

    If the entire string is a single expression, returns the raw value
    (preserving type).  Otherwise, substitutes each expression inline
    and returns a string.

    Parameters
    ----------
    template:
        The template string (e.g., ``"{{ steps.plan.output.task_count }}"``
        or ``"Processed {{ inputs.spec }}"``.
    context:
        A ``StepContext`` or compatible object.

    Returns
    -------
    The resolved value (any type for single-expression templates,
    string for multi-expression or mixed templates).
    """
    if not isinstance(template, str):
        return template

    namespace = _build_namespace(context)
    return _evaluate_template(template, namespace)


def evaluate_condition(condition: str, context: Any) -> bool:
    """Evaluate a condition expression and return a boolean.

    Convenience wrapper around ``evaluate_expression`` that coerces
    the result to bool.
    """
    result = evaluate_expression(condition, context)
    # Treat plain "false"/"true" strings as booleans so that
    # condition: "false" (without {{ }}) behaves as expected.
    #
    # Strip before matching: the string a condition resolves to is most often
    # captured command output, and a ``shell`` step stores ``proc.stdout``
    # verbatim, so ``run: echo false`` resolves to ``"false\n"``. Without the
    # strip that trailing newline matches neither branch and falls through to
    # ``bool("false\n")`` -> True, silently taking an ``if`` step's ``then``
    # branch (and keeping a ``while``/``do-while`` looping) on a step that
    # printed "false". A workflow cannot strip it itself -- no registered
    # filter trims whitespace (there is no ``trim``).
    # ``InitStep._resolve_bool`` and the catalog readers already strip before
    # matching boolean text. ``bool(result)`` below still sees the raw string,
    # so no non-boolean text changes truthiness.
    if isinstance(result, str):
        lower = result.strip().lower()
        if lower == "false":
            return False
        if lower == "true":
            return True
    return bool(result)
