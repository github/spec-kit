"""Shared helpers for Spec Kit intake readiness validators."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:  # pragma: no cover - exercised in user environments
    Draft202012Validator = None

try:
    import yaml
except ImportError:  # pragma: no cover - exercised in user environments
    yaml = None


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


def has_needs_clarification(value: Any) -> bool:
    if isinstance(value, str):
        return "[NEEDS CLARIFICATION]" in value
    if isinstance(value, dict):
        return any(has_needs_clarification(item) for item in value.values())
    if isinstance(value, list):
        return any(has_needs_clarification(item) for item in value)
    return False


def non_empty(value: Any) -> bool:
    return value not in (None, "", [], {})


def validate_json_schema(
    *,
    instance_path: Path,
    schema_name: str,
    details_key: str,
    details: dict[str, Any],
    blocker_codes: list[str],
    schema_error_code: str,
) -> None:
    schema_details = details.setdefault("schema_validation", {})
    schema_detail: dict[str, Any] = {
        "schema": schema_name,
        "instance": str(instance_path),
        "valid": False,
        "errors": [],
    }
    schema_details[details_key] = schema_detail

    if Draft202012Validator is None:
        schema_detail["errors"].append(
            {"path": "$", "message": "jsonschema package is required for schema validation"}
        )
        blocker_codes.append(schema_error_code)
        return

    schema_path = Path(__file__).resolve().parents[2] / "templates" / "schemas" / schema_name
    if not schema_path.exists():
        schema_detail["errors"].append({"path": "$", "message": f"schema file not found: {schema_path}"})
        blocker_codes.append(schema_error_code)
        return

    instance = load_yaml(instance_path)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        for error in errors:
            path = "$"
            if error.path:
                path += "".join(
                    f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
                )
            schema_detail["errors"].append({"path": path, "message": error.message})
        blocker_codes.append(schema_error_code)
        return

    schema_detail["valid"] = True


def validate_source_manifest(
    *,
    intake_dir: Path,
    manifest_name: str,
    allowed_source_types: set[str],
    required_manifest_fields: list[str],
    required_source_file_fields: list[str],
    details: dict[str, Any],
    blocker_codes: list[str],
    missing_manifest_code: str,
    unsupported_source_code: str,
    missing_file_code: str,
    hash_mismatch_code: str,
    integrity_code: str,
    schema_name: str | None = None,
    schema_error_code: str | None = None,
) -> str:
    manifest_path = intake_dir / manifest_name
    if not manifest_path.exists():
        blocker_codes.append(missing_manifest_code)
        details["source_manifest"] = {"missing": True}
        return ""

    if schema_name and schema_error_code:
        validate_json_schema(
            instance_path=manifest_path,
            schema_name=schema_name,
            details_key="source_manifest",
            details=details,
            blocker_codes=blocker_codes,
            schema_error_code=schema_error_code,
        )

    manifest = load_yaml(manifest_path)
    source_type = str(manifest.get("source_type") or "").strip().lower()
    missing_manifest_fields = [
        field for field in required_manifest_fields if field not in manifest
    ]

    details["source_manifest"] = {
        "source_type": source_type,
        "source_integrity_complete": manifest.get("source_integrity_complete"),
        "captured_at": manifest.get("captured_at"),
        "capture_method": manifest.get("capture_method"),
        "missing_required_fields": missing_manifest_fields,
    }

    for field in required_manifest_fields:
        if field not in {"source_type", "source_integrity_complete", "captured_at", "capture_method", "source_files"}:
            details["source_manifest"][field] = manifest.get(field)

    if missing_manifest_fields:
        blocker_codes.append(integrity_code)

    if source_type not in allowed_source_types:
        blocker_codes.append(unsupported_source_code)

    if not is_truthy(manifest.get("source_integrity_complete")):
        blocker_codes.append(integrity_code)

    validate_source_files(
        intake_dir=intake_dir,
        manifest=manifest,
        required_source_file_fields=required_source_file_fields,
        details=details,
        blocker_codes=blocker_codes,
        missing_file_code=missing_file_code,
        hash_mismatch_code=hash_mismatch_code,
        integrity_code=integrity_code,
    )
    return source_type


def validate_source_files(
    *,
    intake_dir: Path,
    manifest: dict[str, Any],
    required_source_file_fields: list[str],
    details: dict[str, Any],
    blocker_codes: list[str],
    missing_file_code: str,
    hash_mismatch_code: str,
    integrity_code: str,
) -> None:
    source_files = manifest.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        blocker_codes.append(missing_file_code)
        details["source_files"] = []
        return

    validated_files: list[dict[str, Any]] = []
    for source_file in source_files:
        if not isinstance(source_file, dict):
            blocker_codes.append(missing_file_code)
            continue

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
            blocker_codes.append(integrity_code)

        if not rel_path:
            blocker_codes.append(missing_file_code)
            validated_files.append(file_detail)
            continue

        if is_remote_ref(rel_path):
            file_detail["exists"] = True
            file_detail["remote_ref"] = True
            validated_files.append(file_detail)
            continue

        source_path = intake_dir / rel_path
        if not source_path.exists():
            blocker_codes.append(missing_file_code)
            validated_files.append(file_detail)
            continue

        file_detail["exists"] = True
        expected_size = source_file.get("byte_size")
        if expected_size is not None:
            try:
                file_detail["byte_size_match"] = int(expected_size) == source_path.stat().st_size
                if not file_detail["byte_size_match"]:
                    blocker_codes.append(hash_mismatch_code)
            except (TypeError, ValueError):
                blocker_codes.append(integrity_code)
        if expected:
            actual = sha256(source_path)
            file_detail["sha256_match"] = expected == actual
            if expected != actual:
                blocker_codes.append(hash_mismatch_code)

        validated_files.append(file_detail)

    if not any(item.get("exists") for item in validated_files):
        blocker_codes.append(missing_file_code)

    details["source_files"] = validated_files


def validate_ready_evidence_packet(
    *,
    intake_dir: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
    warnings: list[str],
    missing_packet_code: str,
    ready_without_evidence_code: str,
) -> None:
    evidence_path = intake_dir / "evidence-packet.md"
    if not evidence_path.exists():
        blocker_codes.append(missing_packet_code)
        return

    details["evidence_packet"] = evidence_path.name
    evidence_text = evidence_path.read_text(encoding="utf-8", errors="replace")
    packet_status = parse_evidence_packet_status(evidence_text)
    details["evidence_packet_metadata"] = packet_status["metadata"]
    if packet_status["warnings"]:
        warnings.extend(packet_status["warnings"])
    if packet_status["errors"]:
        blocker_codes.append(ready_without_evidence_code)
        return

    packet_blockers = packet_status["metadata"].get("blockers")
    has_packet_blockers = isinstance(packet_blockers, list) and bool(packet_blockers)
    if packet_status["ready_gate"] != "PASS":
        blocker_codes.append(ready_without_evidence_code)
        return

    if blocker_codes or has_packet_blockers:
        blocker_codes.append(ready_without_evidence_code)


def parse_evidence_packet_status(evidence_text: str) -> dict[str, Any]:
    text = evidence_text.lstrip("\ufeff")
    result: dict[str, Any] = {
        "ready_gate": "",
        "metadata": {},
        "errors": [],
        "warnings": [],
        "used_front_matter": False,
    }
    front_matter = re.match(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", text, re.DOTALL)
    if front_matter:
        result["used_front_matter"] = True
        if yaml is None:
            result["errors"].append("PyYAML is required to parse evidence packet front matter")
            return result
        metadata = yaml.safe_load(front_matter.group(1)) or {}
        if not isinstance(metadata, dict):
            result["errors"].append("evidence packet front matter must be a mapping")
            return result
        result["metadata"] = metadata
        missing_fields = [
            field
            for field in [
                "ready_gate",
                "blockers",
                "source_ref_count",
                "extracted_item_count",
                "generated_at",
            ]
            if field not in metadata
        ]
        if missing_fields:
            result["errors"].append(f"missing evidence packet metadata fields: {', '.join(missing_fields)}")
        ready_gate = str(metadata.get("ready_gate") or "").strip().upper()
        if ready_gate not in {"PASS", "BLOCKED"}:
            result["errors"].append("evidence packet ready_gate must be PASS or BLOCKED")
        if not isinstance(metadata.get("blockers"), list):
            result["errors"].append("evidence packet blockers must be an array")
        for count_field in ["source_ref_count", "extracted_item_count"]:
            value = metadata.get(count_field)
            if not isinstance(value, int) or value < 0:
                result["errors"].append(f"evidence packet {count_field} must be a non-negative integer")
        if not non_empty(metadata.get("generated_at")):
            result["errors"].append("evidence packet generated_at must be populated")
        result["ready_gate"] = ready_gate
        return result

    ready_match = re.search(
        r"^\s*[-*]?\s*ready[_ ]gate:\s*(PASS|BLOCKED)\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if ready_match:
        ready_gate = ready_match.group(1).upper()
        result["ready_gate"] = ready_gate
        result["metadata"] = {"ready_gate": ready_gate, "blockers": []}
        result["warnings"].append(
            "evidence packet uses legacy Markdown ready_gate; add YAML front matter metadata"
        )
        return result

    result["errors"].append("evidence packet readiness metadata not found")
    return result


def emit(
    *,
    label: str,
    json_mode: bool,
    details: dict[str, Any],
    blockers: list[str],
    warnings: list[str],
) -> int:
    result = {
        "status": "BLOCKED" if blockers else "PASS",
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "details": details,
    }
    if json_mode:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{label} intake readiness: {result['status']}")
        if result["blockers"]:
            print("Blockers:")
            for blocker in result["blockers"]:
                print(f"- {blocker}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"- {warning}")
    return 1 if result["blockers"] else 0
