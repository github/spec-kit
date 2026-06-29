#!/usr/bin/env python3
"""Validate Spec Kit visual-design intake artifacts."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised in user environments
    yaml = None

from intake_validator_common import parse_evidence_packet_status, validate_json_schema


ALLOWED_SOURCE_TYPES = {"image", "pdf", "markdown", "figma"}
ALLOWED_FIDELITY_LEVELS = {"low", "medium", "high"}

BLOCKERS = {
    "VISUAL_SOURCE_MANIFEST_MISSING": "VISUAL_SOURCE_MANIFEST_MISSING",
    "VISUAL_SOURCE_TYPE_UNSUPPORTED": "VISUAL_SOURCE_TYPE_UNSUPPORTED",
    "VISUAL_FIDELITY_LEVEL_UNSUPPORTED": "VISUAL_FIDELITY_LEVEL_UNSUPPORTED",
    "VISUAL_SOURCE_FILE_MISSING": "VISUAL_SOURCE_FILE_MISSING",
    "VISUAL_SOURCE_HASH_MISMATCH": "VISUAL_SOURCE_HASH_MISMATCH",
    "VISUAL_SOURCE_INTEGRITY_INCOMPLETE": "VISUAL_SOURCE_INTEGRITY_INCOMPLETE",
    "VISUAL_REQUIREMENTS_MISSING": "VISUAL_REQUIREMENTS_MISSING",
    "VISUAL_REQUIREMENTS_UNTRACEABLE": "VISUAL_REQUIREMENTS_UNTRACEABLE",
    "VISUAL_FIDELITY_RULES_MISSING": "VISUAL_FIDELITY_RULES_MISSING",
    "VISUAL_PARITY_PLAN_MISSING": "VISUAL_PARITY_PLAN_MISSING",
    "VISUAL_READY_WITHOUT_EVIDENCE": "VISUAL_READY_WITHOUT_EVIDENCE",
    "VISUAL_EVIDENCE_PACKET_MISSING": "VISUAL_EVIDENCE_PACKET_MISSING",
    "VISUAL_BLOCKER_LINT_ERRORS": "VISUAL_BLOCKER_LINT_ERRORS",
    "VISUAL_INFERENCE_CONTRACT_INVALID": "VISUAL_INFERENCE_CONTRACT_INVALID",
    "VISUAL_SCHEMA_INVALID": "VISUAL_SCHEMA_INVALID",
    "FIGMA_RENDER_NODE_MISMATCH": "FIGMA_RENDER_NODE_MISMATCH",
    "FIGMA_HIDDEN_LAYER_POLLUTION": "FIGMA_HIDDEN_LAYER_POLLUTION",
    "FIGMA_NON_INSTANCE_COMPONENT": "FIGMA_NON_INSTANCE_COMPONENT",
    "FIGMA_PROTOTYPE_METADATA_MISSING": "FIGMA_PROTOTYPE_METADATA_MISSING",
    "FIGMA_UNSUPPORTED_STATE_INFERENCE": "FIGMA_UNSUPPORTED_STATE_INFERENCE",
    "FIGMA_BUSINESS_RULE_UNSUPPORTED": "FIGMA_BUSINESS_RULE_UNSUPPORTED",
    "FIGMA_INTERACTION_CONFLICT": "FIGMA_INTERACTION_CONFLICT",
    "FIGMA_RESPONSIVE_RULE_MISSING": "FIGMA_RESPONSIVE_RULE_MISSING",
    "FIGMA_LOW_CONFIDENCE_CANDIDATE": "FIGMA_LOW_CONFIDENCE_CANDIDATE",
    "RAW_METADATA_MISSING": "FIGMA_RAW_METADATA_MISSING",
    "RAW_METADATA_SUMMARY_SUBSTITUTION": "FIGMA_RAW_METADATA_SUMMARY_SUBSTITUTION",
    "RAW_METADATA_TRUNCATED": "FIGMA_RAW_METADATA_TRUNCATED",
    "SELECTED_SUBTREE_INCOMPLETE": "FIGMA_SELECTED_SUBTREE_INCOMPLETE",
    "METADATA_INDEX_MISSING": "FIGMA_METADATA_INDEX_MISSING",
    "METADATA_PARITY_FAILED": "FIGMA_METADATA_PARITY_FAILED",
    "READY_WITHOUT_COMPLETENESS_PROOF": "FIGMA_READY_WITHOUT_COMPLETENESS_PROOF",
}


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to validate YAML intake artifacts")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_truthy(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def is_remote_ref(value: str) -> bool:
    return value.startswith(("http://", "https://", "figma://"))


def has_summary_substitution(text: str) -> bool:
    patterns = [
        r"\bsummary\b",
        r"\bsummarized\b",
        r"\bomitted\b",
        r"\btruncated for brevity\b",
        r"\bnatural language summary\b",
    ]
    lower = text.lower()
    return any(re.search(pattern, lower) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake_dir", help="Directory containing visual-design intake artifacts")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    intake_dir = Path(args.intake_dir)
    blocker_codes: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"intake_dir": str(intake_dir)}

    if not intake_dir.exists() or not intake_dir.is_dir():
        blocker_codes.extend(
            [
                BLOCKERS["VISUAL_SOURCE_MANIFEST_MISSING"],
                BLOCKERS["VISUAL_REQUIREMENTS_MISSING"],
                BLOCKERS["VISUAL_EVIDENCE_PACKET_MISSING"],
            ]
        )
        return emit(args.json, details, blocker_codes, warnings)

    manifest_path = intake_dir / "design-source-manifest.yaml"
    source_type = ""
    visual_gate_active = manifest_path.exists()

    if visual_gate_active:
        source_type = validate_visual_contract(intake_dir, manifest_path, details, blocker_codes)
    else:
        blocker_codes.append(BLOCKERS["VISUAL_SOURCE_MANIFEST_MISSING"])
        details["source_manifest"] = {"missing": True}

    has_figma_artifacts = any(
        [
            list(intake_dir.glob("figma-metadata.part-*.xml")),
            (intake_dir / "figma-metadata.index.yaml").exists(),
            (intake_dir / "figma-node-inventory.yaml").exists(),
        ]
    )
    if source_type == "figma" or (not source_type and has_figma_artifacts):
        validate_figma_provider(intake_dir, details, blocker_codes)

    validate_evidence_packet(
        intake_dir=intake_dir,
        details=details,
        blocker_codes=blocker_codes,
        warnings=warnings,
        visual_gate_active=visual_gate_active,
    )

    return emit(args.json, details, sorted(set(blocker_codes)), warnings)


def validate_visual_contract(
    intake_dir: Path,
    manifest_path: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> str:
    validate_json_schema(
        instance_path=manifest_path,
        schema_name="visual-source-manifest.schema.json",
        details_key="visual_source_manifest",
        details=details,
        blocker_codes=blocker_codes,
        schema_error_code=BLOCKERS["VISUAL_SCHEMA_INVALID"],
    )

    manifest = load_yaml(manifest_path)
    source_type = str(manifest.get("source_type") or "").strip().lower()
    required_fidelity = str(manifest.get("required_fidelity") or "").strip().lower()

    details["source_manifest"] = {
        "source_type": source_type,
        "required_fidelity": required_fidelity,
        "source_integrity_complete": manifest.get("source_integrity_complete"),
        "captured_at": manifest.get("captured_at"),
        "capture_method": manifest.get("capture_method"),
        "page_or_frame_count": manifest.get("page_or_frame_count"),
        "processed_count": manifest.get("processed_count"),
        "extraction_scope": manifest.get("extraction_scope"),
    }

    required_manifest_fields = [
        "source_type",
        "required_fidelity",
        "source_files",
        "source_integrity_complete",
        "captured_at",
        "capture_method",
        "page_or_frame_count",
        "processed_count",
        "extraction_scope",
    ]
    missing_manifest_fields = [field for field in required_manifest_fields if field not in manifest]
    details["source_manifest"]["missing_required_fields"] = missing_manifest_fields
    if missing_manifest_fields:
        blocker_codes.append(BLOCKERS["VISUAL_SOURCE_INTEGRITY_INCOMPLETE"])

    if source_type not in ALLOWED_SOURCE_TYPES:
        blocker_codes.append(BLOCKERS["VISUAL_SOURCE_TYPE_UNSUPPORTED"])

    if required_fidelity not in ALLOWED_FIDELITY_LEVELS:
        blocker_codes.append(BLOCKERS["VISUAL_FIDELITY_LEVEL_UNSUPPORTED"])

    if not is_truthy(manifest.get("source_integrity_complete")):
        blocker_codes.append(BLOCKERS["VISUAL_SOURCE_INTEGRITY_INCOMPLETE"])

    validate_source_files(intake_dir, manifest, source_type, details, blocker_codes)
    validate_visual_requirements(intake_dir, required_fidelity, details, blocker_codes)
    return source_type


def validate_source_files(
    intake_dir: Path,
    manifest: dict[str, Any],
    source_type: str,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    source_files = manifest.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        blocker_codes.append(BLOCKERS["VISUAL_SOURCE_FILE_MISSING"])
        details["source_files"] = []
        return

    validated_files: list[dict[str, Any]] = []
    for source_file in source_files:
        if not isinstance(source_file, dict):
            blocker_codes.append(BLOCKERS["VISUAL_SOURCE_FILE_MISSING"])
            continue

        required_source_file_fields = ["path", "mime_type", "byte_size", "sha256", "role"]
        missing_source_file_fields = [
            field for field in required_source_file_fields if field not in source_file
        ]
        rel_path = str(source_file.get("path") or "").strip()
        expected = str(source_file.get("sha256") or "").replace("sha256:", "").strip()
        file_detail: dict[str, Any] = {
            "path": rel_path,
            "exists": False,
            "sha256_match": None,
            "missing_required_fields": missing_source_file_fields,
        }

        if missing_source_file_fields:
            blocker_codes.append(BLOCKERS["VISUAL_SOURCE_INTEGRITY_INCOMPLETE"])

        if not rel_path:
            blocker_codes.append(BLOCKERS["VISUAL_SOURCE_FILE_MISSING"])
            validated_files.append(file_detail)
            continue

        if is_remote_ref(rel_path):
            file_detail["exists"] = True
            file_detail["remote_ref"] = True
            validated_files.append(file_detail)
            continue

        source_path = intake_dir / rel_path
        if not source_path.exists():
            blocker_codes.append(BLOCKERS["VISUAL_SOURCE_FILE_MISSING"])
            validated_files.append(file_detail)
            continue

        file_detail["exists"] = True
        expected_size = source_file.get("byte_size")
        if expected_size is not None:
            try:
                file_detail["byte_size_match"] = int(expected_size) == source_path.stat().st_size
                if not file_detail["byte_size_match"]:
                    blocker_codes.append(BLOCKERS["VISUAL_SOURCE_HASH_MISMATCH"])
            except (TypeError, ValueError):
                blocker_codes.append(BLOCKERS["VISUAL_SOURCE_INTEGRITY_INCOMPLETE"])
        if expected:
            actual = sha256(source_path)
            file_detail["sha256_match"] = expected == actual
            if expected != actual:
                blocker_codes.append(BLOCKERS["VISUAL_SOURCE_HASH_MISMATCH"])

        validated_files.append(file_detail)

    if source_type != "figma" and not any(item.get("exists") for item in validated_files):
        blocker_codes.append(BLOCKERS["VISUAL_SOURCE_FILE_MISSING"])

    details["source_files"] = validated_files


def validate_visual_requirements(
    intake_dir: Path,
    required_fidelity: str,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    requirements_path = intake_dir / "visual-requirements.yaml"
    if not requirements_path.exists():
        blocker_codes.append(BLOCKERS["VISUAL_REQUIREMENTS_MISSING"])
        return

    validate_json_schema(
        instance_path=requirements_path,
        schema_name="visual-requirements.schema.json",
        details_key="visual_requirements",
        details=details,
        blocker_codes=blocker_codes,
        schema_error_code=BLOCKERS["VISUAL_SCHEMA_INVALID"],
    )

    requirements_doc = load_yaml(requirements_path)
    requirements = requirements_doc.get("requirements")
    if not isinstance(requirements, list):
        requirements = []

    declared_requirements_count = requirements_doc.get("visual_requirements_count")
    try:
        requirements_count = (
            len(requirements)
            if declared_requirements_count is None
            else int(declared_requirements_count)
        )
    except (TypeError, ValueError):
        requirements_count = len(requirements)
    visual_requirements_complete = is_truthy(requirements_doc.get("visual_requirements_complete"))
    source_refs_complete = is_truthy(requirements_doc.get("source_refs_complete"))
    fidelity_rules_applied = is_truthy(requirements_doc.get("fidelity_rules_applied"))
    visual_parity_plan_complete = is_truthy(requirements_doc.get("visual_parity_plan_complete"))
    blocker_lint_errors = requirements_doc.get("blocker_lint_errors")
    parity_plan = requirements_doc.get("parity_plan")

    details["visual_requirements"] = {
        "visual_requirements_complete": requirements_doc.get("visual_requirements_complete"),
        "visual_requirements_count": requirements_count,
        "source_refs_complete": requirements_doc.get("source_refs_complete"),
        "fidelity_rules_applied": requirements_doc.get("fidelity_rules_applied"),
        "visual_parity_plan_complete": requirements_doc.get("visual_parity_plan_complete"),
        "required_fidelity": required_fidelity,
        "blocker_lint_errors": blocker_lint_errors,
        "parity_plan": parity_plan,
    }

    if not visual_requirements_complete or requirements_count <= 0:
        blocker_codes.append(BLOCKERS["VISUAL_REQUIREMENTS_MISSING"])

    count_matches = requirements_count == len(requirements)
    if not count_matches:
        blocker_codes.append(BLOCKERS["VISUAL_REQUIREMENTS_MISSING"])

    required_fields = [
        "id",
        "category",
        "requirement",
        "source_refs",
        "evidence_type",
        "confidence",
        "confidence_rationale",
        "engineering_action",
        "acceptance_check",
        "fidelity_level",
    ]
    allowed_evidence_types = {
        "observed",
        "inferred",
        "candidate",
        "unsupported",
        "missing",
        "out_of_scope",
    }
    allowed_categories = {
        "layout",
        "spacing",
        "sizing",
        "typography",
        "color",
        "asset",
        "component",
        "state",
        "interaction",
        "responsive",
        "accessibility",
        "content",
    }
    requirement_errors: list[dict[str, Any]] = []
    has_untraceable = not source_refs_complete
    has_missing_required = False
    has_bad_fidelity = False
    has_blocker_lint = isinstance(blocker_lint_errors, list) and len(blocker_lint_errors) > 0
    has_inference_contract_error = False
    evidence_type_counts: dict[str, int] = {}

    for index, item in enumerate(requirements):
        if not isinstance(item, dict):
            requirement_errors.append({"index": index, "error": "requirement must be a mapping"})
            has_missing_required = True
            continue

        missing_fields = [field for field in required_fields if not item.get(field)]
        if missing_fields:
            requirement_errors.append({"index": index, "missing_fields": missing_fields})
            has_missing_required = True

        source_refs = item.get("source_refs")
        if not isinstance(source_refs, list) or not source_refs or any(not str(ref).strip() for ref in source_refs):
            has_untraceable = True

        evidence_type = str(item.get("evidence_type") or "").strip().lower()
        if evidence_type:
            evidence_type_counts[evidence_type] = evidence_type_counts.get(evidence_type, 0) + 1
        if evidence_type and evidence_type not in allowed_evidence_types:
            requirement_errors.append({"index": index, "unsupported_evidence_type": evidence_type})
            has_missing_required = True
        elif evidence_type in {"inferred", "candidate", "unsupported"}:
            inference_errors = validate_bounded_inference_claim(item, evidence_type)
            if inference_errors:
                requirement_errors.append({"index": index, "inference_contract_errors": inference_errors})
                has_inference_contract_error = True

        category = str(item.get("category") or "").strip().lower()
        if category and category not in allowed_categories:
            requirement_errors.append({"index": index, "unsupported_category": category})
            has_missing_required = True

        fidelity_level = str(item.get("fidelity_level") or "").strip().lower()
        if fidelity_level and fidelity_level != required_fidelity:
            requirement_errors.append({"index": index, "fidelity_level_mismatch": fidelity_level})
            has_bad_fidelity = True

        blockers = item.get("blockers")
        if isinstance(blockers, list) and blockers:
            has_blocker_lint = True

    details["visual_requirements"]["requirement_errors"] = requirement_errors
    details["visual_requirements"]["evidence_type_counts"] = evidence_type_counts
    details["visual_requirements"]["count_matches_requirements"] = count_matches

    if has_missing_required:
        blocker_codes.append(BLOCKERS["VISUAL_REQUIREMENTS_MISSING"])

    if has_untraceable:
        blocker_codes.append(BLOCKERS["VISUAL_REQUIREMENTS_UNTRACEABLE"])

    if not fidelity_rules_applied or has_bad_fidelity:
        blocker_codes.append(BLOCKERS["VISUAL_FIDELITY_RULES_MISSING"])

    required_parity_fields = [
        "comparison_targets",
        "original_refs",
        "comparison_method",
        "thresholds",
        "accepted_exceptions",
        "blocking_difference_categories",
    ]
    missing_parity_fields: list[str] = []
    if not isinstance(parity_plan, dict):
        missing_parity_fields = required_parity_fields
    else:
        missing_parity_fields = []
        for field in required_parity_fields:
            if field not in parity_plan:
                missing_parity_fields.append(field)
                continue
            value = parity_plan.get(field)
            if field == "accepted_exceptions":
                if value is None:
                    missing_parity_fields.append(field)
            elif value in (None, "") or value == [] or value == {}:
                missing_parity_fields.append(field)
    details["visual_requirements"]["missing_parity_fields"] = missing_parity_fields

    if not visual_parity_plan_complete or missing_parity_fields:
        blocker_codes.append(BLOCKERS["VISUAL_PARITY_PLAN_MISSING"])

    if has_blocker_lint:
        blocker_codes.append(BLOCKERS["VISUAL_BLOCKER_LINT_ERRORS"])

    if has_inference_contract_error:
        blocker_codes.append(BLOCKERS["VISUAL_INFERENCE_CONTRACT_INVALID"])


def validate_bounded_inference_claim(item: dict[str, Any], evidence_type: str) -> list[str]:
    errors: list[str] = []

    def has_non_empty(field: str) -> bool:
        value = item.get(field)
        return value not in (None, "", [], {})

    source_refs = item.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        errors.append("non_observed_claim_requires_source_refs")

    if evidence_type == "inferred":
        required = [
            "inference_rule",
            "confidence_method",
            "score_breakdown",
            "downstream_use",
            "blocking_conditions",
        ]
        missing = [field for field in required if not has_non_empty(field)]
        if missing:
            errors.append(f"inferred_missing_fields:{','.join(missing)}")
        if item.get("confidence") != "high":
            errors.append("inferred_claim_requires_high_confidence")
        if item.get("downstream_use") != "accepted_claim":
            errors.append("inferred_claim_requires_downstream_use_accepted_claim")

    if evidence_type == "candidate":
        required = [
            "inference_rule",
            "confidence_method",
            "score_breakdown",
            "downstream_use",
            "missing_evidence",
            "blocking_conditions",
        ]
        missing = [field for field in required if not has_non_empty(field)]
        if missing:
            errors.append(f"candidate_missing_fields:{','.join(missing)}")
        if item.get("confidence") not in {"low", "medium"}:
            errors.append("candidate_claim_requires_low_or_medium_confidence")
        if item.get("downstream_use") != "reference_only":
            errors.append("candidate_claim_requires_downstream_use_reference_only")

    if evidence_type == "unsupported":
        required = ["blocker_code", "reason", "downstream_use", "missing_evidence", "blockers"]
        missing = [field for field in required if not has_non_empty(field)]
        if missing:
            errors.append(f"unsupported_missing_fields:{','.join(missing)}")
        if item.get("downstream_use") != "blocked":
            errors.append("unsupported_claim_requires_downstream_use_blocked")
        blockers = item.get("blockers")
        blocker_code = item.get("blocker_code")
        if isinstance(blockers, list) and blocker_code and blocker_code not in blockers:
            errors.append("unsupported_claim_blocker_code_must_match_blockers")

    score_breakdown = item.get("score_breakdown")
    if evidence_type in {"inferred", "candidate"}:
        if not isinstance(score_breakdown, list) or not score_breakdown:
            errors.append("score_breakdown_requires_at_least_one_signal")
        else:
            for signal_index, signal in enumerate(score_breakdown):
                if not isinstance(signal, dict):
                    errors.append(f"score_breakdown_signal_{signal_index}_must_be_mapping")
                    continue
                if not has_non_empty_in_mapping(signal, "signal"):
                    errors.append(f"score_breakdown_signal_{signal_index}_missing_signal")
                if "weight" not in signal:
                    errors.append(f"score_breakdown_signal_{signal_index}_missing_weight")

    return errors


def has_non_empty_in_mapping(value: dict[str, Any], field: str) -> bool:
    return value.get(field) not in (None, "", [], {})


def validate_figma_provider(intake_dir: Path, details: dict[str, Any], blocker_codes: list[str]) -> None:
    metadata_parts = sorted(Path(p) for p in glob.glob(str(intake_dir / "figma-metadata.part-*.xml")))
    details["metadata_shards"] = [p.name for p in metadata_parts]
    details["metadata_shard_count"] = len(metadata_parts)

    if not metadata_parts:
        blocker_codes.append(BLOCKERS["RAW_METADATA_MISSING"])

    for part in metadata_parts:
        text = part.read_text(encoding="utf-8", errors="replace")
        if has_summary_substitution(text):
            blocker_codes.append(BLOCKERS["RAW_METADATA_SUMMARY_SUBSTITUTION"])
        if "truncated" in text.lower() and "truncated=\"false\"" not in text.lower():
            blocker_codes.append(BLOCKERS["RAW_METADATA_TRUNCATED"])

    index_path = intake_dir / "figma-metadata.index.yaml"
    inventory_path = intake_dir / "figma-node-inventory.yaml"

    index: dict[str, Any] = {}
    inventory: dict[str, Any] = {}

    if not index_path.exists():
        blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
    else:
        validate_json_schema(
            instance_path=index_path,
            schema_name="figma-metadata-index.schema.json",
            details_key="figma_metadata_index",
            details=details,
            blocker_codes=blocker_codes,
            schema_error_code=BLOCKERS["VISUAL_SCHEMA_INVALID"],
        )
        index = load_yaml(index_path)
        required_source_fields = [
            "file_url",
            "file_key",
            "page_id",
            "selected_node_ids",
            "captured_at",
            "mcp_tool",
            "design_version_or_timestamp",
        ]
        required_completeness_fields = [
            "selected_subtree_complete",
            "raw_metadata_complete",
            "expected_root_node_ids",
            "captured_root_node_ids",
            "missing_root_node_ids",
            "gap_count",
            "gaps",
        ]
        missing_index_fields = [
            field for field in required_source_fields + required_completeness_fields if field not in index
        ]
        details["index"] = {
            "raw_metadata_complete": index.get("raw_metadata_complete"),
            "selected_subtree_complete": index.get("selected_subtree_complete"),
            "gap_count": index.get("gap_count"),
            "missing_required_fields": missing_index_fields,
        }
        if missing_index_fields:
            blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
        if index.get("mcp_tool") and str(index.get("mcp_tool")).strip() != "get_metadata":
            blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
        if not is_truthy(index.get("raw_metadata_complete")):
            blocker_codes.append(BLOCKERS["READY_WITHOUT_COMPLETENESS_PROOF"])
        if not is_truthy(index.get("selected_subtree_complete")):
            blocker_codes.append(BLOCKERS["SELECTED_SUBTREE_INCOMPLETE"])
        shards = index.get("shards", [])
        if isinstance(shards, list):
            indexed_shard_paths: set[str] = set()
            for shard in shards:
                if not isinstance(shard, dict):
                    blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
                    continue
                rel_path = shard.get("path")
                if not rel_path:
                    blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
                    continue
                indexed_shard_paths.add(str(rel_path))
                missing_shard_fields = [
                    field
                    for field in ["path", "byte_size", "sha256", "root_node_ids", "node_count", "truncated"]
                    if field not in shard
                ]
                if missing_shard_fields:
                    blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
                shard_path = intake_dir / str(rel_path)
                if not shard_path.exists():
                    blocker_codes.append(BLOCKERS["RAW_METADATA_MISSING"])
                    continue
                expected = str(shard.get("sha256", "")).replace("sha256:", "")
                if expected and expected != sha256(shard_path):
                    blocker_codes.append(BLOCKERS["VISUAL_SOURCE_HASH_MISMATCH"])
                expected_size = shard.get("byte_size")
                if expected_size is not None:
                    try:
                        if int(expected_size) != shard_path.stat().st_size:
                            blocker_codes.append(BLOCKERS["VISUAL_SOURCE_HASH_MISMATCH"])
                    except (TypeError, ValueError):
                        blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
                if is_truthy(shard.get("truncated")):
                    blocker_codes.append(BLOCKERS["RAW_METADATA_TRUNCATED"])
            actual_shard_paths = {part.name for part in metadata_parts}
            if actual_shard_paths != indexed_shard_paths:
                blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])
        else:
            blocker_codes.append(BLOCKERS["METADATA_INDEX_MISSING"])

    if not inventory_path.exists():
        blocker_codes.append(BLOCKERS["METADATA_PARITY_FAILED"])
    else:
        validate_json_schema(
            instance_path=inventory_path,
            schema_name="figma-node-inventory.schema.json",
            details_key="figma_node_inventory",
            details=details,
            blocker_codes=blocker_codes,
            schema_error_code=BLOCKERS["VISUAL_SCHEMA_INVALID"],
        )
        inventory = load_yaml(inventory_path)
        raw_node_count = int(inventory.get("raw_node_count") or 0)
        inventory_node_count = int(inventory.get("inventory_node_count") or 0)
        excluded_node_count = int(inventory.get("excluded_node_count") or 0)
        missing_node_count = int(inventory.get("missing_node_count") or 0)
        duplicate_node_count = int(inventory.get("duplicate_node_count") or 0)
        coverage = str(inventory.get("node_inventory_coverage") or "")
        parity_passed = is_truthy(inventory.get("parity_passed"))
        truncated_raw_evidence = is_truthy(inventory.get("truncated_raw_evidence"))

        details["inventory"] = {
            "raw_node_count": raw_node_count,
            "inventory_node_count": inventory_node_count,
            "excluded_node_count": excluded_node_count,
            "missing_node_count": missing_node_count,
            "duplicate_node_count": duplicate_node_count,
            "node_inventory_coverage": coverage,
            "parity_passed": parity_passed,
            "truncated_raw_evidence": truncated_raw_evidence,
        }

        balanced = inventory_node_count + excluded_node_count + missing_node_count == raw_node_count
        if not balanced or duplicate_node_count != 0 or missing_node_count != 0:
            blocker_codes.append(BLOCKERS["METADATA_PARITY_FAILED"])
        if coverage != "100%" or not parity_passed or truncated_raw_evidence:
            blocker_codes.append(BLOCKERS["METADATA_PARITY_FAILED"])
        if truncated_raw_evidence:
            blocker_codes.append(BLOCKERS["RAW_METADATA_TRUNCATED"])


def validate_evidence_packet(
    intake_dir: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
    warnings: list[str],
    visual_gate_active: bool,
) -> None:
    packet_candidates = [
        intake_dir / "visual-evidence-packet.md",
        intake_dir / "figma-evidence-packet.md",
    ]
    evidence_path = next((path for path in packet_candidates if path.exists()), None)
    if evidence_path is None:
        blocker_codes.append(BLOCKERS["VISUAL_EVIDENCE_PACKET_MISSING"])
        return
    if evidence_path.name == "figma-evidence-packet.md":
        warnings.append("figma-evidence-packet.md is a legacy evidence packet alias; prefer visual-evidence-packet.md")
    details["evidence_packet"] = evidence_path.name

    evidence_text = evidence_path.read_text(encoding="utf-8", errors="replace")
    packet_status = parse_evidence_packet_status(evidence_text)
    details["evidence_packet_metadata"] = packet_status["metadata"]
    if packet_status["warnings"]:
        warnings.extend(packet_status["warnings"])
    if packet_status["errors"]:
        blocker_codes.append(BLOCKERS["VISUAL_READY_WITHOUT_EVIDENCE"])
        return

    if packet_status["ready_gate"] != "PASS":
        blocker_codes.append(BLOCKERS["VISUAL_READY_WITHOUT_EVIDENCE"])
        return

    visual_requirements = details.get("visual_requirements", {})
    index = details.get("index", {})
    packet_blockers = packet_status["metadata"].get("blockers")
    has_packet_blockers = isinstance(packet_blockers, list) and bool(packet_blockers)

    if visual_gate_active:
        if blocker_codes or has_packet_blockers or not is_truthy(visual_requirements.get("visual_requirements_complete")):
            blocker_codes.append(BLOCKERS["VISUAL_READY_WITHOUT_EVIDENCE"])
    elif blocker_codes or has_packet_blockers or not is_truthy(index.get("raw_metadata_complete")):
        blocker_codes.append(BLOCKERS["READY_WITHOUT_COMPLETENESS_PROOF"])


def emit(json_mode: bool, details: dict[str, Any], blockers: list[str], warnings: list[str]) -> int:
    result = {
        "status": "BLOCKED" if blockers else "PASS",
        "blockers": blockers,
        "warnings": warnings,
        "details": details,
    }
    if json_mode:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Visual design intake readiness: {result['status']}")
        if blockers:
            print("Blockers:")
            for blocker in blockers:
                print(f"- {blocker}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"- {warning}")
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
