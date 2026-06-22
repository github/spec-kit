# Figma Intake Contract

Required Figma intake artifacts and readiness gates. The runtime agent or
external Figma intake performs extraction before Design Requirement Intake
consumes provider evidence.

## Raw Metadata Shards

`figma-metadata.part-*.xml` must preserve raw get_metadata output.

- Do not summarize, rewrite, compress into prose, or replace real nodes with
  natural language.
- Cover the complete descendant subtree for every selected frame or node.
- Treat truncation as failed evidence.

Each part must be listed with:

- path:
- byte_size:
- sha256:
- root_node_ids:
- node_count:
- truncated:

## Metadata Index Completeness

`figma-metadata.index.yaml` must prove source identity, shard integrity, and
selected subtree completeness.

Required source fields:

- file_url:
- file_key:
- page_id:
- selected_node_ids:
- captured_at:
- mcp_tool: get_metadata
- design_version_or_timestamp:

Required completeness fields:

- selected_subtree_complete:
- raw_metadata_complete:
- expected_root_node_ids:
- captured_root_node_ids:
- missing_root_node_ids:
- gap_count:
- gaps:

## Node Inventory Parity

`figma-node-inventory.yaml` must reconcile inventory with raw metadata.

Required parity fields:

- raw_node_count:
- inventory_node_count:
- excluded_node_count:
- missing_node_count:
- duplicate_node_count:
- truncated_raw_evidence:
- node_inventory_coverage: 100%
- parity_passed: true

Required parity rules:

- inventory_node_count + excluded_node_count + missing_node_count == raw_node_count
- duplicate_node_count == 0
- missing_node_count == 0
- truncated_raw_evidence == false
- parity_passed equals count balance, no duplicates, no missing nodes, and no truncation

## Evidence Readiness Gate

Figma intake is ready only when all conditions pass. This gate is provider source readiness only; it proves raw Figma metadata and node inventory completeness.
It must not decide Visual Fidelity planning readiness, proof sufficiency, accepted exception rules, checklist Gate Status, or checklist Blocking Items.

- raw_metadata_complete: true
- node_inventory_coverage: 100%
- parity_passed: true
- No blocker lint errors

## Normalized Visual Item Matrix

When UI/UX visual fidelity is in scope, the external intake should also write a
normalized `speckit.design.visual_item_matrix.v1` JSON artifact that conforms to
`schemas/speckit.design.visual-item-matrix.v1.schema.json`.
This JSON is derived from the raw metadata shards, metadata index, node
inventory, screenshots, and qualified provider notes. It must not replace raw provider evidence.

The normalized matrix carries Visual Item IDs, source refs, observed variant/state evidence, requirement-level component roles, explicit component use constraints, asset/copy/drawing constraints, screenshot refs, visual proof level, blockers, and `spec.md` requirement targets.
Its blockers are provider evidence blockers, not checklist Blocking Items, and
the matrix must not create a second visual readiness gate.
Explicit constraints such as must-reuse-existing, no-self-draw, or no-new-copy
must include constraint source refs.

## Blocker Lint Errors

- FIGMA_RAW_METADATA_MISSING
- FIGMA_RAW_METADATA_SUMMARY_SUBSTITUTION
- FIGMA_RAW_METADATA_TRUNCATED
- FIGMA_SELECTED_SUBTREE_INCOMPLETE
- FIGMA_METADATA_INDEX_MISSING
- FIGMA_METADATA_PARITY_FAILED
- FIGMA_READY_WITHOUT_COMPLETENESS_PROOF

## Gap Rules

Record a gap instead of passing silently when raw metadata is missing,
summarized, truncated, incomplete, missing parity proof, missing nodes, duplicate
nodes, or marked ready without completeness proof.

## Preset Boundary

Preset boundary:

- must not call Figma MCP
- must not fetch Figma URLs
- must not write `figma-metadata.part-*.xml`
- must not run adapter scripts
- must not authenticate to Figma
- must not generate artifact instances
