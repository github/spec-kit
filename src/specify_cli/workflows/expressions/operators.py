"""Comparison and membership semantics for workflow expressions.

Leaf module: no dependencies on the evaluator, the namespace, or the filters,
so an alternative engine can reuse these operators unchanged.
"""

from __future__ import annotations

from typing import Any


def _coerce_number(value: Any) -> Any:
    """Return *value* as int/float if it is a numeric string, else unchanged."""
    if isinstance(value, str):
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return value
    return value


def _coerce_numeric_pair(left: Any, right: Any) -> tuple[Any, Any]:
    """Return both operands as numbers if both look numeric, else unchanged.

    Coercing only when *both* convert keeps a numeric string paired with a
    plain string as two strings, rather than an int-vs-str mismatch.
    """
    cl, cr = _coerce_number(left), _coerce_number(right)
    if isinstance(cl, (int, float)) and isinstance(cr, (int, float)):
        return cl, cr
    return left, right


def _safe_equals(left: Any, right: Any, *, negate: bool) -> bool:
    """Evaluate ``left == right`` (or ``!=``) with the same numeric coercion
    as the ordering operators.

    Without it, a numeric string such as captured stdout ``"10"`` was both
    ``>= 10`` and ``<= 10`` but not ``== 10``.
    """
    left, right = _coerce_numeric_pair(left, right)
    equal = left == right
    return not equal if negate else equal


def _safe_membership(left: Any, right: Any, *, negate: bool) -> bool:
    """Safely evaluate ``left in right`` (or ``not in``) without crashing.

    ``left in right`` raises ``TypeError`` whenever the operands don't support
    membership testing — most commonly a non-iterable right operand (``None``,
    an int, a bool), but also cases like an unhashable ``left`` against a set.
    In every such case the membership relation is undefined, so treat it as
    ``False`` (``not in`` as ``True``) rather than leaking the error out of the
    evaluator and crashing the whole workflow. Mirrors the graceful
    ``TypeError`` handling in ``_safe_compare`` for the ordering operators, and
    generalizes the previous ``right is not None`` guard to any operand pair
    that can't be membership-tested.
    """
    try:
        contained = left in right
    except TypeError:
        contained = False
    return not contained if negate else contained


def _safe_compare(left: Any, right: Any, op: str) -> bool:
    """Compare two values for ordering, coercing numeric strings when possible.

    Numeric coercion is applied only when *both* operands look numeric, so a
    pair like ``"10"`` and ``"9"`` compares as numbers (10 > 9). When either
    side is a non-numeric string, both fall back to their original values and
    are compared directly -- so ordinary strings (dates, semver-ish tags,
    names) compare lexicographically the way Python does, instead of every
    such comparison silently returning ``False`` after a failed int()/float()
    coercion. A genuinely incomparable pair (e.g. number vs non-numeric string)
    raises ``TypeError`` and yields ``False``.
    """
    left, right = _coerce_numeric_pair(left, right)
    try:
        if op == ">":
            return left > right  # type: ignore[operator]
        if op == "<":
            return left < right  # type: ignore[operator]
        if op == ">=":
            return left >= right  # type: ignore[operator]
        if op == "<=":
            return left <= right  # type: ignore[operator]
    except TypeError:
        return False
    return False
