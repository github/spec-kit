"""Pytest-integrated benchmark tests for the Evaluator Contract extension.

These tests validate the benchmark scenarios as correctness assertions
and can be run as part of the normal test suite. For performance
benchmarking, use ``benchmarks/evaluator/run_benchmarks.py`` directly.

Usage:
    pytest tests/extensions/evaluator/test_benchmarks.py -v
    pytest tests/extensions/evaluator/test_benchmarks.py -v -k "scale"  # scale tests only
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add the evaluator scripts to path
_SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "extensions" / "evaluator" / "scripts" / "python"
)
sys.path.insert(0, str(_SCRIPTS_DIR))

from compose_results import compose_results


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_result(evaluator_id: str, outcome: str, phase: str, findings: list | None = None) -> dict:
    return {
        "schema_version": "1.0",
        "evaluator": {"id": evaluator_id, "version": "1.0.0"},
        "phase": phase,
        "outcome": outcome,
        "summary": f"Result from {evaluator_id}",
        "findings": findings or [],
        "next_action": {"kind": outcome, "target_phase": None, "message": ""},
        "metadata": {"timestamp": "2026-01-01T00:00:00Z"},
        "state": {},
    }


def _make_finding(fid: str, severity: str, kind: str, subject: str, **kwargs) -> dict:
    f = {
        "id": fid,
        "severity": severity,
        "kind": kind,
        "subject": subject,
        "description": f"{kind} in {subject}",
        "evidence_refs": kwargs.get("evidence_refs", []),
        "provenance_refs": [f"spec.md#{subject}"],
        "uncertainty": kwargs.get("uncertainty", "low"),
        "recommended_action": kwargs.get("recommended_action", "none"),
        "rationale": kwargs.get("rationale", ""),
    }
    return f


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark: SDD Workflow Simulation
# ═══════════════════════════════════════════════════════════════════════════════


class TestSDDWorkflowSimulation:
    """Verify the full SDD lifecycle with evaluators at each phase."""

    PHASES = ["after_specify", "after_plan", "after_tasks", "after_implement"]

    def test_all_phases_have_evaluators(self):
        """Every SDD phase has at least one evaluator registered."""
        from benchmarks.evaluator.run_benchmarks import PHASE_EVALUATORS
        for phase in self.PHASES:
            assert phase in PHASE_EVALUATORS, f"No evaluators for {phase}"
            assert len(PHASE_EVALUATORS[phase]) >= 1, f"Empty evaluator list for {phase}"

    def test_workflow_composition_at_each_phase(self, tmp_path: Path):
        """Composition works correctly at each phase."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        for phase in self.PHASES:
            # Create two evaluator results per phase
            r1 = _make_result(f"eval-{phase}-a", "warn", phase, [
                _make_finding("F-001", "medium", "unsupported_claim", "REQ-001")
            ])
            r2 = _make_result(f"eval-{phase}-b", "pass", phase, [])
            (results_dir / f"eval-{phase}-a-{phase}-20260101T000000Z.json").write_text(json.dumps(r1))
            (results_dir / f"eval-{phase}-b-{phase}-20260101T000001Z.json").write_text(json.dumps(r2))

            composed = compose_results(results_dir, phase, "strict")
            assert composed["composed_outcome"] == "warn"
            assert composed["metadata"]["evaluator_count"] == 2

    def test_workflow_outcome_propagation(self, tmp_path: Path):
        """A block at any phase propagates correctly."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "block", "after_plan", [
            _make_finding("F-001", "critical", "security_concern", "COMP-002")
        ])
        r2 = _make_result("eval-b", "pass", "after_plan", [])
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "eval-b-after_plan-20260101T000001Z.json").write_text(json.dumps(r2))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "block"
        assert composed["next_action"]["kind"] == "block"


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark: Composition at Scale
# ═══════════════════════════════════════════════════════════════════════════════


class TestCompositionScale:
    """Verify composition correctness at increasing scale."""

    def test_compose_10_evaluators_50_findings_each(self, tmp_path: Path):
        """500 findings across 10 evaluators compose correctly."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        for i in range(10):
            findings = [
                _make_finding(f"E{i:02d}-{j:03d}", "medium", "coverage_gap", f"REQ-{j:03d}")
                for j in range(50)
            ]
            result = _make_result(f"eval-{i:02d}", "warn", "after_plan", findings)
            (results_dir / f"eval-{i:02d}-after_plan-20260101T000000Z.json").write_text(json.dumps(result))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["metadata"]["evaluator_count"] == 10
        assert len(composed["findings"]) == 500
        assert composed["composed_outcome"] == "warn"

    def test_compose_20_evaluators_100_findings_each(self, tmp_path: Path):
        """2000 findings across 20 evaluators compose correctly."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        for i in range(20):
            findings = [
                _make_finding(f"E{i:02d}-{j:03d}", "low", "coverage_gap", f"REQ-{j:03d}")
                for j in range(100)
            ]
            result = _make_result(f"eval-{i:02d}", "warn", "after_tasks", findings)
            (results_dir / f"eval-{i:02d}-after_tasks-20260101T000000Z.json").write_text(json.dumps(result))

        composed = compose_results(results_dir, "after_tasks", "strict")
        assert composed["metadata"]["evaluator_count"] == 20
        assert len(composed["findings"]) == 2000
        assert composed["composed_outcome"] == "warn"

    def test_findings_preserve_origin_at_scale(self, tmp_path: Path):
        """Each finding retains its evaluator origin tag at scale."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        for i in range(5):
            findings = [
                _make_finding(f"E{i}-{j:02d}", "medium", "unsupported_claim", f"REQ-{j:02d}")
                for j in range(10)
            ]
            result = _make_result(f"eval-{i}", "warn", "after_specify", findings)
            (results_dir / f"eval-{i}-after_specify-20260101T000000Z.json").write_text(json.dumps(result))

        composed = compose_results(results_dir, "after_specify", "strict")
        evaluator_ids = {f["_evaluator_id"] for f in composed["findings"]}
        assert evaluator_ids == {f"eval-{i}" for i in range(5)}


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark: Contradiction Detection
# ═══════════════════════════════════════════════════════════════════════════════


