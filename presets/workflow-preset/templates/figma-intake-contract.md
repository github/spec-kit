# Figma Intake Contract

This preset defines the required artifact formats and gates. The runtime agent
or external Figma intake performs extraction.

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

Figma intake is ready only when all conditions pass:

- raw_metadata_complete: true
- node_inventory_coverage: 100%
- parity_passed: true
- No blocker lint errors

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

The preset defines the required artifact formats and gates.

- does not call Figma MCP
- does not fetch Figma URLs
- does not write `figma-metadata.part-*.xml`
- does not run adapter scripts
- does not authenticate to Figma
- does not generate artifact instances
