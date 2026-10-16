"""Parsing and bounded matching tests for the command selector engine."""

import re
import subprocess
import sys
import time
import warnings

import pytest

from specify_cli.presets._selectors import (
    _MAX_INPUT,
    SelectorSafetyError,
    compile_name_selector,
    selector_matches,
)


_PATHOLOGICAL_PAYLOAD = "a*" * 400 + "b"


def test_complexity_guard_is_what_answers_the_payload_not_a_limit():
    """Inside every limit, the bounded matcher must answer correctly and fast.

    This runs in a killed-and-reaped child process. If the matcher ever regressed to
    a backtracking engine, this payload would keep it busy for effectively forever;
    the case must then fail on the timeout rather than hang the suite.
    """
    code = f"""
import time
from specify_cli.presets._selectors import _MAX_INPUT, compile_name_selector
text = "a" * _MAX_INPUT
compiled = compile_name_selector("regex:" + {_PATHOLOGICAL_PAYLOAD!r})
assert compiled is not None, "pattern is outside a cap, so nothing is proven"
assert compiled.edge_count < 2048
assert len(text) <= _MAX_INPUT, "input is outside the limit, so nothing is proven"
started = time.perf_counter()
assert compiled.matches(text) is False
assert compiled.matches("a" * (_MAX_INPUT - 1) + "b") is True
elapsed = time.perf_counter() - started
assert elapsed < 5.0, f"{{elapsed:.3f}}s for a payload a backtracker cannot do"
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            "the matcher did not finish this payload inside 30s: the complexity "
            "protection has regressed"
        )
    assert result.returncode == 0, result.stderr


def test_the_payload_is_genuinely_pathological_for_a_backtracking_engine():
    """Effectiveness proof: the payload must defeat plain ``re``, or it proves nothing.

    Without this, the case above could pass simply because the pattern is easy.
    ``re.fullmatch`` is run in a killed-and-reaped child, so the cost is bounded.
    """
    code = (
        "import re, sys\n"
        f"pattern = {_PATHOLOGICAL_PAYLOAD!r}\n"
        f"text = 'a' * {_MAX_INPUT}\n"
        "print(re.fullmatch(pattern, text) is not None)\n"
    )
    started = time.perf_counter()
    try:
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=5
        )
    except subprocess.TimeoutExpired:
        return  # pathological: killed and reaped, exactly as required
    elapsed = time.perf_counter() - started
    assert result.returncode != 0 or elapsed > 1.0, (
        "the payload is not pathological for a backtracking engine, so the "
        f"complexity case above proves nothing (re finished in {elapsed:.3f}s)"
    )


@pytest.mark.parametrize("pattern", ["(a+)+$", "(a|a)*$", "(a*)*$"])
def test_rejected_payloads_are_refused_loudly(pattern):
    with pytest.raises(SelectorSafetyError, match="safety boundary"):
        compile_name_selector("regex:" + pattern)


@pytest.mark.parametrize("pattern", ["(a+)+$", "(a|a)*$", "(a*)*$"])
def test_rejected_payloads_never_hang_a_worker(pattern):
    """The whole pipeline stays alive and fail-closed, with the input inside the limit."""
    code = f"""
import warnings
from specify_cli.presets._selectors import selector_matches
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    matched = selector_matches("regex:" + {pattern!r}, "a" * 1024 + "!")
    assert matched is False, "unsafe selector matched"
    assert any("safety boundary" in str(w.message) for w in caught), [
        str(w.message) for w in caught
    ]
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr


def test_supported_semantics_and_limits():
    start = time.monotonic()
    cases = [
        ("plan", "plan"),
        ("plan", "plan-template"),
        ("regex:plan", "plan-template"),
        (r"regex:^speckit\.(plan|tasks)$", "speckit.plan"),
        (r"regex:(foo|bar)+[a-z]{2,4}\d?", "foobarxy2"),
        (r"regex:(ab)+c*", "ababccc"),
        (r"regex:a.*z", "a.b.z"),
        (r"regex:a.*z", "a\nz"),
        (r"regex:(?s)a.*z", "a\nz"),
        (r"regex:(?i:a)(?-i:B)", "aB"),
        (r"regex:(?i)a(?-i:B)", "Ab"),
        (r"regex:\b\w+\b", "éabc"),
        (r"regex:a+?b{1,3}?$", "aaaabb"),
        (r"regex:^a$", "a\n"),
        (r"regex:(ab|c)?", ""),
    ]
    for selector, name in cases:
        expected = (
            re.fullmatch(selector[6:], name) is not None
            if selector.startswith("regex:")
            else selector == name
        )
        assert selector_matches(selector, name) == expected, (selector, name)
    assert selector_matches("x" * 100000, "x" * 100000)
    assert selector_matches("regex:a+", "a" * 1000)
    # An execution limit is a non-match with a warning, never an exception: the
    # callers of selector_matches are boolean predicates in resolution paths.
    with pytest.warns(UserWarning, match="input character limit"):
        assert selector_matches("regex:.*", "a" * 100000) is False
    with pytest.raises(re.error, match="pattern character limit"):
        compile_name_selector("regex:" + "a" * 4097)
    with pytest.raises(re.error, match="state limit"):
        compile_name_selector("regex:a{10000}")
    assert time.monotonic() - start < 5


