"""Quote- and bracket-aware string scanners used by the expression evaluator.

Leaf module: pure string/token scanning only, no evaluation. The evaluator and
the condition diagnostics share these so a validator cannot disagree with the
substitution it is predicting.
"""

from __future__ import annotations

import re


_EXPR_PATTERN = re.compile(r"\{\{(.+?)\}\}")


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


def _is_single_list_literal(expr: str) -> bool:
    """Return ``True`` only when *expr* is exactly one bracketed list
    literal -- the opening ``[`` closes at the FINAL character, not partway
    through the string.

    ``expr.startswith("[") and expr.endswith("]")`` alone also matches a
    list literal immediately followed by an index suffix, e.g.
    ``[1,2,3][1]`` (meant as "index 1 of [1,2,3]", i.e. 2). Naively
    stripping the outer brackets from that string yields the garbage
    ``1,2,3][1``, which then silently evaluates to ``[1, 2, None]`` instead
    of raising or resolving the index -- the same "grabs the wrong span"
    failure mode the string-literal check above guards against, just never
    given the same treatment for brackets.
    """
    if not (expr.startswith("[") and expr.endswith("]")):
        return False
    quote: str | None = None
    depth = 0
    n = len(expr)
    for i, ch in enumerate(expr):
        if quote is not None:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return i == n - 1
    return False


def _is_wrapped_in_parens(text: str) -> bool:
    """True when *text* is one parenthesised group, brackets and all.

    ``(a or b)`` is; ``(a) and (b)`` is not, because the opening paren closes
    before the end. Quote-aware, so ``('(')`` does not count its own literal.
    """
    if not (text.startswith("(") and text.endswith(")")):
        return False
    quote: str | None = None
    depth = 0
    for index, ch in enumerate(text):
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return index == len(text) - 1
    return False


def _collapse_whitespace(text: str) -> str:
    """Strip *text* and turn each run of whitespace outside a quoted string into
    one space.

    The operator scans below match word operators by their surrounding spaces
    (``" or "``, ``" not in "``, ``expr.startswith("not ")``), so an operator
    next to a newline or tab was never found. A condition wrapped across lines
    in YAML keeps those newlines -- a ``|`` block scalar keeps every one, and a
    ``>`` folded scalar keeps the break before a more-indented continuation
    line -- so ``{{ inputs.a or\\n   inputs.b }}`` was resolved as one dot path,
    came back ``None``, and read false with no error. Jinja2 treats any
    whitespace between tokens alike; so does this, while quoted operands keep
    their text exactly.
    """
    out: list[str] = []
    quote: str | None = None
    pending_space = False
    for ch in text.strip():
        if quote is not None:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch.isspace():
            pending_space = True
        else:
            if pending_space:
                out.append(" ")
                pending_space = False
            if ch in ("'", '"'):
                quote = ch
            out.append(ch)
    return "".join(out)


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
