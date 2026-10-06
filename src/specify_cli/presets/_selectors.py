"""Thin helpers for exact preset names and ``regex:`` selectors."""

from __future__ import annotations

import re
from typing import Pattern

REGEX_PREFIX = "regex:"
# String patterns can fail on grammar, repetition limits, or parser nesting.
REGEX_COMPILE_ERRORS = (re.error, OverflowError, RecursionError)


def is_regex_selector(name: str) -> bool:
    """Return whether a manifest name opts into regex selector semantics."""
    return name.startswith(REGEX_PREFIX)


def compile_name_selector(name: str) -> Pattern[str] | None:
    """Compile a regex selector, or return None for an exact-name declaration."""
    if not is_regex_selector(name):
        return None
    return re.compile(name[len(REGEX_PREFIX) :])


def selector_matches(name: str, concrete_name: str) -> bool:
    """Full-match a concrete logical name; exact declarations stay exact."""
    compiled = compile_name_selector(name)
    return (
        compiled.fullmatch(concrete_name) is not None
        if compiled
        else name == concrete_name
    )
