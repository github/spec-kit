"""Unit tests for the compose_results.py script.

Validates:
- Strict composition (most severe outcome wins)
- Majority composition
- Optimistic composition
- Empty results directory handling
- Invalid result file handling
- Finding ordering by severity
- Contradiction detection
- Next action derivation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add the evaluator scripts directory to the path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "extensions" / "evaluator" / "scripts" / "python"
sys.path.insert(0, str(_SCRIPTS_DIR))

from compose_results import (
    compose_results,
    _resolve_outcome_strict,
    _resolve_outcome_majority,
    _resolve_outcome_optimistic,
    _detect_contradictions,
    _severity_sort_key,
)


# ── Outcome resolution ───────────────────────────────────────────────────────


class TestOutcomeResolution:
    def test_strict_block_wins(self):
        assert _resolve_outcome_strict(["pass", "warn", "block"]) == "block"

    def test_strict_gather_evidence_over_iterate(self):
        assert _resolve_outcome_strict(["iterate", "gather_evidence", "pass"]) == "gather_evidence"

    def test_strict_iterate_over_clarify(self):
        assert _resolve_outcome_strict(["clarify", "iterate", "pass"]) == "iterate"

    def test_strict_clarify_over_warn(self):
        assert _resolve_outcome_strict(["warn", "clarify"]) == "clarify"

    def test_strict_warn_over_pass(self):
        assert _resolve_outcome_strict(["pass", "warn"]) == "warn"

    def test_strict_all_pass(self):
        assert _resolve_outcome_strict(["pass", "pass", "pass"]) == "pass"

    def test_strict_empty(self):
        assert _resolve_outcome_strict([]) == "pass"

    def test_majority_most_common_wins(self):
        assert _resolve_outcome_majority(["pass", "pass", "warn"]) == "pass"

    def test_majority_tie_breaks_severe(self):
        # Two pass, two warn → tie breaks to warn (more severe)
        assert _resolve_outcome_majority(["pass", "pass", "warn", "warn"]) == "warn"

    def test_majority_single(self):
        assert _resolve_outcome_majority(["block"]) == "block"

    def test_optimistic_least_severe_wins(self):
        assert _resolve_outcome_optimistic(["block", "warn", "pass"]) == "pass"

    def test_optimistic_warn_over_block(self):
        assert _resolve_outcome_optimistic(["block", "warn"]) == "warn"

    def test_optimistic_all_block(self):
        assert _resolve_outcome_optimistic(["block", "block"]) == "block"


# ── Finding ordering ─────────────────────────────────────────────────────────


class TestFindingOrdering:
    def test_severity_sort_critical_first(self):
        findings = [
            {"id": "A", "severity": "low"},
            {"id": "B", "severity": "critical"},
            {"id": "C", "severity": "medium"},
        ]
        sorted_findings = sorted(findings, key=_severity_sort_key)
        assert [f["id"] for f in sorted_findings] == ["B", "C", "A"]

    def test_same_severity_sorted_by_id(self):
        findings = [
            {"id": "Z-003", "severity": "high"},
            {"id": "A-001", "severity": "high"},
            {"id": "M-002", "severity": "high"},
        ]
        sorted_findings = sorted(findings, key=_severity_sort_key)
        assert [f["id"] for f in sorted_findings] == ["A-001", "M-002", "Z-003"]

    def test_missing_severity_defaults_to_info(self):
        findings = [
            {"id": "A", "severity": "critical"},
            {"id": "B"},  # no severity
        ]
        sorted_findings = sorted(findings, key=_severity_sort_key)
        assert [f["id"] for f in sorted_findings] == ["A", "B"]


# ── Contradiction detection ──────────────────────────────────────────────────


class TestContradictionDetection:
    def test_detects_contradiction_on_same_subject(self):
        findings = [
            {"id": "E1", "severity": "high", "kind": "unsupported_claim", "subject": "REQ-001"},
            {"id": "E2", "severity": "medium", "kind": "observed", "subject": "REQ-001"},
        ]
        contradictions = _detect_contradictions(findings)
        assert len(contradictions) == 1
        assert contradictions[0]["subject"] == "REQ-001"
        assert set(contradictions[0]["finding_ids"]) == {"E1", "E2"}

    def test_no_contradiction_when_all_agree(self):
        findings = [
            {"id": "E1", "severity": "high", "kind": "unsupported_claim", "subject": "REQ-001"},
            {"id": "E2", "severity": "medium", "kind": "missing_evidence", "subject": "REQ-001"},
        ]
        contradictions = _detect_contradictions(findings)
        assert len(contradictions) == 0

    def test_no_contradiction_single_finding(self):
        findings = [
            {"id": "E1", "severity": "high", "kind": "unsupported_claim", "subject": "REQ-001"},
        ]
        contradictions = _detect_contradictions(findings)
        assert len(contradictions) == 0

    def test_multiple_subjects(self):
        findings = [
            {"id": "E1", "severity": "high", "kind": "unsupported_claim", "subject": "REQ-001"},
            {"id": "E2", "severity": "medium", "kind": "observed", "subject": "REQ-001"},
            {"id": "E3", "severity": "low", "kind": "unsupported_claim", "subject": "REQ-002"},
            {"id": "E4", "severity": "low", "kind": "observed", "subject": "REQ-002"},
        ]
        contradictions = _detect_contradictions(findings)
        assert len(contradictions) == 2


# ── Compose results integration ──────────────────────────────────────────────


def _make_result(evaluator_id: str, outcome: str, phase: str, findings: list | None = None) -> dict:
    """Create a minimal valid evaluator result."""
    return {
        "schema_version": "1.0",
        "evaluator": {"id": evaluator_id, "version": "0.1.0"},
        "phase": phase,
        "outcome": outcome,
        "summary": f"Test result from {evaluator_id}",
        "findings": findings or [],
        "next_action": {"kind": outcome, "target_phase": None, "message": ""},
        "metadata": {"timestamp": "2026-01-01T00:00:00Z"},
        "state": {},
    }


class TestComposeResults:
    def test_compose_strict_two_evaluators(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Write two result files
        r1 = _make_result("eval-a", "pass", "after_plan")
        r2 = _make_result("eval-b", "warn", "after_plan", [
            {"id": "B-001", "severity": "medium", "kind": "unsupported_claim", "subject": "REQ-001"}
        ])
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "eval-b-after_plan-20260101T000001Z.json").write_text(json.dumps(r2))

        composed = compose_results(results_dir, "after_plan", "strict")

        assert composed["composed_outcome"] == "warn"
        assert composed["metadata"]["evaluator_count"] == 2
        assert len(composed["findings"]) == 1

    def test_compose_strict_block_wins(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "pass", "after_plan")
        r2 = _make_result("eval-b", "block", "after_plan")
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "eval-b-after_plan-20260101T000001Z.json").write_text(json.dumps(r2))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "block"

    def test_compose_majority(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "pass", "after_plan")
        r2 = _make_result("eval-b", "pass", "after_plan")
        r3 = _make_result("eval-c", "warn", "after_plan")
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "eval-b-after_plan-20260101T000001Z.json").write_text(json.dumps(r2))
        (results_dir / "eval-c-after_plan-20260101T000002Z.json").write_text(json.dumps(r3))

        composed = compose_results(results_dir, "after_plan", "majority")
        assert composed["composed_outcome"] == "pass"

    def test_compose_optimistic(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "block", "after_plan")
        r2 = _make_result("eval-b", "pass", "after_plan")
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "eval-b-after_plan-20260101T000001Z.json").write_text(json.dumps(r2))

        composed = compose_results(results_dir, "after_plan", "optimistic")
        assert composed["composed_outcome"] == "pass"

    def test_compose_empty_results_dir(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "pass"
        assert composed["metadata"]["evaluator_count"] == 0
        assert composed["findings"] == []

    def test_compose_nonexistent_dir(self, tmp_path: Path):
        composed = compose_results(tmp_path / "nonexistent", "after_plan", "strict")
        assert composed["composed_outcome"] == "pass"
        assert composed["metadata"]["evaluator_count"] == 0

    def test_compose_skips_invalid_json(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "pass", "after_plan")
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "bad-after_plan-20260101T000001Z.json").write_text("not json")

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "pass"
        assert composed["metadata"]["evaluator_count"] == 1

    def test_compose_skips_missing_required_keys(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "pass", "after_plan")
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "bad-after_plan-20260101T000001Z.json").write_text('{"not": "valid"}')

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "pass"
        assert composed["metadata"]["evaluator_count"] == 1

    def test_compose_excludes_previous_composed(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "warn", "after_plan")
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        # A previously composed file should be excluded
        (results_dir / "composed-after_plan-20260101T000001Z.json").write_text(json.dumps(r1))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["metadata"]["evaluator_count"] == 1

    def test_compose_preserves_evaluator_states(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "pass", "after_plan")
        r1["state"] = {"last_checked": "2026-01-01", "checksum": "abc123"}
        r2 = _make_result("eval-b", "pass", "after_plan")
        r2["state"] = {"session_id": "sess-001"}
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))
        (results_dir / "eval-b-after_plan-20260101T000001Z.json").write_text(json.dumps(r2))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["evaluator_states"]["eval-a"] == {"last_checked": "2026-01-01", "checksum": "abc123"}
        assert composed["evaluator_states"]["eval-b"] == {"session_id": "sess-001"}

    def test_compose_findings_tagged_with_evaluator_id(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "pass", "after_plan", [
            {"id": "A-001", "severity": "high", "kind": "unsupported_claim", "subject": "REQ-001"}
        ])
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["findings"][0]["_evaluator_id"] == "eval-a"

    def test_compose_iterate_target_phase(self, tmp_path: Path):
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        r1 = _make_result("eval-a", "iterate", "after_plan")
        r1["next_action"] = {"kind": "iterate", "target_phase": "plan", "message": "Revisit plan"}
        (results_dir / "eval-a-after_plan-20260101T000000Z.json").write_text(json.dumps(r1))

        composed = compose_results(results_dir, "after_plan", "strict")
        assert composed["composed_outcome"] == "iterate"
        assert composed["next_action"]["target_phase"] == "plan"


# ── Schema validation ────────────────────────────────────────────────────────


class TestSchemaValidation:
    def test_minimal_valid_result_passes(self):
        """A minimal result with only required fields is valid."""
        schema_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "extensions" / "evaluator" / "schemas" / "evaluator-result.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        minimal = {
            "schema_version": "1.0",
            "evaluator": {"id": "test", "version": "0.1.0"},
            "phase": "after_plan",
            "outcome": "pass",
            "findings": [],
        }
        jsonschema.validate(minimal, schema)

    def test_full_result_passes(self):
        """A full result with all optional fields is valid."""
        schema_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "extensions" / "evaluator" / "schemas" / "evaluator-result.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        full = {
            "schema_version": "1.0",
            "evaluator": {
                "id": "epistemic",
                "version": "0.1.0",
                "name": "Epistemic Evaluator",
                "url": "https://example.com/evaluator",
            },
            "phase": "after_plan",
            "outcome": "iterate",
            "summary": "Two high-impact claims are unsupported.",
            "findings": [
                {
                    "id": "EPI-001",
                    "severity": "high",
                    "kind": "unsupported_claim",
                    "subject": "REQ-014",
                    "description": "Claim presented as fact without evidence.",
                    "evidence_refs": [],
                    "provenance_refs": ["spec.md#REQ-014"],
                    "uncertainty": "insufficient_evidence",
                    "recommended_action": "gather_evidence",
                    "rationale": "No supporting evidence found.",
                }
            ],
            "next_action": {
                "kind": "iterate",
                "target_phase": "plan",
                "message": "Revisit plan to address unsupported claims.",
            },
            "metadata": {
                "timestamp": "2026-01-01T00:00:00Z",
                "duration_ms": 1500,
                "artifacts_evaluated": ["spec.md", "plan.md"],
                "model": "gpt-4",
                "deterministic": False,
            },
            "state": {"session_id": "abc123"},
        }
        jsonschema.validate(full, schema)

    def test_invalid_outcome_rejected(self):
        """An invalid outcome value is rejected."""
        schema_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "extensions" / "evaluator" / "schemas" / "evaluator-result.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        invalid = {
            "schema_version": "1.0",
            "evaluator": {"id": "test", "version": "0.1.0"},
            "phase": "after_plan",
            "outcome": "invalid_outcome",
            "findings": [],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid, schema)

    def test_missing_required_field_rejected(self):
        """A result missing a required field is rejected."""
        schema_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "extensions" / "evaluator" / "schemas" / "evaluator-result.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        try:
            import jsonschema
        except ImportError:
            pytest.skip("jsonschema not installed")

        invalid = {
            "schema_version": "1.0",
            "evaluator": {"id": "test", "version": "0.1.0"},
            # missing "phase"
            "outcome": "pass",
            "findings": [],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid, schema)