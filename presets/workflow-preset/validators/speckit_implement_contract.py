from __future__ import annotations

import re
from typing import Any


VALID_EXECUTION_MODES = {"isolated_subagent", "manual_fresh_worker_session"}
VALID_VERTICAL_CAPABILITIES = (
    "domain-model",
    "api-contract",
    "persistence",
    "service-flow",
    "ui",
    "cli",
    "test-validation",
    "documentation",
    "integration",
    "cleanup",
)
SHARD_ID_PATTERN = re.compile(
    rf"^S[0-9]{{2}}-({'|'.join(VALID_VERTICAL_CAPABILITIES)})-[0-9]{{2}}$"
)
CASE_TYPES = {"positive", "negative", "boundary", "permission", "validation", "state_conflict"}
FAILURE_CASE_TYPES = {"negative", "permission", "validation", "state_conflict"}
EXPLICIT_COMPONENT_USE_CONSTRAINTS = {
    "visual-reference-only",
    "must-reuse-existing",
    "figma-export-required",
}
EXPLICIT_COPY_CONSTRAINTS = {
    "no-new-copy",
    "figma-copy-required",
    "product-copy-required",
}
EXPLICIT_DRAWING_CONSTRAINTS = {
    "no-self-draw",
    "figma-export-required",
    "existing-asset-required",
}
PROVIDER_MATRIX_COPY_KEYS = {
    "figma_frame_node_refs",
    "requirement_target",
    "layout_facts",
    "typography_facts",
    "color_token_facts",
    "effect_facts",
    "variant_state_evidence",
    "visual_proof_level",
    "spec_requirement_target",
}
FULL_PROVIDER_MATRIX_KEYS = {
    "source",
    "readiness",
    "visual_items",
    "visual_item_matrix",
    "provider_visual_item_matrix",
}


def _duplicate_ids(items: list[dict[str, Any]], *, key: str, context: str) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        item_id = item.get(key)
        if item_id in seen:
            duplicates.add(item_id)
        seen.add(item_id)
    if duplicates:
        duplicate = sorted(duplicates)[0]
        raise ValueError(f"{context} duplicates {key}: {duplicate}")
    return seen


def _duplicate_values(values: list[Any], *, context: str, label: str = "value") -> None:
    seen: set[str] = set()
    for value in values:
        key = str(value)
        if key in seen:
            raise ValueError(f"{context} duplicates {label}: {key}")
        seen.add(key)


def _shard_id_capability(shard_id: Any) -> str:
    match = SHARD_ID_PATTERN.match(str(shard_id))
    if match is None:
        raise ValueError(f"invalid shard_id: {shard_id}")
    return match.group(1)


def _normalized_path_parts(path: Any) -> tuple[bool, tuple[str, ...]]:
    text = str(path).replace("\\", "/").rstrip("/")
    is_absolute = text.startswith("/")
    parts: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append(part)
            continue
        parts.append(part)
    return is_absolute, tuple(parts)


def _is_prefix_path(parent: tuple[str, ...], child: tuple[str, ...]) -> bool:
    return len(parent) < len(child) and child[: len(parent)] == parent


def _paths_overlap(left: Any, right: Any) -> bool:
    left_absolute, left_parts = _normalized_path_parts(left)
    right_absolute, right_parts = _normalized_path_parts(right)
    if left_absolute != right_absolute:
        return False
    return (
        left_parts == right_parts
        or _is_prefix_path(left_parts, right_parts)
        or _is_prefix_path(right_parts, left_parts)
    )


def _first_path_overlap(
    paths: list[Any],
    candidates: list[Any],
) -> tuple[str, str] | None:
    for path in paths:
        for candidate in candidates:
            if _paths_overlap(path, candidate):
                return str(path), str(candidate)
    return None


def _find_owned_path_overlap(
    owned_paths: list[tuple[str, str]],
    path: Any,
    owner: str,
) -> tuple[str, str] | None:
    for owned_path, owned_by in owned_paths:
        if owned_by != owner and _paths_overlap(owned_path, path):
            return owned_path, owned_by
    return None


def _require_non_empty_list(item: dict[str, Any], *, key: str, context: str) -> None:
    values = item.get(key)
    item_id = item.get("id", "<unknown>")
    if not isinstance(values, list) or not values:
        raise ValueError(f"{context} {item_id} must include non-empty {key}")


