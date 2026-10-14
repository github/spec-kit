"""Exact names and bounded, non-backtracking ``regex:`` selectors.

Regexes use a Thompson state machine, never Python's backtracking matcher for
compound expressions. Each state is visited at most once per input position, so
the work is bounded by (input length + 1) x (number of compiled edges) and no
pattern can backtrack. Compilation and matching limits are 4,096 pattern
characters, 4,096 states, 2,048 compiled edges and 1,024 input
characters; a pattern past a compilation limit
is rejected with ``SelectorSafetyError`` (a ``re.error`` subclass) that names it,
and exact-name equality is unchanged.

Groups, alternation, character classes, ordinary/lazy quantifiers, flags and
anchors retain Python full-match semantics. Rejected during validation AND runtime
compilation are backreferences, lookarounds, atomic and possessive constructs,
nested repetitions, a repetition whose body can match empty, and an unbounded
repetition over a zero-width alternation (every alternative of a factorised branch
empty, as in (a|a)*). An alternation the parser factorises while some alternative
still consumes input -- (ab|a)*, (ba|b)*, (a|ab)* -- is ordinary and accepted:
safety comes from the state machine and the graph limits, not from recognising
payload shapes, so the accepted set only narrows where a repetition cannot be
analysed without guessing.

CPython's regex parser/compiler (Python 3.11-3.14) supply syntax and single-atom
predicates only. No user-controlled compound expression reaches ``re`` execution.
"""

from __future__ import annotations

import re
from functools import lru_cache
from re import _compiler, _constants as C, _parser

REGEX_PREFIX = "regex:"
REGEX_COMPILE_ERRORS = (re.error, OverflowError, RecursionError)
_MAX_PATTERN = 4096
_MAX_STATES = 4096
# Concrete resource names are logical names: manifest-declared names and
# filesystem stems, which are capped at 255 bytes by every filesystem we run on.
# 1024 leaves roughly four times the 255-byte
# filesystem limit while keeping a hostile many-state pattern from being run
# over an unbounded pseudo-name. Matching rejects longer input with the same
# ``SelectorSafetyError``; exact-name equality is never length-capped.
_MAX_INPUT = 1024
# Edges must be capped independently of states: a branch reuses its entry state for
# every alternative and a repetition unrolls those edges, so a branch of N empty
# alternatives unrolled K times keeps the state count small while producing N*K
# edges. With only a state cap, `(?:a|\B|\B|...)` with 1000 alternatives under
# `{4000}` compiles to 4004 states but 4,004,003 edges, i.e. 16 billion edge
# examinations against the largest permitted name -- a hang, not a slow match.
_MAX_EDGES = 2048
# There is deliberately no fixed transition budget. Work is provably bounded by
# (len(concrete name) + 1) x (number of compiled edges), and both factors are
# capped here, so the bound is computed per match from the compiled graph and the
# actual input instead of being guessed. Every earlier fixed budget (100_000, then
# 2_000_000) was reachable by a pattern that passes validation -- "a*" * 200 + "b"
# on a 100-character name, then "a*" * 800 + "b" on a 1,000-character name -- and
# turned a selector that does match into a non-match. The caps here keep the
# worst permitted match at about (_MAX_INPUT + 1) * _MAX_EDGES, near a second.


_ATOM_CACHE_LIMIT = 4096
_atom_cache: dict[tuple[int, str, int], re.Pattern[str]] = {}


def _atom_predicate(op: int, arg: object, flags: int) -> re.Pattern[str]:
    """Compile a single-token predicate once per distinct token and flags.

    Unrolling a repetition compiles the same atom once per copy, and compiling a
    large case-folded character set is not cheap: ``(?i:[\u0000-\uffff]){4000}``
    asked CPython's compiler for the same predicate 4000 times and spent over
    eight seconds at import, before a single character was matched. The token and
    its flags determine the predicate completely and compiled patterns are
    immutable, so one compile is reused for every copy. The cache is bounded and
    cleared wholesale rather than evicted, which keeps it trivial to reason about.
    """
    key = (op, repr(arg), flags)
    cached = _atom_cache.get(key)
    if cached is None:
        atom = _parser.SubPattern(_parser.State(), [(op, arg)])
        cached = _compiler.compile(atom, flags)
        if len(_atom_cache) >= _ATOM_CACHE_LIMIT:
            _atom_cache.clear()
        _atom_cache[key] = cached
    return cached


def _can_match_empty(tokens) -> bool:
    """Return whether a token sequence can match the empty string.

    ``LITERAL``/``NOT_LITERAL``/``IN``/``ANY``/``CATEGORY`` each consume exactly
    one character, so a sequence holding one cannot match empty. ``AT`` (^ $ \\b
    \\B \\A \\Z) is zero-width. A repetition matches empty when it may be taken
    zero times *or* when its body can; a branch matches empty when any alternative
    does. Anything else is unsupported here and already rejected by construction.
    """
    for op, arg in tokens:
        if op is C.SUBPATTERN:
            if not _can_match_empty(arg[3]):
                return False
        elif op is C.BRANCH:
            if not any(_can_match_empty(body) for body in arg[1]):
                return False
        elif op in (C.MAX_REPEAT, C.MIN_REPEAT):
            minimum, _maximum, body = arg
            if minimum > 0 and not _can_match_empty(body):
                return False
        elif op is C.AT:
            continue
        else:
            return False
    return True


