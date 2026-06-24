#!/usr/bin/env python3
"""Validate Spec Kit PRD intake artifacts."""

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


ALLOWED_SOURCE_TYPES = {"markdown", "pdf", "doc", "url", "issue", "mixed"}
ALLOWED_CATEGORIES = {
    "goal",
    "non_goal",
    "user",
    "actor",
    "scope",
    "flow",
    "business_rule",
    "data",
    "permission",
    "integration",
    "compliance",
    "acceptance",
    "metric",
    "risk",
    "open_question",
}
ALLOWED_EVIDENCE_TYPES = {"observed", "inferred", "missing", "out_of_scope"}

BLOCKERS = {
    "SOURCE_MANIFEST_MISSING": "PRD_SOURCE_MANIFEST_MISSING",
    "SOURCE_TYPE_UNSUPPORTED": "PRD_SOURCE_TYPE_UNSUPPORTED",
    "SOURCE_FILE_MISSING": "PRD_SOURCE_FILE_MISSING",
    "SOURCE_HASH_MISMATCH": "PRD_SOURCE_HASH_MISMATCH",
    "SOURCE_INTEGRITY_INCOMPLETE": "PRD_SOURCE_INTEGRITY_INCOMPLETE",
    "INTAKE_MISSING": "PRD_INTAKE_MISSING",
    "FACTS_UNTRACEABLE": "PRD_FACTS_UNTRACEABLE",
    "ACCEPTANCE_EVIDENCE_MISSING": "PRD_ACCEPTANCE_EVIDENCE_MISSING",
    "CLARIFICATION_MARKING_MISSING": "PRD_CLARIFICATION_MARKING_MISSING",
    "READY_WITHOUT_EVIDENCE": "PRD_READY_WITHOUT_EVIDENCE",
    "EVIDENCE_PACKET_MISSING": "PRD_EVIDENCE_PACKET_MISSING",
    "BLOCKER_LINT_ERRORS": "PRD_BLOCKER_LINT_ERRORS",
    "SCHEMA_INVALID": "PRD_SCHEMA_INVALID",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake_dir", help="Directory containing PRD intake artifacts")
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
            label="PRD",
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
            "document_version",
            "extraction_scope",
        ],
        required_source_file_fields=["path", "mime_type", "byte_size", "sha256", "role"],
        details=details,
        blocker_codes=blocker_codes,
        missing_manifest_code=BLOCKERS["SOURCE_MANIFEST_MISSING"],
        unsupported_source_code=BLOCKERS["SOURCE_TYPE_UNSUPPORTED"],
        missing_file_code=BLOCKERS["SOURCE_FILE_MISSING"],
        hash_mismatch_code=BLOCKERS["SOURCE_HASH_MISMATCH"],
        integrity_code=BLOCKERS["SOURCE_INTEGRITY_INCOMPLETE"],
        schema_name="prd-source-manifest.schema.json",
        schema_error_code=BLOCKERS["SCHEMA_INVALID"],
    )

    validate_prd_intake(intake_dir, details, blocker_codes)
    validate_ready_evidence_packet(
        intake_dir=intake_dir,
        details=details,
        blocker_codes=blocker_codes,
        warnings=warnings,
        missing_packet_code=BLOCKERS["EVIDENCE_PACKET_MISSING"],
        ready_without_evidence_code=BLOCKERS["READY_WITHOUT_EVIDENCE"],
    )

    return emit(
        label="PRD",
        json_mode=args.json,
        details=details,
        blockers=blocker_codes,
        warnings=warnings,
    )


