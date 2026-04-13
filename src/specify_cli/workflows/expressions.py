"""Sandboxed expression evaluator for workflow templates.

Provides a safe Jinja2 subset for evaluating expressions in workflow YAML.
No file I/O, no imports, no arbitrary code execution.
"""

from __future__ import annotations

import re
from typing import Any


# -- Custom filters -------------------------------------------------------

def _filter_default(value: Any, default_value: Any = "") -> Any:
    """Return *default_value* when *value* is ``None`` or empty string."""
    if value is None or value == "":
        return default_value
    return value


def _filter_join(value: Any, separator: str = ", ") -> str:
    """Join a list into a string with *separator*."""
    if isinstance(value, list):
        return separator.join(str(v) for v in value)
    return str(value)


def _filter_map(value: Any, attr: str) -> list[Any]:
    """Map a list of dicts to a specific attribute."""
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, dict):
                # Support dot notation: "result.status" → item["result"]["status"]
                parts = attr.split(".")
                v = item
                for part in parts:
                    if isinstance(v, dict):
                        v = v.get(part)
                    else:
                        v = None
                        break
                result.append(v)
            else:
                result.append(item)
        return result
    return []


def _filter_contains(value: Any, substring: str) -> bool:
    """Check if a string or list contains *substring*."""
    if isinstance(value, str):
        return substring in value
    if isinstance(value, list):
        return substring in value
    return False


# -- Expression resolution ------------------------------------------------

_EXPR_PATTERN = re.compile(r"\{\{(.+?)\}\}")


def _resolve_dot_path(obj: Any, path: str) -> Any:
    """Resolve a dotted path like ``steps.specify.output.file`` against *obj*.

    Supports dict key access and list indexing (e.g., ``task_list[0]``).
    """
    parts = path.split(".")
    current = obj
    for part in parts:
        # Handle list indexing: name[0]
        idx_match = re.match(r"^(\w+)\[(\d+)\]$", part)
        if idx_match:
            key, idx = idx_match.group(1), int(idx_match.group(2))
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
            if isinstance(current, list) and 0 <= idx < len(current):
                current = current[idx]
            else:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def _build_namespace(context: Any) -> dict[str, Any]:
    """Build the variable namespace from a StepContext."""
    ns: dict[str, Any] = {}
    if hasattr(context, "inputs"):
        ns["inputs"] = context.inputs or {}
    if hasattr(context, "steps"):
        ns["steps"] = context.steps or {}
    if hasattr(context, "item"):
        ns["item"] = context.item
    if hasattr(context, "fan_in"):
        ns["fan_in"] = context.fan_in or {}
    return ns


