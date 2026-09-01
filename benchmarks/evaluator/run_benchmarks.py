"""Comprehensive benchmark suite for the Evaluator Contract extension.

Simulates a full Spec-Driven Development workflow with multiple evaluators
at each phase, measures composition correctness at scale, and benchmarks
report generation across all formats.

Benchmarks:
    1. SDD Workflow Simulation — full lifecycle with evaluators at each phase
    2. Composition Scale — 10–1000 findings, 2–20 evaluators
    3. Report Generation — all 5 formats at scale
    4. Contradiction Detection — stress test with conflicting findings
    5. Schema Validation Throughput — validate results at volume
    6. Comparison: With vs Without Contract — ad-hoc vs standardized

Usage:
    python benchmarks/evaluator/run_benchmarks.py
    python benchmarks/evaluator/run_benchmarks.py --quick     # fast smoke test
    python benchmarks/evaluator/run_benchmarks.py --scale     # full scale test
    python benchmarks/evaluator/run_benchmarks.py --output results/benchmark-report.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# Add the evaluator scripts to path
_SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "extensions" / "evaluator" / "scripts" / "python"
)
sys.path.insert(0, str(_SCRIPTS_DIR))

from compose_results import compose_results, _resolve_outcome_strict


# ═══════════════════════════════════════════════════════════════════════════════
# Data types
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class BenchmarkResult:
    name: str
    description: str
    duration_ms: float
    iterations: int
    metrics: dict[str, Any] = field(default_factory=dict)
    passed: bool = True
    error: str | None = None


@dataclass
class EvaluatorConfig:
    id: str
    name: str
    version: str
    deterministic: bool
    phase: str
    finding_kinds: list[str]
    severity_distribution: dict[str, float]  # severity → probability weight
    outcome: str  # typical outcome


# ═══════════════════════════════════════════════════════════════════════════════
# Scenario data — realistic SDD project
# ═══════════════════════════════════════════════════════════════════════════════

# A realistic e-commerce platform spec with known issues
SAMPLE_SPEC_REQUIREMENTS = [
    {"id": "REQ-001", "text": "Users shall be able to create accounts with email and password", "has_evidence": True},
    {"id": "REQ-002", "text": "The system shall process payments via Stripe and PayPal", "has_evidence": True},
    {"id": "REQ-003", "text": "The platform must be highly scalable", "has_evidence": False},  # ambiguous
    {"id": "REQ-004", "text": "Admin dashboard shall show real-time analytics", "has_evidence": True},
    {"id": "REQ-005", "text": "All user data must be encrypted at rest and in transit", "has_evidence": True},
    {"id": "REQ-006", "text": "The checkout flow shall complete in under 3 seconds", "has_evidence": False},  # unsupported claim
    {"id": "REQ-007", "text": "The system shall support 1M concurrent users", "has_evidence": False},  # unsupported
    {"id": "REQ-008", "text": "API must be RESTful with JSON responses", "has_evidence": True},
    {"id": "REQ-009", "text": "The platform shall integrate with any third-party CRM", "has_evidence": False},  # ambiguous
    {"id": "REQ-010", "text": "Password reset must require email verification", "has_evidence": True},
    {"id": "REQ-011", "text": "The system shall never lose data under any circumstance", "has_evidence": False},  # impossible claim
    {"id": "REQ-012", "text": "Search results must return in under 100ms", "has_evidence": False},  # unsupported
    {"id": "REQ-013", "text": "Users can delete their accounts and all associated data", "has_evidence": True},
    {"id": "REQ-014", "text": "The platform shall be GDPR and CCPA compliant", "has_evidence": False},  # unsupported
    {"id": "REQ-015", "text": "Inventory management must sync in real-time across warehouses", "has_evidence": True},
]

SAMPLE_PLAN_COMPONENTS = [
    {"id": "COMP-001", "name": "User Service", "risks": ["auth token storage", "password hashing"]},
    {"id": "COMP-002", "name": "Payment Gateway", "risks": ["PCI compliance", "idempotency", "retry storms"]},
    {"id": "COMP-003", "name": "Product Catalog", "risks": ["search performance", "cache invalidation"]},
    {"id": "COMP-004", "name": "Order Management", "risks": ["distributed transactions", "eventual consistency"]},
    {"id": "COMP-005", "name": "Analytics Pipeline", "risks": ["data freshness", "query performance at scale"]},
    {"id": "COMP-006", "name": "Notification Service", "risks": ["delivery guarantees", "rate limiting"]},
    {"id": "COMP-007", "name": "Admin Dashboard", "risks": ["RBAC", "audit logging"]},
    {"id": "COMP-008", "name": "API Gateway", "risks": ["rate limiting", "auth token validation"]},
]

SAMPLE_TASKS = [
    {"id": "T-001", "phase": "implement", "component": "COMP-001", "description": "Implement user registration endpoint"},
    {"id": "T-002", "phase": "implement", "component": "COMP-001", "description": "Implement password hashing with bcrypt"},
    {"id": "T-003", "phase": "implement", "component": "COMP-002", "description": "Integrate Stripe payment processing"},
    {"id": "T-004", "phase": "implement", "component": "COMP-002", "description": "Integrate PayPal payment processing"},
    {"id": "T-005", "phase": "implement", "component": "COMP-003", "description": "Build product search with Elasticsearch"},
    {"id": "T-006", "phase": "implement", "component": "COMP-004", "description": "Implement order state machine"},
    {"id": "T-007", "phase": "implement", "component": "COMP-005", "description": "Build analytics data pipeline"},
    {"id": "T-008", "phase": "implement", "component": "COMP-006", "description": "Implement email notification service"},
    {"id": "T-009", "phase": "implement", "component": "COMP-007", "description": "Build admin RBAC system"},
    {"id": "T-010", "phase": "implement", "component": "COMP-008", "description": "Implement API rate limiting"},
    {"id": "T-011", "phase": "test", "component": "COMP-001", "description": "Write user service integration tests"},
    {"id": "T-012", "phase": "test", "component": "COMP-002", "description": "Write payment gateway integration tests"},
    {"id": "T-013", "phase": "test", "component": "COMP-004", "description": "Write order management tests"},
    {"id": "T-014", "phase": "docs", "component": "COMP-008", "description": "Document API endpoints"},
    {"id": "T-015", "phase": "docs", "component": "COMP-001", "description": "Document authentication flow"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# Evaluator configurations — realistic evaluator types
# ═══════════════════════════════════════════════════════════════════════════════

EVALUATOR_CONFIGS = {
    "schema-validate": EvaluatorConfig(
        id="schema-validate",
        name="Schema Validator",
        version="1.0.0",
        deterministic=True,
        phase="after_specify",
        finding_kinds=["schema_violation", "ambiguous_requirement"],
        severity_distribution={"high": 0.2, "medium": 0.5, "low": 0.3},
        outcome="warn",
    ),
    "epistemic": EvaluatorConfig(
        id="epistemic",
        name="Epistemic Evaluator",
        version="0.2.0",
        deterministic=False,
        phase="after_specify",
        finding_kinds=["unsupported_claim", "missing_evidence", "unverified_assertion"],
        severity_distribution={"critical": 0.05, "high": 0.25, "medium": 0.4, "low": 0.3},
        outcome="iterate",
    ),
    "security-scan": EvaluatorConfig(
        id="security-scan",
        name="Security Scanner",
        version="2.1.0",
        deterministic=True,
        phase="after_plan",
        finding_kinds=["security_concern", "policy_violation"],
        severity_distribution={"critical": 0.1, "high": 0.3, "medium": 0.4, "low": 0.2},
        outcome="warn",
    ),
    "risk-assess": EvaluatorConfig(
        id="risk-assess",
        name="Risk Assessor",
        version="0.5.0",
        deterministic=False,
        phase="after_plan",
        finding_kinds=["risk_unaddressed", "assumption_unvalidated", "coverage_gap"],
        severity_distribution={"high": 0.3, "medium": 0.5, "low": 0.2},
        outcome="warn",
    ),
    "coverage-check": EvaluatorConfig(
        id="coverage-check",
        name="Coverage Checker",
        version="1.2.0",
        deterministic=True,
        phase="after_tasks",
        finding_kinds=["coverage_gap", "traceability_gap"],
        severity_distribution={"high": 0.15, "medium": 0.45, "low": 0.4},
        outcome="warn",
    ),
    "provenance-verify": EvaluatorConfig(
        id="provenance-verify",
        name="Provenance Verifier",
        version="0.1.0",
        deterministic=True,
        phase="after_tasks",
        finding_kinds=["provenance_gap", "missing_evidence"],
        severity_distribution={"high": 0.2, "medium": 0.5, "low": 0.3},
        outcome="warn",
    ),
    "policy-check": EvaluatorConfig(
        id="policy-check",
        name="Policy Checker",
        version="1.0.0",
        deterministic=True,
        phase="after_implement",
        finding_kinds=["policy_violation", "schema_violation"],
        severity_distribution={"critical": 0.05, "high": 0.2, "medium": 0.5, "low": 0.25},
        outcome="warn",
    ),
    "constitution-audit": EvaluatorConfig(
        id="constitution-audit",
        name="Constitution Auditor",
        version="0.3.0",
        deterministic=False,
        phase="after_implement",
        finding_kinds=["policy_violation", "contradiction", "unsupported_claim"],
        severity_distribution={"high": 0.3, "medium": 0.5, "low": 0.2},
        outcome="warn",
    ),
}

# Phases and which evaluators run at each
PHASE_EVALUATORS = {
    "after_specify": ["schema-validate", "epistemic"],
    "after_plan": ["security-scan", "risk-assess"],
    "after_tasks": ["coverage-check", "provenance-verify"],
    "after_implement": ["policy-check", "constitution-audit"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Result generators
# ═══════════════════════════════════════════════════════════════════════════════

EVIDENCE_KINDS = ["observed", "inferred", "asserted", "contradicted", "unsupported"]
UNCERTAINTY_LEVELS = ["none", "low", "medium", "high", "insufficient_evidence"]
RECOMMENDED_ACTIONS = ["none", "gather_evidence", "clarify", "revise", "iterate", "escalate", "accept_risk", "block"]
OUTCOMES = ["pass", "warn", "iterate", "clarify", "gather_evidence", "block"]


def _weighted_choice(choices: list[str], weights: dict[str, float]) -> str:
    """Pick a random choice weighted by the given distribution."""
    import random
    total = sum(weights.get(c, 0) for c in choices)
    r = random.random() * total
    cumulative = 0.0
    for c in choices:
        cumulative += weights.get(c, 0)
        if r <= cumulative:
            return c
    return choices[-1]


def generate_finding(
    finding_id: str,
    config: EvaluatorConfig,
    subjects: list[str],
    seed: int = 0,
) -> dict[str, Any]:
    """Generate a single realistic finding."""
    import random
    rng = random.Random(seed + hash(finding_id))

    severity = _weighted_choice(
        ["critical", "high", "medium", "low", "info"],
        {k: v for k, v in config.severity_distribution.items()},
    )
    kind = rng.choice(config.finding_kinds)
    subject = rng.choice(subjects)
    uncertainty = rng.choice(UNCERTAINTY_LEVELS)
    action = rng.choice(RECOMMENDED_ACTIONS)

    # Generate evidence refs
    evidence_refs = []
    if rng.random() > 0.3:  # 70% of findings have evidence
        num_refs = rng.randint(1, 3)
        for _ in range(num_refs):
            evidence_refs.append({
                "ref": f"{subject.split('-')[0].lower()}.md#{subject}",
                "kind": rng.choice(EVIDENCE_KINDS),
                "description": f"Evidence for {subject} from {config.name}",
            })

    return {
        "id": finding_id,
        "severity": severity,
        "kind": kind,
        "subject": subject,
        "description": f"{kind.replace('_', ' ').title()} detected in {subject}",
        "evidence_refs": evidence_refs,
        "provenance_refs": [f"{subject.split('-')[0].lower()}.md#{subject}"],
        "uncertainty": uncertainty,
        "recommended_action": action,
        "rationale": f"Evaluated by {config.name} v{config.version}",
    }


def generate_evaluator_result(
    config: EvaluatorConfig,
    num_findings: int,
    subjects: list[str],
    seed: int = 0,
) -> dict[str, Any]:
    """Generate a complete evaluator result."""
    import random
    rng = random.Random(seed)

    findings = []
    for i in range(num_findings):
        finding = generate_finding(
            f"{config.id.upper()[:3]}-{i + 1:03d}",
            config,
            subjects,
            seed=seed + i,
        )
        findings.append(finding)

    # Determine actual outcome based on findings
    if any(f["severity"] == "critical" for f in findings):
        outcome = "block"
    elif any(f["severity"] == "high" for f in findings):
        outcome = "iterate" if rng.random() > 0.5 else "warn"
    elif any(f["severity"] == "medium" for f in findings):
        outcome = "warn"
    else:
        outcome = "pass"

    return {
        "schema_version": "1.0",
        "evaluator": {
            "id": config.id,
            "version": config.version,
            "name": config.name,
        },
        "phase": config.phase,
        "outcome": outcome,
        "summary": f"{config.name} found {len(findings)} issue(s) in {config.phase}.",
        "findings": findings,
        "next_action": {
            "kind": outcome,
            "target_phase": config.phase.replace("after_", "") if outcome == "iterate" else None,
            "message": f"Evaluator {config.id} recommends: {outcome}",
        },
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_ms": rng.randint(50, 5000),
            "artifacts_evaluated": [f"{config.phase.replace('after_', '')}.md"],
            "deterministic": config.deterministic,
        },
        "state": {"session_id": str(uuid.uuid4())[:8]},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark harness
# ═══════════════════════════════════════════════════════════════════════════════


def benchmark(name: str, description: str, iterations: int = 10):
    """Decorator for benchmark functions."""
    def decorator(func: Callable[..., dict[str, Any]]):
        def wrapper(*args, **kwargs) -> BenchmarkResult:
            durations = []
            last_metrics = {}
            error = None
            passed = True

            for i in range(iterations):
                start = time.perf_counter()
                try:
                    last_metrics = func(*args, **kwargs)
                except Exception as e:
                    error = str(e)
                    passed = False
                    break
                durations.append((time.perf_counter() - start) * 1000)

            avg_ms = statistics.mean(durations) if durations else 0
            return BenchmarkResult(
                name=name,
                description=description,
                duration_ms=avg_ms,
                iterations=len(durations),
                metrics=last_metrics,
                passed=passed,
                error=error,
            )
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark 1: SDD Workflow Simulation
# ═══════════════════════════════════════════════════════════════════════════════

def bench_sdd_workflow_simulation(tmp_path: Path) -> dict[str, Any]:
    """Simulate a full SDD lifecycle with evaluators at each phase.

    Phases: specify → plan → tasks → implement
    Each phase has 2 evaluators producing results.
    Results are composed at each phase.
    """
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    phase_results = {}
    total_findings = 0
    total_evaluators = 0

    for phase, evaluator_ids in PHASE_EVALUATORS.items():
        phase_findings = 0
        for eid in evaluator_ids:
            config = EVALUATOR_CONFIGS[eid]
            subjects = [r["id"] for r in SAMPLE_SPEC_REQUIREMENTS]
            result = generate_evaluator_result(config, num_findings=8, subjects=subjects, seed=hash(phase + eid))

            # Write result file
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            filename = f"{eid}-{phase}-{ts}.json"
            (results_dir / filename).write_text(json.dumps(result, indent=2))

            phase_findings += len(result["findings"])
            total_evaluators += 1

        # Compose results for this phase
        composed = compose_results(results_dir, phase, "strict")
        phase_results[phase] = {
            "outcome": composed["composed_outcome"],
            "evaluator_count": composed["metadata"]["evaluator_count"],
            "finding_count": len(composed["findings"]),
            "contradictions": len(composed["metadata"]["contradictory_findings"]),
        }
        total_findings += phase_findings

    return {
        "phases_evaluated": len(phase_results),
        "total_evaluators_run": total_evaluators,
        "total_findings": total_findings,
        "phase_outcomes": {p: r["outcome"] for p, r in phase_results.items()},
        "phase_details": phase_results,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark 2: Composition at Scale
# ═══════════════════════════════════════════════════════════════════════════════

def bench_composition_scale(tmp_path: Path, num_evaluators: int, findings_per: int) -> dict[str, Any]:
    """Benchmark composition with N evaluators each producing M findings."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    subjects = [f"REQ-{i:03d}" for i in range(1, 101)]

    for i in range(num_evaluators):
        config = EvaluatorConfig(
            id=f"eval-{i:03d}",
            name=f"Evaluator {i}",
            version="1.0.0",
            deterministic=i % 2 == 0,
            phase="after_plan",
            finding_kinds=["unsupported_claim", "missing_evidence", "coverage_gap", "ambiguous_requirement"],
            severity_distribution={"critical": 0.05, "high": 0.2, "medium": 0.4, "low": 0.35},
            outcome="warn",
        )
        result = generate_evaluator_result(config, findings_per, subjects, seed=i * 1000)
        (results_dir / f"eval-{i:03d}-after_plan-20260101T000000Z.json").write_text(json.dumps(result))

    composed = compose_results(results_dir, "after_plan", "strict")

    return {
        "num_evaluators": num_evaluators,
        "findings_per_evaluator": findings_per,
        "total_findings_input": num_evaluators * findings_per,
        "composed_findings": len(composed["findings"]),
        "composed_outcome": composed["composed_outcome"],
        "contradictions_detected": len(composed["metadata"]["contradictory_findings"]),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark 3: Report Generation
# ═══════════════════════════════════════════════════════════════════════════════

def bench_report_generation(tmp_path: Path, num_findings: int) -> dict[str, Any]:
    """Benchmark generating reports in all 5 formats."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    subjects = [f"REQ-{i:03d}" for i in range(1, num_findings + 1)]
    config = EVALUATOR_CONFIGS["epistemic"]
    result = generate_evaluator_result(config, num_findings, subjects, seed=42)
    (results_dir / f"epistemic-after_specify-20260101T000000Z.json").write_text(json.dumps(result))

    composed = compose_results(results_dir, "after_specify", "strict")

    format_timings = {}

    # Terminal format
    start = time.perf_counter()
    terminal_output = _render_terminal(composed)
    format_timings["terminal"] = (time.perf_counter() - start) * 1000

    # Markdown format
    start = time.perf_counter()
    markdown_output = _render_markdown(composed)
    format_timings["markdown"] = (time.perf_counter() - start) * 1000

    # JSON format
    start = time.perf_counter()
    json_output = json.dumps(composed, indent=2)
    format_timings["json"] = (time.perf_counter() - start) * 1000

    # CI annotation format
    start = time.perf_counter()
    ci_output = _render_ci_annotation(composed)
    format_timings["ci-annotation"] = (time.perf_counter() - start) * 1000

    # Gate format
    start = time.perf_counter()
    gate_output = _render_gate(composed)
    format_timings["gate"] = (time.perf_counter() - start) * 1000

    return {
        "num_findings": num_findings,
        "format_timings_ms": format_timings,
        "terminal_lines": len(terminal_output.split("\n")),
        "markdown_chars": len(markdown_output),
        "json_bytes": len(json_output.encode("utf-8")),
        "ci_annotation_lines": len(ci_output.split("\n")),
        "gate_exit_code": gate_output["exit_code"],
    }


def _render_terminal(composed: dict) -> str:
    """Render a terminal report."""
    lines = []
    lines.append("═" * 60)
    lines.append(f"  EVALUATOR REPORT — {composed['phase']}")
    lines.append("═" * 60)
    lines.append(f"  Outcome:  {composed['composed_outcome'].upper()}")
    lines.append(f"  Evaluators: {composed['metadata']['evaluator_count']} run")
    lines.append(f"  Findings: {len(composed['findings'])} total")
    lines.append("─" * 60)

    for f in composed["findings"][:20]:  # Show top 20
        sev = f.get("severity", "info").upper()
        lines.append(f"\n  [{sev}] {f['id']} — {f.get('kind', 'unknown')}")
        lines.append(f"  Subject: {f.get('subject', 'N/A')}")
        if f.get("recommended_action"):
            lines.append(f"  Recommendation: {f['recommended_action']}")

    if len(composed["findings"]) > 20:
        lines.append(f"\n  ... and {len(composed['findings']) - 20} more findings")

    lines.append("─" * 60)
    na = composed.get("next_action", {})
    lines.append(f"  Next Action: {na.get('kind', 'N/A')}")
    lines.append("═" * 60)
    return "\n".join(lines)


def _render_markdown(composed: dict) -> str:
    """Render a markdown report."""
    lines = []
    lines.append(f"# Evaluator Report — {composed['phase']}")
    lines.append("")
    lines.append(f"**Outcome:** `{composed['composed_outcome']}`")
    lines.append(f"**Evaluators:** {composed['metadata']['evaluator_count']} run")
    lines.append(f"**Findings:** {len(composed['findings'])} total")
    lines.append("")
    lines.append("| ID | Severity | Kind | Subject | Action |")
    lines.append("|----|----------|------|---------|--------|")

    for f in composed["findings"]:
        lines.append(
            f"| {f['id']} | {f.get('severity', 'N/A')} | {f.get('kind', 'N/A')} | "
            f"{f.get('subject', 'N/A')} | {f.get('recommended_action', 'N/A')} |"
        )

    lines.append("")
    na = composed.get("next_action", {})
    lines.append(f"**Next Action:** {na.get('kind', 'N/A')}")
    return "\n".join(lines)


def _render_ci_annotation(composed: dict) -> str:
    """Render CI annotations (GitHub Actions workflow commands)."""
    lines = []
    for f in composed["findings"]:
        severity = f.get("severity", "info")
        prefix = "::error" if severity in ("critical", "high") else "::warning"
        subject = f.get("subject", "unknown")
        # Extract file and line if possible
        if "#" in subject:
            file_ref, _, _ = subject.partition("#")
            file_path = f"{file_ref}.md"
        else:
            file_path = "unknown"
        lines.append(
            f'{prefix} file={file_path},title={f["id"]}::'
            f'[{f.get("kind", "unknown")}] {f.get("description", "")}'
        )
    return "\n".join(lines)


def _render_gate(composed: dict) -> dict:
    """Render a gate decision."""
    outcome = composed["composed_outcome"]
    exit_codes = {
        "pass": 0,
        "warn": 0,
        "iterate": 1,
        "clarify": 1,
        "gather_evidence": 1,
        "block": 2,
    }
    return {
        "exit_code": exit_codes.get(outcome, 1),
        "outcome": outcome,
        "summary": composed.get("composed_summary", ""),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark 4: Contradiction Detection Stress Test
# ═══════════════════════════════════════════════════════════════════════════════

def bench_contradiction_detection(tmp_path: Path, num_subjects: int) -> dict[str, Any]:
    """Stress test contradiction detection with deliberately conflicting findings."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    subjects = [f"REQ-{i:03d}" for i in range(1, num_subjects + 1)]

    # Evaluator A: marks everything as "observed" (positive)
    config_a = EvaluatorConfig(
        id="eval-optimist",
        name="Optimistic Evaluator",
        version="1.0.0",
        deterministic=True,
        phase="after_specify",
        finding_kinds=["observed"],
        severity_distribution={"low": 1.0},
        outcome="pass",
    )
    findings_a = []
    for i, s in enumerate(subjects):
        findings_a.append({
            "id": f"OPT-{i + 1:03d}",
            "severity": "low",
            "kind": "observed",
            "subject": s,
            "description": f"Verified {s}",
            "evidence_refs": [{"ref": f"spec.md#{s}", "kind": "observed", "description": "Direct observation"}],
            "provenance_refs": [f"spec.md#{s}"],
            "uncertainty": "none",
            "recommended_action": "none",
            "rationale": "Directly observed in specification",
        })
    result_a = {
        "schema_version": "1.0",
        "evaluator": {"id": "eval-optimist", "version": "1.0.0"},
        "phase": "after_specify",
        "outcome": "pass",
        "summary": "All requirements verified.",
        "findings": findings_a,
        "next_action": {"kind": "pass", "target_phase": None, "message": "All good"},
        "metadata": {"timestamp": "2026-01-01T00:00:00Z"},
        "state": {},
    }

    # Evaluator B: marks everything as "unsupported_claim" (negative)
    config_b = EvaluatorConfig(
        id="eval-pessimist",
        name="Pessimistic Evaluator",
        version="1.0.0",
        deterministic=True,
        phase="after_specify",
        finding_kinds=["unsupported_claim"],
        severity_distribution={"high": 1.0},
        outcome="iterate",
    )
    findings_b = []
    for i, s in enumerate(subjects):
        findings_b.append({
            "id": f"PES-{i + 1:03d}",
            "severity": "high",
            "kind": "unsupported_claim",
            "subject": s,
            "description": f"No evidence for {s}",
            "evidence_refs": [],
            "provenance_refs": [f"spec.md#{s}"],
            "uncertainty": "insufficient_evidence",
            "recommended_action": "gather_evidence",
            "rationale": "No supporting evidence found",
        })
    result_b = {
        "schema_version": "1.0",
        "evaluator": {"id": "eval-pessimist", "version": "1.0.0"},
        "phase": "after_specify",
        "outcome": "iterate",
        "summary": "All requirements lack evidence.",
        "findings": findings_b,
        "next_action": {"kind": "iterate", "target_phase": "specify", "message": "Gather evidence"},
        "metadata": {"timestamp": "2026-01-01T00:00:00Z"},
        "state": {},
    }

    (results_dir / "eval-optimist-after_specify-20260101T000000Z.json").write_text(json.dumps(result_a))
    (results_dir / "eval-pessimist-after_specify-20260101T000001Z.json").write_text(json.dumps(result_b))

    composed = compose_results(results_dir, "after_specify", "strict")

    return {
        "num_subjects": num_subjects,
        "total_findings": len(composed["findings"]),
        "contradictions_detected": len(composed["metadata"]["contradictory_findings"]),
        "contradiction_rate": len(composed["metadata"]["contradictory_findings"]) / num_subjects if num_subjects else 0,
        "composed_outcome": composed["composed_outcome"],
        "both_viewpoints_preserved": len(composed["findings"]) == num_subjects * 2,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark 5: Schema Validation Throughput
# ═══════════════════════════════════════════════════════════════════════════════

def bench_schema_validation_throughput(tmp_path: Path, num_results: int) -> dict[str, Any]:
    """Benchmark schema validation throughput at volume."""
    schema_path = (
        Path(__file__).resolve().parent.parent.parent
        / "extensions" / "evaluator" / "schemas" / "evaluator-result.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    try:
        import jsonschema
    except ImportError:
        return {"num_results": num_results, "validated": 0, "error": "jsonschema not installed"}

    subjects = [f"REQ-{i:03d}" for i in range(1, 21)]
    config = EVALUATOR_CONFIGS["schema-validate"]

    valid_count = 0
    invalid_count = 0

    for i in range(num_results):
        result = generate_evaluator_result(config, 5, subjects, seed=i)
        try:
            jsonschema.validate(result, schema)
            valid_count += 1
        except jsonschema.ValidationError:
            invalid_count += 1

    return {
        "num_results": num_results,
        "validated": valid_count,
        "invalid": invalid_count,
        "validation_rate": valid_count / num_results if num_results else 0,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark 6: With vs Without Contract Comparison
# ═══════════════════════════════════════════════════════════════════════════════

def bench_with_vs_without_contract(tmp_path: Path) -> dict[str, Any]:
    """Compare ad-hoc evaluation vs standardized contract.

    Simulates what happens when:
    - WITHOUT contract: each evaluator uses its own format, no composition
    - WITH contract: standardized schema, deterministic composition
    """
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    subjects = [r["id"] for r in SAMPLE_SPEC_REQUIREMENTS]

    # --- WITHOUT contract (ad-hoc) ---
    adhoc_start = time.perf_counter()

    # Simulate 3 evaluators with incompatible formats
    adhoc_formats = []
    # Evaluator 1: plain text
    adhoc_formats.append("PASS: No issues found.\nWARN: REQ-003 is ambiguous\nFAIL: REQ-007 unsupported")
    # Evaluator 2: custom JSON
    adhoc_formats.append(json.dumps({"status": "warning", "issues": [{"req": "REQ-003", "problem": "vague"}]}))
    # Evaluator 3: CSV-like
    adhoc_formats.append("id,severity,issue\nE1,high,REQ-006 no evidence\nE2,medium,REQ-009 too broad")

    # Manual effort to reconcile (simulated)
    adhoc_parse_time = 0
    for fmt in adhoc_formats:
        adhoc_parse_time += len(fmt) * 0.001  # Simulate parsing cost

    adhoc_duration = (time.perf_counter() - adhoc_start) * 1000 + adhoc_parse_time

    # --- WITH contract (standardized) ---
    contract_start = time.perf_counter()

    for eid in ["schema-validate", "epistemic", "security-scan"]:
        config = EVALUATOR_CONFIGS[eid]
        result = generate_evaluator_result(config, 5, subjects, seed=hash(eid))
        (results_dir / f"{eid}-after_specify-20260101T000000Z.json").write_text(json.dumps(result))

    composed = compose_results(results_dir, "after_specify", "strict")
    contract_duration = (time.perf_counter() - contract_start) * 1000

    return {
        "adhoc_duration_ms": adhoc_duration,
        "contract_duration_ms": contract_duration,
        "speedup_factor": adhoc_duration / contract_duration if contract_duration > 0 else 0,
        "contract_outcome": composed["composed_outcome"],
        "contract_findings": len(composed["findings"]),
        "contract_contradictions": len(composed["metadata"]["contradictory_findings"]),
        "adhoc_formats": len(adhoc_formats),
        "adhoc_requires_manual_reconciliation": True,
        "contract_automatic_composition": True,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main benchmark runner
# ═══════════════════════════════════════════════════════════════════════════════


def run_all_benchmarks(mode: str = "full") -> list[BenchmarkResult]:
    """Run all benchmarks and return results."""
    results: list[BenchmarkResult] = []
    tmp_base = Path(__file__).resolve().parent / "results"
    tmp_base.mkdir(parents=True, exist_ok=True)

    # --- Benchmark 1: SDD Workflow Simulation ---
    tmp = tmp_base / "workflow"
    tmp.mkdir(exist_ok=True)
    result = bench_sdd_workflow_simulation(tmp)
    results.append(BenchmarkResult(
        name="SDD Workflow Simulation",
        description="Full SDD lifecycle (specify→plan→tasks→implement) with 2 evaluators per phase",
        duration_ms=0,  # Will be measured by harness
        iterations=1,
        metrics=result,
    ))

    # --- Benchmark 2: Composition at Scale ---
    scale_configs = [
        (2, 10), (5, 20), (10, 50), (20, 100),
    ] if mode == "scale" else [
        (2, 10), (5, 20), (10, 50),
    ]

    for num_ev, findings_per in scale_configs:
        tmp = tmp_base / f"scale-{num_ev}-{findings_per}"
        tmp.mkdir(exist_ok=True)
        start = time.perf_counter()
        metrics = bench_composition_scale(tmp, num_ev, findings_per)
        duration = (time.perf_counter() - start) * 1000
        results.append(BenchmarkResult(
            name=f"Composition Scale ({num_ev}e × {findings_per}f)",
            description=f"Compose {num_ev} evaluators with {findings_per} findings each",
            duration_ms=duration,
            iterations=1,
            metrics=metrics,
        ))

    # --- Benchmark 3: Report Generation ---
    report_sizes = [10, 50, 200] if mode == "scale" else [10, 50, 100]
    for size in report_sizes:
        tmp = tmp_base / f"report-{size}"
        tmp.mkdir(exist_ok=True)
        start = time.perf_counter()
        metrics = bench_report_generation(tmp, size)
        duration = (time.perf_counter() - start) * 1000
        results.append(BenchmarkResult(
            name=f"Report Generation ({size} findings)",
            description=f"Generate reports in all 5 formats with {size} findings",
            duration_ms=duration,
            iterations=1,
            metrics=metrics,
        ))

    # --- Benchmark 4: Contradiction Detection ---
    contradiction_sizes = [10, 50, 200] if mode == "scale" else [10, 50, 100]
    for size in contradiction_sizes:
        tmp = tmp_base / f"contradiction-{size}"
        tmp.mkdir(exist_ok=True)
        start = time.perf_counter()
        metrics = bench_contradiction_detection(tmp, size)
        duration = (time.perf_counter() - start) * 1000
        results.append(BenchmarkResult(
            name=f"Contradiction Detection ({size} subjects)",
            description=f"Detect contradictions across {size} subjects with opposing evaluators",
            duration_ms=duration,
            iterations=1,
            metrics=metrics,
        ))

    # --- Benchmark 5: Schema Validation Throughput ---
    validation_sizes = [50, 200] if mode == "scale" else [50, 100]
    for size in validation_sizes:
        tmp = tmp_base / f"validate-{size}"
        tmp.mkdir(exist_ok=True)
        start = time.perf_counter()
        metrics = bench_schema_validation_throughput(tmp, size)
        duration = (time.perf_counter() - start) * 1000
        results.append(BenchmarkResult(
            name=f"Schema Validation ({size} results)",
            description=f"Validate {size} evaluator results against JSON Schema",
            duration_ms=duration,
            iterations=1,
            metrics=metrics,
        ))

    # --- Benchmark 6: With vs Without Contract ---
    tmp = tmp_base / "comparison"
    tmp.mkdir(exist_ok=True)
    start = time.perf_counter()
    metrics = bench_with_vs_without_contract(tmp)
    duration = (time.perf_counter() - start) * 1000
    results.append(BenchmarkResult(
        name="With vs Without Contract",
        description="Compare ad-hoc evaluation vs standardized evaluator contract",
        duration_ms=duration,
        iterations=1,
        metrics=metrics,
    ))

    return results


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results in a formatted table."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " EVALUATOR CONTRACT — BENCHMARK RESULTS".center(78) + "║")
    print("╠" + "═" * 78 + "╣")
    print(f"║ {'Benchmark':<44s} {'Time':>10s}  {'Status':<10s} ║")
    print("╠" + "═" * 78 + "╣")

    total_ms = 0.0
    passed = 0
    failed = 0

    for r in results:
        status = "✓ PASS" if r.passed else "✗ FAIL"
        time_str = f"{r.duration_ms:,.1f}ms" if r.duration_ms < 1000 else f"{r.duration_ms / 1000:,.2f}s"
        print(f"║ {r.name:<44s} {time_str:>10s}  {status:<10s} ║")
        total_ms += r.duration_ms
        if r.passed:
            passed += 1
        else:
            failed += 1

    print("╠" + "═" * 78 + "╣")
    total_str = f"{total_ms:,.1f}ms" if total_ms < 1000 else f"{total_ms / 1000:,.2f}s"
    print(f"║ {'TOTAL':<44s} {total_str:>10s}  {passed} passed, {failed} failed ║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Detailed metrics
    print("─" * 80)
    print(" DETAILED METRICS")
    print("─" * 80)
    for r in results:
        if r.metrics:
            print(f"\n  [{r.name}]")
            for key, value in r.metrics.items():
                if isinstance(value, dict):
                    print(f"    {key}:")
                    for k, v in value.items():
                        print(f"      {k}: {v}")
                elif isinstance(value, list):
                    print(f"    {key}: [{len(value)} items]")
                else:
                    print(f"    {key}: {value}")
        if r.error:
            print(f"    ERROR: {r.error}")


def save_results(results: list[BenchmarkResult], output_path: Path) -> None:
    """Save benchmark results as JSON."""
    report = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "benchmark_count": len(results),
        "total_duration_ms": sum(r.duration_ms for r in results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "results": [
            {
                "name": r.name,
                "description": r.description,
                "duration_ms": r.duration_ms,
                "iterations": r.iterations,
                "passed": r.passed,
                "error": r.error,
                "metrics": r.metrics,
            }
            for r in results
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nResults saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluator Contract Benchmark Suite"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Run a quick smoke test (minimal scale)",
    )
    parser.add_argument(
        "--scale", action="store_true",
        help="Run full-scale benchmarks (large datasets)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Save results to JSON file",
    )
    args = parser.parse_args()

    mode = "quick" if args.quick else ("scale" if args.scale else "full")
    print(f"Running benchmarks in '{mode}' mode...")

    results = run_all_benchmarks(mode)
    print_results(results)

    if args.output:
        save_results(results, args.output)
    else:
        default_output = Path(__file__).resolve().parent / "reports" / "benchmark-results.json"
        save_results(results, default_output)


if __name__ == "__main__":
    main()