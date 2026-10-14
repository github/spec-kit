"""The current hand-written workflow expression engine.

This module is the engine behind the ``engine.py`` contract. It owns the
grammar walk (``_evaluate_simple_expression``), the filter dispatcher
(``_apply_filter``), template interpolation, and the probe/primitives the
condition diagnostics consume. It imports the shared leaf modules
(``namespace``, ``filters``, ``operators``, ``template``) and is imported only
by ``engine.py`` and the package facade.
"""

from __future__ import annotations

import re
from contextvars import ContextVar
from typing import Any

from .filters import (
    _EXPECTED_FILTERS,
    _REGISTERED_FILTERS,
    _ZERO_ARG_FILTERS,
    _filter_contains,
    _filter_default,
    _filter_join,
    _filter_map,
    _filter_split,
)
from .namespace import _NAMESPACE_ROOTS, _resolve_dot_path
from .operators import _safe_compare, _safe_membership
from .template import (
    _collapse_whitespace,
    _find_block_close,
    _find_top_level,
    _first_unclosable_block,
    _is_single_expression,
    _is_single_list_literal,
    _is_wrapped_in_parens,
    _split_top_level,
    _split_top_level_commas,
)


# The contract this engine fulfills. ``engine.py`` re-exports exactly these;
# anything else here is an internal of this engine.
__all__ = [
    "_COMPARISON_OPERATORS",
    "_WORD_OPERATORS",
    "_collect_leaves",
    "_evaluate_template",
    "_evaluator_rejects",
    "_first_unclosable_block",
    "_has_incomplete_operand",
    "_is_single_expression",
    "_leaf_sink",
    "_syntax_error",
]


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
    # Zero-argument filters are strict: they take no arguments and tolerate no
    # trailing tokens. Match on the leading filter name and require the whole
    # filter to be exactly that name, so every mis-wired form (`from_json()`,
    # `from_json('x')`, `from_json)`, `from_json extra`, and the same for
    # `upper`/`lower`/`length`/`to_json`) fails loudly instead of silently
    # falling through to the unknown-filter path.
    leading = re.match(r"\w+", filter_expr)
    if leading and leading.group(0) in _ZERO_ARG_FILTERS:
        fname = leading.group(0)
        if filter_expr != fname:
            raise ValueError(
                f"{fname}: expected '| {fname}' with no arguments or "
                f"trailing tokens, got '| {filter_expr}'"
            )
        return _ZERO_ARG_FILTERS[fname](value)

    # Parse filter name and argument. Use fullmatch (not match) so trailing
    # tokens after the closing paren — e.g. a comparison/boolean operator that
    # binds looser than the pipe, as in ``count | default(0) > 5`` — are not
    # silently discarded but fall through to the "unsupported form" ValueError
    # below, mirroring the strict trailing-token handling of the from_json
    # branch above. The greedy ``.+`` still handles literal ``)`` and ``|``
    # inside quoted args.
    filter_match = re.fullmatch(r"(\w+)\((.+)\)", filter_expr)
    # A multi-argument call is not a supported form: every filter here takes
    # exactly one argument, and the whole captured argument text was handed to
    # ``_evaluate_simple_expression`` as ONE expression. "1, 2" is not a valid
    # expression, so it evaluated to None -- making ``default(1, 2)`` return
    # None (silently wrong) and ``join(",", "extra")`` raise a message blaming
    # the separator rather than the extra argument. Fall through to the
    # unsupported-form error below instead, which names the filter and lists
    # the accepted forms.
    #
    # Use ``_find_top_level``, the same scanner the operator splitting uses: it
    # skips commas inside quotes AND inside nested brackets, so a single
    # argument that happens to contain a comma still works -- ``join(", ")``,
    # ``default("a, b")``, and the list literals the evaluator supports
    # (``default([1, 2])``).
    #
    # List literals are the only container form ``_evaluate_simple_expression``
    # implements; a mapping such as ``{"a": 1}`` has no branch there and falls
    # through to dot-path resolution, which yields ``None``. The scanner does
    # skip commas inside braces too, so nothing here changes if that ever gains
    # support -- but do not read this comment as a promise that it exists.
    if filter_match and _find_top_level(filter_match.group(2), ",") != -1:
        filter_match = None
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
        if fname == "split":
            return _filter_split(value, farg)
    # Filter without args
    if filter_expr == "default":
        return _filter_default(value)
    # No recognized filter matched. Fail loudly rather than silently returning
    # the unfiltered value. Distinguish a *registered* filter used in an
    # unsupported form (e.g. `| join` or `| map` with no argument) from a
    # genuinely unknown filter name, so the message names the real problem
    # instead of calling a known filter "unknown".
    name = leading.group(0) if leading else filter_expr
    # Derived from the filter table, so the message lists exactly what is
    # registered instead of a second copy of the set.
    expected = _EXPECTED_FILTERS
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

# Set only while `_collect_leaves` probes an expression; None everywhere else, so
# a normal evaluation costs one `.get()`. A ContextVar rather than a module global
# so concurrent probes cannot append into each other's list.
_leaf_sink: ContextVar[list[str] | None] = ContextVar("_leaf_sink", default=None)


