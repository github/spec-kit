from __future__ import annotations

from typing import Any


def validate_manifest_contract(manifest: dict[str, Any]) -> None:
    shard_ids = {shard["shard_id"] for shard in manifest.get("shards", [])}
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

        receipt_path = shard["receipt_path"]
        receipt = receipts_by_path.get(receipt_path)
        if receipt is not None:
            validate_receipt_contract(handoff, receipt, receipt_path)


def validate_handoff_contract(handoff: dict[str, Any]) -> None:
    receipt_path = handoff["task_status_update"]["receipt_path"]
    allowed_write_paths = set(handoff.get("allowed_write_paths", []))
    if receipt_path not in allowed_write_paths:
        raise ValueError("allowed_write_paths must include receipt_path")

    for path in allowed_write_paths:
        if path.endswith("tasks.md"):
            raise ValueError("allowed_write_paths must not include tasks.md")

    vertical_capability = handoff["vertical_capability"]
    planner_capability = handoff["planner_outputs"]["vertical_capability"]
    if planner_capability != vertical_capability:
        raise ValueError("planner_outputs vertical_capability mismatch")

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

    for path in receipt.get("changed_paths", []):
        if path not in handoff.get("allowed_write_paths", []):
            raise ValueError(f"receipt changed path outside allowed_write_paths: {path}")
