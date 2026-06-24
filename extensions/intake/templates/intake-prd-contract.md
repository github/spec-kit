# PRD Intake Contract

Required PRD intake artifacts and readiness gates. Runtime agents or external intake tools extract source-backed product facts before downstream SDD workflows project them into requirements, scope, acceptance criteria, and clarification items.

Intake does not generate requirements. It preserves all reachable source files, stable source refs, checksums or retrieval metadata, and schema-required source-backed facts that SDD `specify` can consume accurately.

The machine-readable structures in this contract are enforced by JSON Schemas under `templates/schemas/` before readiness-specific validation runs. Field lists in this document are semantic summaries; the JSON Schemas are canonical for required fields, types, and enums.

This contract is intentionally provider-neutral. It must not require downstream-owned requirement IDs, implementation tasks, code component names, or product semantics that are not evidenced by the source.

## Supported Sources

`source-manifest.yaml` must identify the original PRD source and preserve source integrity.

Required source fields:

- source_type: markdown|pdf|doc|url|issue|mixed
- source_files:
  - path:
  - mime_type:
  - byte_size:
  - sha256:
  - role: original|export|attachment|snapshot
- source_integrity_complete:
- captured_at:
- capture_method:
- document_version:
- extraction_scope:

Source-specific requirements:

- Markdown or text PRDs must record heading coverage, linked asset refs, and parsed section coverage.
- PDF or exported docs must record original file hash, page count, processed page count, and text extraction status.
- URL, issue, or epic sources must record stable URL, retrieval timestamp, visible title, author or owner, and snapshot refs; unavailable values must be represented by `snapshot_status` and `integrity_gap_reason`.
- Remote source refs may use a stable URL as `source_files[].path`; when no local snapshot exists, record `retrieval_metadata`, `snapshot_status`, and `integrity_gap_reason` instead of marking source integrity complete.
- Mixed stakeholder notes must record each source separately and mark conflicting or unsupported claims.

## Vertical Scenario Coverage

- Product brief: capture problem, target users, value proposition, scope, non-goals, success signals, and open business questions.
- Feature PRD: capture flows, functional requirements, user stories, edge cases, acceptance criteria, dependencies, rollout or migration notes, and unresolved decisions.
- Executive or strategy doc: capture goals, constraints, metrics, launch criteria, risks, and non-functional expectations without inventing detailed behavior.
- Issue or epic thread: capture requested behavior, comments that change scope, linked bugs, decisions, and stale or contradictory context.
- Mixed source packet: reconcile source precedence, record conflicts, and keep each extracted fact traceable to one or more source refs.

## PRD Intake Facts

`prd-intake.yaml` must normalize source-backed product facts into engineering input.

Required top-level fields:

- prd_intake_complete:
- source_refs_complete:
- extracted_fact_count:
- acceptance_evidence_complete:
- unresolved_ambiguity_marked:
- acceptance_gaps:
- open_questions:
- blocker_lint_errors:
- facts:

Each fact must include:

- id:
- category: goal|non_goal|user|actor|scope|flow|business_rule|data|permission|integration|compliance|acceptance|metric|risk|open_question
- statement:
- source_refs:
- evidence_type: observed|inferred|missing|out_of_scope
- confidence: low|medium|high
- confidence_rationale:
- downstream_hint:
- acceptance_or_validation_signal:

When evidenced by the source, include provider-neutral optional fields:

- priority:
- dependency_refs:
- related_decisions:
- conflict_refs:
- blockers:

## Readiness Gate

PRD intake is ready only when:

- source_integrity_complete: true
- prd_intake_complete: true
- source_refs_complete: true
- extracted_fact_count greater than 0 and equal to the number of records in `facts`
- acceptance evidence or explicit acceptance gaps are recorded
- unresolved ambiguity is marked `[NEEDS CLARIFICATION]`
- no blocker lint errors exist

## Blocker Lint Errors

- PRD_SOURCE_MANIFEST_MISSING
- PRD_SOURCE_TYPE_UNSUPPORTED
- PRD_SOURCE_FILE_MISSING
- PRD_SOURCE_HASH_MISMATCH
- PRD_SOURCE_INTEGRITY_INCOMPLETE
- PRD_INTAKE_MISSING
- PRD_FACTS_UNTRACEABLE
- PRD_ACCEPTANCE_EVIDENCE_MISSING
- PRD_CLARIFICATION_MARKING_MISSING
- PRD_READY_WITHOUT_EVIDENCE
- PRD_EVIDENCE_PACKET_MISSING
- PRD_BLOCKER_LINT_ERRORS
- PRD_SCHEMA_INVALID

## Gap Rules

Record a gap instead of passing silently when source evidence is missing, contradictory, stale, inaccessible, untraceable, or only implied. Product intent may be inferred only when marked `evidence_type: inferred` with confidence and source refs.

## Evidence Packet Metadata

`evidence-packet.md` must start with YAML front matter:

- ready_gate: `PASS|BLOCKED`
- blockers:
- source_ref_count:
- extracted_item_count:
- generated_at:

Human-readable sections may summarize the same records, but readiness metadata is validated from the front matter when present.