def _validate_expected_uif_contract(uif_contract: dict[str, Any]) -> None:
    uif_id = uif_contract.get("id", "<unknown>")
    steps = uif_contract.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"expected UIF contract {uif_id} must include non-empty steps")

    for index, step in enumerate(steps):
        step_type = step.get("type")
        context = f"expected UIF contract {uif_id} step {index}"
        if step_type == "api_call":
            api = step.get("api")
            if not isinstance(api, dict) or not api.get("method") or not api.get("path"):
                raise ValueError(f"{context} api_call requires api.method and api.path")
        elif step_type == "local_route":
            if "to" not in step or step.get("to") in ("", None):
                raise ValueError(f"{context} local_route requires to")
        elif step_type == "user_event":
            if not step.get("id") and not step.get("label"):
                raise ValueError(f"{context} user_event requires id or label")


def _validate_non_positive_behavior_scenario(
    scenario: dict[str, Any],
    assertions_by_id: dict[str, dict[str, Any]],
) -> None:
    scenario_id = scenario.get("id", "<unknown>")
    scenario_type = scenario.get("type")
    if scenario_type == "positive":
        return

    request_case = scenario.get("request_case")
    if not isinstance(request_case, dict):
        raise ValueError(f"behavior scenario {scenario_id} must include request_case")
    case_kind = request_case.get("case_kind")
    if not case_kind:
        raise ValueError(f"behavior scenario {scenario_id} missing case_kind")
    if case_kind != scenario_type:
        raise ValueError(f"behavior scenario {scenario_id} case_kind must match type")
    outcome = request_case.get("outcome")
    if outcome not in {"success", "failure"}:
        raise ValueError(f"behavior scenario {scenario_id} missing outcome")
    if not request_case.get("trigger"):
        raise ValueError(f"behavior scenario {scenario_id} missing trigger")

    if scenario_type in FAILURE_CASE_TYPES and outcome != "failure":
        raise ValueError(f"behavior scenario {scenario_id} failure case must declare failure outcome")
    if outcome != "failure":
        return

    expected_response = scenario.get("expected_response")
    if not isinstance(expected_response, dict) or not expected_response:
        raise ValueError(f"behavior scenario {scenario_id} missing expected_response")
    if not expected_response.get("error_code"):
        raise ValueError(f"behavior scenario {scenario_id} missing error_code")

    expected_feedback = scenario.get("expected_feedback")
    if not isinstance(expected_feedback, dict) or not expected_feedback:
        raise ValueError(f"behavior scenario {scenario_id} missing expected_feedback")
    if not expected_feedback.get("type"):
        raise ValueError(f"behavior scenario {scenario_id} missing feedback_type")
    if not expected_feedback.get("message"):
        raise ValueError(f"behavior scenario {scenario_id} missing feedback_message")

    invariant_intents = {"state_invariant", "rollback", "compensation"}
    if not any(
        assertions_by_id.get(assertion_id, {}).get("intent") in invariant_intents
        for assertion_id in scenario.get("assertion_ids", [])
    ):
        raise ValueError(
            f"behavior scenario {scenario_id} missing state_invariant_rollback_or_compensation_assertion"
        )


def _case_coverage_blockers_by_id(scenario_instances: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        blocker["id"]: blocker
        for blocker in scenario_instances.get("case_coverage_blockers", [])
        if "id" in blocker
    }


