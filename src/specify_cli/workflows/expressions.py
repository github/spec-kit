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
    """Join a list into a string with *separator*.

    Raises ``ValueError`` when *separator* is not a string. Without the guard a
    non-string separator (an authoring mistake like ``| join(5)``) reaches
    ``str.join`` and raises a cryptic ``AttributeError: 'int' object has no
    attribute 'join'`` that escapes the evaluator and crashes the whole run,
    since the engine wraps neither expression evaluation nor ``execute`` in a
    try/except. Mirrors the strict argument handling in ``from_json``.
    """
    if not isinstance(separator, str):
        raise ValueError(
            f"join: expected a string separator, got {type(separator).__name__}"
        )
    if isinstance(value, list):
        return separator.join(str(v) for v in value)
    return str(value)


def _filter_map(value: Any, attr: str) -> list[Any]:
    """Map a list of dicts to a specific attribute.

    Raises ``ValueError`` when *attr* is not a string. Without the guard a
    non-string attribute (an authoring mistake like ``| map(5)``) reaches
    ``attr.split(".")`` and raises a cryptic ``AttributeError: 'int' object has
    no attribute 'split'`` that escapes the evaluator and crashes the whole run,
    since the engine wraps neither expression evaluation nor ``execute`` in a
    try/except. Mirrors the strict argument handling in ``from_json``.
    """
    if not isinstance(attr, str):
        raise ValueError(
            f"map: expected a string attribute name, got {type(attr).__name__}"
        )
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


def _filter_contains(value: Any, substring: Any) -> bool:
    """Check if a string or list contains *substring*.

    For a string *value*, *substring* must itself be a string: ``x in y`` on a
    string requires a string left operand, so a non-string argument (an
    authoring mistake like ``| contains(5)``) would otherwise raise a cryptic
    ``TypeError`` that escapes the evaluator and crashes the whole run, since
    the engine wraps neither expression evaluation nor ``execute`` in a
    try/except. Raise a ``ValueError`` naming the problem instead, mirroring the
    strict argument handling in ``from_json``. For a list *value*, membership of
    any element type is legitimate (``5 in [1, 2, 5]``), so that branch is left
    unguarded.
    """
    if isinstance(value, str):
        if not isinstance(substring, str):
            raise ValueError(
                "contains: expected a string argument when the value is a "
                f"string, got {type(substring).__name__}"
            )
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
    workflow_dir = getattr(context, "workflow_dir", None) or ""
    ns["context"] = {"run_id": run_id, "workflow_dir": workflow_dir}
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


def _interpolate_expressions(template: str, namespace: dict[str, Any]) -> str:
    """Substitute every top-level ``{{ ... }}`` block in *template*, quote-aware.

    Walks the template and, for each block, finds the closing ``}}`` that lies
    outside string literals -- the same quote-scanning used by
    ``_is_single_expression``. This keeps a literal ``}}`` inside a string
    argument (e.g. ``| default('}}')``) from prematurely closing a block.

    ``_EXPR_PATTERN.sub`` cannot do this: its non-greedy body stops at the first
    ``}}`` regardless of quoting, so in a multi-expression template any block
    whose argument contains a literal ``}}`` is captured truncated and mis-parsed
    (raising ``ValueError`` from the filter parser). #3208/#3228 fixed exactly
    this for the single-expression fast path but left the interpolation path on
    the old regex.
    """
    out: list[str] = []
    i = 0
    n = len(template)
    while i < n:
        start = template.find("{{", i)
        if start == -1:
            out.append(template[i:])
            break
        out.append(template[i:start])
        # Scan for the block-closing ``}}`` that is outside any string literal.
        j = start + 2
        quote: str | None = None
        close = -1
        while j < n:
            ch = template[j]
            if quote is not None:
                if ch == quote:
                    quote = None
            elif ch in ("'", '"'):
                quote = ch
            elif ch == "}" and j + 1 < n and template[j + 1] == "}":
                close = j
                break
            j += 1
        if close == -1:
            # No quote-aware close. Two sub-cases, both kept identical to the old
            # regex so a malformed template is never silently hidden:
            #   * a raw ``}}`` still exists in the tail (e.g. an unbalanced quote
            #     in a filter arg swallowed the real delimiter) -- fall back to
            #     that first raw ``}}`` and evaluate, letting the parser surface
            #     a ValueError just as ``_EXPR_PATTERN.sub`` would have.
            #   * no ``}}`` at all -- a genuinely unterminated ``{{``; leave the
            #     tail verbatim, again matching the regex (which cannot match).
            raw_close = template.find("}}", start + 2)
            if raw_close == -1:
                out.append(template[start:])
                break
            close = raw_close
        val = _evaluate_simple_expression(template[start + 2:close].strip(), namespace)
        out.append(str(val) if val is not None else "")
        i = close + 2
    return "".join(out)


