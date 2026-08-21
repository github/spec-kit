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


def _find_block_close(text: str, start: int) -> int:
    """Index of the ``}}`` closing the block opened by the ``{{`` at *start*, or -1.

    Quote-aware, so a literal ``}}`` inside a string argument
    (``{{ inputs.text | default('}}') }}``) does not close the block early --
    the same rule ``_is_single_expression`` applies. Shared with
    ``condition_is_never_evaluated`` so the validator cannot disagree with the
    substitution it is predicting.
    """
    quote: str | None = None
    i = start + 2
    n = len(text)
    while i < n:
        ch = text[i]
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "}" and i + 1 < n and text[i + 1] == "}":
            return i
        i += 1
    return -1


def _first_unclosable_block(text: str) -> str | None:
    """How ``_interpolate_expressions`` will fail on the first block it cannot
    close with the quote-aware scan, or ``None`` when every block closes.

    Returns ``"evaluated"`` when a raw ``}}`` still follows the opener -- the
    interpolator falls back to it and evaluates the truncated body, which reaches
    the filter parser and raises ``ValueError``. Returns ``"verbatim"`` when no
    ``}}`` follows at all -- the tail is emitted unchanged, so it survives into the
    result as truthy text.

    Walks blocks exactly the way ``_interpolate_expressions`` does, continuing past
    each block that *does* close. Checking only the first opener let a later
    unterminated block through both validators: ``{{ true }} and {{ inputs.ready``
    closes its first block, so the scan stopped and reported no fault, while
    interpolation leaves ``and {{ inputs.ready`` in the result and ``bool()`` makes
    the condition always true.
    """
    i = 0
    while True:
        start = text.find("{{", i)
        if start == -1:
            return None
        close = _find_block_close(text, start)
        if close == -1:
            return "evaluated" if text.find("}}", start + 2) != -1 else "verbatim"
        i = close + 2


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
        close = _find_block_close(template, start)
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


# Order matters -- multi-char operators first, so "!=" is not split as "!" + "=".
# Shared with the remediation check so a validator cannot drift from what the
# evaluator will actually split on.
_COMPARISON_OPERATORS = ("!=", "==", ">=", "<=", ">", "<", " not in ", " in ")


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
    for op in _COMPARISON_OPERATORS:
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
    #
    # Strip before matching: the string a condition resolves to is most often
    # captured command output, and a ``shell`` step stores ``proc.stdout``
    # verbatim, so ``run: echo false`` resolves to ``"false\n"``. Without the
    # strip that trailing newline matches neither branch and falls through to
    # ``bool("false\n")`` -> True, silently taking an ``if`` step's ``then``
    # branch (and keeping a ``while``/``do-while`` looping) on a step that
    # printed "false". A workflow cannot strip it itself -- the registered
    # filters are default/join/map/contains/from_json, there is no ``trim``.
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


def condition_is_never_evaluated(condition: Any) -> bool:
    """True when a string *condition* is silently treated as always-true text.

    ``evaluate_condition`` resolves its argument through
    ``evaluate_expression``, which only substitutes ``{{ ... }}`` blocks. A
    string with no such block comes back unchanged, and — unless it reads
    ``true``/``false`` — is then coerced by ``bool()``. So an expression
    authored without the braces, e.g. ``condition: inputs.count > 100``, is
    never evaluated at all: it is a non-empty string, so the ``if`` step always
    takes ``then`` and a ``while``/``do-while`` step always runs to
    ``max_iterations``.

    That is the same silent-truthiness authoring mistake the step validators
    already reject for a list/dict/number condition, and it is easy to write:
    GitHub Actions accepts a bare expression in ``if:``.

    The empty string is excluded — it coerces to ``False``, which is a definite
    answer rather than a silent always-true. Non-empty whitespace is *not*
    excluded: ``bool("   ")`` is true, and ``evaluate_condition`` strips only
    while testing the ``true``/``false`` keywords before falling through to
    ``bool()`` on the raw string. That runtime behaviour is pinned deliberately
    by ``test_condition_whitespace_only_string_stays_truthy``, so the authoring
    mistake has to be caught here instead: ``condition: "   "`` always takes
    ``then``.
    """
    if not isinstance(condition, str):
        return False
    if condition == "":
        return False
    stripped = condition.strip()
    if not stripped:
        return True
    if stripped.lower() in ("true", "false"):
        return False
    if "{{" not in stripped:
        return True
    # An opening ``{{`` the substituter cannot close is no better than a missing
    # one -- but only when the substituter really does leave it alone.
    # ``_interpolate_expressions`` has two sub-cases when its quote-aware scan
    # fails, and they do not behave alike: with no raw ``}}`` in the tail the
    # block is emitted verbatim (never evaluated, so ``bool()`` makes it true),
    # while a raw ``}}`` further along is used as the close and the truncated
    # body *is* evaluated. Only the first is "never evaluated"; see
    # ``condition_has_malformed_expression_block`` for the second.
    return _first_unclosable_block(stripped) == "verbatim"