def validate_behavior_case_coverage(
    case_coverage: dict[str, Any],
    scenarios_draft: dict[str, Any],
    scenario_instances: dict[str, Any],
    tasks_text: str,
    quickstart_text: str,
) -> None:
    draft_by_id = {
        scenario.get("id"): scenario
        for scenario in scenarios_draft.get("scenarios", [])
        if "id" in scenario
    }
    formal_by_id = {
        scenario.get("id"): scenario
        for scenario in scenario_instances.get("scenarios", [])
        if "id" in scenario
    }
    blockers_by_id = _case_coverage_blockers_by_id(scenario_instances)

    coverage_rows = case_coverage.get("case_coverage")
    if not isinstance(coverage_rows, list) or not coverage_rows:
        raise ValueError("case_coverage must include a non-empty case_coverage matrix")

    for row in coverage_rows:
        story = row.get("story", "<unknown>")
        case_type = row.get("case_type")
        status = row.get("status")
        context = f"{story} {case_type}"

        if case_type not in CASE_TYPES:
            raise ValueError(f"case coverage row {context} has unknown case_type")
        if status not in {"Required", "Not Applicable", "Unknown"}:
            raise ValueError(f"case coverage row {context} has unknown status")

        if status == "Not Applicable":
            if not row.get("rationale"):
                raise ValueError(f"Not Applicable case {context} missing rationale")
            continue

        if status == "Unknown":
            if not row.get("blocker_id"):
                raise ValueError(f"Unknown case {context} missing Blocking Items reference")
            continue

        if status != "Required":
            continue

        if not row.get("source"):
            raise ValueError(f"Required case {context} missing source")

        scenario_id = row.get("scenario_id")
        blocker_id = row.get("blocker_id")
        if bool(scenario_id) == bool(blocker_id):
            raise ValueError(
                f"Required case {context} must name exactly one scenario_id or blocker_id"
            )

        if blocker_id:
            blocker = blockers_by_id.get(blocker_id)
            if blocker is None:
                raise ValueError(f"Required case {context} references unknown blocker")
            if blocker.get("case_id") != row.get("case_id"):
                raise ValueError(f"Required case {context} blocker case_id mismatch")
            if blocker.get("case_type") != case_type:
                raise ValueError(f"Required case {context} blocker case_type mismatch")
            if blocker.get("source") != row.get("source"):
                raise ValueError(f"Required case {context} blocker source mismatch")
            if blocker_id not in tasks_text:
                raise ValueError(f"Required case {context} missing tasks.md blocker evidence")
            if blocker_id not in quickstart_text:
                raise ValueError(f"Required case {context} missing quickstart.md blocker evidence")
            continue

        draft = draft_by_id.get(scenario_id)
        formal = formal_by_id.get(scenario_id)
        if draft is None or formal is None:
            raise ValueError(f"Required case {context} missing draft or formal scenario")
        if draft.get("type") != case_type or formal.get("type") != case_type:
            raise ValueError(f"Required case {context} scenario type mismatch")
        if scenario_id not in tasks_text:
            raise ValueError(f"Required case {context} missing tasks.md evidence")
        if scenario_id not in quickstart_text:
            raise ValueError(f"Required case {context} missing quickstart.md evidence")


def validate_visual_item_matrix_contract(matrix: dict[str, Any]) -> None:
    readiness = matrix.get("readiness", {})
    if readiness.get("status") == "PASS":
        if readiness.get("raw_metadata_complete") is not True:
            raise ValueError("visual item matrix PASS requires raw_metadata_complete")
        if readiness.get("node_inventory_coverage") != 100:
            raise ValueError("visual item matrix PASS requires node_inventory_coverage 100")
        if readiness.get("parity_passed") is not True:
            raise ValueError("visual item matrix PASS requires parity_passed")
        if readiness.get("blocker_lint_errors"):
            raise ValueError("visual item matrix PASS requires no blocker_lint_errors")

    visual_items = matrix.get("visual_items", [])
    if not visual_items:
        raise ValueError("visual item matrix must include visual_items")
    _duplicate_ids(visual_items, key="id", context="visual item matrix")

    for item in visual_items:
        item_id = item.get("id", "<unknown>")
        explicit_component = item.get("component_use_constraint") in EXPLICIT_COMPONENT_USE_CONSTRAINTS
        explicit_copy = item.get("copy_content_constraint") in EXPLICIT_COPY_CONSTRAINTS
        explicit_drawing = item.get("drawing_asset_constraint") in EXPLICIT_DRAWING_CONSTRAINTS
        if (explicit_component or explicit_copy or explicit_drawing) and not item.get(
            "constraint_source_refs"
        ):
            raise ValueError(
                f"visual item {item_id} explicit constraints require constraint_source_refs"
            )

        if item.get("fidelity_scope") in {"pixel-perfect", "brand-critical"}:
            if item.get("visual_proof_level") != "L3":
                raise ValueError(
                    f"visual item {item_id} pixel-perfect or brand-critical requires L3 proof"
                )
            if not item.get("screenshot_refs"):
                raise ValueError(
                    f"visual item {item_id} pixel-perfect or brand-critical requires screenshot_refs"
                )


