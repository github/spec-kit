"""Sandboxed expression evaluator for workflow templates.

Provides a safe Jinja2 subset for evaluating expressions in workflow YAML.
Templates cannot perform file I/O, import modules, or run arbitrary code —
the evaluator only walks the namespace and applies a fixed set of filters.
"""

from __future__ import annotations

import json
import re
from typing import Any


# The filters the expression evaluator recognizes. Used to tell a
# *registered* filter used in an unsupported form (e.g. `| join` with no
# argument) apart from a genuinely unknown filter name, so each raises an
# error that names the real problem.
_REGISTERED_FILTERS: tuple[str, ...] = (
    "default",
    "join",
    "map",
    "contains",
    "from_json",
)


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


def _filter_from_json(value: Any) -> Any:
    """Parse a JSON string into a typed value (list/dict/scalar).

    Raises ``ValueError`` on non-string input or invalid JSON — a parse
    failure here means the pipeline wiring is wrong, and silently
    passing the unparsed value through would hide it.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"from_json: expected a JSON string, got {type(value).__name__}"
        )
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"from_json: invalid JSON: {exc}") from exc


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
        idx_match = re.match(r"^([\w-]+)\[(\d+)\]$", part)
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
    # Engine-managed runtime metadata. Always present (even outside a
    # run) so templates referencing it never error: `run_id` falls back
    # to an empty string when no run is active (dry-run, validation,
    # ad-hoc evaluator usage). The value is the same one Spec Kit
    # prints as `Run ID:` at the end of `workflow run` — auto-generated
    # runs use an 8-character uuid4 hex; operator-supplied ids may be
    # any alphanumeric string with hyphens or underscores.
    run_id = getattr(context, "run_id", None) or ""
    ns["context"] = {"run_id": run_id}
    return ns


def _is_single_expression(stripped: str) -> bool:
    """True when *stripped* is exactly one top-level ``{{ ... }}`` block.

    Scans the block body for a ``}}`` that would close it early, ignoring any
    braces inside string literals. This keeps a lone expression whose string
    argument contains a literal ``{{`` or ``}}`` (e.g.
    ``{{ inputs.text | contains('}}') }}``) on the typed fast path, while
    ``{{ a }} {{ b }}`` and ``{{ a }}{{ b }}`` are correctly seen as
    multi-expression. Mirrors the quote handling in
    ``_split_top_level_commas``.

    A regex span check cannot decide this: the pattern's non-greedy body stops
    at the first ``}}``, so a literal ``}}`` inside a string argument would be
    mistaken for the closing delimiter (issue #3208, follow-up review).
    """
    if not (stripped.startswith("{{") and stripped.endswith("}}")):
        return False
    inner = stripped[2:-2]
    if not inner.strip():
        return False
    quote: str | None = None
    i = 0
    n = len(inner)
    while i < n:
        ch = inner[i]
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "}" and i + 1 < n and inner[i + 1] == "}":
            # A ``}}`` outside quotes closes the first block early.
            return False
        i += 1
    return True


def _split_top_level_commas(text: str) -> list[str]:
    """Split *text* on commas that are not inside quotes or nested brackets.

    Used for list-literal elements so a quoted element containing a comma
    (e.g. ``["a, b", "c"]``) is not split mid-string, and nested lists/calls
    (e.g. ``[[1, 2], 3]``) are kept intact.
    """
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    depth = 0
    for ch in text:
        if quote is not None:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch in "([{":
            depth += 1
            buf.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def _find_top_level(text: str, token: str) -> int:
    """Return the index of the first occurrence of *token* in *text* that lies
    outside any quoted string or nested bracket, or ``-1`` if there is none.

    Used so operator/keyword splitting (``and``/``or``/``in``/comparisons) does
    not match a separator that appears *inside* a quoted operand -- e.g. the
    ``and`` in ``mode == 'read and write'`` or the ``or`` in ``'approve or reject'``.
    """
    quote: str | None = None
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0 and text.startswith(token, i):
            return i
        i += 1
    return -1


def _evaluate_simple_expression(expr: str, namespace: dict[str, Any]) -> Any:
    """Evaluate a simple expression against the namespace.

    Supports:
    - Dot-path access: ``steps.specify.output.file``
    - Comparisons: ``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``
    - Boolean operators: ``and``, ``or``, ``not``
    - ``in``, ``not in``
    - Pipe filters: ``| default('...')``, ``| join(', ')``, ``| contains('...')``, ``| from_json``, ``| map('...')``
    - String and numeric literals
    """
    expr = expr.strip()

    # String literal — only when the WHOLE expression is one quoted string,
    # i.e. the opening quote's matching close is the final character. Checking
    # startswith/endswith alone would also grab `'a' == 'b'` and strip it to the
    # garbage `a' == 'b`; a genuine single literal short-circuits here so quoted
    # strings containing `|` or operator keywords are not mis-parsed downstream.
    if expr[:1] in ("'", '"') and expr.find(expr[0], 1) == len(expr) - 1:
        return expr[1:-1]

    # Handle pipe filters. Detect the pipe at the top level only, so a literal
    # '|' inside a quoted operand (e.g. `inputs.x == 'a|b'`) or nested brackets is
    # not mistaken for a filter separator — mirroring the operator parsing below.
    pipe_idx = _find_top_level(expr, "|")
    if pipe_idx != -1:
        value = _evaluate_simple_expression(expr[:pipe_idx].strip(), namespace)
        filter_expr = expr[pipe_idx + 1:].strip()

        # `from_json` is strict: it takes no arguments and tolerates no
        # trailing tokens. Match on the leading filter name and require the
        # whole filter to be exactly `from_json`, so every mis-wired form
        # (`from_json()`, `from_json('x')`, `from_json)`, `from_json extra`)
        # fails loudly instead of silently falling through to the
        # unknown-filter path and returning the unparsed value. (filter_expr
        # is already stripped above.)
        leading = re.match(r"\w+", filter_expr)
        if leading and leading.group(0) == "from_json":
            if filter_expr != "from_json":
                raise ValueError(
                    "from_json: expected '| from_json' with no arguments or "
                    f"trailing tokens, got '| {filter_expr}'"
                )
            return _filter_from_json(value)

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
        # No recognized filter matched. Fail loudly rather than silently
        # returning the unfiltered value: a passthrough turns a mis-typed or
        # unsupported filter into a wrong result with no signal. Mirrors the
        # strict `from_json` handling above. Distinguish a *registered* filter
        # used in an unsupported form (e.g. `| join` or `| map` with no
        # argument) from a genuinely unknown filter name, so the message names
        # the real problem instead of calling a known filter "unknown".
        leading_name = re.match(r"\w+", filter_expr)
        name = leading_name.group(0) if leading_name else filter_expr
        expected = (
            "expected one of default or default('x'), join('sep'), "
            "map('attr'), contains('s'), or from_json"
        )
        if name in _REGISTERED_FILTERS:
            raise ValueError(
                f"filter '{name}' used in an unsupported form (got "
                f"'| {filter_expr}'): {expected}"
            )
        raise ValueError(
            f"unknown filter '{name}': {expected} (got '| {filter_expr}')"
        )

    # Boolean operators — parse 'or' first (lower precedence) so that
    # 'a or b and c' is evaluated as 'a or (b and c)'. Splits are quote/bracket
    # aware so a keyword inside a quoted operand (e.g. the 'and' in
    # 'read and write') is not mistaken for an operator.
    or_idx = _find_top_level(expr, " or ")
    if or_idx != -1:
        left = _evaluate_simple_expression(expr[:or_idx].strip(), namespace)
        right = _evaluate_simple_expression(expr[or_idx + 4:].strip(), namespace)
        return bool(left) or bool(right)

    and_idx = _find_top_level(expr, " and ")
    if and_idx != -1:
        left = _evaluate_simple_expression(expr[:and_idx].strip(), namespace)
        right = _evaluate_simple_expression(expr[and_idx + 5:].strip(), namespace)
        return bool(left) and bool(right)

    if expr.startswith("not "):
        inner = _evaluate_simple_expression(expr[4:].strip(), namespace)
        return not bool(inner)

    # Comparison operators (order matters — check multi-char ops first). Split at
    # the first top-level occurrence so an operator inside a quoted operand is
    # ignored.
    for op in ("!=", "==", ">=", "<=", ">", "<", " not in ", " in "):
        op_idx = _find_top_level(expr, op)
        if op_idx != -1:
            left = _evaluate_simple_expression(expr[:op_idx].strip(), namespace)
            right = _evaluate_simple_expression(expr[op_idx + len(op):].strip(), namespace)
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
        items = [
            _evaluate_simple_expression(i.strip(), namespace)
            for i in _split_top_level_commas(inner)
        ]
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

    # Single expression: return typed value (preserving type).
    #
    # The fast path must fire only when the whole template is one ``{{ ... }}``
    # block. Neither ``fullmatch`` nor a match-span check on ``_EXPR_PATTERN``
    # can decide this reliably: the non-greedy body stops at the first ``}}``,
    # so ``fullmatch`` over-expands ``"{{ a }} {{ b }}"`` to garbage (returning
    # ``None`` and bypassing interpolation, issue #3208), while a span check
    # trips over a literal ``}}`` inside a string argument such as
    # ``{{ inputs.text | contains('}}') }}`` and mis-routes it to interpolation
    # (coercing its typed return to ``str``). ``_is_single_expression`` scans
    # for a block-closing ``}}`` outside string literals, so both cases resolve
    # correctly.
    stripped = template.strip()
    if _is_single_expression(stripped):
        return _evaluate_simple_expression(stripped[2:-2].strip(), namespace)

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
    # Treat plain "false"/"true" strings as booleans so that
    # condition: "false" (without {{ }}) behaves as expected.
    if isinstance(result, str):
        lower = result.lower()
        if lower == "false":
            return False
        if lower == "true":
            return True
    return bool(result)
