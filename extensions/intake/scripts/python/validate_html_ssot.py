#!/usr/bin/env python3
"""Validate Spec Kit Figma-derived HTML visual SSOT bundles."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised in user environments
    yaml = None

from intake_validator_common import validate_json_schema


BLOCKERS = {
    "SOURCE_INTAKE_BLOCKED": "HTML_SSOT_SOURCE_INTAKE_BLOCKED",
    "REQUIRED_ARTIFACT_MISSING": "HTML_SSOT_REQUIRED_ARTIFACT_MISSING",
    "FIGMA_NODE_COVERAGE_INCOMPLETE": "HTML_SSOT_FIGMA_NODE_COVERAGE_INCOMPLETE",
    "COMPONENT_STATE_COVERAGE_INCOMPLETE": "HTML_SSOT_COMPONENT_STATE_COVERAGE_INCOMPLETE",
    "PAGE_COVERAGE_INCOMPLETE": "HTML_SSOT_PAGE_COVERAGE_INCOMPLETE",
    "ASSET_TRACEABILITY_INCOMPLETE": "HTML_SSOT_ASSET_TRACEABILITY_INCOMPLETE",
    "VIEWPORT_CAPTURE_INCOMPLETE": "HTML_SSOT_VIEWPORT_CAPTURE_INCOMPLETE",
    "VISUAL_DIFF_BLOCKED": "HTML_SSOT_VISUAL_DIFF_BLOCKED",
    "KNOWN_GAP_UNRESOLVED": "HTML_SSOT_KNOWN_GAP_UNRESOLVED",
    "SCHEMA_INVALID": "HTML_SSOT_SCHEMA_INVALID",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_ssot_dir", help="Directory containing figma2htmlssot artifacts")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    html_dir = Path(args.html_ssot_dir)
    blocker_codes: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"html_ssot_dir": str(html_dir)}

    if not html_dir.exists() or not html_dir.is_dir():
        blocker_codes.append(BLOCKERS["REQUIRED_ARTIFACT_MISSING"])
        return emit(args.json, details, sorted(set(blocker_codes)), warnings)

    validate_source_intake(html_dir, details, blocker_codes)

    required_files = {
        "visual_spec": html_dir / "visual-spec.html",
        "figma_map": html_dir / "figma-map.json",
        "assets_manifest": html_dir / "assets-manifest.json",
        "coverage_report": html_dir / "coverage-report.md",
        "known_gaps": html_dir / "known-gaps.md",
    }
    missing = [name for name, path in required_files.items() if not path.exists()]
    screenshots_dir = html_dir / "screenshots"
    if not screenshots_dir.exists() or not screenshots_dir.is_dir():
        missing.append("screenshots")
    if missing:
        blocker_codes.append(BLOCKERS["REQUIRED_ARTIFACT_MISSING"])
    details["required_artifacts"] = {"missing": missing}

    figma_map = load_json_artifact(
        required_files["figma_map"],
        "figma-map.schema.json",
        "figma_map",
        details,
        blocker_codes,
    )
    assets_manifest = load_json_artifact(
        required_files["assets_manifest"],
        "assets-manifest.schema.json",
        "assets_manifest",
        details,
        blocker_codes,
    )
    coverage = load_coverage_report(
        required_files["coverage_report"],
        details,
        blocker_codes,
    )

    html_text = ""
    if required_files["visual_spec"].exists():
        html_text = required_files["visual_spec"].read_text(encoding="utf-8", errors="replace")

    validate_map_coverage(figma_map, html_text, details, blocker_codes)
    validate_asset_traceability(html_dir, assets_manifest, details, blocker_codes)
    validate_screenshot_coverage(screenshots_dir, details, blocker_codes)
    validate_coverage_readiness(coverage, details, blocker_codes)
    validate_known_gaps(required_files["known_gaps"], details, blocker_codes)

    return emit(args.json, details, sorted(set(blocker_codes)), warnings)


def validate_source_intake(
    html_dir: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    upstream = html_dir.parent
    packet = upstream / "visual-evidence-packet.md"
    if not packet.exists():
        details["source_intake"] = {"missing": True}
        blocker_codes.append(BLOCKERS["SOURCE_INTAKE_BLOCKED"])
        return

    text = packet.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    metadata: dict[str, Any] = {}
    if match and yaml is not None:
        loaded = yaml.safe_load(match.group(1)) or {}
        metadata = loaded if isinstance(loaded, dict) else {}
    ready_gate = str(metadata.get("ready_gate") or "").strip().upper()
    blockers = metadata.get("blockers")
    details["source_intake"] = {
        "path": str(packet),
        "ready_gate": ready_gate,
        "blockers": blockers,
    }
    if ready_gate != "PASS" or (isinstance(blockers, list) and blockers):
        blocker_codes.append(BLOCKERS["SOURCE_INTAKE_BLOCKED"])


def load_json_artifact(
    path: Path,
    schema_name: str,
    details_key: str,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> dict[str, Any]:
    if not path.exists():
        return {}
    validate_json_schema(
        instance_path=path,
        schema_name=schema_name,
        details_key=details_key,
        details=details,
        blocker_codes=blocker_codes,
        schema_error_code=BLOCKERS["SCHEMA_INVALID"],
    )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        blocker_codes.append(BLOCKERS["SCHEMA_INVALID"])
        return {}
    return data if isinstance(data, dict) else {}


def load_coverage_report(
    path: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
    match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not match or yaml is None:
        blocker_codes.append(BLOCKERS["SCHEMA_INVALID"])
        details["coverage_report"] = {"front_matter_missing": True}
        return {}
    loaded = yaml.safe_load(match.group(1)) or {}
    coverage = loaded if isinstance(loaded, dict) else {}
    temp_path = path.with_suffix(".frontmatter.tmp.yaml")
    try:
        temp_path.write_text(yaml.safe_dump(coverage), encoding="utf-8")
        validate_json_schema(
            instance_path=temp_path,
            schema_name="html-ssot-coverage.schema.json",
            details_key="coverage_report",
            details=details,
            blocker_codes=blocker_codes,
            schema_error_code=BLOCKERS["SCHEMA_INVALID"],
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return coverage


def selector_in_html(selector: str, html_text: str) -> bool:
    if selector.startswith("[") and selector.endswith("]"):
        body = selector[1:-1].strip()
        if "=" in body:
            attr, value = body.split("=", 1)
            attr = attr.strip()
            value = value.strip().strip("\"'")
            return f'{attr}="{value}"' in html_text or f"{attr}='{value}'" in html_text
        return body in html_text
    if selector.startswith("#"):
        value = selector[1:]
        return f'id="{value}"' in html_text or f"id='{value}'" in html_text
    if selector.startswith("."):
        value = selector[1:]
        return re.search(rf"class=['\"][^'\"]*\b{re.escape(value)}\b", html_text) is not None
    return selector in html_text


def validate_map_coverage(
    figma_map: dict[str, Any],
    html_text: str,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    mappings = figma_map.get("mappings", [])
    required = [item for item in mappings if isinstance(item, dict) and item.get("required") is True]
    missing_selectors: list[str] = []
    incomplete_units: list[str] = []
    page_units = 0
    for item in required:
        selector = str(item.get("selector") or "")
        if selector and not selector_in_html(selector, html_text):
            missing_selectors.append(selector)
        if item.get("acceptance_unit") == "component-state":
            if not all(item.get(field) for field in ("states", "viewports", "content_sample", "container_constraint")):
                incomplete_units.append(str(item.get("figma_node_id") or selector))
        if item.get("acceptance_unit") == "page":
            page_units += 1

    details["figma_map_coverage"] = {
        "required_mapping_count": len(required),
        "missing_selectors": missing_selectors,
        "incomplete_component_state_units": incomplete_units,
        "page_unit_count": page_units,
    }
    if not required or missing_selectors:
        blocker_codes.append(BLOCKERS["FIGMA_NODE_COVERAGE_INCOMPLETE"])
    if incomplete_units:
        blocker_codes.append(BLOCKERS["COMPONENT_STATE_COVERAGE_INCOMPLETE"])
    if page_units == 0:
        blocker_codes.append(BLOCKERS["PAGE_COVERAGE_INCOMPLETE"])


def validate_asset_traceability(
    html_dir: Path,
    assets_manifest: dict[str, Any],
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    assets = assets_manifest.get("assets", [])
    untraceable: list[str] = []
    for asset in assets:
        if not isinstance(asset, dict):
            untraceable.append("<invalid>")
            continue
        path = str(asset.get("path") or "")
        source_refs = asset.get("source_refs")
        checksum = str(asset.get("sha256") or "")
        if path.startswith("data:") or not source_refs or not checksum:
            untraceable.append(str(asset.get("id") or path or "<unknown>"))
            continue
        if path and not path.startswith(("http://", "https://")) and not (html_dir / path).exists():
            untraceable.append(str(asset.get("id") or path))
    details["asset_traceability"] = {"asset_count": len(assets), "untraceable": untraceable}
    if untraceable:
        blocker_codes.append(BLOCKERS["ASSET_TRACEABILITY_INCOMPLETE"])


def validate_screenshot_coverage(
    screenshots_dir: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    screenshots = []
    if screenshots_dir.exists() and screenshots_dir.is_dir():
        screenshots = [path.name for path in screenshots_dir.iterdir() if path.is_file()]
    details["screenshots"] = {"count": len(screenshots), "files": screenshots}
    if not screenshots:
        blocker_codes.append(BLOCKERS["VIEWPORT_CAPTURE_INCOMPLETE"])


def validate_coverage_readiness(
    coverage: dict[str, Any],
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    if not coverage:
        return
    details["coverage_readiness"] = {
        "ready_gate": coverage.get("ready_gate"),
        "blockers": coverage.get("blockers"),
        "required_nodes_total": coverage.get("required_nodes_total"),
        "required_nodes_covered": coverage.get("required_nodes_covered"),
    }
    if coverage.get("required_nodes_covered") != coverage.get("required_nodes_total"):
        blocker_codes.append(BLOCKERS["FIGMA_NODE_COVERAGE_INCOMPLETE"])
    if coverage.get("component_state_coverage_complete") is not True:
        blocker_codes.append(BLOCKERS["COMPONENT_STATE_COVERAGE_INCOMPLETE"])
    if coverage.get("page_coverage_complete") is not True:
        blocker_codes.append(BLOCKERS["PAGE_COVERAGE_INCOMPLETE"])
    if coverage.get("asset_traceability_complete") is not True:
        blocker_codes.append(BLOCKERS["ASSET_TRACEABILITY_INCOMPLETE"])
    if coverage.get("viewport_capture_complete") is not True:
        blocker_codes.append(BLOCKERS["VIEWPORT_CAPTURE_INCOMPLETE"])
    if coverage.get("visual_diff_status") == "blocked":
        blocker_codes.append(BLOCKERS["VISUAL_DIFF_BLOCKED"])
    blockers = coverage.get("blockers")
    if coverage.get("ready_gate") != "PASS" or (isinstance(blockers, list) and blockers):
        blocker_codes.append(BLOCKERS["KNOWN_GAP_UNRESOLVED"])


def validate_known_gaps(
    known_gaps_path: Path,
    details: dict[str, Any],
    blocker_codes: list[str],
) -> None:
    if not known_gaps_path.exists():
        return
    text = known_gaps_path.read_text(encoding="utf-8", errors="replace")
    unresolved = bool(re.search(r"\b(UNRESOLVED|BLOCKED|TODO)\b", text, re.IGNORECASE))
    details["known_gaps"] = {"unresolved": unresolved}
    if unresolved:
        blocker_codes.append(BLOCKERS["KNOWN_GAP_UNRESOLVED"])


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
        print(f"HTML SSOT readiness: {result['status']}")
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