def validate_design_requirement_intake_trace_contract(intake: dict[str, Any]) -> None:
    rows = intake.get("visual_restoration_trace", [])
    if rows in (None, []):
        return
    if not isinstance(rows, list):
        raise ValueError("visual restoration trace must be a list")

    _duplicate_ids(rows, key="visual_item_id", context="visual restoration trace")

    for row in rows:
        item_id = row.get("visual_item_id", "<unknown>")
        copied_structures = FULL_PROVIDER_MATRIX_KEYS.intersection(row)
        if copied_structures:
            raise ValueError(
                f"visual restoration trace {item_id} must not copy full provider Visual Item Matrix"
            )

        copied_provider_fields = PROVIDER_MATRIX_COPY_KEYS.intersection(row)
        if len(copied_provider_fields) >= 3:
            raise ValueError(
                f"visual restoration trace {item_id} must record only requirement-level facts"
            )

        if not row.get("requirement_id") and not row.get("spec_requirement_ref"):
            raise ValueError(f"visual restoration trace {item_id} missing requirement reference")
        if not row.get("supporting_evidence_refs") and not row.get("provider_source_refs"):
            raise ValueError(
                f"visual restoration trace {item_id} missing supporting evidence refs"
            )


def _handoff_has_behavior_contract_context(handoff: dict[str, Any]) -> bool:
    markers = (
        "contracts/bdd/",
        "contracts/uif/",
        "contracts/behavior/",
        "BehaviorScenarioInstance",
        "BDD scenario",
        "behavior assertion",
    )
    values: list[str] = []
    for key in ("allowed_read_paths", "allowed_write_paths", "task_text"):
        field = handoff.get(key, [])
        if isinstance(field, list):
            values.extend(str(item) for item in field)
    haystack = "\n".join(values)
    return any(marker in haystack for marker in markers)


def _receipt_references_behavior_evidence(receipt: dict[str, Any]) -> bool:
    markers = (
        "SCN-",
        "AST-",
        "BDD",
        "contracts/bdd/",
        "contracts/uif/",
        "contracts/behavior/",
        "contracts/api/",
        "quickstart.md",
    )
    evidence = "\n".join(str(item) for item in receipt.get("validation_evidence", []))
    return any(marker in evidence for marker in markers)


def _handoff_is_code_review_task(handoff: dict[str, Any]) -> bool:
    if handoff.get("task_type") == "code_review":
        return True
    text = "\n".join(str(item) for item in handoff.get("task_text", []))
    normalized = text.lower().replace("-", " ")
    return "code review" in normalized


def _receipt_defers_real_e2e(receipt: dict[str, Any]) -> bool:
    evidence = "\n".join(str(item) for item in receipt.get("validation_evidence", []))
    normalized = evidence.lower().replace("-", " ")
    return (
        "real e2e" in normalized
        and any(
            marker in normalized
            for marker in ("deferred", "cannot run", "unavailable", "missing")
        )
    )


def _code_review_checked_source_allowed(handoff: dict[str, Any], source: Any) -> bool:
    allowed_sources = list(handoff.get("allowed_read_paths", []))
    context_digest_path = handoff.get("context_digest_path")
    if context_digest_path:
        allowed_sources.append(context_digest_path)
    return any(_paths_overlap(source, allowed_source) for allowed_source in allowed_sources)


def _receipt_mentions_any_command(receipt: dict[str, Any], commands: list[Any]) -> bool:
    evidence = "\n".join(str(item) for item in receipt.get("validation_evidence", []))
    return any(str(command) in evidence for command in commands)


def _unresolved_high_or_critical(finding: dict[str, Any]) -> bool:
    return (
        finding.get("severity") in {"critical", "high"}
        and finding.get("resolution") in {"todo", "blocked"}
    )


def validate_behavior_draft_contract(
    scenarios_draft: dict[str, Any],
    data_fixtures_intent: dict[str, Any],
) -> None:
    scenarios = scenarios_draft.get("scenarios", [])
    if not scenarios:
        raise ValueError("behavior draft scenarios must include at least one scenario")

    scenario_ids = _duplicate_ids(
        scenarios,
        key="id",
        context="behavior draft scenarios",
    )
    for scenario in scenarios:
        for key in ("given", "when", "then"):
            _require_non_empty_list(
                scenario,
                key=key,
                context="behavior draft scenario",
            )

    _duplicate_ids(
        data_fixtures_intent.get("fixtures", []),
        key="id",
        context="behavior data fixture intents",
    )

    for fixture in data_fixtures_intent.get("fixtures", []):
        for scenario_id in fixture.get("required_for", []):
            if scenario_id not in scenario_ids:
                raise ValueError(f"fixture required_for references unknown scenario: {scenario_id}")