def _split_top_level(text: str, sep: str) -> list[str]:
    """Split *text* on each occurrence of *sep* that lies outside any quoted
    string or nested brackets.

    Used to break a filter chain (``a | map('x') | join(',')``) into its
    individual filter segments without splitting on a ``|`` that appears inside
    a quoted argument. Each returned segment is a slice at a top-level
    boundary, so the quote/bracket scan restarts cleanly on the remainder.
    """
    parts: list[str] = []
    start = 0
    while True:
        idx = _find_top_level(text[start:], sep)
        if idx == -1:
            parts.append(text[start:])
            return parts
        parts.append(text[start:start + idx])
        start += idx + len(sep)


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


def _apply_filter(value: Any, filter_expr: str, namespace: dict[str, Any]) -> Any:
    """Apply a single pipe filter segment to *value*.

    *filter_expr* is one link of a filter chain — the text between two
    top-level ``|`` separators, already stripped (e.g. ``map('name')``,
    ``default('x')``, ``from_json``). Returns the filtered value so the caller
    can feed it into the next link.

    Raises ``ValueError`` on any mis-wired or unknown filter rather than
    silently returning *value* unchanged: a passthrough would turn a mistyped
    or unsupported filter into a wrong result with no signal.
    """
    # `from_json` is strict: it takes no arguments and tolerates no trailing
    # tokens. Match on the leading filter name and require the whole filter to
    # be exactly `from_json`, so every mis-wired form (`from_json()`,
    # `from_json('x')`, `from_json)`, `from_json extra`) fails loudly instead of
    # silently falling through to the unknown-filter path.
    leading = re.match(r"\w+", filter_expr)
    if leading and leading.group(0) == "from_json":
        if filter_expr != "from_json":
            raise ValueError(
                "from_json: expected '| from_json' with no arguments or "
                f"trailing tokens, got '| {filter_expr}'"
            )
        return _filter_from_json(value)

    # Parse filter name and argument. Use fullmatch (not match) so trailing
    # tokens after the closing paren — e.g. a comparison/boolean operator that
    # binds looser than the pipe, as in ``count | default(0) > 5`` — are not
    # silently discarded but fall through to the "unsupported form" ValueError
    # below, mirroring the strict trailing-token handling of the from_json
    # branch above. The greedy ``.+`` still handles literal ``)`` and ``|``
    # inside quoted args.
    filter_match = re.fullmatch(r"(\w+)\((.+)\)", filter_expr)
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
    if filter_expr == "default":
        return _filter_default(value)
    # No recognized filter matched. Fail loudly rather than silently returning
    # the unfiltered value. Distinguish a *registered* filter used in an
    # unsupported form (e.g. `| join` or `| map` with no argument) from a
    # genuinely unknown filter name, so the message names the real problem
    # instead of calling a known filter "unknown".
    name = leading.group(0) if leading else filter_expr
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
    # Filters chain left-to-right: `list | map('name') | join(', ')` feeds each
    # filter's result into the next, so `map` (which yields a list) can be
    # rendered by `join`. Splitting only at the first pipe would hand the whole
    # tail to one filter and mangle any later `|`.
    pipe_idx = _find_top_level(expr, "|")
    if pipe_idx != -1:
        segments = _split_top_level(expr, "|")
        value = _evaluate_simple_expression(segments[0].strip(), namespace)
        for segment in segments[1:]:
            value = _apply_filter(value, segment.strip(), namespace)
        return value

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
                return _safe_membership(left, right, negate=False)
            if op == " not in ":
                return _safe_membership(left, right, negate=True)

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
            # Drop empty segments from trailing/leading/double commas ([1, 2,] ->
            # [1, 2], not [1, 2, None]). An intentional empty-string element
            # ('') strips to "''" (truthy), so ['', 'a'] is preserved.
            if i.strip()
        ]
        return items

    # Variable reference (dot-path)
    return _resolve_dot_path(namespace, expr)


def _coerce_number(value: Any) -> Any:
    """Return *value* as int/float if it is a numeric string, else unchanged."""
    if isinstance(value, str):
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return value
    return value


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
    cl, cr = _coerce_number(left), _coerce_number(right)
    # Only use the coerced numbers when both converted; otherwise a numeric
    # string paired with a plain string would become an int-vs-str mismatch
    # (always False) rather than a lexicographic string comparison.
    if isinstance(cl, (int, float)) and isinstance(cr, (int, float)):
        left, right = cl, cr
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

    # Multi-expression: interpolate each block inline. Uses a quote-aware scan
    # (not ``_EXPR_PATTERN.sub``) so a literal ``}}`` inside a string argument
    # in any block does not close that block early -- matching the handling the
    # single-expression path above already got in #3208/#3228.
    return _interpolate_expressions(template, namespace)


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
