# Visual Design Intake Contract

Required visual design intake artifacts and readiness gates. Runtime agents or external intake tools extract traceable, provider-neutral visual facts before downstream SDD workflows project evidence into requirements or visual verification criteria.

Intake does not generate requirements. It preserves all reachable design sources, raw provider evidence, stable source refs, checksums or retrieval metadata, and schema-required visual facts that SDD `specify` can consume accurately.

The machine-readable structures in this contract are enforced by JSON Schemas under `templates/schemas/` before readiness-specific validation runs. Field lists in this document are semantic summaries; the JSON Schemas are canonical for required fields, types, and enums.

This contract is intentionally not a downstream workflow schema. It must not require downstream-owned artifact names, item IDs, code component names, or product semantics that are not directly evidenced by the source. Downstream workflows own any projection from these neutral facts into their local schemas.

## Supported Sources

`design-source-manifest.yaml` must identify the original design source and preserve source integrity.

Required source fields:

- source_type: image|pdf|markdown|figma
- required_fidelity: low|medium|high
- source_files:
  - path:
  - mime_type:
  - byte_size:
  - sha256:
  - role: original|rendered_page|screenshot|asset|markdown
- source_integrity_complete:
- captured_at:
- capture_method:
- page_or_frame_count:
- processed_count:
- extraction_scope:

Source-specific requirements:

- Image sources must record image dimensions, crop/region coverage, OCR status when text is present, and any exported asset refs.
- PDF sources must record original PDF hash, page count, processed page count, rendered page references, and text extraction status.
- Markdown sources must record original Markdown hash, embedded or linked asset refs, heading structure, and design-note parsing status.
- Figma sources must additionally satisfy the Figma provider contract below.

## Fidelity Profile

The required fidelity level controls extraction depth and validation strength.

- Low fidelity: capture screen or page intent, rough layout hierarchy, major content groups, interaction hints, missing information, and source refs.
- Medium fidelity: include low-fidelity requirements plus key spacing, sizing, typography categories, color roles, assets, states, and responsive clues.
- High fidelity: include medium-fidelity requirements plus exact or bounded dimensions, spacing, typography, tokens, asset export contracts, component variants, page/frame coverage, and comparison thresholds.

The intake must record `fidelity_rules_applied: true` and explain any accepted gap.

## Visual Requirements

`visual-requirements.yaml` must normalize extracted visual facts into engineering input. The evidence packet may summarize the same records for human review, but readiness validation uses the standalone machine-readable file.

Visual design intake uses a bounded inference model. Intake may preserve direct observations, rule-backed derived claims, and candidate completions, but it must not smooth missing or contradictory evidence into a confirmed requirement. Every non-observed claim must remain auditable through source refs, inference rules, confidence method, score breakdown, downstream use, and blocking conditions.

Each requirement must include:

- id:
- category: layout|spacing|sizing|typography|color|asset|component|state|interaction|responsive|accessibility|content
- requirement:
- source_refs:
- evidence_type: observed|inferred|candidate|unsupported|missing|out_of_scope
- confidence: low|medium|high
- confidence_rationale:
- engineering_action:
- acceptance_check:
- fidelity_level:

Use `id` as a stable visual evidence ID within this intake package. IDs MUST remain unchanged across recaptures unless the source ref or normalized fact changes. Changed IDs MUST be recorded as a traceability gap. IDs must not be named or formatted as downstream-owned requirement IDs or item IDs.

When evidenced by the source, include provider-neutral optional fields:

- state_or_variant_refs:
- asset_refs:
- constraint_refs:
- proof_refs:
- blockers:

Bounded inference statuses:

- `observed`: source-backed fact from Figma metadata, exported/rendered evidence, preserved design files, OCR/text extraction, or prototype metadata.
- `inferred`: rule-backed derived claim. It is not a source-backed fact. It must use `confidence: high`, `downstream_use: accepted_claim`, and include `inference_rule`, `confidence_method`, `score_breakdown`, and `blocking_conditions`.
- `candidate`: low- or medium-confidence completion. It must use `downstream_use: reference_only` and include `missing_evidence`. Downstream workflows must not promote it into confirmed requirements without additional source evidence.
- `unsupported`: rejected or blocked claim. It must use `downstream_use: blocked`, include `blocker_code`, `reason`, `missing_evidence`, and a matching entry in `blockers`.
- `missing` and `out_of_scope`: explicit gap markers for absent evidence or intentionally excluded surfaces. They must not be rewritten as inferred requirements.

Evidence priority for Figma-derived claims:

1. Component, instance, and variant metadata
2. Prototype reactions
3. Variables, styles, and tokens
4. Auto Layout and constraints
5. Rendered visual evidence
6. Layer naming
7. VLM semantic reading
8. LLM product-pattern inference

Priority does not resolve conflicts by overwrite. When rendered evidence, node geometry, metadata, naming, or prototype data disagree, preserve the conflicting claims and emit a blocker rather than merging them into a single false certainty.

Suitable automatic completions include visual roles, layout relations, spacing token candidates, color token candidates, typography token candidates, asset usage maps, basic interaction targets, and component grouping candidates. Do not auto-complete business rules, permissions, form validation, error copy, loading or disabled or focus states, complex responsive rules, data sources, backend fields, analytics, security, or compliance logic as confirmed specifications without direct source support.

