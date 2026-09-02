#!/usr/bin/env python3
"""Compose multiple evaluator results with deterministic precedence.

Reads evaluator result JSON files from a results directory, validates them
against the evaluator result schema, and produces a composed result with
deterministic outcome resolution.

Usage:
    compose_results.py --results-dir <path> --phase <phase> [--strategy strict|majority|optimistic] [--output <path>] [--json]

Output:
    A composed evaluator result written to stdout (--json) or to the specified
    output file. Exit code 0 on success, 1 on error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# -- Outcome precedence for strict composition (most severe first) ----------
_STRICT_PRECEDENCE = [
    "block",
    "gather_evidence",
    "iterate",
    "clarify",
    "warn",
    "pass",
]

_SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


def _resolve_outcome_strict(outcomes: list[str]) -> str:
    """Return the most severe outcome from the list."""
    for candidate in _STRICT_PRECEDENCE:
        if candidate in outcomes:
            return candidate
    return "pass"


def _resolve_outcome_majority(outcomes: list[str]) -> str:
    """Return the outcome with the most evaluators supporting it.

    Ties break toward the more severe outcome (strict precedence).
    """
    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o] = counts.get(o, 0) + 1
    max_count = max(counts.values())
    tied = [o for o, c in counts.items() if c == max_count]
    if len(tied) == 1:
        return tied[0]
    return _resolve_outcome_strict(tied)


def _resolve_outcome_optimistic(outcomes: list[str]) -> str:
    """Return the least severe outcome."""
    for candidate in reversed(_STRICT_PRECEDENCE):
        if candidate in outcomes:
            return candidate
    return "pass"


def _resolve_outcome(outcomes: list[str], strategy: str) -> str:
    if not outcomes:
        return "pass"
    if strategy == "majority":
        return _resolve_outcome_majority(outcomes)
    if strategy == "optimistic":
        return _resolve_outcome_optimistic(outcomes)
    return _resolve_outcome_strict(outcomes)


def _outcome_to_next_action(outcome: str, iterate_phase: str | None) -> dict[str, Any]:
    """Derive the next_action block from the composed outcome."""
    kind = outcome
    target_phase = None
    if outcome == "iterate":
        target_phase = iterate_phase
    return {
        "kind": kind,
        "target_phase": target_phase,
        "message": f"Composed outcome: {outcome}.",
    }


def _severity_sort_key(finding: dict[str, Any]) -> tuple[int, str]:
    return (_SEVERITY_ORDER.get(finding.get("severity", "info"), 99), finding.get("id", ""))


def _detect_contradictions(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect pairs of findings that contradict each other on the same subject."""
    by_subject: dict[str, list[dict[str, Any]]] = {}
    for f in findings:
        subject = f.get("subject", "")
        by_subject.setdefault(subject, []).append(f)

    contradictions: list[dict[str, Any]] = []
    for subject, group in by_subject.items():
        if len(group) < 2:
            continue
        kinds = {f.get("kind") for f in group}
        # Contradiction: one says "supported" / passes, another says "unsupported" / fails
        has_positive = any(k in ("pass", "observed") for k in kinds)
        has_negative = any(
            k in ("unsupported_claim", "contradiction", "missing_evidence", "unverified_assertion")
            for k in kinds
        )
        if has_positive and has_negative:
            contradictions.append(
                {
                    "subject": subject,
                    "finding_ids": [f["id"] for f in group],
                    "description": f"Conflicting findings on subject '{subject}'",
                }
            )
    return contradictions


def _load_result_file(filepath: Path) -> dict[str, Any] | None:
    """Load and validate a single evaluator result file.

    Returns the parsed result dict, or None if the file is invalid.
    """
    try:
        with open(filepath, encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"Warning: skipping invalid result file {filepath}: {exc}", file=sys.stderr)
        return None

    # Basic structural validation (full schema validation is done by the
    # command template; this is a lightweight check for the script).
    required = ["schema_version", "evaluator", "phase", "outcome", "findings"]
    for key in required:
        if key not in data:
            print(f"Warning: skipping {filepath}: missing required key '{key}'", file=sys.stderr)
            return None

    if not isinstance(data.get("findings"), list):
        print(f"Warning: skipping {filepath}: 'findings' is not an array", file=sys.stderr)
        return None

    return data


def _merge_model_routing(
    results: list[dict[str, Any]], composed_outcome: str
) -> dict[str, Any] | None:
    """Merge model routing recommendations from multiple evaluators.

    When multiple evaluators provide model_routing, the most conservative
    (highest tier) recommendation wins. If no evaluator provides routing,
    derive one from the composed outcome and findings.
    """
    routings = [r.get("model_routing") for r in results if r.get("model_routing")]
    if not routings:
        return None

    # Collect all recommended tiers
    tiers = [mr["recommended_tier"] for mr in routings]
    tier_precedence = {"premium": 3, "standard": 2, "budget": 1, "portfolio": 2}

    # Most conservative (highest tier) wins
    best_tier = max(tiers, key=lambda t: tier_precedence.get(t, 0))

    # Merge escalation triggers from all evaluators
    all_triggers = []
    for mr in routings:
        all_triggers.extend(mr.get("escalation_triggers", []))

    # Merge tier breakdowns (take max estimates)
    merged_breakdown: dict[str, dict[str, Any]] = {}
    for tier_key in ("budget", "standard", "premium"):
        estimates = [
            mr.get("tier_breakdown", {}).get(tier_key, {})
            for mr in routings
            if mr.get("tier_breakdown", {}).get(tier_key)
        ]
        if estimates:
            merged_breakdown[tier_key] = {
                "estimated_tokens": max(e.get("estimated_tokens", 0) for e in estimates),
                "estimated_cost_usd": max(e.get("estimated_cost_usd", 0) for e in estimates),
            }

    # Build reason from the evaluator that recommended the winning tier
    winning_routing = next(
        (mr for mr in routings if mr["recommended_tier"] == best_tier),
        routings[0],
    )

    return {
        "recommended_tier": best_tier,
        "reason": f"[Composed from {len(routings)} evaluator(s)] {winning_routing.get('reason', '')}",
        "escalation_triggers": all_triggers[:5],  # Cap at 5
        "estimated_tokens": winning_routing.get("estimated_tokens", 0),
        "estimated_cost_usd": winning_routing.get("estimated_cost_usd", 0),
        "tier_breakdown": merged_breakdown if merged_breakdown else None,
    }