@pytest.mark.parametrize(
    ("pattern", "name"),
    [
        (r"(a|b)*c|d", "ad"),
        (r".*-plan|tasks", "speckit.tasks"),
        (r"a*b|c", "ac"),
        (r"(?:a*b|c)d", "acd"),
        (r"[a-z]*x|y", "xy"),
        (r"(a*)b|c", "ac"),
    ],
)
def test_quantifier_led_alternation_does_not_leak_into_a_sibling(pattern, name):
    """A repetition must not fall out of its own alternative into a sibling branch.

    A repetition with a zero minimum owns its entry state; reusing the enclosing
    branch entry as that state let the loop-back edge return to the shared branch
    entry, so the partially matched alternative could then follow a *different*
    alternative's edge. Every case below was a false positive before the fix, which
    would have let a preset selector claim lower-layer resources it must not.
    """
    assert re.fullmatch(pattern, name) is None
    assert selector_matches(f"regex:{pattern}", name) is False


@pytest.mark.parametrize(
    ("pattern", "name"),
    [
        (r"(a|b)*c", "abc"),
        (r".*-plan|tasks", "tasks"),
        (r"a*b|c", "b"),
        (r"a*b|c", "c"),
        (r"[a-z]*x|y", "y"),
        (r"(a*)b|c", "c"),
        (r"(a*)b|c", "ab"),
    ],
)
def test_quantifier_led_alternation_still_accepts_its_own_language(pattern, name):
    """Guard against over-correcting the leak fix into false negatives."""
    assert re.fullmatch(pattern, name) is not None
    assert selector_matches(f"regex:{pattern}", name) is True


@pytest.mark.parametrize("repeats", [50, 100, 200])
def test_transition_budget_never_turns_a_valid_selector_into_a_non_match(repeats):
    """A manifest-valid selector must not stop matching because of the work budget.

    ``"a*" * 200 + "b"`` compiles (well under the pattern and state limits) and
    ``re.fullmatch`` accepts it, but a budget tight enough to be exhausted by
    (len(input) + 1) x (edges) made ``selector_matches`` report a non-match for a
    selector that does match — silently dropping the preset's declaration.
    """
    pattern = "a*" * repeats + "b"
    concrete_name = "a" * 100 + "b"
    assert re.fullmatch(pattern, concrete_name) is not None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert selector_matches(f"regex:{pattern}", concrete_name) is True
    assert not caught, [str(w.message) for w in caught]


@pytest.mark.parametrize("pattern", ["(", "a{2,1}", "[", r"(a)\2", "a**"])
def test_malformed_selector_degrades_without_raising(pattern):
    """A selector the parser cannot compile must warn and not match, not raise.

    ``selector_matches`` is used as a boolean predicate by every resolution,
    installation and diagnostics caller, so a malformed selector has to degrade
    the same way an unsafe one does rather than propagate ``re.error``.
    """
    with pytest.warns(UserWarning, match="Ignoring regex selector"):
        assert selector_matches(f"regex:{pattern}", "x") is False


@pytest.mark.parametrize(
    ("repeats", "name_length"), [(200, 100), (300, 1000), (200, 1023)]
)
def test_no_fixed_transition_budget_can_deny_a_valid_match(repeats, name_length):
    """The work bound is derived, so no finite budget can turn a match into a miss.

    A fixed budget is always reachable by some pattern that validates: 100_000 was
    exceeded by ``"a*" * 200 + "b"`` on a 100-character name, and 2_000_000 by
    ``"a*" * 800 + "b"`` on a 1,000-character name. Both match under
    ``re.fullmatch``, so every case that still fits the caps must match here, with
    no warning about a budget.
    """
    pattern = "a*" * repeats + "b"
    concrete_name = "a" * name_length + "b"
    assert re.fullmatch(pattern, concrete_name) is not None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert selector_matches(f"regex:{pattern}", concrete_name) is True
    assert not caught, [str(w.message) for w in caught]