class TestContradictionDetection:
    """Verify contradiction detection at scale."""

    def test_all_subjects_contradicted(self, tmp_path: Path):
        """When two evaluators disagree on every subject, all are detected."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        subjects = [f"REQ-{i:03d}" for i in range(50)]

        # Evaluator A: all positive
        findings_a = [
            _make_finding(f"POS-{i:03d}", "low", "observed", s,
                          evidence_refs=[{"ref": f"spec.md#{s}", "kind": "observed", "description": "Verified"}])
            for i, s in enumerate(subjects)
        ]
        r_a = _make_result("eval-optimist", "pass", "after_specify", findings_a)

        # Evaluator B: all negative
        findings_b = [
            _make_finding(f"NEG-{i:03d}", "high", "unsupported_claim", s,
                          evidence_refs=[])
            for i, s in enumerate(subjects)
        ]
        r_b = _make_result("eval-pessimist", "iterate", "after_specify", findings_b)

        (results_dir / "eval-optimist-after_specify-20260101T000000Z.json").write_text(json.dumps(r_a))
        (results_dir / "eval-pessimist-after_specify-20260101T000001Z.json").write_text(json.dumps(r_b))

        composed = compose_results(results_dir, "after_specify", "strict")
        assert composed["metadata"]["evaluator_count"] == 2
        assert len(composed["findings"]) == 100  # Both viewpoints preserved
        assert len(composed["metadata"]["contradictory_findings"]) == 50  # All subjects contradicted

    def test_contradictions_preserved_not_collapsed(self, tmp_path: Path):
        """Contradictory findings are both present, not collapsed."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r_a = _make_result("eval-a", "pass", "after_specify", [
            _make_finding("A-001", "low", "observed", "REQ-001",
                          evidence_refs=[{"ref": "spec.md#REQ-001", "kind": "observed", "description": "Verified"}])
        ])
        r_b = _make_result("eval-b", "iterate", "after_specify", [
            _make_finding("B-001", "high", "unsupported_claim", "REQ-001",
                          evidence_refs=[])
        ])

        (results_dir / "eval-a-after_specify-20260101T000000Z.json").write_text(json.dumps(r_a))
        (results_dir / "eval-b-after_specify-20260101T000001Z.json").write_text(json.dumps(r_b))

        composed = compose_results(results_dir, "after_specify", "strict")
        finding_ids = {f["id"] for f in composed["findings"]}
        assert "A-001" in finding_ids, "Positive finding was dropped"
        assert "B-001" in finding_ids, "Negative finding was dropped"
        assert len(composed["metadata"]["contradictory_findings"]) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark: Report Generation Correctness
# ═══════════════════════════════════════════════════════════════════════════════