def validate_prd_intake(
    intake_dir: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    intake_path = intake_dir / "prd-intake.yaml"
    if not intake_path.exists():
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])
        return

    validate_json_schema(
        instance_path=intake_path,
        schema_name="prd-intake.schema.json",
        details_key="prd_intake",
        details=details,
        blocker_codes=blocker_codes,
        schema_error_code=BLOCKERS["SCHEMA_INVALID"],
    )

    intake_doc = load_yaml(intake_path)
    facts = intake_doc.get("facts")
    if not isinstance(facts, list):
        facts = []

    declared_fact_count = intake_doc.get("extracted_fact_count")
    try:
        extracted_fact_count = len(facts) if declared_fact_count is None else int(declared_fact_count)
    except (TypeError, ValueError):
        extracted_fact_count = len(facts)
    intake_complete = is_truthy(intake_doc.get("prd_intake_complete"))
    source_refs_complete = is_truthy(intake_doc.get("source_refs_complete"))
    acceptance_evidence_complete = is_truthy(intake_doc.get("acceptance_evidence_complete"))
    unresolved_ambiguity_marked = is_truthy(intake_doc.get("unresolved_ambiguity_marked"))
    blocker_lint_errors = intake_doc.get("blocker_lint_errors")

    details["prd_intake"] = {
        "prd_intake_complete": intake_doc.get("prd_intake_complete"),
        "source_refs_complete": intake_doc.get("source_refs_complete"),
        "extracted_fact_count": extracted_fact_count,
        "acceptance_evidence_complete": intake_doc.get("acceptance_evidence_complete"),
        "unresolved_ambiguity_marked": intake_doc.get("unresolved_ambiguity_marked"),
        "blocker_lint_errors": blocker_lint_errors,
    }

    if not intake_complete or extracted_fact_count <= 0:
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])

    count_matches = extracted_fact_count == len(facts)
    if not count_matches:
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])

    fact_errors: list[dict[str, Any]] = []
    has_untraceable = not source_refs_complete
    has_missing_required = False
    has_acceptance_signal = acceptance_evidence_complete
    has_clarification_marker = unresolved_ambiguity_marked or has_needs_clarification(intake_doc)
    has_blocker_lint = isinstance(blocker_lint_errors, list) and len(blocker_lint_errors) > 0

    required_fields = [
        "id",
        "category",
        "statement",
        "source_refs",
        "evidence_type",
        "confidence",
        "confidence_rationale",
        "downstream_hint",
        "acceptance_or_validation_signal",
    ]

    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            fact_errors.append({"index": index, "error": "fact must be a mapping"})
            has_missing_required = True
            continue

        missing_fields = [field for field in required_fields if not non_empty(fact.get(field))]
        if missing_fields:
            fact_errors.append({"index": index, "missing_fields": missing_fields})
            has_missing_required = True

        source_refs = fact.get("source_refs")
        if not isinstance(source_refs, list) or not source_refs or any(not str(ref).strip() for ref in source_refs):
            has_untraceable = True

        category = str(fact.get("category") or "").strip().lower()
        if category and category not in ALLOWED_CATEGORIES:
            fact_errors.append({"index": index, "unsupported_category": category})
            has_missing_required = True

        evidence_type = str(fact.get("evidence_type") or "").strip().lower()
        if evidence_type and evidence_type not in ALLOWED_EVIDENCE_TYPES:
            fact_errors.append({"index": index, "unsupported_evidence_type": evidence_type})
            has_missing_required = True

        if category in {"acceptance", "open_question"} or non_empty(fact.get("acceptance_or_validation_signal")):
            has_acceptance_signal = True
        if has_needs_clarification(fact):
            has_clarification_marker = True
        blockers = fact.get("blockers")
        if isinstance(blockers, list) and blockers:
            has_blocker_lint = True

    if non_empty(intake_doc.get("acceptance_gaps")):
        has_acceptance_signal = True
    if non_empty(intake_doc.get("open_questions")):
        has_clarification_marker = has_clarification_marker or has_needs_clarification(intake_doc.get("open_questions"))

    details["prd_intake"]["fact_errors"] = fact_errors
    details["prd_intake"]["count_matches_facts"] = count_matches

    if has_missing_required:
        blocker_codes.append(BLOCKERS["INTAKE_MISSING"])
    if has_untraceable:
        blocker_codes.append(BLOCKERS["FACTS_UNTRACEABLE"])
    if not has_acceptance_signal:
        blocker_codes.append(BLOCKERS["ACCEPTANCE_EVIDENCE_MISSING"])
    if not has_clarification_marker:
        blocker_codes.append(BLOCKERS["CLARIFICATION_MARKING_MISSING"])
    if has_blocker_lint:
        blocker_codes.append(BLOCKERS["BLOCKER_LINT_ERRORS"])


if __name__ == "__main__":
    sys.exit(main())