def validate_behavior_contract_bundle(
    scenario_instances: dict[str, Any],
    data_fixtures: dict[str, Any],
    assertions: dict[str, Any],
    uif_expected_contracts: list[dict[str, Any]],
) -> None:
    scenarios = scenario_instances.get("scenarios", [])
    if not scenarios:
        raise ValueError("behavior scenario instances must include at least one scenario")

    scenario_ids = _duplicate_ids(
        scenarios,
        key="id",
        context="behavior scenario instances",
    )
    fixture_ids = _duplicate_ids(
        data_fixtures.get("fixtures", []),
        key="id",
        context="behavior data fixtures",
    )
    assertion_ids = _duplicate_ids(
        assertions.get("assertions", []),
        key="id",
        context="behavior assertions",
    )
    assertions_by_id = {
        assertion["id"]: assertion
        for assertion in assertions.get("assertions", [])
        if "id" in assertion
    }
    uif_path_ids = _duplicate_ids(
        uif_expected_contracts,
        key="id",
        context="expected UIF contracts",
    )
    for uif_contract in uif_expected_contracts:
        _validate_expected_uif_contract(uif_contract)

    for scenario in scenarios:
        _require_non_empty_list(
            scenario,
            key="fixture_ids",
            context="behavior scenario instance",
        )
        _require_non_empty_list(
            scenario,
            key="assertion_ids",
            context="behavior scenario instance",
        )

        uif_path_id = scenario.get("uif_path_id")
        if uif_path_id not in uif_path_ids:
            raise ValueError(f"scenario references unknown uif_path_id: {uif_path_id}")

        for fixture_id in scenario.get("fixture_ids", []):
            if fixture_id not in fixture_ids:
                raise ValueError(f"scenario references unknown fixture: {fixture_id}")

        for assertion_id in scenario.get("assertion_ids", []):
            if assertion_id not in assertion_ids:
                raise ValueError(f"scenario references unknown assertion: {assertion_id}")

        _validate_non_positive_behavior_scenario(scenario, assertions_by_id)

    if len(scenario_ids) != len(scenario_instances.get("scenarios", [])):
        raise ValueError("behavior scenario instances contain duplicate ids")


def validate_manifest_contract(manifest: dict[str, Any]) -> None:
    execution_mode = manifest.get("execution_mode")
    if execution_mode not in VALID_EXECUTION_MODES:
        raise ValueError(
            "manifest execution_mode must be isolated_subagent or manual_fresh_worker_session"
        )

    shards = manifest.get("shards", [])
    shard_ids = _duplicate_ids(shards, key="shard_id", context="manifest shards")
    for shard in shards:
        shard_capability = _shard_id_capability(shard.get("shard_id"))
        vertical_capability = shard.get("vertical_capability")
        if shard_capability != vertical_capability:
            raise ValueError(
                f"shard_id vertical_capability mismatch: {shard.get('shard_id')}"
            )

        task_ids = shard.get("task_ids")
        if not isinstance(task_ids, list) or not task_ids:
            raise ValueError(
                f"manifest shard {shard.get('shard_id', '<unknown>')} "
                "must include non-empty task_ids"
            )
        _duplicate_values(
            task_ids,
            context=f"manifest shard {shard.get('shard_id', '<unknown>')}",
            label="task_ids",
        )

    ordered_shard_ids: list[str] = []
    for layer in manifest.get("dispatch_order", []):
        for shard_id in layer:
            if shard_id not in shard_ids:
                raise ValueError(f"dispatch_order references unknown shard: {shard_id}")
            if shard_id in ordered_shard_ids:
                raise ValueError(f"dispatch_order duplicates shard: {shard_id}")
            ordered_shard_ids.append(shard_id)

    if ordered_shard_ids and set(ordered_shard_ids) != shard_ids:
        missing = sorted(shard_ids - set(ordered_shard_ids))
        extra = sorted(set(ordered_shard_ids) - shard_ids)
        if missing:
            raise ValueError(f"dispatch_order missing shard: {missing[0]}")
        if extra:
            raise ValueError(f"dispatch_order references unknown shard: {extra[0]}")

    planner_capabilities = {
        output["vertical_capability"] for output in manifest.get("planner_outputs", [])
    }
    for shard in manifest.get("shards", []):
        capability = shard.get("vertical_capability")
        if capability not in planner_capabilities:
            raise ValueError(f"shard has no matching planner output: {shard['shard_id']}")

    for dependency in manifest.get("dependencies", []):
        shard_id = dependency["shard_id"]
        if shard_id not in shard_ids:
            raise ValueError(f"dependency references unknown shard: {shard_id}")
        for depends_on in dependency.get("depends_on", []):
            if depends_on not in shard_ids:
                raise ValueError(f"dependency references unknown shard: {depends_on}")
            if depends_on == shard_id:
                raise ValueError(f"dependency self-cycle: {shard_id}")

    shard_order = {shard_id: index for index, shard_id in enumerate(ordered_shard_ids)}
    for dependency in manifest.get("dependencies", []):
        dependent_index = shard_order.get(dependency["shard_id"])
        if dependent_index is None:
            continue
        for depends_on in dependency.get("depends_on", []):
            depends_on_index = shard_order.get(depends_on)
            if depends_on_index is None:
                continue
            if depends_on_index >= dependent_index:
                raise ValueError(
                    f"dependency must appear before dependent in dispatch_order: {depends_on}"
                )


