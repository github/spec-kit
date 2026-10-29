"""Variant A2: Lark (LALR) as the parser, used the way the library is meant to be.

The Earley spike (``engine_lark.py``) emulated ``engine_current``'s internals:
an if-chain filter dispatcher rebuilt from strings, the probe walk with its
leaf sink, and a grammar that accepted shapes the current parser refuses. This
engine answers the question A/C left open -- what a grammar-based parser costs
and buys when it is not written to mimic the old code:

* **The precedence guards are in the grammar, not in a post-check.** A filter
  chain is only valid where the current parser allows one: the head is a plain
  operand, and the chain is a whole expression or sits in parentheses, a list
  element or a filter argument. ``count > limit | default(5)``, ``not x |
  default(1)`` and ``x | default(0) > 5`` do not parse at all; the first two
  keep the "ambiguous filter precedence" message through the offending ``|``
  token.
* **The path terminal is derived from ``namespace``.** ``_PLAIN_SEGMENT`` and
  ``_INDEXED_SEGMENT`` are the one definition of a path segment; widening
  either rebuilds the parser (the cache is keyed on the patterns) and reaches
  evaluation and validation together. No second copy to drift.
* **The contract primitives are static.** ``_collect_leaves`` walks the parse
  tree for ``path`` nodes -- there is no probe run, no context variable, no
  placeholder namespace. ``_evaluator_rejects`` checks filter nodes against
  ``FILTER_TABLE``. ``_has_incomplete_operand`` classifies the parse failure:
  end of text or an operator token means a missing operand, anything else is a
  syntax error and reported with its position through ``_syntax_error``.
* **Template level unchanged.** The shared quote-aware scanner still decides
  what is one block and what is text; only the block body is parsed here.

Everything else -- namespace, filters, comparison semantics, diagnostics --
is the shared package, unchanged.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import UnexpectedCharacters, UnexpectedInput, UnexpectedToken

from . import namespace
from .filters import FILTER_TABLE, _EXPECTED_FILTERS
from .namespace import _resolve_dot_path
from .operators import _safe_compare, _safe_membership
from .template import (
    _collapse_whitespace,
    _find_block_close,
    _first_unclosable_block,
    _is_single_expression,
)


__all__ = [
    "_COMPARISON_OPERATORS",
    "_WORD_OPERATORS",
    "_collect_leaves",
    "_evaluate_template",
    "_evaluator_rejects",
    "_first_unclosable_block",
    "_has_incomplete_operand",
    "_is_single_expression",
    "_syntax_error",
]


# Order matters -- multi-char operators first. The contract constant the
# diagnostics and the tests read; the grammar below implements the same set
# (``CMP_OP`` and the word terminals), so a new operator needs both lines.
_COMPARISON_OPERATORS = ("!=", "==", ">=", "<=", ">", "<", " not in ", " in ")

_WORD_OPERATORS = tuple(
    op for op in (" or ", " and ") + _COMPARISON_OPERATORS if op.startswith(" ")
)


def _path_terminal_pattern(plain_pattern: str, indexed_pattern: str) -> str:
    """The ``PATH`` regex, built from the namespace's own segment definitions.

    ``_PLAIN_SEGMENT`` (``^[\\w-]+$``) and ``_INDEXED_SEGMENT``
    (``^([\\w-]+)\\[(-?\\d+)\\]$``) are stripped of their anchors and combined:
    every segment is a plain or an indexed one. The *first* segment's first
    character excludes digits so ``123`` keeps lexing as a number; that is the
    only difference from the namespace pattern, and it is why this derivation
    reads the pattern instead of re-describing the shape.

    ``_INDEXED_SEGMENT`` is read through ``namespace`` at call time, so the
    parser cache below rebuilds when it is widened -- the drift guard
    ``test_gate_reads_the_shared_indexed_segment_definition`` rests on that.
    """
    plain = plain_pattern.strip("^$")
    indexed = indexed_pattern.strip("^$")
    later = f"(?:{indexed}|{plain})"
    first = f"(?:{indexed}|[^\\W\\d]{plain[:-1]}*)"
    return f"{first}(?:\\.{later})*"


def _grammar(path_pattern: str) -> str:
    return r"""
