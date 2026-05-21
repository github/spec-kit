"""Gate-script loader and validator for non-interactive gate testing.

A gate script lets CI or test runners drive gate verdicts without
operator interaction. Used by `specify workflow run --gate-script <path>`
and by the workflow engine to consult scripted verdicts before
prompting.

The schema (``speckit.gate-script/v1``) is intentionally minimal:

.. code-block:: yaml

    schema: speckit.gate-script/v1
    verdicts:
      - gate_id: review-overview
        iteration: 0
        verdict: improve
      - gate_id: review-overview
        iteration: 1
        verdict: approve

``gate_id`` matches the YAML step ``id``. For gates that fire multiple
times (e.g. inside a ``while`` loop), ``iteration`` selects which
firing the verdict applies to (0-indexed, counting from the first
time the gate runs within the current workflow run). ``verdict`` is
the option string the gate would otherwise produce — typically one
of ``approve`` / ``reject`` / ``edit`` / a custom route name.

When the engine consults the script and finds no matching entry for a
gate firing, the gate falls back to its normal behaviour (interactive
prompt on TTY, ``PAUSED`` otherwise).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


GATE_SCRIPT_SCHEMA = "speckit.gate-script/v1"


def load_gate_script(path: Path) -> list[dict[str, Any]]:
    """Load and validate a gate-script YAML file.

    Returns the parsed ``verdicts`` list. Raises ``ValueError`` with a
    clear message on any structural problem so CLI callers can surface
    the error directly to the operator.
    """
    if not path.exists():
        msg = f"Gate script not found: {path}"
        raise FileNotFoundError(msg)

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return parse_gate_script(data, source=str(path))


def parse_gate_script(
    data: Any, *, source: str | None = None
) -> list[dict[str, Any]]:
    """Validate a parsed gate-script mapping and return its verdicts.

    Separated from ``load_gate_script`` so tests and callers with
    pre-parsed YAML (e.g. from a string) can reuse the validator
    without writing to disk.
    """
    where = f" in {source}" if source else ""
    if not isinstance(data, dict):
        msg = f"Gate script{where} must be a mapping at the top level."
        raise ValueError(msg)

    schema = data.get("schema")
    if schema != GATE_SCRIPT_SCHEMA:
        msg = (
            f"Gate script{where} has unsupported schema {schema!r}. "
            f"Expected {GATE_SCRIPT_SCHEMA!r}."
        )
        raise ValueError(msg)

    verdicts = data.get("verdicts")
    if not isinstance(verdicts, list):
        msg = (
            f"Gate script{where}: 'verdicts' must be a list, "
            f"got {type(verdicts).__name__}."
        )
        raise ValueError(msg)

    seen_keys: set[tuple[str, int]] = set()
    for index, entry in enumerate(verdicts):
        if not isinstance(entry, dict):
            msg = (
                f"Gate script{where}: verdict at index {index} must be a "
                f"mapping with 'gate_id', 'iteration', and 'verdict'."
            )
            raise ValueError(msg)
        for required in ("gate_id", "iteration", "verdict"):
            if required not in entry:
                msg = (
                    f"Gate script{where}: verdict at index {index} is "
                    f"missing required field {required!r}."
                )
                raise ValueError(msg)
        if not isinstance(entry["gate_id"], str):
            msg = (
                f"Gate script{where}: verdict at index {index}: "
                f"'gate_id' must be a string."
            )
            raise ValueError(msg)
        if not isinstance(entry["iteration"], int) or isinstance(
            entry["iteration"], bool
        ):
            msg = (
                f"Gate script{where}: verdict at index {index}: "
                f"'iteration' must be an integer (got "
                f"{type(entry['iteration']).__name__})."
            )
            raise ValueError(msg)
        if entry["iteration"] < 0:
            msg = (
                f"Gate script{where}: verdict at index {index}: "
                f"'iteration' must be >= 0."
            )
            raise ValueError(msg)
        if not isinstance(entry["verdict"], str):
            msg = (
                f"Gate script{where}: verdict at index {index}: "
                f"'verdict' must be a string."
            )
            raise ValueError(msg)

        # Reject duplicate (gate_id, iteration) pairs at parse time.
        # `lookup_scripted_verdict` returns the first match, so a
        # duplicate would silently shadow the later entry — almost
        # always a copy-paste authoring mistake. Failing fast surfaces
        # the conflict immediately instead of leaving it for runtime
        # detective work.
        key = (entry["gate_id"], entry["iteration"])
        if key in seen_keys:
            msg = (
                f"Gate script{where}: verdict at index {index}: "
                f"duplicate (gate_id={entry['gate_id']!r}, "
                f"iteration={entry['iteration']}) — each pair must "
                f"appear at most once."
            )
            raise ValueError(msg)
        seen_keys.add(key)

    return verdicts


def lookup_scripted_verdict(
    script: list[dict[str, Any]],
    base_gate_id: str,
    iteration: int,
) -> str | None:
    """Return the scripted verdict for ``(base_gate_id, iteration)``,
    or ``None`` if no entry matches.

    The engine maintains per-gate firing counters and consults this
    helper before prompting interactively.
    """
    if not script:
        return None
    for entry in script:
        if entry.get("gate_id") == base_gate_id and entry.get("iteration") == iteration:
            verdict = entry.get("verdict")
            if isinstance(verdict, str):
                return verdict
    return None


def extract_base_gate_id(step_id: str) -> str:
    """Strip loop-iteration suffix from a step id to recover its base.

    The engine namespaces nested loop steps as
    ``parent_id:child_id:iter_num``. Gate scripts match on the
    workflow-author-visible ``child_id`` — not the engine-internal
    namespaced form — so this helper inverts that namespacing.

    Examples::

        "my-gate"                  → "my-gate"
        "my-loop:my-gate:1"        → "my-gate"
        "outer:inner:my-gate:2"    → "my-gate"
    """
    parts = step_id.split(":")
    if len(parts) >= 3 and parts[-1].isdigit():
        return parts[-2]
    return step_id
