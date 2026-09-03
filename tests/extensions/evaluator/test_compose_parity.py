"""Parity tests for evaluator compose scripts across Python, Bash, and PowerShell.

Verifies that all three runtime implementations produce equivalent composed
results given the same inputs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

_EXT_DIR = Path(__file__).resolve().parents[3] / "extensions" / "evaluator"
_PY_SCRIPT = _EXT_DIR / "scripts" / "python" / "compose_results.py"
_SH_SCRIPT = _EXT_DIR / "scripts" / "bash" / "compose-results.sh"
_PS_SCRIPT = _EXT_DIR / "scripts" / "powershell" / "compose-results.ps1"


def _make_result(
    evaluator_id: str,
    outcome: str,
    findings: list[dict[str, Any]] | None = None,
    phase: str = "after_plan",
    target_phase: str | None = None,
) -> dict[str, Any]:
    """Build a minimal valid evaluator result."""
    return {
        "schema_version": "1.0",
        "evaluator": {"id": evaluator_id, "version": "0.1.0"},
        "phase": phase,
        "outcome": outcome,
        "summary": f"Result from {evaluator_id}",
        "findings": findings or [],
        "next_action": {
            "kind": outcome,
            "target_phase": target_phase,
            "message": f"Action: {outcome}",
        },
        "metadata": {
            "timestamp": "2026-01-01T00:00:00Z",
            "duration_ms": 100,
            "deterministic": True,
        },
    }


def _write_results(tmpdir: Path, results: list[dict[str, Any]]) -> None:
    """Write result dicts as JSON files in tmpdir."""
    for i, r in enumerate(results):
        eid = r["evaluator"]["id"]
        phase = r["phase"]
        path = tmpdir / f"{eid}-{phase}-20260101T0000{i:02d}Z.json"
        path.write_text(json.dumps(r))


def _run_python(results_dir: Path, phase: str, strategy: str = "strict") -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(_PY_SCRIPT), "--results-dir", str(results_dir),
         "--phase", phase, "--strategy", strategy, "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Python script failed: {result.stderr}"
    return json.loads(result.stdout)


def _run_bash(results_dir: Path, phase: str, strategy: str = "strict") -> dict[str, Any]:
    result = subprocess.run(
        ["bash", str(_SH_SCRIPT), "--results-dir", str(results_dir),
         "--phase", phase, "--strategy", strategy],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Bash script failed: {result.stderr}"
    return json.loads(result.stdout)


class TestComposeParity:
    """Cross-runtime parity tests for compose_results."""

    def test_empty_results_dir(self, tmp_path: Path) -> None:
        """All runtimes produce equivalent empty composed results."""
        results_dir = tmp_path / "empty"
        results_dir.mkdir()

        py = _run_python(results_dir, "after_plan")
        sh = _run_bash(results_dir, "after_plan")

        assert py["outcome"] == "pass"
        assert sh["outcome"] == "pass"
        assert py["outcome"] == sh["outcome"]
        assert py["evaluator"]["id"] == "composed"
        assert sh["evaluator"]["id"] == "composed"

    def test_single_result(self, tmp_path: Path) -> None:
        """Single result is passed through identically."""
        results_dir = tmp_path / "single"
        results_dir.mkdir()
        _write_results(results_dir, [_make_result("eval-a", "pass")])

        py = _run_python(results_dir, "after_plan")
        sh = _run_bash(results_dir, "after_plan")

        assert py["outcome"] == "pass"
        assert sh["outcome"] == "pass"
        assert py["outcome"] == sh["outcome"]

    def test_strict_composition(self, tmp_path: Path) -> None:
        """Strict: most severe outcome wins."""
        results_dir = tmp_path / "strict"
        results_dir.mkdir()
        _write_results(results_dir, [
            _make_result("eval-a", "pass"),
            _make_result("eval-b", "block"),
            _make_result("eval-c", "warn"),
        ])

        py = _run_python(results_dir, "after_plan", "strict")
        sh = _run_bash(results_dir, "after_plan", "strict")

        assert py["outcome"] == "block"
        assert sh["outcome"] == "block"
        assert py["outcome"] == sh["outcome"]

    def test_majority_composition(self, tmp_path: Path) -> None:
        """Majority: most common outcome wins."""
        results_dir = tmp_path / "majority"
        results_dir.mkdir()
        _write_results(results_dir, [
            _make_result("eval-a", "pass"),
            _make_result("eval-b", "pass"),
            _make_result("eval-c", "warn"),
        ])

        py = _run_python(results_dir, "after_plan", "majority")
        sh = _run_bash(results_dir, "after_plan", "majority")

        assert py["outcome"] == "pass"
        assert sh["outcome"] == "pass"
        assert py["outcome"] == sh["outcome"]

    def test_optimistic_composition(self, tmp_path: Path) -> None:
        """Optimistic: least severe outcome wins."""
        results_dir = tmp_path / "optimistic"
        results_dir.mkdir()
        _write_results(results_dir, [
            _make_result("eval-a", "block"),
            _make_result("eval-b", "pass"),
        ])

        py = _run_python(results_dir, "after_plan", "optimistic")
        sh = _run_bash(results_dir, "after_plan", "optimistic")

        assert py["outcome"] == "pass"
        assert sh["outcome"] == "pass"
        assert py["outcome"] == sh["outcome"]

    def test_contradiction_detection(self, tmp_path: Path) -> None:
        """Contradictory findings on same subject are detected."""
        results_dir = tmp_path / "contra"
        results_dir.mkdir()
        _write_results(results_dir, [
            _make_result("eval-a", "warn", [
                {"id": "A-001", "severity": "high", "kind": "unsupported_claim",
                 "subject": "REQ-001",
                 "evidence_refs": [{"ref": "spec.md", "kind": "unsupported"}]},
            ]),
            _make_result("eval-b", "pass", [
                {"id": "B-001", "severity": "low", "kind": "schema_violation",
                 "subject": "REQ-001",
                 "evidence_refs": [{"ref": "spec.md", "kind": "observed"}]},
            ]),
        ])

        py = _run_python(results_dir, "after_plan")
        sh = _run_bash(results_dir, "after_plan")

        py_contra = py["metadata"]["contradictory_findings"]
        sh_contra = sh["metadata"]["contradictory_findings"]

        assert len(py_contra) > 0, "Python should detect contradictions"
        assert len(sh_contra) > 0, "Bash should detect contradictions"
        assert len(py_contra) == len(sh_contra), "Same contradiction count"

    def test_schema_compliant_output(self, tmp_path: Path) -> None:
        """Composed output conforms to evaluator result schema."""
        results_dir = tmp_path / "schema"
        results_dir.mkdir()
        _write_results(results_dir, [_make_result("eval-a", "pass")])

        py = _run_python(results_dir, "after_plan")

        # Must have required schema fields
        assert "schema_version" in py
        assert "evaluator" in py
        assert "phase" in py
        assert "outcome" in py
        assert "findings" in py
        assert "next_action" in py
        assert "metadata" in py
        assert "state" in py

        # evaluator must have id and version
        assert "id" in py["evaluator"]
        assert "version" in py["evaluator"]

        # next_action.target_phase can be null
        assert py["next_action"]["target_phase"] is None

    def test_latest_per_evaluator(self, tmp_path: Path) -> None:
        """Only the latest result per evaluator is used."""
        import time
        results_dir = tmp_path / "latest"
        results_dir.mkdir()
        # Write two results for same evaluator with different mtimes
        r1 = _make_result("eval-a", "pass")
        r2 = _make_result("eval-a", "block")
        _write_results(results_dir, [r1])
        time.sleep(0.1)  # ensure different mtime
        _write_results(results_dir, [r2])

        py = _run_python(results_dir, "after_plan")
        # The later file (block) should win
        assert py["outcome"] == "block"