?start: filtered
      | expr

filtered: operand ("|" filter)+

?expr: or_expr

?or_expr: and_expr
        | or_expr OR and_expr      -> or_op

?and_expr: not_expr
         | and_expr AND not_expr   -> and_op

?not_expr: NOT not_expr            -> not_op
         | comparison

?comparison: operand
           | comparison CMP_OP operand  -> cmp

?operand: string
        | number
        | list_lit
        | path
        | group

group: "(" start ")"

string: STRING
number: NUMBER
path: PATH

list_lit: "[" list_body? "]"
list_body: [start] ("," [start])*

?filter: filter_bare
       | filter_call

filter_bare: FILTER_NAME
filter_call: FILTER_NAME "(" [start ("," start)*] ")"

CMP_OP.2: "!=" | "==" | ">=" | "<=" | ">" | "<" | /(?<![\w-])not\s+in(?![\w-])/ | /(?<![\w-])in(?![\w-])/
NOT.2: /(?<![\w-])not(?![\w-])/
AND.2: /(?<![\w-])and(?![\w-])/
OR.2: /(?<![\w-])or(?![\w-])/
FILTER_NAME: /[A-Za-z_][\w-]*/
PATH: /""" + path_pattern + r"""/
STRING: /'[^']*'/ | /"[^"]*"/
NUMBER: /-?\d+(\.\d+)?/
%import common.WS
%ignore WS
"""


@lru_cache(maxsize=None)
def _parser_for(plain_pattern: str, indexed_pattern: str) -> Lark:
    """Build the parser for one pair of namespace patterns, once.

    Keyed on the patterns (not a single cached instance) so widening
    ``namespace._INDEXED_SEGMENT`` builds a parser that accepts the wider form
    instead of serving a stale one.
    """
    return Lark(
        _grammar(_path_terminal_pattern(plain_pattern, indexed_pattern)),
        parser="lalr",
        maybe_placeholders=False,
    )


def _parser() -> Lark:
    return _parser_for(
        namespace._PLAIN_SEGMENT.pattern, namespace._INDEXED_SEGMENT.pattern
    )


@v_args(inline=True)
class _BuildAst(Transformer):
    """Turn the parse tree into the same kind of tuples the other engines walk.

    One small method per grammar rule; aliases (``-> cmp``, ``-> filter_call``)
    name the shape, and anonymous terminals (``"|"``, ``"("``, ``","``) are
    filtered out by Lark, so the children are exactly the operands.
    """

    def string(self, token: Token) -> tuple[str, str]:
        return ("lit", str(token)[1:-1])

    def number(self, token: Token) -> tuple[str, Any]:
        text = str(token)
        return ("lit", float(text) if "." in text else int(text))

    def path(self, token: Token) -> tuple[str, str]:
        return ("path", str(token))

    def group(self, inner: Any) -> Any:
        return inner

    def list_body(self, *items: Any) -> tuple[Any, ...]:
        return items

    def list_lit(self, body: tuple[Any, ...] | None = None) -> tuple[str, tuple[Any, ...]]:
        return ("list", body or ())

    def filter_bare(self, name: Token) -> tuple[str, str, tuple[Any, ...], bool]:
        return ("filter", str(name), (), False)

    def filter_call(self, name: Token, *args: Any) -> tuple[str, str, tuple[Any, ...], bool]:
        return ("filter", str(name), args, True)

    def filtered(self, head: Any, *filters: Any) -> tuple[str, Any, tuple[Any, ...]]:
        return ("pipe", head, filters)

    def cmp(self, left: Any, op: Token, right: Any) -> tuple[str, ...]:
        return ("cmp", " ".join(str(op).split()), left, right)

    def or_op(self, left: Any, _op: Token, right: Any) -> tuple[str, Any, Any]:
        return ("or", left, right)

    def and_op(self, left: Any, _op: Token, right: Any) -> tuple[str, Any, Any]:
        return ("and", left, right)

    def not_op(self, _op: Token, inner: Any) -> tuple[str, Any]:
        return ("not", inner)


def _parse(text: str) -> Any:
    """Parse one block body into the tuple AST. Raises ``lark`` errors."""
    return _BuildAst().transform(_parser().parse(text))


def _parse_error_message(text: str, exc: UnexpectedInput) -> str:
    """The author-facing message for a parse failure of *text*.

    The pipe case is the one carried-over semantic: a ``|`` where an operand
    was expected is the shape the current evaluator refuses as an ambiguous
    filter precedence, so it gets the same wording. Everything else names the
    offending character and column.
    """
    token = getattr(exc, "token", None)
    if token is not None and token.value == "|" and getattr(token, "column", 1) > 1:
        return (
            f"ambiguous filter precedence in '{text}': a filter cannot be an "
            f"operand of an operator. Filter the operand in its own expression "
            f"instead."
        )
    if token is not None and token.type == "$END":
        return f"invalid expression '{text}': unexpected end of text"
    if isinstance(exc, UnexpectedCharacters):
        char = getattr(exc, "char", "?")
        column = getattr(exc, "column", "?")
        return f"invalid expression '{text}': unexpected character '{char}' at column {column}"
    if token is not None and token.value:
        column = getattr(token, "column", "?")
        return f"invalid expression '{text}': unexpected '{token.value}' at column {column}"
    return f"invalid expression '{text}'"


def _syntax_error(text: str) -> str | None:
    """The parser's complaint about *text*, or ``None`` when it parses.

    The diagnostics ask this before walking leaves: text that does not parse
    has no leaves, and "no unresolvable term" would tell the author their
    expression is fine when the evaluator will refuse it.
    """
    collapsed = _collapse_whitespace(text)
    if not collapsed:
        return None
    try:
        _parse(collapsed)
    except UnexpectedInput as exc:
        return _parse_error_message(collapsed, exc)
    return None


# -- Evaluation ---------------------------------------------------------------

def _apply_filter(
    value: Any, filt: tuple[str, str, tuple[Any, ...], bool], namespace_: dict[str, Any]
) -> Any:
    """Apply one ``("filter", name, args, has_parens)`` node to *value*.

    Arguments are evaluated here, before the table lookup, so a leaf in an
    argument is visible to the diagnostics even when the filter name is wrong.
    The accepted call forms and the error wording come from ``FILTER_TABLE``
    and``_EXPECTED_FILTERS``: the same table the message lists, so adding a
    filter cannot leave the two disagreeing.
    """
    _, name, arg_nodes, has_parens = filt
    args = [_eval(node, namespace_) for node in arg_nodes]
    display = f"{name}(...)" if has_parens else name

    spec = FILTER_TABLE.get(name)
    if spec is None:
        raise ValueError(
            f"unknown filter '{name}': {_EXPECTED_FILTERS} (got '| {display}')"
        )
    if not spec.argument:
        # A zero-argument filter tolerates no parentheses and no trailing
        # tokens; `from_json()` and `from_json('x')` are the same mistake.
        if has_parens:
            raise ValueError(
                f"{name}: expected '| {name}' with no arguments or trailing "
                f"tokens, got '| {display}'"
            )
        return spec.function(value)
    if has_parens and len(args) == 1:
        return spec.function(value, args[0])
    if not has_parens and spec.bare:
        return spec.function(value)
    raise ValueError(
        f"filter '{name}' used in an unsupported form (got '| {display}'): "
        f"{_EXPECTED_FILTERS}"
    )


def _eval(node: Any, namespace_: dict[str, Any]) -> Any:
    """Evaluate a tuple AST node against *namespace_*."""
    tag = node[0]
    if tag == "lit":
        return node[1]
    if tag == "path":
        text = node[1]
        # A bare word that is a literal keyword is a value, not a name; the
        # dot/bracket guard keeps `inputs.true` a path.
        if _is_literal_path(text):
            lowered = text.lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
            return None
        return _resolve_dot_path(namespace_, text)
    if tag == "list":
        return [_eval(item, namespace_) for item in node[1]]
    if tag == "pipe":
        value = _eval(node[1], namespace_)
        for filt in node[2]:
            value = _apply_filter(value, filt, namespace_)
        return value
    if tag == "not":
        return not bool(_eval(node[1], namespace_))

    if tag == "cmp":
        op = node[1]
        left = _eval(node[2], namespace_)
        right = _eval(node[3], namespace_)
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "in":
            return _safe_membership(left, right, negate=False)
        if op == "not in":
            return _safe_membership(left, right, negate=True)
        return _safe_compare(left, right, op)

    left = _eval(node[1], namespace_)
    # Skip the right operand when the left one decides, so a guard protects it.
    # Validation walks the parse tree instead, so it still visits both sides.
    if tag == "or" and bool(left):
        return True
    if tag == "and" and not bool(left):
        return False
    right = _eval(node[2], namespace_)
    if tag == "or":
        return bool(left) or bool(right)
    if tag == "and":
        return bool(left) and bool(right)
    raise ValueError(f"unsupported expression node {tag!r}")


def _evaluate_simple_expression(expr: str, namespace_: dict[str, Any]) -> Any:
    """Evaluate the body of one ``{{ }}`` block against *namespace_*.

    A syntax error is raised as ``ValueError``, the type the evaluator already
    uses for a malformed expression, rather than leaking the parser's own
    exception. The message names the character and column.
    """
    collapsed = _collapse_whitespace(expr)
    if not collapsed:
        return None
    try:
        ast = _parse(collapsed)
    except UnexpectedInput as exc:
        raise ValueError(_parse_error_message(collapsed, exc)) from exc
    return _eval(ast, namespace_)


def _interpolate_expressions(template: str, namespace_: dict[str, Any]) -> str:
    """Substitute every top-level ``{{ ... }}`` block, quote-aware.

    The template level is the shared scanner, unchanged: only the body handed
    to ``_evaluate_simple_expression`` goes through the parser.
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
        close = _find_block_close(template, start)
        if close == -1:
            raw_close = template.find("}}", start + 2)
            if raw_close == -1:
                out.append(template[start:])
                break
            close = raw_close
        val = _evaluate_simple_expression(template[start + 2:close].strip(), namespace_)
        out.append(str(val) if val is not None else "")
        i = close + 2
    return "".join(out)