def _evaluate_simple_expression(expr: str, namespace: dict[str, Any]) -> Any:
    """Evaluate a simple expression against the namespace.

    Supports:
    - Dot-path access: ``steps.specify.output.file``
    - Comparisons: ``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``
    - Boolean operators: ``and``, ``or``, ``not``
    - ``in``, ``not in``
    - Pipe filters: ``| default('...')``, ``| join(', ')``, ``| contains('...')``, ``| from_json``, ``| map('...')``, ``| split(',')``, ``| upper``, ``| lower``, ``| length``, ``| to_json``
    - String and numeric literals
    """
    expr = _collapse_whitespace(expr)

    # String literal — only when the WHOLE expression is one quoted string,
    # i.e. the opening quote's matching close is the final character. Checking
    # startswith/endswith alone would also grab `'a' == 'b'` and strip it to the
    # garbage `a' == 'b`; a genuine single literal short-circuits here so quoted
    # strings containing `|` or operator keywords are not mis-parsed downstream.
    if expr[:1] in ("'", '"') and expr.find(expr[0], 1) == len(expr) - 1:
        return expr[1:-1]

    # A parenthesised group. The operator scans below deliberately skip over
    # bracketed text so an operator inside a quoted or nested operand is not
    # split on -- which also means nothing ever looked inside a group that
    # wraps the WHOLE expression. `(a or b) and c` split at the top-level
    # `and`, then evaluated `(a or b)` as a dot path, found no such key, and
    # returned None: the `or` was never evaluated and the whole thing read
    # false. Unwrap here so grouping means what it says.
    if _is_wrapped_in_parens(expr):
        return _evaluate_simple_expression(expr[1:-1], namespace)

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
        # The pipe is detected before the operators below, so a filter written on
        # the right-hand operand of a comparison was applied to the comparison's
        # BOOLEAN RESULT instead: `count > limit | default(5)` evaluated
        # `count > limit` first and then `default` on the bool, which is a no-op,
        # so the expression silently returned the comparison against the
        # *unfiltered* operand. This is the mirror of a filter followed by a
        # comparison (`default('7') > '5'`), which this module already refuses
        # rather than guessing at the intended precedence. Refuse both the same
        # way, so an ambiguous expression is reported instead of quietly
        # producing the answer the author did not ask for.
        head = segments[0].strip()
        # Unary ``not`` is a leading prefix, not an infix token, so it has no
        # surrounding space for the scan below to match -- it has to be checked
        # the same way the parser itself does (``expr.startswith("not ")``).
        # Without this, ``not inputs.missing | default(1)`` still evaluated
        # ``not inputs.missing`` first and applied the filter to that boolean,
        # which is the exact mis-binding this guard exists to reject.
        # (A ``not`` that follows ``and``/``or`` is already caught by those
        # tokens below.)
        _ambiguous_op = "not" if head.startswith("not ") else None
        if _ambiguous_op is None:
            for _op in ("!=", "==", ">=", "<=", ">", "<", " not in ", " in ",
                        " or ", " and "):
                if _find_top_level(head, _op) != -1:
                    _ambiguous_op = _op.strip()
                    break
        if _ambiguous_op is not None:
            raise ValueError(
                f"ambiguous filter precedence in '{expr}': "
                f"'| {segments[1].strip()}' would apply to the result of "
                f"'{head}', not to an operand of '{_ambiguous_op}'. Filter the "
                f"operand in its own expression instead."
            )
        value = _evaluate_simple_expression(head, namespace)
        sink = _leaf_sink.get()
        for segment in segments[1:]:
            if sink is None:
                value = _apply_filter(value, segment.strip(), namespace)
                continue
            # Probing. A filter handed a placeholder can raise on it -- from_json
            # on a mapping is the common one -- and letting that end the walk
            # hides every leaf further along the chain, which is the one thing
            # this collection exists to report: `inputs.blob | from_json |
            # contains(bogus)` recorded `inputs.blob` and stopped, so `bogus`
            # was never offered to _unresolvable_leaf. _apply_filter evaluates a
            # filter's argument before it can raise on the value, so the leaves
            # of the failing segment are already recorded when we get here.
            # Carry a fresh placeholder so the next filter sees the same kind of
            # unknown the namespace hands out. Real evaluation is untouched: the
            # sink is armed only by _collect_leaves, and _evaluator_rejects runs
            # its own probe without it, so a mis-wired filter is still reported.
            try:
                value = _apply_filter(value, segment.strip(), namespace)
            except Exception:  # noqa: BLE001 - probe values, not the author's text
                value = _ProbeNamespace()
        return value

    # Boolean operators — parse 'or' first (lower precedence) so that
    # 'a or b and c' is evaluated as 'a or (b and c)'. Splits are quote/bracket
    # aware so a keyword inside a quoted operand (e.g. the 'and' in
    # 'read and write') is not mistaken for an operator.
    or_idx = _find_top_level(expr, " or ")
    if or_idx != -1:
        left = _evaluate_simple_expression(expr[:or_idx].strip(), namespace)
        # Validation probes must still visit operands that runtime can skip.
        if bool(left) and not isinstance(namespace, _ProbeNamespace):
            return True
        right = _evaluate_simple_expression(expr[or_idx + 4:].strip(), namespace)
        return bool(left) or bool(right)

    and_idx = _find_top_level(expr, " and ")
    if and_idx != -1:
        left = _evaluate_simple_expression(expr[:and_idx].strip(), namespace)
        if not bool(left) and not isinstance(namespace, _ProbeNamespace):
            return False
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
    if _is_single_list_literal(expr):
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

    # Variable reference (dot-path). This is the one place a substring stops being
    # grammar and becomes a name to resolve, so it is where a probe can learn what
    # the evaluator will actually look up. Literals have all returned above.
    sink = _leaf_sink.get()
    if sink is not None:
        sink.append(expr)
    return _resolve_dot_path(namespace, expr)


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


