#!/usr/bin/env python3
"""Quick-start demo: Evaluator Contract in action.

Creates sample evaluator results for a realistic scenario, composes them,
generates reports in all formats, and shows model routing — all in one
self-contained script. No dependencies beyond Python 3.11+ stdlib.

Usage:
    python extensions/evaluator/examples/demo.py
    python extensions/evaluator/examples/demo.py --output /tmp/demo-results
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the compose script to path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts" / "python"
sys.path.insert(0, str(_SCRIPTS_DIR))
from compose_results import compose_results


# ═══════════════════════════════════════════════════════════════════════════════
# Scenario: E-commerce Checkout Feature
# ═══════════════════════════════════════════════════════════════════════════════

SCENARIO = """
Scenario: E-Commerce Checkout Feature

A team is building a checkout flow for an e-commerce platform. Three evaluators
run after the specification phase:

  1. schema-validate (deterministic) — checks spec structure and completeness
  2. epistemic (model-backed) — checks evidence quality and unsupported claims
  3. security-scan (deterministic) — checks for security concerns

The evaluators find issues at different severity levels. The compose command
merges them with deterministic precedence. The report command renders the
results in multiple formats. The route command recommends which model tier
to use for the next phase.
"""


def make_result(evaluator_id: str, version: str, outcome: str, phase: str,
                deterministic: bool, findings: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "evaluator": {"id": evaluator_id, "version": version,
                       "name": evaluator_id.replace("-", " ").title()},
        "phase": phase,
        "outcome": outcome,
        "summary": f"{evaluator_id} found {len(findings)} issue(s).",
        "findings": findings,
        "next_action": {"kind": outcome, "target_phase": None, "message": ""},
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "deterministic": deterministic,
        },
        "state": {},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluator Contract Quick-Start Demo")
    parser.add_argument("--output", type=Path, default=None,
                        help="Directory to write result files (default: temp dir)")
    args = parser.parse_args()

    # ── Setup ────────────────────────────────────────────────────────────────
    if args.output:
        results_dir = args.output
        results_dir.mkdir(parents=True, exist_ok=True)
    else:
        import tempfile
        tmp = tempfile.mkdtemp(prefix="evaluator-demo-")
        results_dir = Path(tmp)

    phase = "after_specify"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # ── Evaluator 1: Schema Validator (deterministic) ────────────────────────
    schema_findings = [
        {
            "id": "SCH-001", "severity": "medium", "kind": "ambiguous_requirement",
            "subject": "REQ-003",
            "description": "Requirement 'checkout shall be fast' has no measurable threshold.",
            "evidence_refs": [{"ref": "spec.md#REQ-003", "kind": "observed",
                               "description": "Spec says 'fast' without defining it"}],
            "provenance_refs": ["spec.md#REQ-003"],
            "uncertainty": "none",
            "recommended_action": "clarify",
            "rationale": "Ambiguous terms prevent testable acceptance criteria.",
        },
        {
            "id": "SCH-002", "severity": "low", "kind": "schema_violation",
            "subject": "REQ-007",
            "description": "Requirement missing acceptance criteria section.",
            "evidence_refs": [{"ref": "spec.md#REQ-007", "kind": "observed",
                               "description": "No acceptance criteria block present"}],
            "provenance_refs": ["spec.md#REQ-007"],
            "uncertainty": "none",
            "recommended_action": "revise",
            "rationale": "All requirements should have acceptance criteria per spec template.",
        },
    ]
    schema_result = make_result("schema-validate", "1.0.0", "warn", phase, True, schema_findings)

    # ── Evaluator 2: Epistemic Evaluator (model-backed) ──────────────────────
    epistemic_findings = [
        {
            "id": "EPI-001", "severity": "high", "kind": "unsupported_claim",
            "subject": "REQ-004",
            "description": "Claim that 'checkout completes in under 3 seconds' has no supporting evidence.",
            "evidence_refs": [],
            "provenance_refs": ["spec.md#REQ-004"],
            "uncertainty": "insufficient_evidence",
            "recommended_action": "gather_evidence",
            "rationale": "Performance claims require benchmarks or reference data.",
        },
        {
            "id": "EPI-002", "severity": "high", "kind": "missing_evidence",
            "subject": "REQ-006",
            "description": "PCI compliance claim has no evidence of assessment scope.",
            "evidence_refs": [],
            "provenance_refs": ["spec.md#REQ-006"],
            "uncertainty": "insufficient_evidence",
            "recommended_action": "gather_evidence",
            "rationale": "PCI DSS compliance requires documented scope and assessment.",
        },
        {
            "id": "EPI-003", "severity": "medium", "kind": "unverified_assertion",
            "subject": "REQ-002",
            "description": "Payment method support list is asserted without provider confirmation.",
            "evidence_refs": [{"ref": "spec.md#REQ-002", "kind": "asserted",
                               "description": "Listed providers but no integration confirmation"}],
            "provenance_refs": ["spec.md#REQ-002"],
            "uncertainty": "medium",
            "recommended_action": "gather_evidence",
            "rationale": "Provider support should be confirmed before committing to spec.",
        },
    ]
    epistemic_result = make_result("epistemic", "0.2.0", "iterate", phase, False, epistemic_findings)

    # ── Evaluator 3: Security Scanner (deterministic) ────────────────────────
    security_findings = [
        {
            "id": "SEC-001", "severity": "critical", "kind": "security_concern",
            "subject": "REQ-005",
            "description": "Spec stores PII in checkout but has no data retention or deletion policy.",
            "evidence_refs": [{"ref": "spec.md#REQ-005", "kind": "observed",
                               "description": "PII fields listed without retention policy"}],
            "provenance_refs": ["spec.md#REQ-005"],
            "uncertainty": "none",
            "recommended_action": "block",
            "rationale": "GDPR/CCPA require explicit data retention and deletion policies for PII.",
        },
        {
            "id": "SEC-002", "severity": "high", "kind": "policy_violation",
            "subject": "REQ-008",
            "description": "API key in query parameters — should use Authorization header.",
            "evidence_refs": [{"ref": "spec.md#REQ-008", "kind": "observed",
                               "description": "API design shows api_key query parameter"}],
            "provenance_refs": ["spec.md#REQ-008"],
            "uncertainty": "none",
            "recommended_action": "revise",
            "rationale": "API keys in URLs are logged by proxies and leak in referrer headers.",
        },
    ]
    security_result = make_result("security-scan", "2.1.0", "block", phase, True, security_findings)

    # ── Write results ────────────────────────────────────────────────────────
    (results_dir / f"schema-validate-{phase}-{ts}.json").write_text(
        json.dumps(schema_result, indent=2))
    (results_dir / f"epistemic-{phase}-{ts}.json").write_text(
        json.dumps(epistemic_result, indent=2))
    (results_dir / f"security-scan-{phase}-{ts}.json").write_text(
        json.dumps(security_result, indent=2))

    # ── Compose ──────────────────────────────────────────────────────────────
    composed = compose_results(results_dir, phase, "strict")

    # ── Model Routing ────────────────────────────────────────────────────────
    # Derive routing from composed findings
    critical_count = sum(1 for f in composed["findings"] if f.get("severity") == "critical")
    high_count = sum(1 for f in composed["findings"] if f.get("severity") == "high")
    evidence_gaps = sum(1 for f in composed["findings"]
                        if f.get("kind") in ("unsupported_claim", "missing_evidence"))
    contradictions = len(composed["metadata"]["contradictory_findings"])

    total_weight = critical_count * 0.4 + high_count * 0.3 + evidence_gaps * 0.2 + contradictions * 0.1
    max_possible = len(composed["findings"]) * 0.4
    risk_score = total_weight / max_possible if max_possible > 0 else 0

    if risk_score > 0.5:
        tier = "premium"
        reason = f"Risk score {risk_score:.2f} — critical/high findings require premium review"
    elif risk_score > 0.2:
        tier = "standard"
        reason = f"Risk score {risk_score:.2f} — moderate risk, standard quality recommended"
    else:
        tier = "budget"
        reason = f"Risk score {risk_score:.2f} — low risk, budget tier sufficient"

    routing = {
        "recommended_tier": tier,
        "reason": reason,
        "escalation_triggers": [
            {"condition": "Any new critical finding", "escalate_to": "premium"},
            {"condition": "More than 3 unsupported claims", "escalate_to": "premium"},
        ],
        "estimated_tokens": 12000 if tier == "standard" else (18000 if tier == "budget" else 8000),
        "estimated_cost_usd": 0.22 if tier == "standard" else (0.01 if tier == "budget" else 0.72),
        "tier_breakdown": {
            "budget": {"estimated_tokens": 18000, "estimated_cost_usd": 0.01},
            "standard": {"estimated_tokens": 12000, "estimated_cost_usd": 0.22},
            "premium": {"estimated_tokens": 8000, "estimated_cost_usd": 0.72},
        },
    }

    # ── Print Report ─────────────────────────────────────────────────────────
    S = "=" * 72
    s = "-" * 72

    print()
    print(S)
    print("  EVALUATOR CONTRACT — QUICK-START DEMO")
    print(S)
    print()
    print(SCENARIO)
    print()

    # Evaluator summaries
    print(S)
    print("  EVALUATOR RESULTS (3 evaluators)")
    print(S)
    for name, result, findings in [
        ("Schema Validator", schema_result, schema_findings),
        ("Epistemic Evaluator", epistemic_result, epistemic_findings),
        ("Security Scanner", security_result, security_findings),
    ]:
        sevs = {}
        for f in findings:
            sevs[f["severity"]] = sevs.get(f["severity"], 0) + 1
        sev_str = ", ".join(f"{c} {s}" for s, c in sorted(sevs.items()))
        print(f"  {name}: {result['outcome'].upper()} ({len(findings)} findings: {sev_str})")
        for f in findings:
            print(f"    [{f['severity'].upper():>8s}] {f['id']} — {f['kind']}")
            print(f"              {f['description'][:70]}")
    print()

    # Composition
    print(S)
    print("  COMPOSED RESULT (strict strategy)")
    print(S)
    print(f"  Outcome:          {composed['composed_outcome'].upper()}")
    print(f"  Evaluators:       {composed['metadata']['evaluator_count']} run")
    print(f"  Total Findings:   {len(composed['findings'])}")
    print(f"  Contradictions:   {len(composed['metadata']['contradictory_findings'])}")
    print(f"  Next Action:      {composed['next_action']['kind']}")
    print()
    print(f"  Findings by severity:")
    sevs = {}
    for f in composed["findings"]:
        sevs[f["severity"]] = sevs.get(f["severity"], 0) + 1
    for s in ("critical", "high", "medium", "low", "info"):
        if s in sevs:
            bar = "█" * sevs[s]
            print(f"    {s:>8s}: {bar} {sevs[s]}")
    print()

    # Model Routing
    print(S)
    print("  MODEL ROUTING RECOMMENDATION")
    print(S)
    print(f"  Risk Score:       {risk_score:.2f}")
    print(f"  Recommended Tier: {tier.upper()}")
    print(f"  Reason:           {reason}")
    print()
    print(f"  Cost Comparison (next phase):")
    print(f"    Budget:    ${routing['tier_breakdown']['budget']['estimated_cost_usd']:.2f} "
          f"({routing['tier_breakdown']['budget']['estimated_tokens']:,} tokens)")
    print(f"    Standard:  ${routing['tier_breakdown']['standard']['estimated_cost_usd']:.2f} "
          f"({routing['tier_breakdown']['standard']['estimated_tokens']:,} tokens)")
    print(f"    Premium:   ${routing['tier_breakdown']['premium']['estimated_cost_usd']:.2f} "
          f"({routing['tier_breakdown']['premium']['estimated_tokens']:,} tokens)")
    print()
    print(f"  Escalation Triggers:")
    for t in routing["escalation_triggers"]:
        print(f"    • {t['condition']} → {t['escalate_to']}")
    print()

    # Report formats
    print(S)
    print("  REPORT FORMATS (all generated from same composed result)")
    print(S)

    # Terminal
    print(f"\n  ── TERMINAL ──")
    lines = []
    lines.append(f"  Outcome: {composed['composed_outcome'].upper()}")
    lines.append(f"  Findings: {len(composed['findings'])} total")
    for f in composed["findings"]:
        lines.append(f"  [{f['severity'].upper():>8s}] {f['id']} — {f['kind']}: {f['description'][:60]}")
    lines.append(f"  Next Action: {composed['next_action']['kind']}")
    for line in lines:
        print(f"  {line}")

    # Markdown
    print(f"\n  ── MARKDOWN (table) ──")
    print(f"  | ID | Severity | Kind | Subject | Action |")
    print(f"  |----|----------|------|---------|--------|")
    for f in composed["findings"]:
        print(f"  | {f['id']} | {f['severity']} | {f['kind']} | {f['subject']} | {f.get('recommended_action', 'N/A')} |")

    # CI Annotation
    print(f"\n  ── CI ANNOTATION (GitHub Actions) ──")
    for f in composed["findings"]:
        prefix = "::error" if f["severity"] in ("critical", "high") else "::warning"
        print(f"  {prefix} file=spec.md,title={f['id']}::[{f['kind']}] {f['description'][:80]}")

    # Gate
    print(f"\n  ── GATE ──")
    gate_codes = {"pass": 0, "warn": 0, "iterate": 1, "clarify": 1, "gather_evidence": 1, "block": 2}
    exit_code = gate_codes.get(composed["composed_outcome"], 1)
    print(f"  Exit Code: {exit_code} ({'PASS' if exit_code == 0 else 'BLOCK' if exit_code == 2 else 'WARN'})")
    print(f"  Outcome: {composed['composed_outcome']}")

    # JSON
    print(f"\n  ── JSON (first 3 keys) ──")
    for key in list(composed.keys())[:3]:
        val = composed[key]
        if isinstance(val, list):
            print(f"  \"{key}\": [{len(val)} items]")
        elif isinstance(val, dict):
            print(f"  \"{key}\": {{{len(val)} keys}}")
        else:
            print(f"  \"{key}\": {json.dumps(val)}")

    print()
    print(S)
    print(f"  Results written to: {results_dir}")
    print(f"  Run again with: python {Path(__file__).relative_to(Path.cwd())}")
    print(S)
    print()


if __name__ == "__main__":
    main()