def condition_has_malformed_expression_block(condition: Any) -> bool:
    """True when *condition* holds a ``{{`` block the quote-aware scan cannot close,
    but which ``_interpolate_expressions`` still evaluates through its raw-close
    fallback.

    This is a different fault from the one
    ``condition_is_never_evaluated`` reports, and it deserves a different message.
    The block is not skipped: the interpolator takes the first raw ``}}`` after the
    opener and evaluates whatever it truncated, so

        {{ inputs.missing | default('oops }}

    reaches ``_apply_filter`` and raises ``ValueError`` at run time. The truncation does
    not always raise -- ``{{ inputs.x == '}}'`` evaluates to the residual ``"False'"`` --
    but either way what runs is not what was written, so "never evaluated and always
    true" is the wrong report.

    Kept separate from the never-evaluated check rather than folded in, because the
    two need opposite advice: one says "you forgot the braces", this one says "your
    delimiters or quotes do not balance".
    """
    if not isinstance(condition, str):
        return False
    stripped = condition.strip()
    if not stripped or stripped.lower() in ("true", "false"):
        return False
    return _first_unclosable_block(stripped) == "evaluated"


def _strip_stray_delimiters(text: str) -> str:
    """Remove every ``{{``/``}}`` that lies outside a quoted operand.

    Quote-aware for the same reason the rest of this module is: ``inputs.x == '}}'``
    holds a delimiter as *data*, and a blanket ``re.sub`` would eat it and change
    what the corrected condition compares against. Whitespace orphaned by a removed
    delimiter collapses to one separator so the suggestion still reads as an
    expression; whitespace inside a quoted operand is never touched.

    ``_find_top_level`` cannot serve here: it counts ``{`` and ``}`` as bracket
    depth, so it never reports a ``{{`` as a top-level token at all.
    """
    out: list[str] = []
    quote: str | None = None
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if quote is not None:
            out.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            continue
        if text.startswith("{{", i) or text.startswith("}}", i):
            i += 2
            while i < n and text[i].isspace():
                i += 1
            while out and out[-1].isspace():
                out.pop()
            out.append(" ")
            continue
        out.append(ch)
        i += 1
    return "".join(out)

def format_condition_correction(condition: Any) -> str:
    """Render *condition* wrapped in ``{{ }}`` as a quoted, paste-ready YAML scalar.

    The validators hand this back as the corrected form, so it has to survive a
    round trip through a YAML parser. A plain ``"{{ ... }}"`` does not: a
    condition holding a double quote (``inputs.name == "zzz"``) closes the
    scalar early and the workflow file no longer loads. Quoting is therefore
    chosen from the content. That enumeration was incomplete: a condition loaded
    from a YAML literal block can carry a newline, which a double-quoted scalar
    folds, so the correction did not round-trip.

    ``json.dumps`` decides it instead. Every JSON string is a valid YAML
    double-quoted scalar, and it escapes the quotes, backslashes, newlines and
    other control characters that hand-rolled quoting has to enumerate.
    ``ensure_ascii=False`` keeps non-ASCII operands readable rather than
    expanding them into numeric escapes.

    A stray delimiter is dropped rather than nested: ``{{ inputs.count > 100``
    corrects to ``"{{ inputs.count > 100 }}"``, not to a doubled ``{{ {{ ... }} }}``.
    Every stray delimiter goes, not only the ones sitting at the edges. Trimming
    just the edges left ``prefix {{ inputs.ready`` reading
    ``"{{ prefix {{ inputs.ready }}"`` -- an unclosed inner block, and one whose
    complete *outer* block then carried the correction straight back through
    ``condition_is_never_evaluated`` as if it were valid.
    """
    core = _strip_stray_delimiters(str(condition)).strip()
    # A blank core has nothing to wrap; render the empty block rather than the
    # double-spaced "{{  }}" that string concatenation would otherwise produce.
    body = "{{ " + core + " }}" if core else "{{ }}"
    return json.dumps(body, ensure_ascii=False)


