"""The fixed set of pipe filters the workflow expression evaluator supports.

Leaf module: no dependencies on the evaluator, the namespace, or the
diagnostics. Each filter validates its arguments strictly and raises
``ValueError`` naming the problem rather than letting a cryptic error escape
the evaluator and crash the whole run.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


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


def _filter_upper(value: Any) -> str:
    """Return *value* uppercased.

    Raises ``ValueError`` on non-string input. Without the guard a non-string
    value (an authoring mistake like ``| upper`` on a shell exit code) would
    reach ``str.upper`` and raise a cryptic ``AttributeError`` that escapes the
    evaluator and crashes the whole run, since the engine wraps neither
    expression evaluation nor ``execute`` in a try/except. Silently coercing
    with ``str(value).upper()`` is rejected for the same reason ``from_json``
    does not coerce: a type mismatch here means the pipeline is wired to the
    wrong variable, and rendering ``"0"`` for an int hides that.
    """
    if not isinstance(value, str):
        raise ValueError(f"upper: expected a string value, got {type(value).__name__}")
    return value.upper()


def _filter_lower(value: Any) -> str:
    """Return *value* lowercased.

    Raises ``ValueError`` on non-string input, for the same reason and with the
    same trade-off as ``upper``: a type mismatch means the pipeline is wired to
    the wrong variable, and coercing would hide it.
    """
    if not isinstance(value, str):
        raise ValueError(f"lower: expected a string value, got {type(value).__name__}")
    return value.lower()


def _filter_split(value: Any, separator: str) -> list[str]:
    """Split *value* on *separator* into a list of strings.

    The single-argument ``split(sep)`` form is the only one supported; there is
    no maxsplit, because a partial split has no obvious meaning in a workflow
    expression and an unused parameter is an authoring mistake worth reporting.

    Raises ``ValueError`` when *value* is not a string, *separator* is not a
    string, or *separator* is empty. Without those guards a non-string argument
    reaches ``str.split`` and raises a cryptic ``TypeError``, and an empty
    separator raises the bare ``ValueError: empty separator`` — neither names
    the filter, and both escape the evaluator and crash the whole run, mirroring
    the strict argument handling in ``join`` and ``map``. An empty separator has
    no meaning anyway: ``str.split("")`` is an error in Python, so it is an
    authoring mistake rather than a valid edge case.
    """
    if not isinstance(value, str):
        raise ValueError(f"split: expected a string value, got {type(value).__name__}")
    if not isinstance(separator, str):
        raise ValueError(
            f"split: expected a string separator, got {type(separator).__name__}"
        )
    if separator == "":
        raise ValueError("split: separator must not be empty")
    return value.split(separator)


def _filter_length(value: Any) -> int:
    """Return the length of a list or string.

    Follows Jinja2's ``length``, which also counts characters in a string. The
    two supported input types are exactly ``list`` and ``str``: dicts are
    excluded even though ``len()`` accepts them, because a mapping's length is
    rarely what a workflow author means by ``length`` and accepting it would
    make ``{{ obj | length }}`` silently return a key count for one shape and a
    value count for another. Other types (notably ``bool`` and ``None``) are
    authoring mistakes and raise rather than coercing to 0.
    """
    if isinstance(value, (list, str)):
        return len(value)
    raise ValueError(
        "length: expected a list or string, got "
        f"{type(value).__name__} (mappings are not supported)"
    )


def _filter_to_json(value: Any) -> str:
    """Serialize *value* to a JSON string — the inverse of ``from_json``.

    Serialization is pinned to ``sort_keys=True`` and ``ensure_ascii=False`` so
    the output is byte-stable across runs, platforms, and dict insertion order.
    It is why these flags are not left to the default: the default key order
    varies with insertion order and escapes non-ASCII as ``\\uXXXX``, so the
    same workflow would emit different bytes on different runs and hand
    downstream tools mangled text. Determinism buys *reproducibility* — the same
    value always serializes identically — and nothing more. It does not make the
    result safe to pass through a shell: expression interpolation adds no
    quoting or escaping, so JSON quotes and metacharacters are still interpreted
    by whatever runs the ``run`` field. Interpolate unconstrained JSON into a
    shell step only when you have constrained what it can contain; see the
    "Interpolation and shell safety" section of ``docs/reference/workflows.md``.

    Raises ``ValueError`` when *value* is not JSON-serializable, chained from
    the underlying error so the offending type stays visible. ``allow_nan=False``
    is what makes that true for non-finite floats: ``json.dumps`` would
    otherwise emit bare ``NaN``/``Infinity``/``-Infinity``, none of which is
    valid JSON, and hand downstream parsers a string they must reject.

    Mapping keys must be strings, which is what JSON objects have anyway.
    ``_check_json_keys`` enforces that before ``json.dumps`` is reached, so a
    non-string key is reported as the authoring mistake it is rather than
    surfacing as an ordering ``TypeError`` from ``sort_keys=True`` (mixed key
    types) or as silent ``1`` → ``"1"`` coercion that collides with an existing
    ``"1"`` key.
    """
    _check_json_keys(value)
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"to_json: value is not JSON-serializable: {exc}") from exc


def _check_json_keys(value: Any) -> None:
    """Raise ``ValueError`` if any mapping reachable from *value* has a
    non-string key.

    Walked iteratively with a ``seen`` set: a self-referential structure is
    skipped rather than recursed into, so the circular reference stays for
    ``json.dumps`` to report with its own clearer message instead of the walk
    exhausting the stack first.
    """
    seen: set[int] = set()
    stack: list[Any] = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if id(item) in seen:
                continue
            seen.add(id(item))
            for key, sub_value in item.items():
                if not isinstance(key, str):
                    raise ValueError(
                        "to_json: mapping keys must be strings, got "
                        f"{type(key).__name__}: {key!r}"
                    )
                stack.append(sub_value)
        elif isinstance(item, (list, tuple)):
            if id(item) in seen:
                continue
            seen.add(id(item))
            stack.extend(item)


# -- The filter table ------------------------------------------------------
#
# One entry per filter: the function, the call forms it accepts, and the usage
# text the error messages advertise. ``_REGISTERED_FILTERS`` and the
# "expected one of ..." sentence are derived from this table, so a new
# filter is one row here — not a row here, a branch in the dispatcher and a
# second edit to the message. The table order is the order the message lists.

@dataclass(frozen=True)
class FilterSpec:
    """One pipe filter: its function and the call forms it accepts.

    ``argument``: the filter takes exactly one parenthesised argument
    (``join('sep')``). ``bare``: the unparenthesised form is also valid
    (``default`` alone). Zero-argument filters (``from_json``, ``upper``, ...)
    have ``argument=False`` and are only valid bare — the strictness that turns
    ``from_json()``, ``from_json)`` and ``from_json extra`` into errors naming
    the filter instead of a silent passthrough.
    """

    function: Callable[..., Any]
    argument: bool
    bare: bool = False
    usage: str = ""


FILTER_TABLE: dict[str, FilterSpec] = {
    "default": FilterSpec(
        _filter_default, argument=True, bare=True, usage="default or default('x')"
    ),
    "join": FilterSpec(_filter_join, argument=True, usage="join('sep')"),
    "map": FilterSpec(_filter_map, argument=True, usage="map('attr')"),
    "contains": FilterSpec(_filter_contains, argument=True, usage="contains('s')"),
    "split": FilterSpec(_filter_split, argument=True, usage="split('sep')"),
    "from_json": FilterSpec(_filter_from_json, argument=False, usage="from_json"),
    "upper": FilterSpec(_filter_upper, argument=False, usage="upper"),
    "lower": FilterSpec(_filter_lower, argument=False, usage="lower"),
    "length": FilterSpec(_filter_length, argument=False, usage="length"),
    "to_json": FilterSpec(_filter_to_json, argument=False, usage="to_json"),
}


# The filters the expression evaluator recognizes. Used to tell a
# *registered* filter used in an unsupported form (e.g. `| join` with no
# argument) apart from a genuinely unknown filter name, so each raises an
# error that names the real problem.
_REGISTERED_FILTERS: tuple[str, ...] = tuple(FILTER_TABLE)


# The sentence every filter-wiring error ends with, derived from the table so
# adding a filter cannot leave the message listing the old set.
_EXPECTED_FILTERS = (
    "expected one of "
    + ", ".join(spec.usage for spec in list(FILTER_TABLE.values())[:-1])
    + ", or "
    + list(FILTER_TABLE.values())[-1].usage
)