Readiness requires:

- visual_requirements_complete: true
- visual_requirements_count greater than 0 and equal to the number of records in `requirements`
- source_refs_complete: true
- every requirement has the required fields listed above
- missing_or_uncertain items explicitly recorded instead of silently inferred
- inferred items satisfy the bounded inference contract
- candidate items remain `downstream_use: reference_only`
- unsupported items emit blocker codes and do not pass readiness
- no unsupported summary substitution for original source evidence
- no blocker lint errors

## Intake Parity Plan

The extracted requirements must make later downstream comparison possible against the original design source. The intake package records source-side comparison constraints only; downstream workflows own implementation captures, delivery reports, and final approval decisions.

Required parity fields in `visual-requirements.yaml`:

- visual_parity_plan_complete:
- parity_plan:
  - comparison_targets:
  - original_refs:
  - comparison_method: visual_diff|measurement|token_match|asset_match|manual_review
  - thresholds:
  - accepted_exceptions:
  - blocking_difference_categories:

The evidence packet front matter records the `ready_gate` enum only for intake readiness.

## Figma Provider Contract

For `source_type: figma`, `figma-metadata.part-*.xml` must preserve raw `get_metadata` output.

- Do not summarize, rewrite, compress into prose, or replace real nodes with natural language.
- Cover the complete descendant subtree for every selected frame or node.
- Treat truncation as failed evidence.

Each part must be listed with:

- path:
- byte_size:
- sha256:
- root_node_ids:
- node_count:
- truncated:

`figma-metadata.index.yaml` must prove source identity, shard integrity, and selected subtree completeness.

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

Visual design intake is ready only when all conditions pass:

- source_integrity_complete: true
- source_type is image, pdf, markdown, or figma
- required_fidelity is low, medium, or high
- visual_requirements_complete: true
- source_refs_complete: true
- fidelity_rules_applied: true
- inferred claims satisfy the bounded inference contract
- candidate claims remain `downstream_use: reference_only`
- unsupported claims emit blocker codes and block readiness
- visual_parity_plan_complete: true and required parity plan fields are present
- Figma sources also pass raw_metadata_complete, selected_subtree_complete, node_inventory_coverage, and parity_passed
- No blocker lint errors

## Blocker Lint Errors

- VISUAL_SOURCE_MANIFEST_MISSING
- VISUAL_SOURCE_TYPE_UNSUPPORTED
- VISUAL_FIDELITY_LEVEL_UNSUPPORTED
- VISUAL_SOURCE_FILE_MISSING
- VISUAL_SOURCE_HASH_MISMATCH
- VISUAL_SOURCE_INTEGRITY_INCOMPLETE
- VISUAL_REQUIREMENTS_MISSING
- VISUAL_REQUIREMENTS_UNTRACEABLE
- VISUAL_FIDELITY_RULES_MISSING
- VISUAL_PARITY_PLAN_MISSING
- VISUAL_READY_WITHOUT_EVIDENCE
- VISUAL_EVIDENCE_PACKET_MISSING
- VISUAL_BLOCKER_LINT_ERRORS
- VISUAL_INFERENCE_CONTRACT_INVALID
- VISUAL_SCHEMA_INVALID
- FIGMA_RENDER_NODE_MISMATCH
- FIGMA_HIDDEN_LAYER_POLLUTION
- FIGMA_NON_INSTANCE_COMPONENT
- FIGMA_PROTOTYPE_METADATA_MISSING
- FIGMA_UNSUPPORTED_STATE_INFERENCE
- FIGMA_BUSINESS_RULE_UNSUPPORTED
- FIGMA_INTERACTION_CONFLICT
- FIGMA_RESPONSIVE_RULE_MISSING
- FIGMA_LOW_CONFIDENCE_CANDIDATE
- FIGMA_RAW_METADATA_MISSING
- FIGMA_RAW_METADATA_SUMMARY_SUBSTITUTION
- FIGMA_RAW_METADATA_TRUNCATED
- FIGMA_SELECTED_SUBTREE_INCOMPLETE
- FIGMA_METADATA_INDEX_MISSING
- FIGMA_METADATA_PARITY_FAILED
- FIGMA_READY_WITHOUT_COMPLETENESS_PROOF

## Gap Rules

Record a gap instead of passing silently when source evidence is missing, summarized, truncated, incomplete, untraceable, missing fidelity proof, missing visual requirements, missing comparison proof, missing Figma parity proof, missing nodes, duplicate nodes, or marked ready without completeness proof. For dirty Figma sources, use blocker codes for hidden-layer pollution, render/node mismatch, non-instance pseudo-components, missing prototype metadata, unsupported state inference, interaction conflicts, and missing responsive evidence.

## Evidence Packet Metadata

`visual-evidence-packet.md` must start with YAML front matter:

- ready_gate: `PASS|BLOCKED`
- blockers:
- source_ref_count:
- extracted_item_count:
- generated_at:

Human-readable sections may summarize the same records, but readiness metadata is validated from the front matter when present.