def _evaluate_simple_expression(expr: str, namespace: dict[str, Any]) -> Any:
    """Evaluate a simple expression against the namespace.

    Supports:
    - Dot-path access: ``steps.specify.output.file``
    - Comparisons: ``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``
    - Boolean operators: ``and``, ``or``, ``not``
    - ``in``, ``not in``
    - Pipe filters: ``| default('...')``, ``| join(', ')``, ``| contains('...')``, ``| map('...')``
    - String and numeric literals
    """
    expr = expr.strip()

    # Handle pipe filters first
    if "|" in expr:
        parts = expr.split("|", 1)
        value = _evaluate_simple_expression(parts[0].strip(), namespace)
        filter_expr = parts[1].strip()

        # Parse filter name and argument
        filter_match = re.match(r"(\w+)\((.+)\)", filter_expr)
        if filter_match:
            fname = filter_match.group(1)
            farg = _evaluate_simple_expression(filter_match.group(2).strip(), namespace)
            if fname == "default":
                return _filter_default(value, farg)
            if fname == "join":
                return _filter_join(value, farg)
            if fname == "map":
                return _filter_map(value, farg)
            if fname == "contains":
                return _filter_contains(value, farg)
        # Filter without args
        filter_name = filter_expr.strip()
        if filter_name == "default":
            return _filter_default(value)
        return value

    # String literal — check before operators so quoted strings
    # containing operator keywords (e.g. 'a in b') are not mis-parsed.
    if (expr.startswith("'") and expr.endswith("'")) or (
        expr.startswith('"') and expr.endswith('"')
    ):
        return expr[1:-1]

    # Boolean operators
    if " and " in expr:
        parts = expr.split(" and ", 1)
        left = _evaluate_simple_expression(parts[0].strip(), namespace)
        right = _evaluate_simple_expression(parts[1].strip(), namespace)
        return bool(left) and bool(right)

    if " or " in expr:
        parts = expr.split(" or ", 1)
        left = _evaluate_simple_expression(parts[0].strip(), namespace)
        right = _evaluate_simple_expression(parts[1].strip(), namespace)
        return bool(left) or bool(right)

    if expr.startswith("not "):
        inner = _evaluate_simple_expression(expr[4:].strip(), namespace)
        return not bool(inner)

    # Comparison operators (order matters — check multi-char ops first)
    for op in ("!=", "==", ">=", "<=", ">", "<", " not in ", " in "):
        if op in expr:
            parts = expr.split(op, 1)
            left = _evaluate_simple_expression(parts[0].strip(), namespace)
            right = _evaluate_simple_expression(parts[1].strip(), namespace)
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == ">":
                return _safe_compare(left, right, ">")
            if op == "<":
                return _safe_compare(left, right, "<")
            if op == ">=":
                return _safe_compare(left, right, ">=")
            if op == "<=":
                return _safe_compare(left, right, "<=")
            if op == " in ":
                return left in right if right is not None else False
            if op == " not in ":
                return left not in right if right is not None else True

    # Numeric literal
    try:
        if "." in expr:
            return float(expr)
        return int(expr)
    except (ValueError, TypeError):
        pass

    # Boolean literal
    if expr.lower() == "true":
        return True
    if expr.lower() == "false":
        return False

    # Null
    if expr.lower() in ("none", "null"):
        return None

    # List literal (simple)
    if expr.startswith("[") and expr.endswith("]"):
        inner = expr[1:-1].strip()
        if not inner:
            return []
        items = [_evaluate_simple_expression(i.strip(), namespace) for i in inner.split(",")]
        return items

    # Variable reference (dot-path)
    return _resolve_dot_path(namespace, expr)


def _safe_compare(left: Any, right: Any, op: str) -> bool:
    """Safely compare two values, coercing types when possible."""
    try:
        if isinstance(left, str):
            left = float(left) if "." in left else int(left)
        if isinstance(right, str):
            right = float(right) if "." in right else int(right)
    except (ValueError, TypeError):
        return False
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


def evaluate_expression(template: str, context: Any) -> Any:
    """Evaluate a template string with ``{{ ... }}`` expressions.

    If the entire string is a single expression, returns the raw value
    (preserving type).  Otherwise, substitutes each expression inline
    and returns a string.

    Parameters
    ----------
    template:
        The template string (e.g., ``"{{ steps.plan.output.task_count }}"``
        or ``"Processed {{ inputs.feature_name }}"``.
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

    # Single expression: return typed value
    match = _EXPR_PATTERN.fullmatch(template.strip())
    if match:
        return _evaluate_simple_expression(match.group(1).strip(), namespace)

    # Multi-expression: string interpolation
    def _replacer(m: re.Match[str]) -> str:
        val = _evaluate_simple_expression(m.group(1).strip(), namespace)
        return str(val) if val is not None else ""

    return _EXPR_PATTERN.sub(_replacer, template)


def evaluate_condition(condition: str, context: Any) -> bool:
    """Evaluate a condition expression and return a boolean.

    Convenience wrapper around ``evaluate_expression`` that coerces
    the result to bool.
    """
    result = evaluate_expression(condition, context)
    return bool(result)
