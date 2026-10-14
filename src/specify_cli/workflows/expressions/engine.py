"""Selection point for the workflow expression engine.

Every runtime use (``api.py``) and every validation use (``diagnostics.py``)
imports the evaluator only through this module, so a single line here switches
both together and they cannot drift onto different engines. The names below are
the full engine contract: an engine is not plugged in until it provides all of
them, not just ``_evaluate_template``.
"""

from __future__ import annotations

from .engine_current import (
    _COMPARISON_OPERATORS,
    _WORD_OPERATORS,
    _collect_leaves,
    _evaluate_template,
    _evaluator_rejects,
    _first_unclosable_block,
    _has_incomplete_operand,
    _is_single_expression,
    _leaf_sink,
    _syntax_error,
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
    "_leaf_sink",
    "_syntax_error",
]
