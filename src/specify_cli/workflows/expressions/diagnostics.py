"""Condition validation and remediation for workflow expressions.

These checks run at validation time and predict what the runtime evaluator will
do. They read the evaluator's own definitions through the ``engine`` contract
(and the shared scanners in ``template``), never a second copy of the grammar,
so a widened engine reaches the gate for free.
"""

from __future__ import annotations

import json
from typing import Any

from . import namespace
from .engine import (
    _collect_leaves,
    _evaluator_rejects,
    _first_unclosable_block,
    _has_incomplete_operand,
    _is_single_expression,
    _syntax_error,
)
from .template import _split_top_level, _strip_stray_delimiters


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


def condition_is_interpolated_to_text(condition: Any) -> bool:
    """True when *condition* holds ``{{ }}`` blocks but is spliced into text, not evaluated.

    ``evaluate_expression`` takes its typed fast path only when the whole string is
    exactly one ``{{ ... }}`` block (``_is_single_expression``). Anything else — two
    blocks, or one block with any text around it — goes to ``_interpolate_expressions``,
    which substitutes each block into the surrounding string and returns a *string*.
    ``evaluate_condition`` then coerces that with ``bool()``, so the result is true for
    every rendering except ``""``, ``"true"`` and ``"false"``::

        {{ inputs.ready }} and {{ inputs.count > 100 }}   ->  "False and False"  ->  True
        not {{ inputs.ready }}                            ->  "not False"        ->  True
        {{ inputs.count }} > 100                          ->  "0 > 100"          ->  True

    Each of those reads as a real expression and is always true, which is the same
    silent-truthiness fault ``condition_is_never_evaluated`` reports one layer out: there
    the braces are missing, here they are present but do not cover the whole condition.
    The operators belong *inside* one block, and the validators already tell authors the
    condition must be "a single complete '{{ }}' block" -- this is the check behind that
    sentence.

    Deliberately derived from ``_is_single_expression`` rather than restated, so this
    cannot drift from the fast path it is predicting.
    """
    if not isinstance(condition, str):
        return False
    stripped = condition.strip()
    if not stripped or "{{" not in stripped:
        return False
    # Leave both of the faults that already have their own message and advice: a block
    # the substituter cannot close is not an interpolation problem.
    if condition_is_never_evaluated(condition) or condition_has_malformed_expression_block(condition):
        return False
    return not _is_single_expression(stripped)


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


def _unresolvable_leaf(leaf: str) -> str | None:
    """Why the evaluator cannot resolve the name *leaf*, or ``None``.

    Namespace knowledge only. Everything about where operands live now comes from
    the evaluator itself, so nothing here restates the grammar.
    """
    segments = _split_top_level(leaf, ".")
    if not namespace._is_path_segment(segments[0].strip()):
        return f"{leaf!r} is not a name the evaluator can resolve"
    # `item` is the only root that is not always a mapping: `StepContext.item` is
    # `Any` and a fan-out assigns the item value itself, so when that value is a
    # list `_resolve_dot_path` indexes it and `item[0] == 'x'` resolves. Every
    # other root comes back from `_build_namespace` as a mapping, and the index
    # branch returns None for those however it is written -- so the index is
    # stripped for `item` alone rather than for roots in general.
    root = segments[0].strip()
    # Read the module attribute, not an imported copy: the wiring test widens
    # `namespace._INDEXED_SEGMENT` and expects this check to follow.
    indexed_root = namespace._INDEXED_SEGMENT.match(root)
    if indexed_root is not None and indexed_root.group(1) == "item":
        root = indexed_root.group(1)
    if root not in namespace._NAMESPACE_ROOTS:
        return (
            f"{segments[0].strip()!r} is not one of the namespace roots "
            f"({', '.join(namespace._NAMESPACE_ROOTS)})"
        )
    for segment in segments[1:]:
        if not namespace._is_path_segment(segment.strip()):
            return f"{segment.strip()!r} is not a valid path segment"
    return None


def _unresolvable_term(text: str) -> str | None:
    """The first name in *text* the evaluator cannot resolve, or ``None``.

    Asks the evaluator which names it will look up, then applies the namespace
    rules to those. The previous implementation derived the names itself by
    re-walking the grammar -- filters, then ``or``/``and``/``not``, then
    comparisons, then list literals -- and had to be kept in step with
    ``_evaluate_simple_expression`` by hand.

    That is what made this take several rounds: each round fixed one shape the
    walk disagreed about (``inputs.a === inputs.b``, ``bogus == 'x'``, list
    elements, filter arguments, a newline before ``and``) and nothing stopped the
    next one. Reading the leaves off the evaluator removes the class rather than
    another instance of it: the two cannot disagree about where the operands are
    when only one of them decides.
    """
    stripped = text.strip()
    if not stripped:
        return "an operand is empty"

    # A grammar-based engine can name the parse fault directly, position and
    # character included. Prefer that over the leaf walk: text that does not
    # parse has no leaves, and reporting "no unresolvable term" for it would
    # tell the author their expression is fine. ``None`` for the hand-written
    # engine, which resolves unknown shapes to ``None`` instead.
    syntax = _syntax_error(stripped)
    if syntax is not None:
        return syntax

    for leaf in _collect_leaves(stripped):
        reason = _unresolvable_leaf(leaf)
        if reason is not None:
            return reason
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
    # After the incomplete-operand check, not before: the four "missing an
    # operand" shapes are also parse failures, and the specific message is the
    # better one for them. Everything left that does not parse (arithmetic,
    # stray characters, a second literal) gets the engine's own message.
    syntax = _syntax_error(core)
    if syntax is not None:
        return syntax
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