def _evaluate_template(template: str, namespace_: dict[str, Any]) -> Any:
    """Evaluate *template*: a single block stays typed, text is interpolated."""
    stripped = template.strip()
    if _is_single_expression(stripped):
        return _evaluate_simple_expression(stripped[2:-2].strip(), namespace_)
    return _interpolate_expressions(template, namespace_)


# -- Contract primitives --------------------------------------------------------

_LITERAL_WORDS = ("true", "false", "none", "null")


def _is_literal_path(text: str) -> bool:
    """True for a bare literal keyword, which the grammar lexes as a path.

    The evaluator resolves names, not literals; the diagnostics must report the
    same names the evaluator will look up, so both ask this one condition.
    A dot or bracket keeps ``inputs.true`` a path.
    """
    return "." not in text and "[" not in text and text.lower() in _LITERAL_WORDS


def _visit(node: Any, paths: list[str] | None = None, filters: list[Any] | None = None) -> None:
    """Walk *node* in evaluation order, collecting paths and filter nodes.

    One traversal serves both contract primitives: ``_collect_leaves`` asks for
    the names (``paths``), ``_evaluator_rejects`` asks for the filters to check
    against the table (``filters``). Parents are transparent -- both sides of
    ``and``/``or``, every list element and every filter argument is reached.
    Text that does not parse has neither names nor filters; ``_syntax_error``
    explains why separately.
    """
    tag = node[0]
    if tag == "path":
        if paths is not None and not _is_literal_path(node[1]):
            paths.append(node[1])
        return
    if tag == "list":
        for item in node[1]:
            _visit(item, paths, filters)
    elif tag == "pipe":
        _visit(node[1], paths, filters)
        for filt in node[2]:
            if filters is not None:
                filters.append(filt)
            for arg in filt[2]:
                _visit(arg, paths, filters)
    elif tag == "not":
        _visit(node[1], paths, filters)
    elif tag in ("and", "or"):
        _visit(node[1], paths, filters)
        _visit(node[2], paths, filters)
    elif tag == "cmp":
        _visit(node[2], paths, filters)
        _visit(node[3], paths, filters)