class TestReportGeneration:
    """Verify report generation correctness across all formats."""

    def test_terminal_report_contains_all_sections(self, tmp_path: Path):
        """Terminal report has header, findings, and next action."""
        from benchmarks.evaluator.run_benchmarks import _render_terminal

        composed = {
            "phase": "after_plan",
            "composed_outcome": "warn",
            "composed_summary": "Test summary",
            "metadata": {"evaluator_count": 2},
            "findings": [
                {"id": "F-001", "severity": "high", "kind": "unsupported_claim",
                 "subject": "REQ-001", "recommended_action": "gather_evidence"},
            ],
            "next_action": {"kind": "warn", "target_phase": None, "message": "Proceed with caution"},
        }
        output = _render_terminal(composed)
        assert "EVALUATOR REPORT" in output
        assert "F-001" in output
        assert "Next Action" in output

    def test_markdown_report_has_table(self, tmp_path: Path):
        """Markdown report has a proper findings table."""
        from benchmarks.evaluator.run_benchmarks import _render_markdown

        composed = {
            "phase": "after_specify",
            "composed_outcome": "pass",
            "composed_summary": "All good",
            "metadata": {"evaluator_count": 1},
            "findings": [
                {"id": "F-001", "severity": "low", "kind": "observed",
                 "subject": "REQ-001", "recommended_action": "none"},
            ],
            "next_action": {"kind": "pass"},
        }
        output = _render_markdown(composed)
        assert "| ID | Severity | Kind | Subject | Action |" in output
        assert "| F-001 | low | observed | REQ-001 | none |" in output

    def test_ci_annotation_uses_correct_prefix(self, tmp_path: Path):
        """CI annotations use ::error for critical/high, ::warning otherwise."""
        from benchmarks.evaluator.run_benchmarks import _render_ci_annotation

        composed = {
            "phase": "after_plan",
            "composed_outcome": "warn",
            "composed_summary": "",
            "metadata": {"evaluator_count": 1},
            "findings": [
                {"id": "F-001", "severity": "critical", "kind": "security_concern",
                 "subject": "spec.md#auth", "description": "Critical issue"},
                {"id": "F-002", "severity": "medium", "kind": "coverage_gap",
                 "subject": "plan.md#tests", "description": "Medium issue"},
                {"id": "F-003", "severity": "low", "kind": "ambiguous_requirement",
                 "subject": "spec.md#REQ-003", "description": "Low issue"},
            ],
            "next_action": {"kind": "warn"},
        }
        output = _render_ci_annotation(composed)
        lines = output.split("\n")
        assert lines[0].startswith("::error"), f"Critical should be ::error, got: {lines[0][:20]}"
        assert lines[1].startswith("::warning"), f"Medium should be ::warning, got: {lines[1][:20]}"
        assert lines[2].startswith("::warning"), f"Low should be ::warning, got: {lines[2][:20]}"

    def test_gate_exit_codes(self, tmp_path: Path):
        """Gate format returns correct exit codes per outcome."""
        from benchmarks.evaluator.run_benchmarks import _render_gate

        assert _render_gate({"composed_outcome": "pass"})["exit_code"] == 0
        assert _render_gate({"composed_outcome": "warn"})["exit_code"] == 0
        assert _render_gate({"composed_outcome": "iterate"})["exit_code"] == 1
        assert _render_gate({"composed_outcome": "clarify"})["exit_code"] == 1
        assert _render_gate({"composed_outcome": "gather_evidence"})["exit_code"] == 1
        assert _render_gate({"composed_outcome": "block"})["exit_code"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Benchmark: With vs Without Contract
# ═══════════════════════════════════════════════════════════════════════════════


class TestWithVsWithoutContract:
    """Verify the value proposition of standardized contract vs ad-hoc."""

    def test_contract_produces_consistent_structure(self, tmp_path: Path):
        """The contract always produces the same top-level keys."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "warn", "after_plan", [
            _make_finding("A-001", "high", "unsupported_claim", "REQ-001")
        ])
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))

        composed = compose_results(results_dir, "after_plan", "strict")
        required_keys = {"schema_version", "composed", "phase", "composition_strategy",
                         "composed_outcome", "composed_summary", "evaluator_results",
                         "findings", "next_action", "evaluator_states", "metadata"}
        assert required_keys.issubset(set(composed.keys())), \
            f"Missing keys: {required_keys - set(composed.keys())}"

    def test_contract_handles_empty_results_gracefully(self, tmp_path: Path):
        """Empty results directory produces a valid pass result."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "pass"
        assert composed["metadata"]["evaluator_count"] == 0
        assert composed["findings"] == []

    def test_contract_handles_mixed_outcomes(self, tmp_path: Path):
        """Mixed outcomes compose deterministically."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        for i, outcome in enumerate(["pass", "warn", "iterate", "block"]):
            r = _make_result(f"eval-{i}", outcome, "after_plan", [])
            (results_dir / f"eval-{i}-after_plan-20260101T000000Z.json").write_text(json.dumps(r))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "block"  # Most severe wins

    def test_contract_preserves_evaluator_identity(self, tmp_path: Path):
        """Each evaluator's identity is preserved in the composed result."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("security-scan", "warn", "after_plan", [
            _make_finding("SEC-001", "high", "security_concern", "COMP-002")
        ])
        r2 = _make_result("risk-assess", "pass", "after_plan", [])
        (results_dir / "security-scan-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "risk-assess-after_plan-20260101T000001Z.json").write_text(json.dumps(r2))

        composed = compose_results(results_dir, "after_plan", "strict")
        evaluator_ids = {s["evaluator_id"] for s in composed["evaluator_results"]}
        assert evaluator_ids == {"security-scan", "risk-assess"}
