from __future__ import annotations

from typing import Any


VALID_EXECUTION_MODES = {"isolated_subagent", "manual_fresh_worker_session"}


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

    handoff_task_ids = set(handoff.get("task_ids", []))
    if not set(receipt.get("task_ids", [])).issubset(handoff_task_ids):
        raise ValueError("receipt task_ids outside handoff")
    if not set(receipt.get("completed_task_ids", [])).issubset(handoff_task_ids):
        raise ValueError("receipt completed_task_ids outside handoff")
    if not set(receipt.get("completed_task_ids", [])).issubset(set(receipt.get("task_ids", []))):
        raise ValueError("receipt completed_task_ids outside receipt task_ids")

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