@pytest.mark.parametrize(
    "pattern",
    [
        r"(?i:[\u0000-\uffff]){1500}",
        r"(?i:[\u0000-\U0010ffff]){1500}",
        r"(?u:[^\x00]){1500}",
    ],
)
def test_unrolled_repetition_does_not_recompile_each_atom(pattern):
    """Unrolling a repetition must reuse one compiled predicate per distinct atom.

    Compiling a large case-folded character set costs a couple of milliseconds, so
    asking CPython's compiler once per unrolled copy made a manifest-valid selector
    take over eight seconds to compile -- a stall on every command that validates
    or resolves a manifest. The budget below is deliberately loose; the fix removes
    a factor of 4000, so the margin is two orders of magnitude even on a slow runner.
    """
    start = time.monotonic()
    compile_name_selector(f"regex:{pattern}")
    assert time.monotonic() - start < 2.0


def test_oversized_compiled_graph_is_rejected_before_it_can_be_matched():
    """The graph itself must be capped, not only its state count.

    A branch reuses one entry state for all its alternatives, and a repetition
    unrolls those edges, so ``(?:a|\B|\B|...)`` stays under the state cap while
    producing millions of edges. Only a state cap let 4004 states carry 4,004,003
    edges, i.e. ~16 billion edge examinations against the largest permitted name.
    The edge cap rejects that shape up front instead.
    """
    # Modest version: this family is now refused by the semantic rule rather than
    # by size -- ``\B`` is zero-width, so the repeated body can match empty and is
    # ambiguous however small it is. It is kept here because it is the shape that
    # produced the oversized graph, and it must still be refused.
    modest = "(?:a|" + "|".join([r"\B"] * 20) + "){20}"
    with pytest.raises(re.error, match="can match empty"):
        compile_name_selector(f"regex:{modest}")

    # Amplified version: same state magnitude, millions of edges.
    amplified = "(?:a|" + "|".join([r"\B"] * 1000) + "){4000}"
    with pytest.raises(re.error, match="edge limit"):
        compile_name_selector(f"regex:{amplified}")

    # Negative control: the cap is not so tight that ordinary selectors suffer.
    for pattern in [r"speckit\.provider\..*", r"^speckit\.(plan|tasks)$", r"a{1000}"]:
        assert compile_name_selector(f"regex:{pattern}") is not None


@pytest.mark.parametrize(
    ("pattern", "name"),
    [
        (r"(ab|a)*c", "aabc"),
        (r"(ab|a)*c", "abc"),
        (r"(ba|b)*c", "bac"),
        (r"(a|a){1}c", "ac"),
        (r"(a|ab)*c", "aabc"),
        (r"(?:ab|a)", "a"),
        (r"(?:ab|ac)*c", "abc"),
    ],
)
def test_factorised_alternation_under_a_repetition_is_accepted(pattern, name):
    """A shared alternative prefix must not make a repetition look empty-bodied.

    CPython factors the prefix out, leaving a trailing branch with an empty
    alternative, so ``(ab|a)*`` parses as ``a`` then ``(b|)``. That body consumes
    ``a`` in every alternative and cannot match empty, yet the old rule refused it
    on the strength of the empty alternative alone -- and refused even a bounded
    ``{1}``. The repetition is only ambiguous when its *body* can match empty, or
    when every alternative of the factorised branch is empty.
    """
    assert re.fullmatch(pattern, name) is not None
    assert selector_matches(f"regex:{pattern}", name) is True


@pytest.mark.parametrize(
    "pattern",
    [
        r"(a|a)*$",
        r"(a+)+$",
        r"(a*)*$",
        r"(?:x|x)*",
        r"(?:)*",
        r"()*",
        r"(a|)*",
        r"(a|b|)*",
    ],
)
def test_empty_or_nested_repetition_is_still_rejected(pattern):
    """The legal-expression fix must not lift the rejection of ambiguous shapes."""
    with pytest.raises(re.error, match="safety boundary"):
        compile_name_selector(f"regex:{pattern}")


@pytest.mark.parametrize("pattern", [r"(a|a){1}c", r"(a|a){2}c", r"(ab|a){1}c"])
def test_bounded_repetition_of_a_factorised_alternation_is_accepted(pattern):
    """A bounded repetition cannot repeat a zero-width alternation without bound."""
    assert compile_name_selector(f"regex:{pattern}") is not None