def _has_unbalanced_quote(text: str) -> bool:
    """True when a quote opened in *text* is never closed.

    Same left-to-right, first-quote-wins scan the rest of this module uses, so the
    answer agrees with what ``_find_block_close`` and ``_strip_stray_delimiters``
    consider "inside a string".
    """
    quote: str | None = None
    for ch in text:
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
    return quote is not None


_BRACKET_PAIRS = {")": "(", "]": "[", "}": "{"}

# The operators the evaluator delimits with spaces; derived so the check cannot
# drift from _COMPARISON_OPERATORS.
_WORD_OPERATORS = tuple(
    op for op in (" or ", " and ") + _COMPARISON_OPERATORS if op.startswith(" ")
)


def _has_unbalanced_bracket(text: str) -> bool:
    """True when brackets outside a quoted operand do not nest and match.

    A depth counter is not enough: it calls ``inputs.f(]`` balanced, because the
    ``]`` cancels the ``(``. The evaluator then resolves that body to ``None`` and
    the comparison is false, which is the inversion this module is trying to keep
    out of the suggested correction. Track the opener types instead.
    """
    stack: list[str] = []
    quote: str | None = None
    for ch in text:
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch in "([{":
            stack.append(ch)
        elif ch in _BRACKET_PAIRS and (not stack or stack.pop() != _BRACKET_PAIRS[ch]):
            return True
    return bool(stack)


def _has_incomplete_operand(text: str) -> bool:
    """True when an operator in *text* is missing an operand on either side.

    Splits on **every** top-level occurrence rather than the first. Checking only
    the first is the same defect this module exists to reject one level up: it let
    ``inputs.a == inputs.b ==`` through, because the leading ``==`` has operands on
    both sides and the scan stopped there.

    Reads ``_COMPARISON_OPERATORS`` from the evaluator rather than restating it, so
    the check cannot drift from what ``_evaluate_simple_expression`` splits on.
    """
    stripped = text.strip()
    if not stripped:
        return True

    # `not x` is a valid prefix form; `and x` and `or x` are not, and none of the
    # three is valid alone or trailing. The keyword scans below use bare words
    # because a leading operator has no space in front of it to match on.
    if stripped in ("and", "or", "not") or stripped.endswith(" not"):
        return True
    # Word operators lose their delimiting space at the ends of a stripped core, so
    # a trailing "not in" or a leading "and" needs matching without it. Derived from
    # the evaluator's own table rather than restated.
    for op in _WORD_OPERATORS:
        if stripped.endswith(op.rstrip()) or stripped.startswith(op.lstrip()):
            return True

    for op in (" or ", " and ") + _COMPARISON_OPERATORS:
        if _find_top_level(stripped, op) == -1:
            continue
        if any(not segment.strip() for segment in _split_top_level(stripped, op)):
            return True

    return _find_top_level(stripped, "|") != -1 and any(
        not segment.strip() for segment in _split_top_level(stripped, "|")
    )


# The roots _build_namespace supplies. A reference to anything else resolves to
# None, so a correction built on one turns a truthy condition false.
_NAMESPACE_ROOTS = ("inputs", "steps", "item", "fan_in", "context")

# Exactly what _resolve_dot_path accepts: a name, optionally one numeric index.
_PATH_SEGMENT = re.compile(r"^[\w-]+(\[\d+\])?$")


class _ProbeNamespace(dict):
    """Namespace for the parse probe: every root exists, every leaf is absent.

    Enough for ``_evaluate_simple_expression`` to walk the grammar without needing
    real inputs. Deliberately *not* resolving leaves to a sentinel value: a probe
    that answers every lookup also answers ``inputs.count+1``, which is the
    malformed shape the probe is meant to expose.
    """

    def __missing__(self, key: str) -> "_ProbeNamespace":  # noqa: UP037  # pragma: no cover
        return _ProbeNamespace()