def _evaluate_template(template: str, namespace: dict[str, Any]) -> Any:
    """Evaluate *template* against an already-built *namespace*.

    If the whole template is one ``{{ ... }}`` block, returns the raw value
    (preserving type). Otherwise, interpolates each block inline and returns a
    string. Split out of ``evaluate_expression`` so the API layer owns only
    namespace construction and the engine contract exposes the whole decision.

    The single-expression fast path must fire only when the whole template is
    one ``{{ ... }}`` block. Neither ``fullmatch`` nor a match-span check on
    ``_EXPR_PATTERN`` can decide this reliably: the non-greedy body stops at the
    first ``}}``, so ``fullmatch`` over-expands ``"{{ a }} {{ b }}"`` to garbage
    (returning ``None`` and bypassing interpolation, issue #3208), while a span
    check trips over a literal ``}}`` inside a string argument such as
    ``{{ inputs.text | contains('}}') }}`` and mis-routes it to interpolation
    (coercing its typed return to ``str``). ``_is_single_expression`` scans for a
    block-closing ``}}`` outside string literals, so both cases resolve
    correctly.
    """
    stripped = template.strip()
    if _is_single_expression(stripped):
        return _evaluate_simple_expression(stripped[2:-2].strip(), namespace)

    # Multi-expression: interpolate each block inline. Uses a quote-aware scan
    # (not ``_EXPR_PATTERN.sub``) so a literal ``}}`` inside a string argument
    # in any block does not close that block early -- matching the handling the
    # single-expression path above already got in #3208/#3228.
    return _interpolate_expressions(template, namespace)


class _ProbeNamespace(dict):
    """Namespace for the parse probe: every root exists, every leaf is absent.

    Enough for ``_evaluate_simple_expression`` to walk the grammar without needing
    real inputs. Deliberately *not* resolving leaves to a sentinel value: a probe
    that answers every lookup also answers ``inputs.count+1``, which is the
    malformed shape the probe is meant to expose.

    The probes also pass one as the outer namespace, which tells
    ``_evaluate_simple_expression`` to evaluate both operands of ``and``/``or``
    instead of short-circuiting, so a leaf or filter in a skipped operand is
    still checked.
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
            text, _ProbeNamespace({root: _ProbeNamespace() for root in _NAMESPACE_ROOTS})
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


def _collect_leaves(text: str) -> list[str]:
    """Every substring *text* hands to the evaluator as a name to resolve.

    Runs the same probe ``_evaluator_rejects`` uses, with the leaf sink armed.
    Literals never reach the dot-path resolution, and operands, filter arguments
    and list elements all do -- probe evaluation visits both sides of
    ``or``/``and`` eagerly rather than short-circuiting, so a leaf is
    recorded whatever the other side is worth.

    A probe run can still raise on its own placeholder values, which is what
    ``_evaluator_rejects`` sorts out. The leaves seen before that point are real
    -- the evaluator reached them -- so they are kept rather than discarded:
    ``inputs.tags | join(bogus)`` records ``bogus`` and only then trips over the
    placeholder handed to ``join``.
    """
    leaves: list[str] = []
    token = _leaf_sink.set(leaves)
    try:
        _evaluate_simple_expression(
            text, _ProbeNamespace({root: _ProbeNamespace() for root in _NAMESPACE_ROOTS})
        )
    except Exception:  # noqa: BLE001 - probe values, reported by _evaluator_rejects
        pass
    finally:
        _leaf_sink.reset(token)
    return leaves


# The operators the evaluator delimits with spaces; derived so the check cannot
# drift from _COMPARISON_OPERATORS.
_WORD_OPERATORS = tuple(
    op for op in (" or ", " and ") + _COMPARISON_OPERATORS if op.startswith(" ")
)


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


def _syntax_error(text: str) -> str | None:
    """A parse-error message for *text*, or ``None``.

    This engine has no syntax layer: an unknown shape falls through to the
    dot-path resolution and becomes ``None``, and the diagnostics describe that
    through ``_collect_leaves`` and ``_has_incomplete_operand``. Grammar-based
    engines return the parser's complaint here, naming the character and column
    instead of classifying the text by heuristics; the diagnostics prefer it
    when it is present. Always ``None`` here, so the hook changes nothing for
    this engine.
    """
    return None
