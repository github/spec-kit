#!/usr/bin/env python3
"""Validate Spec Kit test-case intake artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from intake_validator_common import (
    emit,
    has_needs_clarification,
    is_truthy,
    load_yaml,
    non_empty,
    validate_json_schema,
    validate_ready_evidence_packet,
    validate_source_manifest,
)


ALLOWED_SOURCE_TYPES = {"code", "gherkin", "spreadsheet", "test_management", "issue", "mixed"}
ALLOWED_CATEGORIES = {
    "unit",
    "component",
    "integration",
    "api",
    "e2e",
    "manual",
    "regression",
    "bug_repro",
    "performance",
    "accessibility",
    "security",
}
ALLOWED_EVIDENCE_TYPES = {"observed", "inferred", "missing", "out_of_scope"}

BLOCKERS = {
    "SOURCE_MANIFEST_MISSING": "TEST_SOURCE_MANIFEST_MISSING",
    "SOURCE_TYPE_UNSUPPORTED": "TEST_SOURCE_TYPE_UNSUPPORTED",
    "SOURCE_FILE_MISSING": "TEST_SOURCE_FILE_MISSING",
    "SOURCE_HASH_MISMATCH": "TEST_SOURCE_HASH_MISMATCH",
    "SOURCE_INTEGRITY_INCOMPLETE": "TEST_SOURCE_INTEGRITY_INCOMPLETE",
    "INTAKE_MISSING": "TEST_CASE_INTAKE_MISSING",
    "SCENARIOS_UNTRACEABLE": "TEST_SCENARIOS_UNTRACEABLE",
    "ASSERTIONS_MISSING": "TEST_ASSERTIONS_MISSING",
    "FIXTURE_EVIDENCE_MISSING": "TEST_FIXTURE_EVIDENCE_MISSING",
    "COVERAGE_GAPS_MISSING": "TEST_COVERAGE_GAPS_MISSING",
    "READY_WITHOUT_EVIDENCE": "TEST_READY_WITHOUT_EVIDENCE",
    "EVIDENCE_PACKET_MISSING": "TEST_EVIDENCE_PACKET_MISSING",
    "BLOCKER_LINT_ERRORS": "TEST_BLOCKER_LINT_ERRORS",
    "SCHEMA_INVALID": "TEST_SCHEMA_INVALID",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake_dir", help="Directory containing test-case intake artifacts")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    intake_dir = Path(args.intake_dir)
    blocker_codes: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"intake_dir": str(intake_dir)}

    if not intake_dir.exists() or not intake_dir.is_dir():
        blocker_codes.extend(
            [
                BLOCKERS["SOURCE_MANIFEST_MISSING"],
                BLOCKERS["INTAKE_MISSING"],
                BLOCKERS["EVIDENCE_PACKET_MISSING"],
            ]
        )
        return emit(
            label="Test-case",
            json_mode=args.json,
            details=details,
            blockers=blocker_codes,
            warnings=warnings,
        )

    validate_source_manifest(
        intake_dir=intake_dir,
        manifest_name="source-manifest.yaml",
        allowed_source_types=ALLOWED_SOURCE_TYPES,
        required_manifest_fields=[
            "source_type",
            "source_files",
            "source_integrity_complete",
            "captured_at",
            "capture_method",
            "framework_or_format",
            "execution_scope",
        ],
        required_source_file_fields=["path", "mime_type", "byte_size", "sha256", "role"],
        details=details,
        blocker_codes=blocker_codes,
        missing_manifest_code=BLOCKERS["SOURCE_MANIFEST_MISSING"],
        unsupported_source_code=BLOCKERS["SOURCE_TYPE_UNSUPPORTED"],
        missing_file_code=BLOCKERS["SOURCE_FILE_MISSING"],
        hash_mismatch_code=BLOCKERS["SOURCE_HASH_MISMATCH"],
        integrity_code=BLOCKERS["SOURCE_INTEGRITY_INCOMPLETE"],
        schema_name="test-case-source-manifest.schema.json",
        schema_error_code=BLOCKERS["SCHEMA_INVALID"],
    )

    validate_test_case_intake(intake_dir, details, blocker_codes)
    validate_ready_evidence_packet(
        intake_dir=intake_dir,
        details=details,
        blocker_codes=blocker_codes,
        warnings=warnings,
        missing_packet_code=BLOCKERS["EVIDENCE_PACKET_MISSING"],
        ready_without_evidence_code=BLOCKERS["READY_WITHOUT_EVIDENCE"],
    )

    return emit(
        label="Test-case",
        json_mode=args.json,
        details=details,
        blockers=blocker_codes,
        warnings=warnings,
    )


def validate_test_case_intake(
    intake_dir: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    intake_path = intake_dir / "test-case-intake.yaml"
    if not intake_path.exists():
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])
        return

    validate_json_schema(
        instance_path=intake_path,
        schema_name="test-case-intake.schema.json",
        details_key="test_case_intake",
        details=details,
        blocker_codes=blocker_codes,
        schema_error_code=BLOCKERS["SCHEMA_INVALID"],
    )

    intake_doc = load_yaml(intake_path)
    scenarios = intake_doc.get("scenarios")
    if not isinstance(scenarios, list):
        scenarios = []

    declared_scenario_count = intake_doc.get("scenario_count")
    try:
        scenario_count = len(scenarios) if declared_scenario_count is None else int(declared_scenario_count)
    except (TypeError, ValueError):
        scenario_count = len(scenarios)
    intake_complete = is_truthy(intake_doc.get("test_case_intake_complete"))
    source_refs_complete = is_truthy(intake_doc.get("source_refs_complete"))
    assertions_complete = is_truthy(intake_doc.get("assertions_complete"))
    fixture_evidence_complete = is_truthy(intake_doc.get("fixture_evidence_complete"))
    coverage_gaps_recorded = is_truthy(intake_doc.get("coverage_gaps_recorded"))
    blocker_lint_errors = intake_doc.get("blocker_lint_errors")

    details["test_case_intake"] = {
        "test_case_intake_complete": intake_doc.get("test_case_intake_complete"),
        "source_refs_complete": intake_doc.get("source_refs_complete"),
        "scenario_count": scenario_count,
        "assertions_complete": intake_doc.get("assertions_complete"),
        "fixture_evidence_complete": intake_doc.get("fixture_evidence_complete"),
        "coverage_gaps_recorded": intake_doc.get("coverage_gaps_recorded"),
        "blocker_lint_errors": blocker_lint_errors,
    }

    if not intake_complete or scenario_count <= 0:
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])

    count_matches = scenario_count == len(scenarios)
    if not count_matches:
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])

    scenario_errors: list[dict[str, Any]] = []
    has_untraceable = not source_refs_complete
    has_missing_required = False
    has_assertions = assertions_complete
    has_fixture_evidence = fixture_evidence_complete
    has_coverage_gaps = coverage_gaps_recorded
    has_blocker_lint = isinstance(blocker_lint_errors, list) and len(blocker_lint_errors) > 0

    required_fields = [
        "id",
        "category",
        "scenario",
        "source_refs",
        "evidence_type",
        "confidence",
        "confidence_rationale",
        "actors",
        "preconditions",
        "actions",
        "expected_outcomes",
        "assertions",
        "fixtures_or_test_data",
        "coverage_signal",
    ]

    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            scenario_errors.append({"index": index, "error": "scenario must be a mapping"})
            has_missing_required = True
            continue

        missing_fields = [
            field for field in required_fields if not non_empty(scenario.get(field))
        ]
        if missing_fields:
            scenario_errors.append({"index": index, "missing_fields": missing_fields})
            has_missing_required = True

        source_refs = scenario.get("source_refs")
        if not isinstance(source_refs, list) or not source_refs or any(not str(ref).strip() for ref in source_refs):
            has_untraceable = True

        category = str(scenario.get("category") or "").strip().lower()
        if category and category not in ALLOWED_CATEGORIES:
            scenario_errors.append({"index": index, "unsupported_category": category})
            has_missing_required = True

        evidence_type = str(scenario.get("evidence_type") or "").strip().lower()
        if evidence_type and evidence_type not in ALLOWED_EVIDENCE_TYPES:
            scenario_errors.append({"index": index, "unsupported_evidence_type": evidence_type})
            has_missing_required = True

        assertions = scenario.get("assertions")
        if non_empty(assertions) or has_needs_clarification(assertions):
            has_assertions = True
        fixtures = scenario.get("fixtures_or_test_data")
        if non_empty(fixtures) or has_needs_clarification(fixtures):
            has_fixture_evidence = True
        if non_empty(scenario.get("coverage_signal")):
            has_coverage_gaps = True

        blockers = scenario.get("blockers")
        if isinstance(blockers, list) and blockers:
            has_blocker_lint = True

    if non_empty(intake_doc.get("assertion_gaps")):
        has_assertions = True
    if non_empty(intake_doc.get("fixture_or_test_data_gaps")):
        has_fixture_evidence = True
    if non_empty(intake_doc.get("coverage_gaps")) or non_empty(intake_doc.get("flaky_or_skipped_cases")):
        has_coverage_gaps = True

    details["test_case_intake"]["scenario_errors"] = scenario_errors
    details["test_case_intake"]["count_matches_scenarios"] = count_matches

    if has_missing_required:
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])
    if has_untraceable:
        blocker_codes.append(BLOCKERS["SCENARIOS_UNTRACEABLE"])
    if not has_assertions:
        blocker_codes.append(BLOCKERS["ASSERTIONS_MISSING"])
    if not has_fixture_evidence:
        blocker_codes.append(BLOCKERS["FIXTURE_EVIDENCE_MISSING"])
    if not has_coverage_gaps:
        blocker_codes.append(BLOCKERS["COVERAGE_GAPS_MISSING"])
    if has_blocker_lint:
        blocker_codes.append(BLOCKERS["BLOCKER_LINT_ERRORS"])


if __name__ == "__main__":
    sys.exit(main())