def _evaluator_rejects(text: str) -> str | None:
    """The evaluator's own complaint about how *text* is wired, or ``None``.

    Structural checks cannot establish that a core is parseable -- four rounds of
    review found a new shape each time -- so this asks the evaluator. It reports
    only the two failures ``_apply_filter`` raises about the expression itself: an
    unknown filter name, and a registered filter used in an unsupported form.

    Anything else a probe run raises is about the probe's placeholder values, not
    the author's text. ``steps.emit.output.stdout | from_json`` is valid against a
    string output and is exercised in ``tests/test_workflows.py``; the probe hands
    ``from_json`` a dict and it raises, so treating every error as a rejection
    withheld a correction from a perfectly good condition.
    """
    try:
        _evaluate_simple_expression(
            text, {root: _ProbeNamespace() for root in _NAMESPACE_ROOTS}
        )
    except ValueError as exc:
        message = str(exc)
        # Every error _apply_filter raises about the filter *expression* quotes the
        # segment back as `got '| ...'`. Its value errors instead name the type they
        # received, which under a probe is the placeholder, not anything the author
        # wrote -- treating those as rejections withheld corrections from valid
        # conditions such as `steps.emit.output.stdout | from_json`.
        if "got '| " in message:
            return message.split(":", 1)[0]
    except Exception:  # noqa: BLE001 - probe values, not the author's text
        return None
    return None



def _looks_numeric(text: str) -> bool:
    """Mirror the evaluator's numeric literal test exactly.

    `_evaluate_simple_expression` only calls `float()` when a `.` is present and
    `int()` otherwise, so `1e3` is not a number to it -- it falls through to a path
    lookup and resolves to None. A bare `float()` here accepted `1e3` and the
    correction turned a truthy condition false.
    """
    try:
        if "." in text:
            float(text)
        else:
            int(text)
    except (ValueError, TypeError):
        return False
    return True


def _is_literal(text: str) -> bool:
    """Mirror the evaluator's literal tests exactly.

    The string case is the opening quote's *matching close being the final
    character*, not first/last-character equality: `'a' 'b'` passes the latter but
    is two literals to the evaluator, which falls through to a path lookup.
    """
    if text[:1] in ("'", '"') and text.find(text[0], 1) == len(text) - 1:
        return True
    return text.lower() in ("true", "false", "none", "null") or _looks_numeric(text)


