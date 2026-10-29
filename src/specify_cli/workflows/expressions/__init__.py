"""Sandboxed expression evaluator for workflow templates.

Provides a safe Jinja2 subset for evaluating expressions in workflow YAML.
Templates cannot perform file I/O, import modules, or run arbitrary code —
the evaluator only walks the namespace and applies a fixed set of filters.

This package is split by responsibility:

- ``namespace``/``filters``/``operators``/``template`` — shared leaves;
- ``engine_current`` — the hand-written evaluator behind the contract;
- ``engine`` — the selection point (the one line that swaps the engine);
- ``api`` — the public evaluation entry points;
- ``diagnostics`` — condition validation and remediation.

This ``__init__`` is a logic-free facade that keeps the historical
``specify_cli.workflows.expressions`` surface — including the private names the
tests import — working unchanged.
"""

from __future__ import annotations

from .api import evaluate_condition, evaluate_expression
from .diagnostics import (
    condition_has_malformed_expression_block,
    condition_is_interpolated_to_text,
    condition_is_never_evaluated,
    format_condition_correction,
    format_condition_remediation,
    switch_expression_is_never_evaluated,
    _has_unbalanced_bracket,
    _has_unbalanced_quote,
    _unresolvable_term,
)
from .engine import (
    _COMPARISON_OPERATORS,
    _WORD_OPERATORS,
    _collect_leaves,
    _evaluator_rejects,
    _has_incomplete_operand,
    _leaf_sink,
)
from .filters import _REGISTERED_FILTERS
from .template import _strip_stray_delimiters

__all__ = [
    "condition_has_malformed_expression_block",
    "condition_is_interpolated_to_text",
    "condition_is_never_evaluated",
    "evaluate_condition",
    "evaluate_expression",
    "format_condition_correction",
    "format_condition_remediation",
    "switch_expression_is_never_evaluated",
    "_COMPARISON_OPERATORS",
    "_REGISTERED_FILTERS",
    "_WORD_OPERATORS",
    "_collect_leaves",
    "_evaluator_rejects",
    "_has_incomplete_operand",
    "_has_unbalanced_bracket",
    "_has_unbalanced_quote",
    "_leaf_sink",
    "_strip_stray_delimiters",
    "_unresolvable_term",
]