def validate_implement_contract(
    manifest: dict[str, Any],
    handoffs_by_path: dict[str, dict[str, Any]],
    receipts_by_path: dict[str, dict[str, Any]] | None = None,
) -> None:
    validate_manifest_contract(manifest)
    receipts_by_path = receipts_by_path or {}
    allowed_handoff_paths = {shard["handoff_path"] for shard in manifest.get("shards", [])}
    allowed_receipt_paths = {shard["receipt_path"] for shard in manifest.get("shards", [])}

    for handoff_path in handoffs_by_path:
        if handoff_path not in allowed_handoff_paths:
            raise ValueError(f"unlisted handoff: {handoff_path}")
    for receipt_path in receipts_by_path:
        if receipt_path not in allowed_receipt_paths:
            raise ValueError(f"unlisted receipt: {receipt_path}")

    write_path_owner: list[tuple[str, str]] = []
    capability_owner: list[tuple[str, str]] = []
    implementation_changed_paths: set[str] = set()
    code_review_receipts: list[dict[str, Any]] = []
    for shard in manifest.get("shards", []):
        handoff_path = shard["handoff_path"]
        handoff = handoffs_by_path.get(handoff_path)
        if handoff is None:
            raise ValueError(f"missing handoff: {handoff_path}")

        validate_handoff_contract(handoff)
        if handoff["shard_id"] != shard["shard_id"]:
            raise ValueError(f"handoff shard_id mismatch: {handoff_path}")
        if handoff["task_ids"] != shard["task_ids"]:
            raise ValueError(f"handoff task_ids mismatch: {handoff_path}")
        if handoff["context_digest_path"] != shard["context_digest_path"]:
            raise ValueError(f"handoff context_digest_path mismatch: {handoff_path}")
        if handoff["task_status_update"]["receipt_path"] != shard["receipt_path"]:
            raise ValueError(f"handoff receipt_path mismatch: {handoff_path}")

        for path in handoff.get("allowed_write_paths", []):
            overlap = _find_owned_path_overlap(
                write_path_owner,
                path,
                handoff["shard_id"],
            )
            if overlap is not None:
                previous_path, previous = overlap
                raise ValueError(
                    f"allowed_write_paths overlap: {path} overlaps {previous_path} "
                    f"in {previous} and {handoff['shard_id']}"
                )
            write_path_owner.append((str(path), handoff["shard_id"]))

        for path in handoff.get("capability_boundary", {}).get("owns", []):
            overlap = _find_owned_path_overlap(
                capability_owner,
                path,
                handoff["shard_id"],
            )
            if overlap is not None:
                previous_path, previous = overlap
                raise ValueError(
                    f"capability_boundary.owns overlap: {path} overlaps {previous_path} "
                    f"in {previous} and {handoff['shard_id']}"
                )
            capability_owner.append((str(path), handoff["shard_id"]))

        receipt_path = shard["receipt_path"]
        receipt = receipts_by_path.get(receipt_path)
        if receipt is not None:
            validate_receipt_contract(handoff, receipt, receipt_path)
            if receipt.get("task_type") == "implementation":
                implementation_changed_paths.update(
                    str(path) for path in receipt.get("changed_paths", [])
                )
            elif _handoff_is_code_review_task(handoff):
                code_review_receipts.append(receipt)

    for receipt in code_review_receipts:
        data_side_effect_review = receipt.get("data_side_effect_review", {})
        reviewed_diff_paths = {
            str(path) for path in data_side_effect_review.get("reviewed_diff_paths", [])
        }
        missing_paths = sorted(implementation_changed_paths - reviewed_diff_paths)
        if missing_paths:
            raise ValueError(
                "code review data_side_effect_review must cover implementation "
                f"changed_paths: {missing_paths[0]}"
            )