def _collect_leaves(text: str) -> list[str]:
    """Every name *text* hands to the evaluator as a path to resolve.

    Walks the parse tree rather than re-running the evaluation: no probe, no
    placeholder namespace, no state to arm.
    """
    collapsed = _collapse_whitespace(text)
    if not collapsed:
        return []
    try:
        ast = _parse(collapsed)
    except UnexpectedInput:
        return []
    leaves: list[str] = []
    _visit(ast, paths=leaves)
    return leaves


def _check_filter(filt: tuple[str, str, tuple[Any, ...], bool]) -> str | None:
    """Why *filt* would be refused at evaluation time, or ``None``."""
    _, name, args, has_parens = filt
    spec = FILTER_TABLE.get(name)
    if spec is None:
        return f"unknown filter '{name}'"
    if not spec.argument:
        if has_parens:
            return f"{name}: expected '| {name}' with no arguments or trailing tokens"
        return None
    if has_parens and len(args) == 1:
        return None
    if not has_parens and spec.bare:
        return None
    return f"filter '{name}' used in an unsupported form"


def _evaluator_rejects(text: str) -> str | None:
    """The evaluator's own complaint about how *text* wires its filters.

    Static: the parse tree is checked against ``FILTER_TABLE`` -- the same
    table the dispatcher uses -- so a filter used under an unknown name or in
    an unsupported form is reported by the code that will run it, without a
    probe evaluation. Text that does not parse is not a filter-wiring fault;
    ``_syntax_error`` covers it.
    """
    collapsed = _collapse_whitespace(text)
    if not collapsed:
        return None
    try:
        ast = _parse(collapsed)
    except UnexpectedInput:
        return None
    filters: list[Any] = []
    _visit(ast, filters=filters)
    for filt in filters:
        problem = _check_filter(filt)
        if problem is not None:
            return problem
    return None