def compose_results(
    results_dir: Path,
    phase: str,
    strategy: str = "strict",
) -> dict[str, Any]:
    """Compose all evaluator results for a phase into one aggregate result.

    Args:
        results_dir: Directory containing evaluator result JSON files.
        phase: Lifecycle phase to filter results by.
        strategy: Composition strategy ('strict', 'majority', or 'optimistic').

    Returns:
        A composed result dict.
    """
    if not results_dir.is_dir():
        return _empty_composed(phase, strategy, "No results directory found.")

    # Discover result files for the phase
    result_files = sorted(results_dir.glob(f"*-{phase}-*.json"))
    # Exclude previously composed files
    result_files = [f for f in result_files if not f.name.startswith("composed-")]

    if not result_files:
        return _empty_composed(phase, strategy, "No evaluator results found for this phase.")

    # Load and validate all results
    results: list[dict[str, Any]] = []
    evaluator_summaries: list[dict[str, Any]] = []
    for fp in result_files:
        data = _load_result_file(fp)
        if data is None:
            continue
        results.append(data)
        evaluator_summaries.append(
            {
                "evaluator_id": data["evaluator"]["id"],
                "outcome": data["outcome"],
                "findings_count": len(data.get("findings", [])),
            }
        )

    if not results:
        return _empty_composed(phase, strategy, "No valid evaluator results found.")

    # Collect all findings
    all_findings: list[dict[str, Any]] = []
    for r in results:
        for f in r.get("findings", []):
            # Tag each finding with its evaluator origin
            f_with_origin = dict(f)
            f_with_origin["_evaluator_id"] = r["evaluator"]["id"]
            all_findings.append(f_with_origin)

    # Sort findings by severity, then by ID
    all_findings.sort(key=_severity_sort_key)

    # Resolve composed outcome
    outcomes = [r["outcome"] for r in results]
    composed_outcome = _resolve_outcome(outcomes, strategy)

    # Determine iterate target phase
    iterate_phases = [
        r.get("next_action", {}).get("target_phase")
        for r in results
        if r["outcome"] == "iterate" and r.get("next_action", {}).get("target_phase")
    ]
    most_common_iterate = max(set(iterate_phases), key=iterate_phases.count) if iterate_phases else None

    # Detect contradictions
    contradictions = _detect_contradictions(all_findings)

    # Merge model routing recommendations
    model_routing = _merge_model_routing(results, composed_outcome)

    # Collect evaluator states
    evaluator_states: dict[str, Any] = {}
    for r in results:
        eid = r["evaluator"]["id"]
        if "state" in r:
            evaluator_states[eid] = r["state"]

    # Build composed result
    composed = {
        "schema_version": "1.0",
        "composed": True,
        "phase": phase,
        "composition_strategy": strategy,
        "composed_outcome": composed_outcome,
        "composed_summary": (
            f"{len(results)} evaluator(s) ran. "
            f"Outcomes: {', '.join(f'{s['evaluator_id']}={s['outcome']}' for s in evaluator_summaries)}. "
            f"{len(all_findings)} finding(s) total."
        ),
        "evaluator_results": evaluator_summaries,
        "findings": all_findings,
        "next_action": _outcome_to_next_action(composed_outcome, most_common_iterate),
        "model_routing": model_routing,
        "evaluator_states": evaluator_states,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evaluator_count": len(results),
            "contradictory_findings": contradictions,
        },
    }

    return composed


def _empty_composed(phase: str, strategy: str, message: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "composed": True,
        "phase": phase,
        "composition_strategy": strategy,
        "composed_outcome": "pass",
        "composed_summary": message,
        "evaluator_results": [],
        "findings": [],
        "next_action": {"kind": "pass", "target_phase": None, "message": message},
        "evaluator_states": {},
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evaluator_count": 0,
            "contradictory_findings": [],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compose multiple evaluator results with deterministic precedence."
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        type=Path,
        help="Directory containing evaluator result JSON files.",
    )
    parser.add_argument(
        "--phase",
        required=True,
        help="Lifecycle phase to compose results for (e.g., after_plan).",
    )
    parser.add_argument(
        "--strategy",
        choices=["strict", "majority", "optimistic"],
        default="strict",
        help="Composition strategy (default: strict).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write composed result to this file instead of stdout.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw JSON to stdout (default when --output is not specified).",
    )

    args = parser.parse_args()

    composed = compose_results(
        results_dir=args.results_dir,
        phase=args.phase,
        strategy=args.strategy,
    )

    output_json = json.dumps(composed, indent=2, ensure_ascii=False)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json + "\n", encoding="utf-8")
        print(f"Composed result written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