def _has_zero_width_alternation(tokens) -> bool:
    """Return whether a branch in ``tokens`` has only empty alternatives.

    CPython's parser factors a shared alternation prefix out of the branches, so
    ``(?:x|x)`` arrives as ``LITERAL x`` followed by ``BRANCH([[], []])``. A branch
    all of whose alternatives are empty is itself zero-width -- repeating that
    without bound is the genuinely ambiguous shape. A factorised *suffix* such as
    ``(?:ab|a)`` leaves at least one alternative that consumes input, so the branch
    is ordinary alternation and is not reported here.
    """
    for op, arg in tokens:
        if op is C.SUBPATTERN:
            if _has_zero_width_alternation(arg[3]):
                return True
        elif op is C.BRANCH:
            bodies = arg[1]
            if bodies and all(not body for body in bodies):
                return True
            if any(_has_zero_width_alternation(body) for body in bodies):
                return True
        elif op in (C.MAX_REPEAT, C.MIN_REPEAT):
            if _has_zero_width_alternation(arg[2]):
                return True
    return False


def _validate_repetitions(tokens) -> None:
    """Refuse repetitions whose body cannot be reasoned about safely.

    Two shapes, both read from the parsed semantics rather than from whether some
    node happens to be an empty list: a repetition whose body can match the empty
    string, and an unbounded repetition over a zero-width alternation. Called once
    the graph exists, so a pattern that exceeds the state or edge cap is reported
    as oversized instead of as ambiguous.
    """
    for op, arg in tokens:
        if op is C.SUBPATTERN:
            _validate_repetitions(arg[3])
        elif op is C.BRANCH:
            for body in arg[1]:
                _validate_repetitions(body)
        elif op in (C.MAX_REPEAT, C.MIN_REPEAT):
            _minimum, maximum, body = arg
            if _can_match_empty(body):
                raise _unsafe("repetition over a body that can match empty")
            if maximum == C.MAXREPEAT and _has_zero_width_alternation(body):
                raise _unsafe("zero-width alternation under an unbounded repetition")
            _validate_repetitions(body)


class SelectorSafetyError(re.error):
    """A selector exceeded the supported syntax or bounded execution limits."""


def _unsafe(reason: str) -> SelectorSafetyError:
    return SelectorSafetyError(
        f"Regex selector safety boundary: {reason}. Bounded non-backtracking "
        f"selectors allow {_MAX_PATTERN} pattern characters, {_MAX_STATES} "
        f"states, {_MAX_EDGES} edges and {_MAX_INPUT} input characters, and reject "
        "nested repetitions, "
        "backreferences, lookarounds and atomic "
        "or possessive constructs. A repetition whose body can match empty, and an "
        "unbounded repetition over a zero-width alternation (for example (a|a)*), "
        "are refused as well."
    )


def is_regex_selector(name: str) -> bool:
    """Return whether a manifest name opts into regex selector semantics."""
    return name.startswith(REGEX_PREFIX)