def validate_handoff_contract(handoff: dict[str, Any]) -> None:
    if handoff.get("context_gaps"):
        raise ValueError("context_gaps must be empty before worker dispatch")

    task_ids = handoff.get("task_ids")
    if not isinstance(task_ids, list) or not task_ids:
        raise ValueError("handoff task_ids must not be empty")
    _duplicate_values(task_ids, context="handoff", label="task_ids")

    receipt_path = handoff["task_status_update"]["receipt_path"]
    _duplicate_values(
        handoff.get("allowed_write_paths", []),
        context="allowed_write_paths",
        label="path",
    )
    allowed_write_paths = list(handoff.get("allowed_write_paths", []))
    if receipt_path not in allowed_write_paths:
        raise ValueError("allowed_write_paths must include receipt_path")

    for path in allowed_write_paths:
        if path.endswith("tasks.md"):
            raise ValueError("allowed_write_paths must not include tasks.md")

    vertical_capability = handoff["vertical_capability"]
    shard_capability = _shard_id_capability(handoff["shard_id"])
    if shard_capability != vertical_capability:
        raise ValueError("shard_id vertical_capability mismatch")

    planner_capability = handoff["planner_outputs"]["vertical_capability"]
    if planner_capability != vertical_capability:
        raise ValueError("planner_outputs vertical_capability mismatch")

    capability_boundary = handoff.get("capability_boundary", {})
    must_not_touch = list(capability_boundary.get("must_not_touch", []))
    conflicting_write_paths = _first_path_overlap(allowed_write_paths, must_not_touch)
    if conflicting_write_paths:
        path, must_not_touch_path = conflicting_write_paths
        raise ValueError(
            "allowed_write_paths must not overlap capability_boundary.must_not_touch: "
            f"{path} overlaps {must_not_touch_path}"
        )

    owns = list(capability_boundary.get("owns", []))
    conflicting_owns = _first_path_overlap(owns, must_not_touch)
    if conflicting_owns:
        path, must_not_touch_path = conflicting_owns
        raise ValueError(
            "capability_boundary.owns must not overlap "
            f"capability_boundary.must_not_touch: {path} overlaps {must_not_touch_path}"
        )

    draft_source = handoff["draft_source"]
    planner_outputs = handoff["planner_outputs"]
    if draft_source["handoff_draft_path"] != planner_outputs["handoff_draft_path"]:
        raise ValueError("draft_source handoff_draft_path mismatch")
    if draft_source["context_digest_draft_path"] != planner_outputs["context_digest_draft_path"]:
        raise ValueError("draft_source context_digest_draft_path mismatch")