def _unresolvable_term(text: str) -> str | None:
    """The first operand in *text* the evaluator cannot resolve, or ``None``.

    Walks operands the way ``_evaluate_simple_expression`` does -- filters, then
    ``or``/``and``/``not``, then comparisons -- and checks each leaf. A leaf must be
    a literal or a dotted path rooted in ``_NAMESPACE_ROOTS``.

    Enumerating broken shapes is what made this take several rounds: each new gate
    only knew the shapes named so far. ``inputs.a === inputs.b`` split cleanly on
    ``==`` and looked complete, while the evaluator read ``= inputs.b`` as a path
    and resolved it to ``None``; ``bogus == 'x'`` passed for the same reason one
    level up. Recursing to the leaves covers both without naming either.
    """
    stripped = text.strip()
    if not stripped:
        return "an operand is empty"

    if _find_top_level(stripped, "|") != -1:
        segments = _split_top_level(stripped, "|")
        reason = _unresolvable_term(segments[0])
        if reason is not None:
            return reason
        # A filter argument is an ordinary operand to `_apply_filter`, which
        # evaluates it with `_evaluate_simple_expression` like any other. Skipping
        # it let `inputs.tags | join(bogus)` be offered as paste-ready: `bogus` is
        # no namespace root, resolves to None, and the wrapped form then raises
        # `join: expected a string separator, got NoneType`. Parse with the same
        # pattern `_apply_filter` uses, so a form this does not recognize is left
        # to the evaluator probe rather than guessed at here.
        for segment in segments[1:]:
            match = re.fullmatch(r"(\w+)\((.+)\)", segment.strip())
            if match is None:
                continue
            reason = _unresolvable_term(match.group(2))
            if reason is not None:
                return reason
        return None

    for op in (" or ", " and "):
        idx = _find_top_level(stripped, op)
        if idx != -1:
            return _unresolvable_term(stripped[:idx]) or _unresolvable_term(
                stripped[idx + len(op):]
            )

    if stripped.startswith("not "):
        return _unresolvable_term(stripped[4:])

    for op in _COMPARISON_OPERATORS:
        idx = _find_top_level(stripped, op)
        if idx != -1:
            return _unresolvable_term(stripped[:idx]) or _unresolvable_term(
                stripped[idx + len(op):]
            )

    if _is_literal(stripped):
        return None

    # A list literal is a term the evaluator understands, and it recurses into the
    # elements rather than resolving the brackets as a name. Not mirroring that
    # denied the correction to `inputs.tag in ['x', 'y']` -- a condition wrapping
    # repairs completely -- while reporting the list as an unresolvable name. The
    # empty-segment skip matches `_evaluate_simple_expression`, which drops them so
    # `[1, 2,]` is `[1, 2]` rather than `[1, 2, None]`.
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if not inner:
            return None
        for element in _split_top_level_commas(inner):
            if not element.strip():
                continue
            reason = _unresolvable_term(element)
            if reason is not None:
                return reason
        return None

    segments = _split_top_level(stripped, ".")
    if not _PATH_SEGMENT.match(segments[0].strip()):
        return f"{stripped!r} is not a name the evaluator can resolve"
    # `item` is the only root that is not always a mapping: `StepContext.item` is
    # `Any` and a fan-out assigns the item value itself, so when that value is a
    # list `_resolve_dot_path` indexes it and `item[0] == 'x'` resolves. Every
    # other root comes back from `_build_namespace` as a mapping, and the index
    # branch returns None for those however it is written -- so the index is
    # stripped for `item` alone rather than for roots in general.
    root = segments[0].strip()
    indexed_root = re.fullmatch(r"([\w-]+)\[\d+\]", root)
    if indexed_root is not None and indexed_root.group(1) == "item":
        root = indexed_root.group(1)
    if root not in _NAMESPACE_ROOTS:
        return (
            f"{segments[0].strip()!r} is not one of the namespace roots "
            f"({', '.join(_NAMESPACE_ROOTS)})"
        )
    for segment in segments[1:]:
        if not _PATH_SEGMENT.match(segment.strip()):
            return f"{segment.strip()!r} is not a valid path segment"
    return None


def _wrapping_would_not_repair(core: str) -> str | None:
    """Why wrapping *core* in ``{{ }}`` would not yield the expression intended.

    ``None`` when it would. Each branch names something observable about the text
    itself, deliberately not the interpolator path it will take: two earlier
    versions of this message asserted an internal route -- the raw-close fallback --
    and were wrong, because ``_is_single_expression`` accepts the wrapped form and
    sends it down the typed fast path instead.
    """
    if not core:
        return "there is no expression here to wrap"
    if _has_unbalanced_quote(core):
        return "the quote opened in it is never closed"
    if _has_unbalanced_bracket(core):
        return "its brackets do not balance"
    if _has_incomplete_operand(core):
        return "an operator in it is missing an operand"
    unresolvable = _unresolvable_term(core)
    if unresolvable is not None:
        return unresolvable
    rejected = _evaluator_rejects(core)
    if rejected is not None:
        return f"the evaluator rejects it ({rejected})"
    return None


def format_condition_remediation(condition: Any) -> str:
    """The advice sentence for a condition that is never evaluated.

    ``format_condition_correction`` wraps whatever it is handed, which is right for a
    formatter but wrong to advertise as paste-ready when wrapping cannot repair the
    input. Measured, each of these was being offered as the fix and each **inverts**
    the condition instead:

        "   "                    -> "{{ }}"                      True  -> False
        {{ inputs.name == 'abc   -> "{{ inputs.name == 'abc }}"  True  -> False
        inputs.name ==           -> "{{ inputs.name == }}"       True  -> False

    The author is told the condition is always true, pastes the suggestion, and now
    has an always-false one. Naming the fault beats handing back something that looks
    authoritative and is not -- the same call already made for
    ``condition_has_malformed_expression_block``, which offers no suggestion at all.
    """
    core = _strip_stray_delimiters(str(condition)).strip()
    reason = _wrapping_would_not_repair(core)
    if reason is None:
        return "Wrap the expression: " + format_condition_correction(condition) + "."
    return (
        f"No correction is offered because {reason}: wrapping it as written would "
        "produce a different expression from the one intended, and its result can "
        "silently invert the condition rather than repair it. Complete the "
        "expression, or use the literal true or false."
    )