class _Selector:
    def __init__(self, pattern: str):
        parsed = _parser.parse(pattern, 0)
        # Edges are (destination, single-atom predicate or None, consumes input).
        self.edges: list[list[tuple[int, re.Pattern | None, bool]]] = []
        self.edge_count = 0

        def state():
            if len(self.edges) >= _MAX_STATES:
                raise _unsafe("compiled state limit exceeded")
            self.edges.append([])
            return len(self.edges) - 1

        def edge(start, end, predicate=None, consumes=False):
            if self.edge_count >= _MAX_EDGES:
                raise _unsafe("compiled edge limit exceeded")
            self.edges[start].append((end, predicate, consumes))
            self.edge_count += 1

        def sequence(tokens, start, end, flags, repeated=False):
            for index, (op, arg) in enumerate(tokens):
                dest = end if index == len(tokens) - 1 else state()
                if op is C.SUBPATTERN:
                    _, add, remove, body = arg
                    sequence(
                        body,
                        start,
                        dest,
                        _compiler._combine_flags(flags, add, remove),
                        repeated,
                    )
                elif op is C.BRANCH:
                    # An empty alternative here is not itself a reason to refuse:
                    # the parser produces one whenever branches share a prefix, and
                    # what matters is whether the enclosing repetition can be
                    # ambiguous. That is decided when the repetition is built, from
                    # the body's semantics rather than from this node's shape.
                    for body in arg[1]:
                        sequence(body, start, dest, flags, repeated)
                elif op in (C.MAX_REPEAT, C.MIN_REPEAT):
                    if repeated:
                        raise _unsafe("nested repetition")
                    minimum, maximum, body = arg
                    if minimum > _MAX_STATES or (
                        maximum != C.MAXREPEAT and maximum > _MAX_STATES
                    ):
                        raise _unsafe("repetition exceeds compiled state limit")
                    # The repetition gets its own entry and exit states. Reusing the
                    # enclosing ``start``/``dest`` makes the loop-back edge point at a
                    # state shared with the surrounding construct; inside a branch
                    # alternative that state is the branch entry, so a partially matched
                    # alternative could leave its own repetition and continue in a
                    # sibling alternative — ``regex:(a|b)*c|d`` wrongly matched "ad",
                    # ``regex:a*b|c`` wrongly matched "ac", ``regex:(a*)b|c`` wrongly
                    # matched "ac".
                    entry = state()
                    exit_state = state()
                    edge(start, entry)
                    cursor = entry
                    for _ in range(minimum):
                        nxt = state()
                        sequence(body, cursor, nxt, flags, True)
                        cursor = nxt
                    if maximum == C.MAXREPEAT:
                        edge(cursor, exit_state)
                        tail = state()
                        sequence(body, cursor, tail, flags, True)
                        edge(tail, cursor)
                    else:
                        for _ in range(maximum - minimum):
                            edge(cursor, exit_state)
                            nxt = state()
                            sequence(body, cursor, nxt, flags, True)
                            cursor = nxt
                        edge(cursor, exit_state)
                    edge(exit_state, dest)
                elif op in (C.LITERAL, C.NOT_LITERAL, C.IN, C.ANY, C.CATEGORY, C.AT):
                    edge(start, dest, _atom_predicate(op, arg, flags), op is not C.AT)
                else:
                    raise _unsafe(f"unsupported construct {op}")
                start = dest
            if not tokens:
                edge(start, end)

        self.start, self.end = state(), state()
        sequence(parsed, self.start, self.end, parsed.state.flags)
        # Deliberately after the walk: the state and edge caps are what bound the
        # work, so an oversized pattern must be reported as oversized. Running the
        # semantic repetition rules first would mask those caps for the very
        # zero-width branch shapes that can inflate the edge count.
        _validate_repetitions(parsed)

    def matches(self, text: str) -> bool:
        if len(text) > _MAX_INPUT:
            raise _unsafe("input character limit exceeded")
        # (positions x edges) is a proven upper bound, not a guess: the epsilon
        # closure below visits a state at most once per position and walks each of
        # its edges once. The guard is therefore an unreachable net for a traversal
        # bug rather than a limit a valid selector can hit.
        budget = (len(text) + 1) * self.edge_count
        active = {self.start}
        work = 0
        for position in range(len(text) + 1):
            pending = list(active)
            following = set()
            while pending:
                current = pending.pop()
                for dest, predicate, consumes in self.edges[current]:
                    work += 1
                    if work > budget:
                        raise _unsafe("transition budget exceeded")
                    if (
                        predicate is not None
                        and predicate.match(text, position) is None
                    ):
                        continue
                    if consumes:
                        following.add(dest)
                    elif dest not in active:
                        active.add(dest)
                        pending.append(dest)
            if position == len(text):
                return self.end in active
            if not following:
                return False
            active = following
        return False


@lru_cache(maxsize=128)
def _compile_pattern(pattern: str) -> _Selector:
    return _Selector(pattern)


def compile_name_selector(name: str) -> _Selector | None:
    """Validate/compile a bounded regex, or return None for an exact name."""
    if not is_regex_selector(name):
        return None
    if len(name) - len(REGEX_PREFIX) > _MAX_PATTERN:
        raise _unsafe("pattern character limit exceeded")
    return _compile_pattern(name[len(REGEX_PREFIX) :])


def selector_matches(name: str, concrete_name: str) -> bool:
    """Full-match with bounded work, including selectors from historical manifests.

    Every caller uses this as a boolean predicate inside resolution, installation
    and diagnostics (``_resolver``, ``_manager``, ``_manager_commands``,
    ``command_info``), so neither a rejected construct nor an exceeded execution
    limit may escape as an exception here: the selector is reported as a non-match
    with a warning instead. The loud, actionable rejection lives where a human can
    act on it — ``compile_name_selector`` still raises during manifest validation,
    and the resolver warns and ignores an unsafe manifest that is already on disk.
    """
    try:
        compiled = compile_name_selector(name)
    except REGEX_COMPILE_ERRORS as exc:
        # Includes SelectorSafetyError plus the parser's own syntax errors
        # (unbalanced group, "a{2,1}", a dangling backreference, ...), so a
        # malformed selector degrades the same way an unsafe one does.
        _warn_ignored_selector(name, concrete_name, exc)
        return False
    if compiled is None:
        return name == concrete_name
    try:
        return compiled.matches(concrete_name)
    except REGEX_COMPILE_ERRORS as exc:
        _warn_ignored_selector(name, concrete_name, exc)
        return False


def _warn_ignored_selector(selector: str, concrete_name: str, exc: Exception) -> None:
    """Report a selector that could not be evaluated, without failing the caller."""
    import warnings

    warnings.warn(
        f"Ignoring regex selector {selector!r} for {concrete_name!r}: {exc}",
        stacklevel=3,
    )