def validate_receipt_contract(
    handoff: dict[str, Any],
    receipt: dict[str, Any],
    receipt_path: str,
) -> None:
    expected_receipt_path = handoff["task_status_update"]["receipt_path"]
    if receipt_path != expected_receipt_path:
        raise ValueError("receipt path does not equal task_status_update.receipt_path")

    if "shard_id" in handoff and receipt.get("shard_id") != handoff["shard_id"]:
        raise ValueError("receipt shard_id does not match handoff")

    if receipt.get("task_type") != handoff.get("task_type"):
        raise ValueError("receipt task_type does not match handoff")

    handoff_task_ids = set(handoff.get("task_ids", []))
    if not set(receipt.get("task_ids", [])).issubset(handoff_task_ids):
        raise ValueError("receipt task_ids outside handoff")
    completed_task_ids = set(receipt.get("completed_task_ids", []))
    if not completed_task_ids.issubset(handoff_task_ids):
        raise ValueError("receipt completed_task_ids outside handoff")
    if not completed_task_ids.issubset(set(receipt.get("task_ids", []))):
        raise ValueError("receipt completed_task_ids outside receipt task_ids")
    if completed_task_ids and receipt.get("deferred_validation_todos"):
        raise ValueError(
            "receipt completed_task_ids must be empty when deferred_validation_todos exist"
        )

    if not receipt.get("validation_evidence"):
        raise ValueError("receipt validation_evidence must not be empty")
    if _handoff_has_behavior_contract_context(
        handoff
    ) and not _receipt_references_behavior_evidence(receipt):
        raise ValueError(
            "receipt validation_evidence must reference relevant BDD scenario, "
            "behavior assertion, API contract, or quickstart path"
        )

    for path in receipt.get("changed_paths", []):
        if path not in handoff.get("allowed_write_paths", []):
            raise ValueError(f"receipt changed path outside allowed_write_paths: {path}")

    if _handoff_is_code_review_task(handoff):
        if receipt.get("task_type") != "code_review":
            raise ValueError("code review receipt must declare task_type code_review")

        if not isinstance(receipt.get("review_conclusion"), dict):
            raise ValueError("code review receipt must include review_conclusion")

        review_conclusion = receipt["review_conclusion"]
        if completed_task_ids and review_conclusion.get("status") != "approved":
            raise ValueError(
                "code review receipt completed_task_ids require approved review_conclusion"
            )
        checked_sources = review_conclusion.get("checked_sources")
        if not isinstance(checked_sources, list) or not checked_sources:
            raise ValueError("code review receipt must include checked_sources")
        for source in checked_sources:
            if not _code_review_checked_source_allowed(handoff, source):
                raise ValueError(
                    "code review checked_sources must come from allowed_read_paths "
                    f"or context_digest_path: {source}"
                )

        data_side_effect_review = receipt.get("data_side_effect_review")
        if not isinstance(data_side_effect_review, dict):
            raise ValueError("code review receipt must include data_side_effect_review")

        reviewed_diff_paths = data_side_effect_review.get("reviewed_diff_paths")
        if not isinstance(reviewed_diff_paths, list) or not reviewed_diff_paths:
            raise ValueError("data_side_effect_review must include reviewed_diff_paths")
        for path in reviewed_diff_paths:
            if not _code_review_checked_source_allowed(handoff, path):
                raise ValueError(
                    "data_side_effect_review reviewed_diff_paths must come from "
                    f"allowed_read_paths or context_digest_path: {path}"
                )

        runtime_data_writes_found = data_side_effect_review.get("runtime_data_writes_found")
        if not isinstance(runtime_data_writes_found, bool):
            raise ValueError("data_side_effect_review must include runtime_data_writes_found")

        mutation_findings = data_side_effect_review.get("mutation_findings")
        if not isinstance(mutation_findings, list):
            raise ValueError("data_side_effect_review must include mutation_findings")

        validation_commands = list(handoff.get("validation_commands", []))
        if validation_commands and not _receipt_mentions_any_command(
            receipt,
            validation_commands,
        ):
            raise ValueError(
                "code review validation_evidence must include quickstart/contract "
                "validation command evidence"
            )

        for repair in receipt.get("consistency_repairs", []):
            for path in repair.get("changed_paths", []):
                if path not in handoff.get("allowed_write_paths", []):
                    raise ValueError(
                        "consistency repair changed path outside allowed_write_paths: "
                        f"{path}"
                    )

        review_status = review_conclusion.get("status")
        for finding in review_conclusion.get("findings", []):
            if review_status == "approved" and _unresolved_high_or_critical(finding):
                raise ValueError(
                    "approved code review receipt must not include unresolved "
                    "critical/high findings"
                )

        for finding in mutation_findings:
            if review_status == "approved" and _unresolved_high_or_critical(finding):
                raise ValueError(
                    "approved code review receipt must not include unresolved "
                    "critical/high data side-effect findings"
                )

        e2e_deferred = _receipt_defers_real_e2e(receipt)
        if e2e_deferred and not receipt.get("deferred_validation_todos"):
            raise ValueError(
                "code review receipt must include deferred_validation_todos when real e2e is deferred"
            )
        if e2e_deferred and review_status == "approved":
            raise ValueError("code review receipt cannot be approved when real e2e is deferred")