_OPERATOR_TOKENS = frozenset({"CMP_OP", "AND", "OR", "NOT"})

# A word operator at the very start of the text. The LALR lexer only offers
# CMP_OP/AND/OR/NOT where the grammar can take them, so without a left operand
# `in`/`and`/`or` lex as paths and the failure lands on the *next* token; the
# leading word is what identifies the missing operand. `not x` is valid, so
# only `not in` counts.
_LEADING_WORD_OPERATOR = re.compile(r"^(?:and|or|in)\b|^not\s+in\b")


def _has_incomplete_operand(text: str) -> bool:
    """True when an operator in *text* is missing an operand on either side.

    Reads the parse failure rather than restating the operator table: text
    that ends where an operand was expected (``inputs.a ==``, ``inputs.a and``,
    ``inputs.x |``) fails at the ``$END`` token; a leading word operator
    (``in inputs.a``, ``and inputs.x``) fails right behind the word. A failure
    anywhere else (arithmetic, a stray character, a second literal) is a
    syntax error, not an incomplete operand, and is reported by
    ``_syntax_error`` instead.
    """
    stripped = text.strip()
    if not stripped:
        return True
    try:
        _parse(_collapse_whitespace(stripped))
    except UnexpectedToken as exc:
        if exc.token.type == "$END":
            return True
        if str(exc.token.type) in _OPERATOR_TOKENS:
            return True
        return bool(_LEADING_WORD_OPERATOR.match(stripped))
    except UnexpectedInput:
        return False
    return False
