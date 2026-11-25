"""Deterministic core of the Spec Kit autopilot extension.

Everything in this package is plain code: no model calls. The conductor's
LLM work (planning epics, implementing, reviewing) happens in agent commands;
ordering, worktrees, caps, merges and the exit gate are decided here.

Stdlib only, Python 3.11+, so it runs under any ``python3`` on PATH without
the Specify CLI's own environment.
"""

__version__ = "1.0.0"
